"""
This management command updates postal code areas from geo-search service.
"""

import logging
import requests
import urllib3
from datetime import datetime
from queue import Empty, Queue
from threading import Thread
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from munigeo.models import PostalCodeArea

PAGE_SIZE = 1000
# Determines how many threads are run simultaneously when importing postal code areas
THREAD_POOL_SIZE = 2
BASE_URL = settings.GEO_SEARCH_LOCATION + "/postal_code_area/"


class Command(BaseCommand):
    help = "Update postal code areas from geo-search service."

    def __init__(self):
        super(Command, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.postal_code_areas_enriched = 0
        self.postal_code_areas_created = 0
        self.start_time = None
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
        self.http = requests.Session()
        self.http.mount("https://", adapter)
        self.http.mount("http://", adapter)
        self.headers = {"Authorization": f"Bearer Api-Key {settings.GEO_SEARCH_API_KEY}"}

    def get_count(self, url):
        try:
            response = self.http.get(url, headers=self.headers)
        except urllib3.exceptions.MaxRetryError as ex:
            self.logger.error(ex)

        count = response.json()["count"]
        return count

    def fetch_page(self, url, page):
        request_url = f"{url}?page={page}&page_size={PAGE_SIZE}"
        try:
            response = self.http.get(request_url, headers=self.headers)
        except urllib3.exceptions.MaxRetryError as ex:
            self.logger.error(ex)

        results = response.json()["results"]
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

    def get_or_create_postal_code_area(self, postal_code, result):
        postal_code_area, created = PostalCodeArea.objects.get_or_create(
            postal_code=postal_code
        )
        if created:
            self.postal_code_areas_created += 1
        name_added = False
        if not postal_code_area.name_fi:
            postal_code_area.name_fi = result["name"]["fi"]
            name_added = True
        if not postal_code_area.name_sv:
            postal_code_area.name_sv = result["name"]["sv"]
            name_added = True
        if name_added:
            self.postal_code_areas_enriched += 1
            postal_code_area.save()
        return postal_code_area

    @transaction.atomic
    def save_page(self, results):
        for result in results:
            self.get_or_create_postal_code_area(result["postal_code"], result)

    def import_postal_code_areas(self):
        # contains the page numbers to fetch
        page_queue = Queue()
        # contains the results fetched
        results_queue = Queue()
        url = BASE_URL

        self.logger.info(f"Fetching postal code areas...")
        count = self.get_count(url)
        max_page = int(count / PAGE_SIZE) + 1
        self.logger.info(
            f"Source data for postal code areas contains {count} items and {max_page} pages(page_size={PAGE_SIZE})."
        )

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
                    self.save_page(results)
                else:
                    raise results

    def handle(self, *args, **options) -> None:
        self.logger.info("Importing postal code areas from geo-search.")
        self.start_time = datetime.now()

        self.import_postal_code_areas()

        end_time = datetime.now()
        duration = end_time - self.start_time
        self.logger.info(
            f"Importing of postal code area from geo_search finished in: {duration}"
        )
        self.logger.info(f"Created {self.postal_code_areas_created} postal_code_areas.")
        self.logger.info(f"Enriched {self.postal_code_areas_enriched} postal_code_areas.")
