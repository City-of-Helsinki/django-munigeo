import logging
from pathlib import Path

import pytest

from munigeo.importer.hsy import HsyImporter
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
HELSINKI_OCD = "ocd-division/country:fi/kunta:helsinki"
ESPOO_OCD = "ocd-division/country:fi/kunta:espoo"
VANTAA_OCD = "ocd-division/country:fi/kunta:vantaa"


@pytest.fixture
def municipalities():
    muni_type = AdministrativeDivisionType.objects.create(
        type="muni", name="Municipality"
    )

    hki_div = AdministrativeDivision.objects.create(
        type=muni_type,
        origin_id="91",
        name_fi="Helsinki",
        name_sv="Helsingfors",
        ocd_id=HELSINKI_OCD,
    )
    helsinki = Municipality.objects.create(
        id="helsinki",
        code="091",
        name_fi="Helsinki",
        name_sv="Helsingfors",
        division=hki_div,
    )

    espoo_div = AdministrativeDivision.objects.create(
        type=muni_type,
        origin_id="49",
        name_fi="Espoo",
        name_sv="Esbo",
        ocd_id=ESPOO_OCD,
    )
    espoo = Municipality.objects.create(
        id="espoo",
        code="049",
        name_fi="Espoo",
        name_sv="Esbo",
        division=espoo_div,
    )

    vantaa_div = AdministrativeDivision.objects.create(
        type=muni_type,
        origin_id="92",
        name_fi="Vantaa",
        name_sv="Vanda",
        ocd_id=VANTAA_OCD,
    )
    vantaa = Municipality.objects.create(
        id="vantaa",
        code="092",
        name_fi="Vantaa",
        name_sv="Vanda",
        division=vantaa_div,
    )

    return {"helsinki": helsinki, "espoo": espoo, "vantaa": vantaa}


@pytest.fixture
def hsy_importer(settings):
    settings.IMPORT_DATA_PATH = str(FIXTURES_DIR)
    return HsyImporter(options={})


def _filter(type_name):
    return AdministrativeDivision.objects.filter(type__type=type_name)


@pytest.mark.django_db
def test_import_divisions(municipalities, hsy_importer, subtests, caplog):
    hki = municipalities["helsinki"]
    espoo = municipalities["espoo"]
    vantaa = municipalities["vantaa"]

    with caplog.at_level(logging.WARNING, logger="import"):
        hsy_importer.import_divisions()

    # No division types should have been skipped
    import_warnings = [
        r for r in caplog.records if r.name == "import" and r.levelno >= logging.WARNING
    ]
    assert not import_warnings, (
        f"Import warnings: {[r.message for r in import_warnings]}"
    )

    # 4 types x 2 features = 8 divisions
    imported = AdministrativeDivision.objects.exclude(type__type="muni")
    assert imported.count() == 8

    # Every imported division has a geometry
    assert AdministrativeDivisionGeometry.objects.count() == 8

    # --- neighborhood: routes to correct municipality, bilingual names ---

    with subtests.test(msg="neighborhood"):
        neighborhoods = _filter("neighborhood")
        assert neighborhoods.count() == 2

        kruununhaka = neighborhoods.get(origin_id="91-091001")
        assert kruununhaka.name_fi == "Kruununhaka"
        assert kruununhaka.name_sv == "Kronohagen"
        assert kruununhaka.municipality == hki
        assert kruununhaka.parent == hki.division
        assert kruununhaka.ocd_id == f"{HELSINKI_OCD}/kaupunginosa:091001"

        tapiola = neighborhoods.get(origin_id="49-049002")
        assert tapiola.name_fi == "Tapiola"
        assert tapiola.name_sv == "Hagalund"
        assert tapiola.municipality == espoo
        assert tapiola.parent == espoo.division
        assert tapiola.ocd_id == f"{ESPOO_OCD}/kaupunginosa:049002"

    # --- postcode_area: name derived from postal code ---

    with subtests.test(msg="postcode_area"):
        postcodes = _filter("postcode_area")
        assert postcodes.count() == 2

        p00100 = postcodes.get(origin_id="91-00100")
        assert p00100.name_fi == "00100"
        assert p00100.municipality == hki
        assert p00100.ocd_id == f"{HELSINKI_OCD}/postinumero:00100"

        p02100 = postcodes.get(origin_id="49-02100")
        assert p02100.name_fi == "02100"
        assert p02100.municipality == espoo
        assert p02100.ocd_id == f"{ESPOO_OCD}/postinumero:02100"

    # --- major_district: ocd_id derived from name ---

    with subtests.test(msg="major_district"):
        majors = _filter("major_district")
        assert majors.count() == 2

        keskinen = majors.get(origin_id="91-MD01")
        assert keskinen.name_fi == "Keskinen"
        assert keskinen.municipality == hki
        assert keskinen.ocd_id == f"{HELSINKI_OCD}/suurpiiri:keskinen"

        tikkurila = majors.get(origin_id="92-MD02")
        assert tikkurila.name_fi == "Tikkurila"
        assert tikkurila.municipality == vantaa
        assert tikkurila.ocd_id == f"{VANTAA_OCD}/suurpiiri:tikkurila"

    # --- sub_district: ocd_id derived from name ---

    with subtests.test(msg="sub_district"):
        subs = _filter("sub_district")
        assert subs.count() == 2

        kluuvi = subs.get(origin_id="91-SD01")
        assert kluuvi.name_fi == "Kluuvi"
        assert kluuvi.municipality == hki
        assert kluuvi.ocd_id == f"{HELSINKI_OCD}/osa-alue:kluuvi"

        hiekkaharju = subs.get(origin_id="92-SD02")
        assert hiekkaharju.name_fi == "Hiekkaharju"
        assert hiekkaharju.municipality == vantaa
        assert hiekkaharju.ocd_id == f"{VANTAA_OCD}/osa-alue:hiekkaharju"
