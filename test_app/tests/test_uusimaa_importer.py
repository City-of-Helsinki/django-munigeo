from datetime import datetime

import pytest
import requests_mock as rm

from munigeo.importer.uusimaa import PAGE_SIZE, UusimaaImporter, get_municipality
from munigeo.models import (
    Address,
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
    PostalCodeArea,
    Street,
)

GEO_SEARCH_BASE = "https://geo-search.test/address/"

# --- Sample API response data ---

SAMPLE_RESULTS = [
    {
        "street": {"name": {"fi": "Mannerheimintie", "sv": "Mannerheimvägen"}},
        "location": {"coordinates": [25.01389, 60.17045]},
        "postal_code_area": {
            "postal_code": "06100",
            "name": {"fi": "Porvoo", "sv": "Borgå"},
        },
        "number": "1",
        "number_end": "",
        "letter": "",
    },
    {
        "street": {"name": {"fi": "Mannerheimintie", "sv": "Mannerheimvägen"}},
        "location": {"coordinates": [25.01400, 60.17055]},
        "postal_code_area": {
            "postal_code": "06100",
            "name": {"fi": "Porvoo", "sv": "Borgå"},
        },
        "number": "3",
        "number_end": "",
        "letter": "A",
    },
    {
        "street": {"name": {"fi": "Rihkamatori", "sv": "Krämartorget"}},
        "location": {"coordinates": [25.01500, 60.17100]},
        "postal_code_area": {
            "postal_code": "06150",
            "name": {"fi": "Porvoo", "sv": "Borgå"},
        },
        "number": "2",
        "number_end": "4",
        "letter": "",
    },
]

SAMPLE_RESULT_NO_LOCATION = {
    "street": {"name": {"fi": "Tontunmäki", "sv": "Trollberget"}},
    "location": {},
    "postal_code_area": {
        "postal_code": "06100",
        "name": {"fi": "Porvoo", "sv": "Borgå"},
    },
    "number": "5",
    "number_end": "",
    "letter": "",
}

SAMPLE_RESULT_NO_SV_NAME = {
    "street": {"name": {"fi": "Testikatu", "sv": None}},
    "location": {"coordinates": [25.01600, 60.17200]},
    "postal_code_area": {
        "postal_code": "06100",
        "name": {"fi": "Porvoo", "sv": "Borgå"},
    },
    "number": "7",
    "number_end": "",
    "letter": "",
}

# Duplicate of SAMPLE_RESULTS[0]
SAMPLE_RESULT_DUPLICATE = {
    "street": {"name": {"fi": "Mannerheimintie", "sv": "Mannerheimvägen"}},
    "location": {"coordinates": [25.01389, 60.17045]},
    "postal_code_area": {
        "postal_code": "06100",
        "name": {"fi": "Porvoo", "sv": "Borgå"},
    },
    "number": "1",
    "number_end": "",
    "letter": "",
}


# --- Fixtures ---

PORVOO_CODE = 638


@pytest.fixture
def muni_type():
    return AdministrativeDivisionType.objects.create(type="muni", name="Municipality")


@pytest.fixture
def porvoo(muni_type):
    division = AdministrativeDivision.objects.create(
        type=muni_type,
        origin_id="638",
        name_fi="Porvoo",
        name_sv="Borgå",
        ocd_id="ocd-division/country:fi/kunta:porvoo",
    )
    return Municipality.objects.create(
        id="porvoo",
        code="638",
        name_fi="Porvoo",
        name_sv="Borgå",
        division=division,
    )


@pytest.fixture
def uusimaa_importer():
    importer = UusimaaImporter(options={})
    # Reset class-level mutable state
    importer.streets_cache = {}
    importer.address_cache = {}
    importer.postal_code_areas_cache = {}
    importer.addresses_imported = 0
    importer.streets_imported = 0
    importer.duplicate_addresses = 0
    importer.postal_code_areas_created = 0
    importer.postal_code_areas_enriched = 0
    # Normally set by import_addresses(); needed by import_municipality()
    importer.start_time = datetime.now()
    return importer


def _mock_geo_search(adapter, municipality_code, results):
    """Register count and page responses for a municipality on a requests_mock adapter."""
    count = len(results)
    # Count URL (page_size=1)
    adapter.get(
        f"{GEO_SEARCH_BASE}?municipalitycode={municipality_code}&page_size=1",
        json={"count": count},
    )
    # Paginated URL - put all results on page 1
    adapter.get(
        f"{GEO_SEARCH_BASE}?municipalitycode={municipality_code}&page_size={PAGE_SIZE}&page=1",
        json={"results": results},
    )


# --- Tests ---


@pytest.mark.django_db
def test_import_municipality_creates_streets_and_addresses(
    porvoo, uusimaa_importer, subtests
):
    with rm.Mocker() as m:
        _mock_geo_search(m, PORVOO_CODE, SAMPLE_RESULTS)
        uusimaa_importer.import_municipality(porvoo, PORVOO_CODE)

    assert Street.objects.count() == 2
    assert Address.objects.count() == 3

    with subtests.test(msg="Mannerheimintie street"):
        street = Street.objects.get(name_fi="Mannerheimintie")
        assert street.name_sv == "Mannerheimvägen"
        assert street.name_en == "Mannerheimintie"  # EN = FI
        assert street.municipality == porvoo

    with subtests.test(msg="Rihkamatori street"):
        street = Street.objects.get(name_fi="Rihkamatori")
        assert street.name_sv == "Krämartorget"

    with subtests.test(msg="Address Mannerheimintie 1"):
        addr = Address.objects.get(
            street__name_fi="Mannerheimintie", number="1", letter=""
        )
        assert addr.municipality == porvoo
        assert addr.full_name_fi == "Mannerheimintie 1"
        assert addr.full_name_sv == "Mannerheimvägen 1"
        assert addr.location is not None
        assert addr.location.srid == 3067

    with subtests.test(msg="Address Mannerheimintie 3A"):
        addr = Address.objects.get(
            street__name_fi="Mannerheimintie", number="3", letter="A"
        )
        assert addr.full_name_fi == "Mannerheimintie 3A"
        assert addr.full_name_sv == "Mannerheimvägen 3A"

    with subtests.test(msg="Address Rihkamatori 2-4 (number_end)"):
        addr = Address.objects.get(street__name_fi="Rihkamatori", number="2")
        assert addr.number_end == "4"
        # number_end appends "-{number}" to full name
        assert addr.full_name_fi == "Rihkamatori 2-2"


@pytest.mark.django_db
def test_import_creates_postal_code_areas(porvoo, uusimaa_importer):
    with rm.Mocker() as m:
        _mock_geo_search(m, PORVOO_CODE, SAMPLE_RESULTS)
        uusimaa_importer.import_municipality(porvoo, PORVOO_CODE)

    assert PostalCodeArea.objects.count() == 2

    pca = PostalCodeArea.objects.get(postal_code="06100")
    assert pca.name_fi == "Porvoo"
    assert pca.name_sv == "Borgå"

    pca2 = PostalCodeArea.objects.get(postal_code="06150")
    assert pca2.name_fi == "Porvoo"


@pytest.mark.django_db
def test_postal_code_area_linked_to_address(porvoo, uusimaa_importer):
    with rm.Mocker() as m:
        _mock_geo_search(m, PORVOO_CODE, SAMPLE_RESULTS)
        uusimaa_importer.import_municipality(porvoo, PORVOO_CODE)

    addr = Address.objects.get(street__name_fi="Mannerheimintie", number="1")
    assert addr.postal_code_area is not None
    assert addr.postal_code_area.postal_code == "06100"

    addr2 = Address.objects.get(street__name_fi="Rihkamatori", number="2")
    assert addr2.postal_code_area.postal_code == "06150"


@pytest.mark.django_db
def test_duplicate_addresses_are_skipped(porvoo, uusimaa_importer):
    results = SAMPLE_RESULTS + [SAMPLE_RESULT_DUPLICATE]

    with rm.Mocker() as m:
        _mock_geo_search(m, PORVOO_CODE, results)
        uusimaa_importer.import_municipality(porvoo, PORVOO_CODE)

    # Duplicate has same street + number + letter as SAMPLE_RESULTS[0]
    assert Address.objects.count() == 3
    assert uusimaa_importer.duplicate_addresses == 1


@pytest.mark.django_db
def test_missing_location_skips_address(porvoo, uusimaa_importer):
    results = [SAMPLE_RESULT_NO_LOCATION]

    with rm.Mocker() as m:
        _mock_geo_search(m, PORVOO_CODE, results)
        uusimaa_importer.import_municipality(porvoo, PORVOO_CODE)

    # Street is still created, but no address (location missing)
    assert Street.objects.count() == 1
    assert Address.objects.count() == 0


@pytest.mark.django_db
def test_missing_sv_name_falls_back_to_fi(porvoo, uusimaa_importer):
    results = [SAMPLE_RESULT_NO_SV_NAME]

    with rm.Mocker() as m:
        _mock_geo_search(m, PORVOO_CODE, results)
        uusimaa_importer.import_municipality(porvoo, PORVOO_CODE)

    street = Street.objects.get(name_fi="Testikatu")
    assert street.name_sv == "Testikatu"  # Falls back to FI


@pytest.mark.usefixtures("muni_type")
@pytest.mark.django_db
def test_missing_municipality_is_skipped(uusimaa_importer, caplog):
    """import_addresses skips municipalities not in DB."""
    # Don't create any Municipality objects - all should be skipped
    with rm.Mocker() as m:
        uusimaa_importer.import_addresses()

    assert Street.objects.count() == 0
    assert Address.objects.count() == 0
    assert "not found" in caplog.text


@pytest.mark.django_db
def test_import_is_idempotent(porvoo, uusimaa_importer):
    """Running import twice does not duplicate data (streets are deleted first)."""
    with rm.Mocker() as m:
        _mock_geo_search(m, PORVOO_CODE, SAMPLE_RESULTS)
        uusimaa_importer.import_municipality(porvoo, PORVOO_CODE)

    assert Street.objects.count() == 2
    assert Address.objects.count() == 3

    # Reset caches (normally done in import_municipality, but we need to
    # simulate what import_addresses does: delete streets then re-import)
    Street.objects.filter(municipality_id=porvoo).delete()

    # Reset importer state for second run
    uusimaa_importer.streets_cache = {}
    uusimaa_importer.address_cache = {}
    uusimaa_importer.addresses_imported = 0
    uusimaa_importer.streets_imported = 0

    with rm.Mocker() as m:
        _mock_geo_search(m, PORVOO_CODE, SAMPLE_RESULTS)
        uusimaa_importer.import_municipality(porvoo, PORVOO_CODE)

    assert Street.objects.count() == 2
    assert Address.objects.count() == 3


@pytest.mark.django_db
def test_import_with_two_threads_multiple_pages(porvoo, uusimaa_importer):
    """Test that threaded fetching with 2 pages works correctly."""
    page1_results = SAMPLE_RESULTS[:2]
    page2_results = [SAMPLE_RESULTS[2]]

    # We need count > PAGE_SIZE to trigger multiple pages.
    # Set count to PAGE_SIZE + 1 so max_page = 2.
    count = PAGE_SIZE + 1

    with rm.Mocker() as m:
        m.get(
            f"{GEO_SEARCH_BASE}?municipalitycode={PORVOO_CODE}&page_size=1",
            json={"count": count},
        )
        m.get(
            f"{GEO_SEARCH_BASE}?municipalitycode={PORVOO_CODE}&page_size={PAGE_SIZE}&page=1",
            json={"results": page1_results},
        )
        m.get(
            f"{GEO_SEARCH_BASE}?municipalitycode={PORVOO_CODE}&page_size={PAGE_SIZE}&page=2",
            json={"results": page2_results},
        )
        uusimaa_importer.import_municipality(porvoo, PORVOO_CODE)

    assert Street.objects.count() == 2
    assert Address.objects.count() == 3
    assert uusimaa_importer.addresses_imported == 3
    assert uusimaa_importer.streets_imported == 2


@pytest.mark.django_db
def test_get_municipality_returns_none_for_unknown():
    assert get_municipality("Nonexistent") is None


@pytest.mark.django_db
def test_get_municipality_returns_municipality(porvoo):
    result = get_municipality("Porvoo")
    assert result == porvoo


@pytest.mark.django_db
def test_coord_transform_srid(porvoo, uusimaa_importer):
    """Addresses are stored in SRID 3067 after transform from 4326."""
    with rm.Mocker() as m:
        _mock_geo_search(m, PORVOO_CODE, SAMPLE_RESULTS[:1])
        uusimaa_importer.import_municipality(porvoo, PORVOO_CODE)

    addr = Address.objects.first()
    assert addr.location.srid == 3067
    assert addr.location.x == pytest.approx(389800.88759799924)
    assert addr.location.y == pytest.approx(6672051.238268088)
