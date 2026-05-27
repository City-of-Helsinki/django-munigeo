"""
Test the data migration in 0010 that populates Address.municipality
from Address.street.municipality for existing rows.

When 0010 adds the non-nullable municipality FK to Address, existing rows
must get their municipality value derived from their street's municipality.
"""

import pytest
from django.contrib.gis.geos import Point
from django.utils import timezone

PRE_STATE = ("munigeo", "0009_alter_administrativedivision_name_en_and_more")


@pytest.mark.django_db(transaction=True)
def test_address_municipality_populated_from_street(migration_executor):
    """Existing Address rows get municipality from their street."""
    executor, latest = migration_executor

    state = executor.migrate([PRE_STATE])
    executor.loader.build_graph()
    apps = state.apps

    # Create test data using historical models (pre-0010: no municipality on Address)
    DivisionType = apps.get_model("munigeo", "AdministrativeDivisionType")
    Division = apps.get_model("munigeo", "AdministrativeDivision")
    Municipality = apps.get_model("munigeo", "Municipality")
    Street = apps.get_model("munigeo", "Street")
    Address = apps.get_model("munigeo", "Address")

    div_type = DivisionType.objects.create(type="muni", name="Municipality")
    div = Division.objects.create(
        type=div_type,
        name_fi="Helsinki",
        origin_id="91",
        ocd_id="ocd-division/country:fi/kunta:helsinki",
        lft=1,
        rght=2,
        tree_id=1,
        level=0,
    )
    muni = Municipality.objects.create(
        id="helsinki", name_fi="Helsinki", name_sv="Helsingfors", division=div
    )

    street = Street.objects.create(
        name_fi="Mannerheimintie",
        name_sv="Mannerheimvägen",
        municipality=muni,
    )

    # At migration 0009, Address has no municipality field
    addr1 = Address.objects.create(
        street=street,
        number="1",
        number_end="",
        letter="",
        location=Point(385000, 6672000, srid=3067).ewkt,
        modified_at=timezone.now(),
    )
    addr2 = Address.objects.create(
        street=street,
        number="3",
        number_end="",
        letter="A",
        location=Point(385100, 6672100, srid=3067).ewkt,
        modified_at=timezone.now(),
    )

    # Apply 0010 - this should populate municipality from street
    state = executor.migrate([latest])
    apps = state.apps

    # Verify using post-migration model
    Address = apps.get_model("munigeo", "Address")

    addr1_after = Address.objects.get(pk=addr1.pk)
    assert addr1_after.municipality_id == "helsinki", (
        f"Expected municipality_id='helsinki', got {addr1_after.municipality_id!r}"
    )

    addr2_after = Address.objects.get(pk=addr2.pk)
    assert addr2_after.municipality_id == "helsinki", (
        f"Expected municipality_id='helsinki', got {addr2_after.municipality_id!r}"
    )


@pytest.mark.django_db(transaction=True)
def test_address_municipality_multiple_municipalities(migration_executor):
    """Addresses on streets in different municipalities get correct values."""
    executor, latest = migration_executor

    state = executor.migrate([PRE_STATE])
    executor.loader.build_graph()
    apps = state.apps

    DivisionType = apps.get_model("munigeo", "AdministrativeDivisionType")
    Division = apps.get_model("munigeo", "AdministrativeDivision")
    Municipality = apps.get_model("munigeo", "Municipality")
    Street = apps.get_model("munigeo", "Street")
    Address = apps.get_model("munigeo", "Address")

    div_type = DivisionType.objects.create(type="muni", name="Municipality")

    div_hki = Division.objects.create(
        type=div_type,
        name_fi="Helsinki",
        origin_id="91",
        ocd_id="ocd-division/country:fi/kunta:helsinki",
        lft=1,
        rght=2,
        tree_id=1,
        level=0,
    )
    div_espoo = Division.objects.create(
        type=div_type,
        name_fi="Espoo",
        origin_id="49",
        ocd_id="ocd-division/country:fi/kunta:espoo",
        lft=3,
        rght=4,
        tree_id=2,
        level=0,
    )

    muni_hki = Municipality.objects.create(
        id="helsinki", name_fi="Helsinki", division=div_hki
    )
    muni_espoo = Municipality.objects.create(
        id="espoo", name_fi="Espoo", division=div_espoo
    )

    street_hki = Street.objects.create(name_fi="Mannerheimintie", municipality=muni_hki)
    street_espoo = Street.objects.create(
        name_fi="Leppävaarankatu", municipality=muni_espoo
    )

    addr_hki = Address.objects.create(
        street=street_hki,
        number="1",
        number_end="",
        letter="",
        location=Point(385000, 6672000, srid=3067).ewkt,
        modified_at=timezone.now(),
    )
    addr_espoo = Address.objects.create(
        street=street_espoo,
        number="5",
        number_end="",
        letter="",
        location=Point(370000, 6680000, srid=3067).ewkt,
        modified_at=timezone.now(),
    )

    # Apply 0010
    state = executor.migrate([latest])
    apps = state.apps

    Address = apps.get_model("munigeo", "Address")

    addr_hki_after = Address.objects.get(pk=addr_hki.pk)
    assert addr_hki_after.municipality_id == "helsinki"

    addr_espoo_after = Address.objects.get(pk=addr_espoo.pk)
    assert addr_espoo_after.municipality_id == "espoo"
