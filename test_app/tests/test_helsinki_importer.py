import logging
from pathlib import Path

import pytest

from munigeo.importer.helsinki import HelsinkiImporter
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
MUNI_OCD = "ocd-division/country:fi/kunta:helsinki"


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
        ocd_id=MUNI_OCD,
    )
    return Municipality.objects.create(
        id="helsinki",
        name_fi="Helsinki",
        name_sv="Helsingfors",
        division=division,
    )


@pytest.fixture
def helsinki_importer():
    importer = HelsinkiImporter(options={})
    importer.data_paths = [str(FIXTURES_DIR)]
    return importer


def _get(type_name, **kwargs):
    return AdministrativeDivision.objects.get(type__type=type_name, **kwargs)


@pytest.mark.django_db
def test_import_divisions(helsinki_municipality, helsinki_importer, subtests, caplog):
    muni = helsinki_municipality

    with caplog.at_level(logging.WARNING, logger="helsinki_importer"):
        helsinki_importer.import_divisions()

    # No division types should have been skipped
    import_warnings = [
        r
        for r in caplog.records
        if r.name == "helsinki_importer" and r.levelno >= logging.WARNING
    ]
    assert not import_warnings, (
        f"Import warnings: {[r.message for r in import_warnings]}"
    )

    # 16 division types, 22 features total (6 types have 2 features each)
    imported = AdministrativeDivision.objects.exclude(type__type="muni")
    assert imported.count() == 22

    # Every imported division has a geometry
    assert AdministrativeDivisionGeometry.objects.count() == 22

    # --- Hierarchy: major_district -> district -> sub_district -> small_district ---

    with subtests.test(msg="major_district"):
        major_1 = _get("major_district", origin_id="001")
        assert major_1.name_fi == "Eteläinen"
        assert major_1.name_sv == "Södra"
        assert major_1.parent == muni.division
        assert major_1.municipality == muni
        assert major_1.ocd_id == f"{MUNI_OCD}/suurpiiri:etel\u00e4inen"

        major_2 = _get("major_district", origin_id="002")
        assert major_2.name_fi == "Pohjoinen"
        assert major_2.name_sv == "Norra"
        assert major_2.parent == muni.division
        assert major_2.ocd_id == f"{MUNI_OCD}/suurpiiri:pohjoinen"

    with subtests.test(msg="district"):
        major_1 = _get("major_district", origin_id="001")
        major_2 = _get("major_district", origin_id="002")

        district_1 = _get("district", origin_id="101")
        assert district_1.name_fi == "Kamppi"
        assert district_1.name_sv == "Kampen"
        assert district_1.parent == major_1
        assert district_1.ocd_id == f"{MUNI_OCD}/peruspiiri:kamppi"

        district_2 = _get("district", origin_id="201")
        assert district_2.name_fi == "Malmi"
        assert district_2.name_sv == "Malm"
        assert district_2.parent == major_2
        assert district_2.ocd_id == f"{MUNI_OCD}/peruspiiri:malmi"

    with subtests.test(msg="sub_district"):
        district_1 = _get("district", origin_id="101")
        district_2 = _get("district", origin_id="201")

        sub_1 = _get("sub_district", origin_id="1001")
        assert sub_1.name_fi == "Kamppi 1"
        assert sub_1.name_sv == "Kampen 1"
        assert sub_1.parent == district_1
        assert sub_1.ocd_id == f"{MUNI_OCD}/osa-alue:kamppi_1"

        sub_2 = _get("sub_district", origin_id="2001")
        assert sub_2.name_fi == "Malmi 1"
        assert sub_2.name_sv == "Malm 1"
        assert sub_2.parent == district_2
        assert sub_2.ocd_id == f"{MUNI_OCD}/osa-alue:malmi_1"

    with subtests.test(msg="small_district"):
        sub_1 = _get("sub_district", origin_id="1001")
        sub_2 = _get("sub_district", origin_id="2001")

        small_1 = _get("small_district", origin_id="10001")
        assert small_1.name_fi is None
        assert small_1.parent == sub_1
        assert small_1.ocd_id == f"{sub_1.ocd_id}/pienalue:10001"

        small_2 = _get("small_district", origin_id="20001")
        assert small_2.name_fi is None
        assert small_2.parent == sub_2
        assert small_2.ocd_id == f"{sub_2.ocd_id}/pienalue:20001"

    # --- csv_to_list types ---

    with subtests.test(msg="voting_district"):
        voting_1 = _get("voting_district", origin_id="001A")
        assert voting_1.name_fi == "Äänestysalue 1"
        assert voting_1.service_point_id == "12345,67890"
        assert voting_1.ocd_id == f"{MUNI_OCD}/\u00e4\u00e4nestysalue:001a"

        voting_2 = _get("voting_district", origin_id="002B")
        assert voting_2.name_fi == "Äänestysalue 2"
        assert voting_2.service_point_id == "55555"
        assert voting_2.ocd_id == f"{MUNI_OCD}/\u00e4\u00e4nestysalue:002b"

    with subtests.test(msg="health_station_district"):
        health = _get("health_station_district")
        assert health.origin_id == "ta01"
        assert health.name_fi == "ta01"
        assert health.service_point_id == "11111,22222"
        assert health.ocd_id == f"{MUNI_OCD}/terveysasema-alue:ta01"

    with subtests.test(msg="maternity_clinic_district"):
        maternity = _get("maternity_clinic_district")
        assert maternity.origin_id == "nv01"
        assert maternity.name_fi == "nv01"
        assert maternity.service_point_id == "33333,44444"
        assert maternity.ocd_id == f"{MUNI_OCD}/neuvola-alue:nv01"

    # --- Simple types ---

    with subtests.test(msg="emergency_care_district"):
        emergency = _get("emergency_care_district")
        assert emergency.origin_id == "EC01"
        assert emergency.name_fi == "paiv01"
        assert emergency.ocd_id == f"{MUNI_OCD}/p\u00e4ivystysalue:paiv01"

    with subtests.test(msg="rescue_area"):
        rescue_a = _get("rescue_area")
        assert rescue_a.origin_id == "SP01"
        assert rescue_a.name_fi == "Suojelupiiri 1"
        assert rescue_a.name_sv == "Skyddsdistrikt 1"
        assert rescue_a.ocd_id == f"{MUNI_OCD}/suojelupiiri:suojelupiiri_1"

    with subtests.test(msg="rescue_district"):
        rescue_d = _get("rescue_district")
        assert rescue_d.origin_id == "SL01"
        assert rescue_d.name_fi == "Suojelulohko 1"
        assert rescue_d.name_sv == "Skyddssektion 1"
        assert rescue_d.ocd_id == f"{MUNI_OCD}/suojelulohko:suojelulohko_1"

    with subtests.test(msg="rescue_sub_district"):
        rescue_sd = _get("rescue_sub_district")
        assert rescue_sd.origin_id == "SAL01"
        assert rescue_sd.name_fi == "Suojelualalohko 1"
        assert rescue_sd.name_sv == "Skyddsundersektion 1"
        assert rescue_sd.ocd_id == f"{MUNI_OCD}/suojelualalohko:suojelualalohko_1"

    # --- statistical_district (no_parent_division) ---

    with subtests.test(msg="statistical_district"):
        stat = _get("statistical_district")
        assert stat.origin_id == "091001"
        assert stat.name_fi == "Tilastoalue 1"
        assert stat.parent is None
        assert stat.municipality is None
        assert stat.ocd_id == "ocd-division/country:fi/tilastoalue:091001"

    # --- nature_reserve ---

    with subtests.test(msg="nature_reserve"):
        nature = _get("nature_reserve")
        assert nature.origin_id == "NR01"
        assert nature.name_fi == "Vanhankaupunginlahti"
        assert nature.ocd_id == f"{MUNI_OCD}/luonnonsuojelualue:lsa01"

    # --- Extra fields types ---

    with subtests.test(msg="resident_parking_zone"):
        parking_zone = _get("resident_parking_zone")
        assert parking_zone.origin_id == "RPZ01"
        assert parking_zone.name_fi == "Kamppi"
        assert parking_zone.ocd_id == f"{MUNI_OCD}/asukaspysakointivyohyke:rpz01"

    with subtests.test(msg="parking_area"):
        parking_1 = _get("parking_area", origin_id="PA01")
        assert parking_1.name_fi is None
        assert parking_1.ocd_id == f"{MUNI_OCD}/pysakointipaikka-alue:pa01"

        parking_2 = _get("parking_area", origin_id="PA02")
        assert parking_2.ocd_id == f"{MUNI_OCD}/pysakointipaikka-alue:pa02"

    with subtests.test(msg="parking_payzone"):
        payzone = _get("parking_payzone")
        assert payzone.origin_id == "PPZ01"
        assert payzone.name_fi == "Vyöhyke 1"
        assert payzone.ocd_id == f"{MUNI_OCD}/pysakointimaksuvyohyke:ppz01"
