from datetime import datetime
from queue import Empty, Queue
from threading import Thread

import requests
import urllib3
from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import Point
from django.db import transaction
from django.utils import timezone
from munigeo.models import Address, PostalCodeArea, Street, Municipality
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from munigeo.importer.base import Importer, register_importer


def get_municipality(name):
    try:
        return Municipality.objects.get(name=name)
    except Municipality.DoesNotExist:
        return None


SOURCE_DATA_SRID = 4326
TARGET_DATA_SRID = 3067
SOURCE_SRS = SpatialReference(SOURCE_DATA_SRID)
TARGET_SRS = SpatialReference(TARGET_DATA_SRID)
PAGE_SIZE = 1000
# Determines how many threads are run simultaneously when importing addresses
THREAD_POOL_SIZE = 2
BASE_URL = settings.GEO_SEARCH_LOCATION + "/address/"

# Contains the municipalities to import
MUNICIPALITIES = {
    18: ("Askola", "Askola"),
    78: ("Hanko", "Hangö"),
    106: ("Hyvinkää", "Hyvinge"),
    149: ("Inkoo", "Ingå"),
    186: ("Järvenpää", "Träskända"),
    224: ("Karkkila", "Högfors"),
    245: ("Kerava", "Kervo"),
    257: ("Kirkkonummi", "Kyrkslätt"),
    407: ("Lapinjärvi", "Lappträsk"),
    434: ("Loviisa", "Lovisa"),
    444: ("Lohja", "Lojo"),
    504: ("Myrskylä", "Mörskom"),
    505: ("Mäntsälä", "Mäntsälä"),
    543: ("Nurmijärvi", "Nurmijärvi"),
    611: ("Pornainen", "Borgnäs"),
    616: ("Pukkila", "Pukkila"),
    638: ("Porvoo", "Borgå"),
    710: ("Raasepori", "Raseborg"),
    753: ("Sipoo", "Sibbo"),
    755: ("Siuntio", "Sjundeå"),
    858: ("Tuusula", "Tusby"),
    927: ("Vihti", "Vichtis"),
}


@register_importer
class UusimaaImporter(Importer):
    name = "uusimaa"
    addresses_imported = 0
    streets_imported = 0
    streets_enriched_with_swedish_translation = 0
    postal_code_areas_enriched = 0
    postal_code_areas_added_to_addresses = 0
    postal_code_areas_created = 0
    duplicate_addresses = 0
    coord_transform = CoordTransform(SOURCE_SRS, TARGET_SRS)

    # Contains the streets of the current municipality, used for caching
    streets_cache = {}
    # Contains the addresses of the current municipality, as the source contains
    # duplicates, the address_cache is used to lookup if the address is already saved.
    address_cache = {}
    postal_code_areas_cache = {}
    # The import source may fail, create import_strategy
    retry_strategy = Retry(
        total=10,
        status_forcelist=[400, 408, 429, 500, 502, 503, 504],
        method_whitelist=[
            "GET",
        ],
        backoff_factor=40,  # 20, 40, 80 , 160, 320, 640, 1280...seconds
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    headers = {"Api-Key": f"{settings.GEO_SEARCH_API_KEY}"}

    def __init__(self, *args, **kwargs):
        super(UusimaaImporter, self).__init__(*args, **kwargs)

    def get_count(self, url):
        try:
            response = self.http.get(url, headers=self.headers)
        except urllib3.exceptions.MaxRetryError as ex:
            self.logger.error(ex)

        count = response.json()["count"]
        return count

    def fetch_page(self, url, page):
        request_url = f"{url}&page={page}"
        try:
            response = self.http.get(request_url, headers=self.headers)
        except urllib3.exceptions.MaxRetryError as ex:
            self.logger.error(ex)

        json = response.json()
        results = json["results"]
        self.logger.info(
            f"Fetched page {page} from {request_url} with {len(results)} items."
        )
        return results

    def worker(self, page_queue, results_queue, url):
        while not page_queue.empty():
            try:
                page = page_queue.get_nowait()
            except Empty:
                break
            try:
                results = self.fetch_page(url, page)
            except Exception as err:
                results_queue.put(err)
            else:
                results_queue.put(results)
            finally:
                page_queue.task_done()

    def get_multilingual_street_names(self, result):
        street_name_fi = result["street"]["name"]["fi"]
        street_name_sv = result["street"]["name"]["sv"]
        # Assign Finnish name to English name, so when searching addresses in English
        # it gives results.
        street_name_en = street_name_fi
        if not street_name_sv:
            street_name_sv = street_name_fi
        return street_name_fi, street_name_sv, street_name_en

    def get_multilingual_full_names(
        self, street_name_fi, street_name_sv, street_name_en, number, number_end, letter
    ):
        """
        Return the multilingual full names used to populate the search columns
        """
        full_name_fi = street_name_fi
        full_name_sv = street_name_sv
        full_name_en = street_name_en
        if number:
            full_name_fi += f" {number}"
            full_name_sv += f" {number}"
            full_name_en += f" {number}"
        if number_end:
            full_name_fi += f"-{number}"
            full_name_sv += f"-{number}"
            full_name_en += f"-{number}"
        if letter:
            full_name_fi += letter
            full_name_sv += letter
            full_name_en += letter
        return full_name_fi, full_name_sv, full_name_en

    def get_location(self, result):
        lat = None
        lon = None
        try:
            lat = result["location"]["coordinates"][0]
            lon = result["location"]["coordinates"][1]
        except KeyError:
            return None
        location = Point(lat, lon, srid=SOURCE_DATA_SRID)
        location.transform(self.coord_transform)
        return location

    def get_or_create_postal_code_area(self, postal_code, result):
        postal_code_area, created = PostalCodeArea.objects.get_or_create(
            postal_code=postal_code
        )
        if created:
            self.postal_code_areas_created += 1
        name_added = False
        if not postal_code_area.name_fi:
            postal_code_area.name_fi = result["postal_code_area"]["name"]["fi"]
            name_added = True
        if not postal_code_area.name_sv:
            postal_code_area.name_sv = result["postal_code_area"]["name"]["sv"]
            name_added = True
        if name_added:
            self.postal_code_areas_enriched + 1
            postal_code_area.save()
        return postal_code_area

    @transaction.atomic
    def save_page(self, results, municipality):
        cache_misses = 0
        cache_hits = 0
        streets = []
        addresses = []
        for result in results:
            postal_code = result["postal_code_area"]["postal_code"]
            if postal_code not in self.postal_code_areas_cache:
                self.postal_code_areas_cache[
                    postal_code
                ] = self.get_or_create_postal_code_area(postal_code, result)

            (
                street_name_fi,
                street_name_sv,
                street_name_en,
            ) = self.get_multilingual_street_names(result)
            if street_name_fi not in self.streets_cache:
                street_entry = {
                    "name": street_name_fi,
                    "name_sv": street_name_sv,
                    "name_en": street_name_en,
                    "municipality": municipality,
                }
                cache_misses += 1
                try:
                    street = Street.objects.get(**street_entry)
                except Street.DoesNotExist:
                    street = Street(**street_entry)
                    streets.append(street)

                self.streets_cache[street_name_fi] = street
            else:
                cache_hits += 1

            location = self.get_location(result)
            if not location:
                continue
            number = result.get("number", "")
            number_end = result.get("number_end", "")
            letter = result.get("letter", "")
            full_name_fi, full_name_sv, full_name_en = self.get_multilingual_full_names(
                street_name_fi,
                street_name_sv,
                street_name_en,
                number,
                number_end,
                letter,
            )

            # Ensures that no duplicates goes to DB, as there are some in the source data
            if full_name_fi not in self.address_cache:
                address = Address(
                    street=self.streets_cache[street_name_fi],
                    number=number,
                    number_end=number_end,
                    letter=letter,
                    location=location,
                    postal_code_area=self.postal_code_areas_cache[postal_code],
                    full_name_fi=full_name_fi,
                    full_name_sv=full_name_sv,
                    full_name_en=full_name_en,
                    municipality=municipality,
                    modified_at=timezone.now()
                )
                addresses.append(address)
                self.address_cache[full_name_fi] = address
            else:
                self.duplicate_addresses += 1
        len_streets = len(streets)
        len_addresses = len(addresses)
        if len_streets > 0:
            Street.objects.bulk_create(streets)
        Address.objects.bulk_create(addresses)

        self.logger.info(
            f"Page saved with {len_addresses} addresses and {len_streets} street."
        )
        self.logger.info(
            f"Page processed with {cache_hits} caches hits and {cache_misses} misses."
        )
        self.addresses_imported += len_addresses
        self.streets_imported += len_streets

    def import_municipality(self, municipality, municipality_code):
        # contains the page numbers to fetch
        page_queue = Queue()
        # contains the results fetched
        results_queue = Queue()
        self.streets_cache = {}
        self.address_cache = {}
        url = f"{BASE_URL}?municipalitycode={municipality_code}&page_size={1}"

        count = self.get_count(url)
        max_page = int(count / PAGE_SIZE) + 1
        self.logger.info(f"Fetching municipality: {municipality}")
        self.logger.info(
            f"Source data for municipality contains {count} items and {max_page} pages(page_size={PAGE_SIZE})."
        )

        url = f"{BASE_URL}?municipalitycode={municipality_code}&page_size={PAGE_SIZE}"
        for pool in range(0, max_page, THREAD_POOL_SIZE):
            threads = []
            # Create threads to the pool
            for page in range(1, THREAD_POOL_SIZE + 1):
                page_number = page + pool
                if page_number <= max_page:
                    page_queue.put(page_number)
                    threads.append(
                        Thread(
                            target=self.worker,
                            args=(page_queue, results_queue, url),
                        )
                    )

            for thread in threads:
                thread.start()
            page_queue.join()
            while threads:
                threads.pop().join()
            while not results_queue.empty():
                results = results_queue.get()
                if not isinstance(results, Exception):
                    self.save_page(results, municipality)
                else:
                    raise results

            end_time = datetime.now()
            duration = end_time - self.start_time
            output_rate = (
                self.streets_imported + self.addresses_imported
            ) / duration.total_seconds()
            self.logger.info(
                f"Duration {duration}, Current (fetching+processing+storing)"
                + f" average rate (addresses&streets/s): {output_rate}"
            )
            self.logger.info(
                f"Addresses imported: {self.addresses_imported}, Streets imported: {self.streets_imported}"
            )

    def import_addresses(self):
        self.logger.info("Importing addresses from geo-search.")

        self.start_time = datetime.now()
        self.postal_code_areas_cache = {}
        self.postal_code_areas_created = 0

        for muni in MUNICIPALITIES.items():
            code = muni[0]
            municipality = get_municipality(muni[1][0])
            if not municipality:
                self.logger.warning(f"Municipality {muni[1][0]} not found.")
                continue
            # Delete all addresses of the municipality, ensures data is up to date.
            Street.objects.filter(municipality_id=municipality).delete()

            self.import_municipality(municipality, code)

        end_time = datetime.now()
        duration = end_time - self.start_time
        output_rate = self.addresses_imported / duration.total_seconds()
        tot_output_rate = (
            self.streets_imported + self.addresses_imported
        ) / duration.total_seconds()
        self.logger.info(
            f"Importing of addresses from geo_search finished in: {duration}"
        )
        self.logger.info(
            "Streets and Addresses where (fetched+processed+stored) at a rate of"
            + f"(addresses&streets/s) {tot_output_rate}"
        )
        self.logger.info(
            f"Found and ignored {self.duplicate_addresses} duplicate adresses."
        )
        self.logger.info(f"Created {self.postal_code_areas_created} postal_code_areas.")
        self.logger.info(
            f"Addresses where fetched and stored at a average rate of (addresses/s): {output_rate}"
        )
        self.logger.info(
            f"THREAD_POOL_SIZE: {THREAD_POOL_SIZE} PAGE_SIZE:{PAGE_SIZE}"
            + f" Fetched {self.addresses_imported} addresses and {self.streets_imported} streets."
        )
