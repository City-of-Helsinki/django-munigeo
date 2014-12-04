# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'AdministrativeDivisionType'
        db.create_table('munigeo_administrativedivisiontype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=30, db_index=True, unique=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('munigeo', ['AdministrativeDivisionType'])

        # Adding model 'AdministrativeDivision'
        db.create_table('munigeo_administrativedivision', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['munigeo.AdministrativeDivisionType'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True)),
            ('name_fi', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True, blank=True)),
            ('name_sv', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True, blank=True)),
            ('name_en', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True, blank=True)),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(to=orm['munigeo.AdministrativeDivision'], null=True, related_name='children')),
            ('origin_id', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('ocd_id', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, db_index=True, unique=True)),
            ('municipality', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['munigeo.Municipality'], null=True)),
            ('start', self.gf('django.db.models.fields.DateField')(null=True)),
            ('end', self.gf('django.db.models.fields.DateField')(null=True)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('munigeo', ['AdministrativeDivision'])

        # Adding unique constraint on 'AdministrativeDivision', fields ['origin_id', 'type', 'parent']
        db.create_unique('munigeo_administrativedivision', ['origin_id', 'type_id', 'parent_id'])

        # Adding model 'AdministrativeDivisionGeometry'
        db.create_table('munigeo_administrativedivisiongeometry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('division', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['munigeo.AdministrativeDivision'], unique=True, related_name='geometry')),
            ('boundary', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')(srid=3067)),
        ))
        db.send_create_signal('munigeo', ['AdministrativeDivisionGeometry'])

        # Adding model 'Municipality'
        db.create_table('munigeo_municipality', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=100, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True)),
            ('name_fi', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True, blank=True)),
            ('name_sv', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True, blank=True)),
            ('name_en', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True, blank=True)),
            ('division', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['munigeo.AdministrativeDivision'], null=True, unique=True, related_name='muni')),
        ))
        db.send_create_signal('munigeo', ['Municipality'])

        # Adding model 'Plan'
        db.create_table('munigeo_plan', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('municipality', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['munigeo.Municipality'])),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')(srid=3067)),
            ('origin_id', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('in_effect', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('munigeo', ['Plan'])

        # Adding unique constraint on 'Plan', fields ['municipality', 'origin_id']
        db.create_unique('munigeo_plan', ['municipality_id', 'origin_id'])

        # Adding model 'Street'
        db.create_table('munigeo_street', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('name_fi', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True, blank=True)),
            ('name_sv', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True, blank=True)),
            ('name_en', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True, blank=True)),
            ('municipality', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['munigeo.Municipality'])),
        ))
        db.send_create_signal('munigeo', ['Street'])

        # Adding unique constraint on 'Street', fields ['municipality', 'name']
        db.create_unique('munigeo_street', ['municipality_id', 'name'])

        # Adding model 'Address'
        db.create_table('munigeo_address', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('street', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['munigeo.Street'], related_name='addresses')),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=6, blank=True)),
            ('number_end', self.gf('django.db.models.fields.CharField')(max_length=6, blank=True)),
            ('letter', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('location', self.gf('django.contrib.gis.db.models.fields.PointField')(srid=3067)),
        ))
        db.send_create_signal('munigeo', ['Address'])

        # Adding unique constraint on 'Address', fields ['street', 'number', 'number_end', 'letter']
        db.create_unique('munigeo_address', ['street_id', 'number', 'number_end', 'letter'])

        # Adding model 'POICategory'
        db.create_table('munigeo_poicategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('munigeo', ['POICategory'])

        # Adding model 'POI'
        db.create_table('munigeo_poi', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['munigeo.POICategory'])),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('location', self.gf('django.contrib.gis.db.models.fields.PointField')(srid=3067)),
            ('municipality', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['munigeo.Municipality'])),
            ('street_address', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('zip_code', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('origin_id', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True, unique=True)),
        ))
        db.send_create_signal('munigeo', ['POI'])


    def backwards(self, orm):
        # Removing unique constraint on 'Address', fields ['street', 'number', 'number_end', 'letter']
        db.delete_unique('munigeo_address', ['street_id', 'number', 'number_end', 'letter'])

        # Removing unique constraint on 'Street', fields ['municipality', 'name']
        db.delete_unique('munigeo_street', ['municipality_id', 'name'])

        # Removing unique constraint on 'Plan', fields ['municipality', 'origin_id']
        db.delete_unique('munigeo_plan', ['municipality_id', 'origin_id'])

        # Removing unique constraint on 'AdministrativeDivision', fields ['origin_id', 'type', 'parent']
        db.delete_unique('munigeo_administrativedivision', ['origin_id', 'type_id', 'parent_id'])

        # Deleting model 'AdministrativeDivisionType'
        db.delete_table('munigeo_administrativedivisiontype')

        # Deleting model 'AdministrativeDivision'
        db.delete_table('munigeo_administrativedivision')

        # Deleting model 'AdministrativeDivisionGeometry'
        db.delete_table('munigeo_administrativedivisiongeometry')

        # Deleting model 'Municipality'
        db.delete_table('munigeo_municipality')

        # Deleting model 'Plan'
        db.delete_table('munigeo_plan')

        # Deleting model 'Street'
        db.delete_table('munigeo_street')

        # Deleting model 'Address'
        db.delete_table('munigeo_address')

        # Deleting model 'POICategory'
        db.delete_table('munigeo_poicategory')

        # Deleting model 'POI'
        db.delete_table('munigeo_poi')


    models = {
        'munigeo.address': {
            'Meta': {'ordering': "['street', 'number']", 'object_name': 'Address', 'unique_together': "(('street', 'number', 'number_end', 'letter'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'letter': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'srid': '3067'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'number_end': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'street': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.Street']", 'related_name': "'addresses'"})
        },
        'munigeo.administrativedivision': {
            'Meta': {'unique_together': "(('origin_id', 'type', 'parent'),)", 'object_name': 'AdministrativeDivision'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.Municipality']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'ocd_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'db_index': 'True', 'unique': 'True'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'to': "orm['munigeo.AdministrativeDivision']", 'null': 'True', 'related_name': "'children'"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.AdministrativeDivisionType']"})
        },
        'munigeo.administrativedivisiongeometry': {
            'Meta': {'object_name': 'AdministrativeDivisionGeometry'},
            'boundary': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'srid': '3067'}),
            'division': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['munigeo.AdministrativeDivision']", 'unique': 'True', 'related_name': "'geometry'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'munigeo.administrativedivisiontype': {
            'Meta': {'object_name': 'AdministrativeDivisionType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True', 'unique': 'True'})
        },
        'munigeo.municipality': {
            'Meta': {'object_name': 'Municipality'},
            'division': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.AdministrativeDivision']", 'null': 'True', 'unique': 'True', 'related_name': "'muni'"}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'munigeo.plan': {
            'Meta': {'unique_together': "(('municipality', 'origin_id'),)", 'object_name': 'Plan'},
            'geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'srid': '3067'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_effect': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.Municipality']"}),
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'munigeo.poi': {
            'Meta': {'object_name': 'POI'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.POICategory']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'srid': '3067'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.Municipality']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True', 'unique': 'True'}),
            'street_address': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'})
        },
        'munigeo.poicategory': {
            'Meta': {'object_name': 'POICategory'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'munigeo.street': {
            'Meta': {'unique_together': "(('municipality', 'name'),)", 'object_name': 'Street'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.Municipality']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['munigeo']