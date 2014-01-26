from modeltranslation.translator import translator, TranslationOptions
from munigeo.models import *

class AdministrativeDivisionTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(AdministrativeDivision, AdministrativeDivisionTranslationOptions)
