from modeltranslation.translator import TranslationOptions, translator

from munigeo.models import (
    Address,
    AdministrativeDivision,
    Municipality,
    PostalCodeArea,
    Street,
)


class AdministrativeDivisionTranslationOptions(TranslationOptions):
    fields = ("name",)


class MunicipalityTranslationOptions(TranslationOptions):
    fields = ("name",)


class StreetTranslationOptions(TranslationOptions):
    fields = ("name",)


class AddressTranslationOptions(TranslationOptions):
    fields = ("full_name",)


class PostalCodeAreaTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(AdministrativeDivision, AdministrativeDivisionTranslationOptions)
translator.register(Municipality, MunicipalityTranslationOptions)
translator.register(Street, StreetTranslationOptions)
translator.register(Address, AddressTranslationOptions)
translator.register(PostalCodeArea, PostalCodeAreaTranslationOptions)
