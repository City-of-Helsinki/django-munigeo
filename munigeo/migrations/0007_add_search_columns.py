# Generated by Django 3.2.10 on 2022-01-13 09:04

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('munigeo', '0006_update_administrativedivision_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='full_name',
            field=models.CharField(db_index=True, help_text='Full address name. Used for generating search_column', max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='address',
            name='full_name_en',
            field=models.CharField(db_index=True, help_text='Full address name. Used for generating search_column', max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='address',
            name='full_name_fi',
            field=models.CharField(db_index=True, help_text='Full address name. Used for generating search_column', max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='address',
            name='full_name_sv',
            field=models.CharField(db_index=True, help_text='Full address name. Used for generating search_column', max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='address',
            name='search_column',
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddField(
            model_name='administrativedivision',
            name='search_column',
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddIndex(
            model_name='address',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_column'], name='munigeo_add_search__351ff4_gin'),
        ),
        migrations.AddIndex(
            model_name='administrativedivision',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_column'], name='munigeo_adm_search__cc1a06_gin'),
        ),
    ]