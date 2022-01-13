from modeltranslation.translator import translator, TranslationOptions
from munigeo.models import Address, AdministrativeDivision, Municipality, Street


class AdministrativeDivisionTranslationOptions(TranslationOptions):
    fields = ('name',)


class MunicipalityTranslationOptions(TranslationOptions):
    fields = ('name',)


class StreetTranslationOptions(TranslationOptions):
    fields = ('name',)


class AddressTranslationOptions(TranslationOptions):
    fields = ('full_name',)


translator.register(AdministrativeDivision, AdministrativeDivisionTranslationOptions)
translator.register(Municipality, MunicipalityTranslationOptions)
translator.register(Street, StreetTranslationOptions)
translator.register(Address, AddressTranslationOptions)
