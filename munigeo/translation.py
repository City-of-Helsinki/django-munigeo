from modeltranslation.translator import translator, TranslationOptions
from munigeo.models import AdministrativeDivision, Municipality, Street

class AdministrativeDivisionTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(AdministrativeDivision, AdministrativeDivisionTranslationOptions)

class MunicipalityTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(Municipality, MunicipalityTranslationOptions)

class StreetTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(Street, StreetTranslationOptions)
