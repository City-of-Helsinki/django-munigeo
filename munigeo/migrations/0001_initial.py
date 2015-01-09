# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('number', models.CharField(max_length=6, blank=True, help_text='Building number')),
                ('number_end', models.CharField(max_length=6, blank=True, help_text='Building number end (if range specified)')),
                ('letter', models.CharField(max_length=2, blank=True, help_text='Building letter if applicable')),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=3067, help_text='Coordinates of the address')),
            ],
            options={
                'ordering': ['street', 'number'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdministrativeDivision',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(null=True, max_length=100, db_index=True)),
                ('name_fi', models.CharField(null=True, max_length=100, db_index=True)),
                ('name_sv', models.CharField(null=True, max_length=100, db_index=True)),
                ('name_en', models.CharField(null=True, max_length=100, db_index=True)),
                ('origin_id', models.CharField(max_length=50, db_index=True)),
                ('ocd_id', models.CharField(null=True, max_length=200, unique=True, db_index=True, help_text='Open Civic Data identifier')),
                ('service_point_id', models.CharField(null=True, max_length=50, blank=True, db_index=True)),
                ('start', models.DateField(null=True)),
                ('end', models.DateField(null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='Time when the information was last changed')),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdministrativeDivisionGeometry',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('boundary', django.contrib.gis.db.models.fields.MultiPolygonField(srid=3067)),
                ('division', models.OneToOneField(to='munigeo.AdministrativeDivision', related_name='geometry')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdministrativeDivisionType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('type', models.CharField(max_length=60, unique=True, db_index=True, help_text='Type name of the division (e.g. muni, school_district)')),
                ('name', models.CharField(max_length=100, help_text='Human-readable name for the division')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Municipality',
            fields=[
                ('id', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('name', models.CharField(null=True, max_length=100, db_index=True)),
                ('name_fi', models.CharField(null=True, max_length=100, db_index=True)),
                ('name_sv', models.CharField(null=True, max_length=100, db_index=True)),
                ('name_en', models.CharField(null=True, max_length=100, db_index=True)),
                ('division', models.ForeignKey(to='munigeo.AdministrativeDivision', null=True, unique=True, related_name='muni')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('geometry', django.contrib.gis.db.models.fields.MultiPolygonField(srid=3067)),
                ('origin_id', models.CharField(max_length=20)),
                ('in_effect', models.BooleanField(default=False)),
                ('municipality', models.ForeignKey(to='munigeo.Municipality')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='POI',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(null=True, blank=True)),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=3067)),
                ('street_address', models.CharField(null=True, max_length=100, blank=True)),
                ('zip_code', models.CharField(null=True, max_length=10, blank=True)),
                ('origin_id', models.CharField(max_length=40, unique=True, db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='POICategory',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('type', models.CharField(max_length=50, db_index=True)),
                ('description', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Street',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=100, db_index=True)),
                ('name_fi', models.CharField(null=True, max_length=100, db_index=True)),
                ('name_sv', models.CharField(null=True, max_length=100, db_index=True)),
                ('name_en', models.CharField(null=True, max_length=100, db_index=True)),
                ('municipality', models.ForeignKey(to='munigeo.Municipality')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='street',
            unique_together=set([('municipality', 'name')]),
        ),
        migrations.AddField(
            model_name='poi',
            name='category',
            field=models.ForeignKey(to='munigeo.POICategory'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='poi',
            name='municipality',
            field=models.ForeignKey(to='munigeo.Municipality'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='plan',
            unique_together=set([('municipality', 'origin_id')]),
        ),
        migrations.AddField(
            model_name='administrativedivision',
            name='municipality',
            field=models.ForeignKey(null=True, to='munigeo.Municipality'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='administrativedivision',
            name='parent',
            field=mptt.fields.TreeForeignKey(to='munigeo.AdministrativeDivision', related_name='children', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='administrativedivision',
            name='type',
            field=models.ForeignKey(to='munigeo.AdministrativeDivisionType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='administrativedivision',
            unique_together=set([('origin_id', 'type', 'parent')]),
        ),
        migrations.AddField(
            model_name='address',
            name='street',
            field=models.ForeignKey(related_name='addresses', to='munigeo.Street'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='address',
            unique_together=set([('street', 'number', 'number_end', 'letter')]),
        ),
    ]
