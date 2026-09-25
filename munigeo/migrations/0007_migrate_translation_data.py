from django.db import migrations
from django.db.models import OuterRef, Subquery

LANGUAGE_CODES = ("fi", "sv", "en")

MODELS = [
    ("AdministrativeDivision", "AdministrativeDivisionTranslation"),
    ("Municipality", "MunicipalityTranslation"),
    ("Street", "StreetTranslation"),
]


def copy_translations_forward(apps, schema_editor):
    """Copy name values from parler translation tables into the new
    name_fi / name_sv / name_en columns on the main tables."""
    for model_name, translation_name in MODELS:
        model = apps.get_model("munigeo", model_name)
        translation = apps.get_model("munigeo", translation_name)
        translated_names = {
            f"name_{language_code}": Subquery(
                translation.objects.filter(
                    master_id=OuterRef("pk"),
                    language_code=language_code,
                ).values("name")[:1]
            )
            for language_code in LANGUAGE_CODES
        }
        model.objects.update(**translated_names)


def copy_translations_backward(apps, schema_editor):
    """Reverse: copy name_fi / name_sv / name_en back into the parler
    translation tables (best-effort for rollback)."""
    for model_name, translation_name in MODELS:
        model = apps.get_model("munigeo", model_name)
        translation = apps.get_model("munigeo", translation_name)
        for obj in model.objects.all():
            for lang in LANGUAGE_CODES:
                val = getattr(obj, f"name_{lang}")
                if val is None:
                    continue
                trans, _created = translation.objects.get_or_create(
                    master_id=obj.pk,
                    language_code=lang,
                    defaults={"name": val},
                )
                if not _created:
                    trans.name = val
                    trans.save(update_fields=["name"])


class Migration(migrations.Migration):
    dependencies = [
        ("munigeo", "0006_add_name_fields"),
    ]

    operations = [
        migrations.RunPython(
            copy_translations_forward,
            copy_translations_backward,
        ),
    ]
