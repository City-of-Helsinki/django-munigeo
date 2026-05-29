import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from django.contrib.gis.gdal import DataSource

from munigeo.importer.helsinki import HelsinkiImporter
from munigeo.models import (
    Address,
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
    PostalCodeArea,
    Street,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
ADDRESS_FIXTURE = str(FIXTURES_DIR / "fi" / "helsinki" / "addresses.geojson")


@pytest.fixture
def helsinki_municipality():
    muni_type = AdministrativeDivisionType.objects.create(
        type="muni", name="Municipality"
    )
    division = AdministrativeDivision.objects.create(
        type=muni_type,
        origin_id="91",
        name_fi="Helsinki",
        name_sv="Helsingfors",
        ocd_id="ocd-division/country:fi/kunta:helsinki",
    )
    return Municipality.objects.create(
        id="helsinki",
        code="091",
        name_fi="Helsinki",
        name_sv="Helsingfors",
        division=division,
    )


@pytest.fixture
def helsinki_importer(settings):
    settings.IMPORT_DATA_PATH = str(FIXTURES_DIR)
    return HelsinkiImporter(options={})


def _patch_datasource():
    """Patch DataSource so the WFS URL is replaced with the local fixture."""
    original_ds = DataSource

    def patched_ds(url, *args, **kwargs):
        if isinstance(url, str) and url.startswith("WFS:"):
            return original_ds(ADDRESS_FIXTURE)
        return original_ds(url, *args, **kwargs)

    return patch(
        "munigeo.importer.helsinki.DataSource",
        side_effect=patched_ds,
    )


@pytest.mark.django_db
def test_import_addresses_creates_streets(helsinki_municipality, helsinki_importer):
    """Streets are created from address data."""
    with _patch_datasource():
        helsinki_importer.import_addresses()

    streets = Street.objects.filter(municipality=helsinki_municipality)
    assert streets.count() == 2

    mannerheimintie = streets.get(name_fi="Mannerheimintie")
    assert mannerheimintie.name_sv == "Mannerheimvägen"

    aleksanterinkatu = streets.get(name_fi="Aleksanterinkatu")
    assert aleksanterinkatu.name_sv == "Alexandersgatan"


@pytest.mark.django_db
def test_import_addresses_creates_addresses(helsinki_municipality, helsinki_importer):
    """Valid addresses are created with correct fields."""
    with _patch_datasource():
        helsinki_importer.import_addresses()

    # 6 features total, but osoitenumero=0 and osoitenumero=null are rejected
    addresses = Address.objects.all()
    assert addresses.count() == 4

    addr = Address.objects.get(street__name_fi="Mannerheimintie", number="1", letter="")
    assert addr.full_name_fi == "Mannerheimintie 1"
    assert addr.full_name_sv == "Mannerheimvägen 1"
    assert addr.municipality == helsinki_municipality
    assert addr.location is not None


@pytest.mark.django_db
def test_import_addresses_number_end(helsinki_municipality, helsinki_importer):
    """Address with number_end is formatted correctly."""
    with _patch_datasource():
        helsinki_importer.import_addresses()

    addr = Address.objects.get(
        street__name_fi="Mannerheimintie", number="10", number_end="12"
    )
    assert addr.full_name_fi == "Mannerheimintie 10-12"
    assert addr.full_name_sv == "Mannerheimvägen 10-12"


@pytest.mark.django_db
def test_import_addresses_letter(helsinki_municipality, helsinki_importer):
    """Address with letter is formatted correctly."""
    with _patch_datasource():
        helsinki_importer.import_addresses()

    addr = Address.objects.get(
        street__name_fi="Mannerheimintie", number="5", letter="A"
    )
    assert addr.full_name_fi == "Mannerheimintie 5 A"
    assert addr.full_name_sv == "Mannerheimvägen 5 A"


@pytest.mark.django_db
def test_import_addresses_creates_postal_code_areas(
    helsinki_municipality, helsinki_importer
):
    """PostalCodeArea objects are created and linked to addresses."""
    with _patch_datasource():
        helsinki_importer.import_addresses()

    assert PostalCodeArea.objects.count() == 2
    assert PostalCodeArea.objects.filter(postal_code="00100").exists()
    assert PostalCodeArea.objects.filter(postal_code="00170").exists()

    addr = Address.objects.get(street__name_fi="Aleksanterinkatu", number="1")
    assert addr.postal_code_area.postal_code == "00170"


@pytest.mark.django_db
def test_import_addresses_rejects_invalid_numbers(
    helsinki_municipality, helsinki_importer, caplog
):
    """Addresses with osoitenumero=0 or null are skipped."""
    with (
        _patch_datasource(),
        caplog.at_level(logging.DEBUG, logger="helsinki_importer"),
    ):
        helsinki_importer.import_addresses()

    # 6 features, 2 rejected (number=0, number=null), 4 created
    assert Address.objects.count() == 4


@pytest.mark.django_db
def test_import_addresses_idempotent(helsinki_municipality, helsinki_importer):
    """Running import twice does not duplicate data."""
    with _patch_datasource():
        helsinki_importer.import_addresses()

    with _patch_datasource():
        helsinki_importer.import_addresses()

    assert Address.objects.count() == 4
    assert Street.objects.count() == 2
