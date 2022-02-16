import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('munigeo', '0007_add_search_columns'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrativedivision',
            name='units',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), default=list, size=None),
        ),
    ]
