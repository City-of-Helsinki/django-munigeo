import pytest

from munigeo.api import (
    AdministrativeDivisionSerializer,
    MunicipalitySerializer,
    StreetSerializer,
)
from munigeo.models import Municipality, Street
from test_app.tests.factories import (
    AdministrativeDivisionFactory,
    AdministrativeDivisionTypeFactory,
)


@pytest.fixture
def division():
    return AdministrativeDivisionFactory(
        type=AdministrativeDivisionTypeFactory(),
        translations={"fi": "Helsinki", "sv": "Helsingfors", "en": "Helsinki"},
    )


def _make_municipality(**names):
    """Create an unsaved Municipality with parler translations set."""
    muni = Municipality()
    for lang, name in names.items():
        muni.set_current_language(lang)
        muni.name = name
    return muni


def _make_street(**names):
    """Create an unsaved Street with parler translations set."""
    street = Street()
    for lang, name in names.items():
        street.set_current_language(lang)
        street.name = name
    return street


@pytest.mark.django_db
def test_municipality_serializer_absent_translations_omitted():
    muni = _make_municipality(fi="Helsinki")
    muni.save()
    data = MunicipalitySerializer(muni).data
    assert data["name"] == {"fi": "Helsinki"}


@pytest.mark.django_db
def test_municipality_serializer_no_translations_returns_empty():
    muni = Municipality()
    muni.save()
    data = MunicipalitySerializer(muni).data
    assert "name" not in data


@pytest.mark.django_db
def test_municipality_serializer_empty_string_is_valid_translation():
    # Empty string is not None; it is a valid translation value.
    muni = _make_municipality(fi="")
    muni.save()
    data = MunicipalitySerializer(muni).data
    assert data["name"] == {"fi": ""}


@pytest.mark.django_db
def test_municipality_serializer_output():
    muni = _make_municipality(fi="Helsinki", sv="Helsingfors", en="Helsinki")
    muni.save()
    data = MunicipalitySerializer(muni).data
    assert data == {
        "id": muni.id,
        "division": None,
        "name": {
            "fi": "Helsinki",
            "sv": "Helsingfors",
            "en": "Helsinki",
        },
    }


@pytest.mark.django_db
def test_street_serializer_output():
    muni = _make_municipality(fi="Helsinki")
    muni.save()
    street = _make_street(fi="Mannerheimintie", sv="Mannerheimvägen")
    street.municipality = muni
    street.save()
    data = StreetSerializer(street).data
    assert data["name"] == {
        "fi": "Mannerheimintie",
        "sv": "Mannerheimvägen",
    }
    assert data["municipality"] == muni.id


@pytest.mark.django_db
def test_street_serializer_no_translations_returns_empty():
    muni = _make_municipality(fi="Helsinki")
    muni.save()
    street = Street(municipality=muni)
    street.save()
    data = StreetSerializer(street).data
    assert "name" not in data


@pytest.mark.django_db
def test_administrative_division_serializer_output(division):
    data = AdministrativeDivisionSerializer(division).data
    assert data["name"] == {"fi": "Helsinki", "sv": "Helsingfors", "en": "Helsinki"}
    for field in (
        "lft",
        "rght",
        "tree_id",
        "level",
    ):
        assert field not in data
