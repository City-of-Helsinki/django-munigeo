"""
munigeo importer for HSY data
"""
import os
import re
import yaml

from datetime import datetime

from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import MultiPolygon
from munigeo import ocd

from munigeo.importer.base import register_importer
from munigeo.importer.helsinki import HelsinkiImporter, GK25_SRID, PROJECTION_SRID
from munigeo.models import Municipality, AdministrativeDivision, AdministrativeDivisionGeometry


MUNICIPALITY_ID_MAP = {
    "091": "Helsinki",
    "092": "Vantaa",
    "049": "Espoo",
    "235": "Kauniainen"
}


@register_importer
class HsyImporter(HelsinkiImporter):
    name = "hsy"

    def __init__(self, *args, **kwargs):
        super(HsyImporter, self).__init__(*args, **kwargs)
        self.muni_data_path = 'fi/hsy'

    def import_divisions(self):
        path = self.find_data_file(os.path.join(self.muni_data_path, 'config.yml'))
        config = yaml.safe_load(open(path, 'r', encoding='utf-8'))
        self.division_data_path = os.path.join(self.muni_data_path, config['paths']['division'])

        for div in config['divisions']:
            try:
                self._import_one_division_type(None, div)
            except GDALException as e:
                self.logger.warning('Skipping division %s : %s' % (div, e))

    def _import_division(self, muni, div, type_obj, syncher, parent_dict, feat):
        #
        # Geometry
        #
        geom = feat.geom
        if not geom.srid:
            geom.srid = GK25_SRID
        if geom.srid != PROJECTION_SRID:
            ct = CoordTransform(SpatialReference(geom.srid), SpatialReference(PROJECTION_SRID))
            geom.transform(ct)
        geom = geom.geos
        if geom.geom_type == 'Polygon':
            geom = MultiPolygon(geom, srid=geom.srid)

        #
        # Attributes
        #
        attr_dict = {}
        lang_dict = {}
        for attr, field in div['fields'].items():
            if isinstance(field, dict):
                # Languages
                d = {}
                for lang, field_name in field.items():
                    val = feat[field_name].as_string()
                    val = val or ''
                    # If the name is in all caps, fix capitalization.
                    if not re.search('[a-z]', val):
                        val = val.title()
                    d[lang] = val.strip()
                lang_dict[attr] = d
            else:
                val = feat[field].as_string()
                if val:
                    attr_dict[attr] = val.strip()
                else:
                    attr_dict[attr] = None

        origin_id = attr_dict['origin_id']
        # if origin_id is not found, we skip the feature
        if not origin_id:
            self.logger.info('Division origin_id is None. Skipping division...')
            return
        del attr_dict['origin_id']

        # Municipality
        municipality_name = MUNICIPALITY_ID_MAP.get(attr_dict.get('parent_municipality_id'))
        try:
            muni = Municipality.objects.get(name=municipality_name)
        except Municipality.DoesNotExist:
            self.logger.error("Feature: %s is invalid" % feat)
            return None

        parent = muni.division

        if parent:
            origin_id = "%s-%s" % (parent.origin_id, origin_id)
        obj = syncher.get(origin_id)
        if not obj:
            obj = AdministrativeDivision(origin_id=origin_id, type=type_obj)

        obj.municipality = muni

        validity_time_period = div.get('validity')
        if validity_time_period:
            obj.start = validity_time_period.get('start')
            obj.end = validity_time_period.get('end')
            if obj.start:
                obj.start = datetime.strptime(obj.start, '%Y-%m-%d').date()
            if obj.end:
                obj.end = datetime.strptime(obj.end, '%Y-%m-%d').date()

        obj.parent = parent

        for attr in attr_dict.keys():
            setattr(obj, attr, attr_dict[attr])
        for attr in lang_dict.keys():
            for lang, val in lang_dict[attr].items():
                key = "%s_%s" % (attr, lang)
                setattr(obj, key, val)

        if 'ocd_id' in div:
            assert (parent and parent.ocd_id) or 'parent_ocd_id' in div
            if parent:
                if div.get('parent_in_ocd_id', False):
                    args = {'parent': parent.ocd_id}
                else:
                    args = {'parent': muni.division.ocd_id}
            else:
                args = {'parent': div['parent_ocd_id']}
            val = attr_dict['ocd_id']
            args[div['ocd_id']] = val
            obj.ocd_id = ocd.make_id(**args)
            self.logger.debug("%s" % obj.ocd_id)
        obj.save()
        syncher.mark(obj, True)

        try:
            geom_obj = obj.geometry
        except AdministrativeDivisionGeometry.DoesNotExist:
            geom_obj = AdministrativeDivisionGeometry(division=obj)

        geom_obj.boundary = geom
        geom_obj.save()
