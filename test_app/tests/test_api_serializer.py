import pytest

from munigeo.api import (
    AdministrativeDivisionSerializer,
    MunicipalitySerializer,
    PostalCodeSerializer,
    StreetSerializer,
)
from munigeo.models import Municipality, PostalCodeArea, Street
from test_app.tests.factories import (
    AdministrativeDivisionFactory,
    AdministrativeDivisionTypeFactory,
)


@pytest.fixture
def division():
    return AdministrativeDivisionFactory(
        type=AdministrativeDivisionTypeFactory(),
        name_fi="Helsinki",
        name_sv="Helsingfors",
        name_en="Helsinki",
    )


def test_municipality_serializer_absent_translations_omitted():
    muni = Municipality(name_fi="Helsinki")
    data = MunicipalitySerializer(muni).data
    assert data["name"] == {"fi": "Helsinki"}


def test_municipality_serializer_no_translations_returns_null():
    muni = Municipality()
    data = MunicipalitySerializer(muni).data
    assert data["name"] is None


def test_municipality_serializer_empty_string_is_valid_translation():
    # Empty string is not None; it is a valid translation value.
    data = MunicipalitySerializer(Municipality(name_fi="")).data
    assert data["name"] == {"fi": ""}


def test_municipality_serializer_output():
    data = MunicipalitySerializer(
        Municipality(name_fi="Helsinki", name_sv="Helsingfors", name_en="Helsinki")
    ).data
    assert data == {
        "code": "",
        "name": {
            "fi": "Helsinki",
            "sv": "Helsingfors",
            "en": "Helsinki",
        },
    }


def test_street_serializer_output():
    street = Street(name_fi="Mannerheimintie", name_sv="Mannerheimvägen", name_en=None)
    data = StreetSerializer(street).data
    assert data == {
        "name": {
            "fi": "Mannerheimintie",
            "sv": "Mannerheimvägen",
        }
    }


def test_street_serializer_no_translations_returns_null():
    data = StreetSerializer(Street()).data
    assert data["name"] is None


def test_postal_code_serializer_output():
    area = PostalCodeArea(
        postal_code="00100", name_fi="Helsinki", name_sv="Helsingfors"
    )
    data = PostalCodeSerializer(area).data
    assert data == {
        "postal_code": "00100",
        "name": {
            "fi": "Helsinki",
            "sv": "Helsingfors",
        },
    }


@pytest.mark.django_db
def test_administrative_division_serializer_output(division):
    data = AdministrativeDivisionSerializer(division).data
    assert data["name"] == {"fi": "Helsinki", "sv": "Helsingfors", "en": "Helsinki"}
    for field in (
        "name_fi",
        "name_sv",
        "name_en",
        "lft",
        "rght",
        "tree_id",
        "level",
        "search_column_fi",
        "search_column_sv",
        "search_column_en",
    ):
        assert field not in data
