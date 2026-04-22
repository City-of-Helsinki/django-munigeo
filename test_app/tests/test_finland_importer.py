from pathlib import Path

import pytest

from munigeo.importer.finland import FinlandImporter
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _name(obj, lang):
    """Read a parler-translated name for the given language code."""
    return obj.safe_translation_getter("name", language_code=lang)


@pytest.fixture
def finland_importer():
    importer = FinlandImporter(options={})
    importer.data_paths = [str(FIXTURES_DIR)]
    return importer


@pytest.mark.django_db
def test_import_municipalities(finland_importer, subtests):
    finland_importer.import_municipalities()

    # Only 4thOrder features are imported (the 1stOrder country feature is skipped)
    assert AdministrativeDivision.objects.count() == 2
    assert Municipality.objects.count() == 2
    assert AdministrativeDivisionGeometry.objects.count() == 2

    # AdministrativeDivisionType is auto-created
    muni_type = AdministrativeDivisionType.objects.get(type="muni")
    assert muni_type.name == "Municipality"

    # --- Helsinki ---

    with subtests.test(msg="Helsinki"):
        hki_div = AdministrativeDivision.objects.get(origin_id="91")
        assert _name(hki_div, "fi") == "Helsinki"
        assert _name(hki_div, "sv") == "Helsingfors"
        assert hki_div.type == muni_type
        assert hki_div.ocd_id == "ocd-division/country:fi/kunta:helsinki"

        hki = Municipality.objects.get(division=hki_div)
        assert _name(hki, "fi") == "Helsinki"
        assert _name(hki, "sv") == "Helsingfors"
        assert hki.id == "helsinki"

        assert AdministrativeDivisionGeometry.objects.filter(division=hki_div).exists()

    # --- Espoo ---

    with subtests.test(msg="Espoo"):
        espoo_div = AdministrativeDivision.objects.get(origin_id="49")
        assert _name(espoo_div, "fi") == "Espoo"
        assert _name(espoo_div, "sv") == "Esbo"
        assert espoo_div.ocd_id == "ocd-division/country:fi/kunta:espoo"

        espoo = Municipality.objects.get(division=espoo_div)
        assert _name(espoo, "fi") == "Espoo"
        assert _name(espoo, "sv") == "Esbo"
        assert espoo.id == "espoo"


@pytest.mark.django_db
def test_import_municipalities_is_idempotent(finland_importer):
    """Running import twice does not duplicate data."""
    finland_importer.import_municipalities()
    finland_importer.import_municipalities()

    assert AdministrativeDivision.objects.count() == 2
    assert Municipality.objects.count() == 2
