import factory

from munigeo.models import AdministrativeDivision, AdministrativeDivisionType


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
