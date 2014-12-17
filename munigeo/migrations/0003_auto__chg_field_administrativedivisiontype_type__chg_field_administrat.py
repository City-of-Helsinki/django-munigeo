# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'AdministrativeDivisionType.type'
        db.alter_column('munigeo_administrativedivisiontype', 'type', self.gf('django.db.models.fields.CharField')(max_length=60, unique=True))

        # Changing field 'AdministrativeDivisionType.name'
        db.alter_column('munigeo_administrativedivisiontype', 'name', self.gf('django.db.models.fields.CharField')(max_length=100))

    def backwards(self, orm):

        # Changing field 'AdministrativeDivisionType.type'
        db.alter_column('munigeo_administrativedivisiontype', 'type', self.gf('django.db.models.fields.CharField')(max_length=30, unique=True))

        # Changing field 'AdministrativeDivisionType.name'
        db.alter_column('munigeo_administrativedivisiontype', 'name', self.gf('django.db.models.fields.CharField')(max_length=50))

    models = {
        'munigeo.address': {
            'Meta': {'ordering': "['street', 'number']", 'unique_together': "(('street', 'number', 'number_end', 'letter'),)", 'object_name': 'Address'},
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True', 'null': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'ocd_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'db_index': 'True', 'null': 'True'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'to': "orm['munigeo.AdministrativeDivision']", 'null': 'True', 'related_name': "'children'"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'service_point_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True', 'null': 'True', 'blank': 'True'}),
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '60', 'unique': 'True', 'db_index': 'True'})
        },
        'munigeo.municipality': {
            'Meta': {'object_name': 'Municipality'},
            'division': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.AdministrativeDivision']", 'null': 'True', 'unique': 'True', 'related_name': "'muni'"}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True', 'null': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True', 'null': 'True', 'blank': 'True'})
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
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'db_index': 'True'}),
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
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['munigeo']