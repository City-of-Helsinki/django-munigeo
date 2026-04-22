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

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        translations = kwargs.pop("translations", {})
        obj = super()._create(model_class, *args, **kwargs)
        for lang, name in translations.items():
            obj.set_current_language(lang)
            obj.name = name
        if translations:
            obj.save()
        return obj
