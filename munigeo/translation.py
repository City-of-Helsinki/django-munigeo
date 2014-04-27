from modeltranslation.translator import translator, TranslationOptions
from munigeo.models import AdministrativeDivision, Municipality

class AdministrativeDivisionTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(AdministrativeDivision, AdministrativeDivisionTranslationOptions)

class MunicipalityTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(Municipality, MunicipalityTranslationOptions)
