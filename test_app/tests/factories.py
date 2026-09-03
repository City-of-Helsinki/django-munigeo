import factory
from django.contrib.gis.geos import Point
from django.utils import timezone

from munigeo.models import (
    Address,
    AdministrativeDivision,
    AdministrativeDivisionType,
    Street,
)


class AdministrativeDivisionTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AdministrativeDivisionType
        django_get_or_create = ("type",)

    type = "muni"
    name = "Municipality"


class AdministrativeDivisionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AdministrativeDivision

    type = factory.SubFactory(AdministrativeDivisionTypeFactory)
    origin_id = factory.Sequence(lambda n: f"div-{n}")
    name_fi = factory.Sequence(lambda n: f"Alue {n}")
    name_sv = None
    name_en = None


class StreetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Street

    name_fi = factory.Faker("word")
    name_sv = factory.LazyAttribute(lambda street: f"{street.name_fi}_sv")
    name_en = factory.LazyAttribute(lambda street: f"{street.name_fi}_en")


class AddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Address

    number = factory.Faker("building_number")
    number_end = ""
    letter = ""
    location = factory.LazyFunction(lambda: Point(389800, 6672051, srid=3067))
    modified_at = factory.LazyFunction(timezone.now)
    full_name_fi = factory.LazyAttribute(
        lambda address: f"{address.street.name_fi} {address.number}"
    )
    full_name_sv = factory.LazyAttribute(
        lambda address: f"{address.street.name_sv} {address.number}"
    )
    full_name_en = factory.LazyAttribute(
        lambda address: f"{address.street.name_en} {address.number}"
    )
