from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("munigeo", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="municipality",
            name="division",
            field=models.OneToOneField(
                related_name="muni",
                to="munigeo.AdministrativeDivision",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
    ]
