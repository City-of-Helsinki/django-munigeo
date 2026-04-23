from django.db import migrations

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
        Model = apps.get_model("munigeo", model_name)
        Translation = apps.get_model("munigeo", translation_name)
        for obj in Model.objects.all():
            for trans in Translation.objects.filter(master_id=obj.pk):
                if trans.language_code in LANGUAGE_CODES:
                    setattr(obj, f"name_{trans.language_code}", trans.name)
            obj.save(update_fields=["name_fi", "name_sv", "name_en"])


def copy_translations_backward(apps, schema_editor):
    """Reverse: copy name_fi / name_sv / name_en back into the parler
    translation tables (best-effort for rollback)."""
    for model_name, translation_name in MODELS:
        Model = apps.get_model("munigeo", model_name)
        Translation = apps.get_model("munigeo", translation_name)
        for obj in Model.objects.all():
            for lang in LANGUAGE_CODES:
                val = getattr(obj, f"name_{lang}")
                if val is None:
                    continue
                trans, _created = Translation.objects.get_or_create(
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
