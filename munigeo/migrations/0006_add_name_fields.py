from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("munigeo", "0005_update_translation_foreign_keys"),
    ]

    operations = [
        migrations.AddField(
            model_name="administrativedivision",
            name="name_en",
            field=models.CharField(db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="administrativedivision",
            name="name_fi",
            field=models.CharField(db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="administrativedivision",
            name="name_sv",
            field=models.CharField(db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="municipality",
            name="name_en",
            field=models.CharField(db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="municipality",
            name="name_fi",
            field=models.CharField(db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="municipality",
            name="name_sv",
            field=models.CharField(db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="street",
            name="name_en",
            field=models.CharField(db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="street",
            name="name_fi",
            field=models.CharField(db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="street",
            name="name_sv",
            field=models.CharField(db_index=True, max_length=100, null=True),
        ),
    ]
