from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("munigeo", "0007_migrate_translation_data"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="municipalitytranslation",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="municipalitytranslation",
            name="master",
        ),
        migrations.AlterUniqueTogether(
            name="streettranslation",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="streettranslation",
            name="master",
        ),
        migrations.AlterUniqueTogether(
            name="street",
            unique_together={
                ("municipality", "name_fi"),
            },
        ),
        migrations.DeleteModel(
            name="AdministrativeDivisionTranslation",
        ),
        migrations.DeleteModel(
            name="MunicipalityTranslation",
        ),
        migrations.DeleteModel(
            name="StreetTranslation",
        ),
    ]
