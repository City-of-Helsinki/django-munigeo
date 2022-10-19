# Generated by Django 3.2.12 on 2022-03-07 12:17

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('munigeo', '0008_administrativedivision_units'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='address',
            name='munigeo_add_search__351ff4_gin',
        ),
        migrations.RemoveIndex(
            model_name='administrativedivision',
            name='munigeo_adm_search__cc1a06_gin',
        ),
        migrations.RenameField(
            model_name='address',
            old_name='search_column',
            new_name='search_column_en',
        ),
        migrations.RenameField(
            model_name='administrativedivision',
            old_name='search_column',
            new_name='search_column_en',
        ),
        migrations.AddField(
            model_name='address',
            name='search_column_fi',
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddField(
            model_name='address',
            name='search_column_sv',
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddField(
            model_name='administrativedivision',
            name='search_column_fi',
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddField(
            model_name='administrativedivision',
            name='search_column_sv',
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddIndex(
            model_name='address',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_column_fi'], name='munigeo_add_search__efb82b_gin'),
        ),
        migrations.AddIndex(
            model_name='address',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_column_sv'], name='munigeo_add_search__2418cb_gin'),
        ),
        migrations.AddIndex(
            model_name='address',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_column_en'], name='munigeo_add_search__c95720_gin'),
        ),
        migrations.AddIndex(
            model_name='administrativedivision',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_column_fi'], name='munigeo_adm_search__ce886a_gin'),
        ),
        migrations.AddIndex(
            model_name='administrativedivision',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_column_sv'], name='munigeo_adm_search__f435c7_gin'),
        ),
        migrations.AddIndex(
            model_name='administrativedivision',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_column_en'], name='munigeo_adm_search__f7bab1_gin'),
        ),
    ]