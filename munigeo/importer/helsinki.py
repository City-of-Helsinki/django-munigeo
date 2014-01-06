"""
munigeo importer for Helsinki data
"""

import os
import csv
import re
import requests
import yaml

from django.conf import settings
from django import db
from django.utils import translation

from django.contrib.gis.gdal import DataSource, SpatialReference, CoordTransform
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon, Point

from munigeo.models import *
from munigeo.importer.sync import ModelSyncher
from munigeo import ocd

from munigeo.importer.base import Importer, register_importer

MUNI_URL = "http://tilastokeskus.fi/meta/luokitukset/kunta/001-2013/tekstitiedosto.txt"

# The Finnish national grid coordinates in TM35-FIN according to JHS-180
# specification. We use it as a bounding box.
FIN_GRID = [-548576, 6291456, 1548576, 8388608]
TM35_SRID = 3067

SERVICE_CATEGORY_MAP = {
    25480: ("library", "Library"),
    28148: ("swimming_pool", "Swimming pool"),
    25402: ("toilet", "Toilet"),
    25344: ("recycling", "Recycling point"),
    25664: ("park", "Park"),
}

GK25_SRID = 3879

def convert_from_gk25(north, east):
    pnt = Point(east, north, srid=GK25_SRID)
    pnt.transform(PROJECTION_SRID)
    return pnt

@register_importer
class HelsinkiImporter(Importer):
    name = "helsinki"

    def __init__(self, *args, **kwargs):
        super(HelsinkiImporter, self).__init__(*args, **kwargs)
        self.data_path = self.options['data_path']
        self.muni_data_path = os.path.join(self.data_path, 'fi', 'helsinki')

    def _find_parent_division(self, parent_info):
        args = {
            'type__type': parent_info['type'], 
            'origin_id': parent_info['id'],
            'parent__parent': parent_info['parent']
        }
        return AdministrativeDivision.objects.get(**args)

    @db.transaction.atomic
    def _import_division(self, parent, div):
        print(div['name'])
        if not 'origin_id' in div['fields']:
            raise Exception("Field 'origin_id' not defined in config section '%s'" % div['name'])
        try:
            type_obj = AdministrativeDivisionType.objects.get(type=div['type'])
        except AdministrativeDivisionType.DoesNotExist:
            type_obj = AdministrativeDivisionType(type=div['type'])
            type_obj.name = div['name']
            type_obj.save()

        div_qs = AdministrativeDivision.objects.filter(parent=parent, type=type_obj)
        syncher = ModelSyncher(div_qs, lambda obj: obj.origin_id)

        path = os.path.join(self.division_data_path, div['file'])
        ds = DataSource(path, encoding='iso8859-1')
        lyr = ds[0]
        assert len(ds) == 1
        for feat in lyr:
            attr_dict = {}
            lang_dict = {}
            for attr, field in div['fields'].items():
                if isinstance(field, dict):
                    # Languages
                    d = {}
                    for lang, field_name in field.items():
                        val = feat[field_name].as_string()
                        # If the name is in all caps, fix capitalization.
                        if not re.search('[a-z]', val):
                            val = val.title()
                        d[lang] = val
                    lang_dict[attr] = d
                else:
                    val = feat[field].as_string()
                    attr_dict[attr] = val

            origin_id = attr_dict['origin_id']
            del attr_dict['origin_id']

            obj = syncher.get(origin_id)
            if not obj:
                obj = AdministrativeDivision(origin_id=origin_id, parent=parent, type=type_obj)
            for attr in attr_dict.keys():
                setattr(obj, attr, attr_dict[attr])
            for attr in lang_dict.keys():
                for lang, val in lang_dict[attr].items():
                    d = {attr: val}
                    obj.translate(language=lang, **d)

            if 'ocd_id' in div:
                assert parent and parent.ocd_id
                args = {'parent': parent.ocd_id}
                val = attr_dict['ocd_id']
                args[div['ocd_id']] = val
                obj.ocd_id = ocd.make_id(**args)

            obj.save()
            syncher.mark(obj)

            try:
                geom_obj = obj.geometry
            except AdministrativeDivisionGeometry.DoesNotExist:
                geom_obj = AdministrativeDivisionGeometry(division=obj)

            geom = feat.geom
            geom.srid = GK25_SRID
            geom.transform(PROJECTION_SRID)
            #geom = geom.geos.intersection(parent.geometry.boundary)
            geom = geom.geos
            if geom.geom_type == 'Polygon':
                geom = MultiPolygon(geom)
            geom_obj.boundary = geom
            geom_obj.save()

    def import_divisions(self):
        path = os.path.join(self.data_path, 'fi', 'helsinki', 'config.yml')
        config = yaml.safe_load(open(path, 'r'))
        self.division_data_path = os.path.join(self.muni_data_path, config['paths']['division'])

        muni = Municipality.objects.get(origin_id=config['origin_id'])
        self.muni = muni
        for div in config['divisions']:
            self._import_division(muni, div)

    def _import_plans(self, fname, in_effect):
        path = os.path.join(self.data_path, 'kaavahakemisto', fname)
        ds = DataSource(path, encoding='iso8859-1')
        lyr = ds[0]

        for idx, feat in enumerate(lyr):
            origin_id = feat['kaavatunnus'].as_string()
            geom = feat.geom
            geom.srid = GK25_SRID
            geom.transform(PROJECTION_SRID)
            if origin_id not in self.plan_map:
                obj = Plan(origin_id=origin_id, municipality=self.muni)
                self.plan_map[origin_id] = obj
            else:
                obj = self.plan_map[origin_id]
                if not obj.found:
                    obj.geometry = None
            poly = GEOSGeometry(geom.wkb, srid=geom.srid)
            if obj.geometry:
                obj.geometry.append(poly)
            else:
                obj.geometry = MultiPolygon(poly)
            obj.in_effect = in_effect
            obj.found = True
            if (idx % 500) == 0:
                print("%d imported" % idx)
        if in_effect:
            type_str = "in effect"
        else:
            type_str = "development"
        print("%d %s plans imported" % (idx, type_str))

    def import_plans(self):
        self.plan_map = {}
        self.muni = Municipality.objects.get(name="Helsinki")
        for obj in Plan.objects.filter(municipality=self.muni):
            self.plan_map[obj.origin_id] = obj
            obj.found = False
        self._import_plans('Lv_rajaus.TAB', True)
        self._import_plans('Kaava_vir_rajaus.TAB', False)
        print("Saving")
        for key, obj in self.plan_map.items():
            if obj.found:
                obj.save()
            else:
                print("Plan %s deleted" % obj.name)

    def import_addresses(self):
        f = open(os.path.join(self.data_path, 'pks_osoite.csv'))
        reader = csv.reader(f, delimiter=',')
        next(reader)
        muni_list = Municipality.objects.all()
        muni_dict = {}
        for muni in muni_list:
            muni_dict[muni.name] = muni
            muni.num_addr = Address.objects.filter(municipality=muni).count()
        bulk_addr_list = []
        count = 0
        for idx, row in enumerate(reader):
            street = row[0].strip()
            if not row[1]:
                continue
            num = int(row[1])
            num2 = row[2]
            if not num2:
                num2 = None
            letter = row[3]
            coord_n = int(row[8])
            coord_e = int(row[9])
            muni_name = row[10]
            if not row[-1]:
                # If the type is missing, assume type 1
                print(row)
                row_type = 1
            else:
                row_type = int(row[-1])
            if row_type != 1:
                continue
            id_s = "%s %d" % (street, num)
            if id_s == 'Eliel Saarisen tie 4':
                muni_name = 'Helsinki'
            muni = muni_dict[muni_name]
            args = dict(municipality=muni, street=street, number=num, number_end=num2, letter=letter)
            # Optimization: if the muni doesn't have any addresses yet,
            # use bulk creation.
            addr = None
            if muni.num_addr != 0:
                try:
                    addr = Address.objects.get(**args)
                except Address.DoesNotExist:
                    pass
            if not addr:
                addr = Address(**args)

            pnt = convert_from_gk25(coord_n, coord_e)
            #print "%s: %s %d%s N%d E%d (%f,%f)" % (muni_name, street, num, letter, coord_n, coord_e, pnt.y, pnt.x)
            addr.location = pnt
            if not addr.pk:
                bulk_addr_list.append(addr)
            else:
                addr.save()
                count += 1

            if len(bulk_addr_list) >= 1000 or (count > 0 and count % 1000 == 0):
                if bulk_addr_list:
                    Address.objects.bulk_create(bulk_addr_list)
                    count += len(bulk_addr_list)
                    bulk_addr_list = []
                print("%d addresses processed (%d skipped)" % (count, idx + 1 - count))
                # Reset DB query store to free up memory
                db.reset_queries()

        if bulk_addr_list:
            Address.objects.bulk_create(bulk_addr_list)
            bulk_addr_list = []

    def import_pois(self):
        URL_BASE = 'http://www.hel.fi/palvelukarttaws/rest/v2/unit/?service=%d'

        muni_dict = {}
        for muni in Municipality.objects.all():
            muni_dict[muni.name] = muni

        for srv_id in list(SERVICE_CATEGORY_MAP.keys()):
            cat_type, cat_desc = SERVICE_CATEGORY_MAP[srv_id]
            cat, c = POICategory.objects.get_or_create(type=cat_type, defaults={'description': cat_desc})

            print("\tImporting %s" % cat_type)
            ret = requests.get(URL_BASE % srv_id)
            for srv_info in ret.json():
                srv_id = str(srv_info['id'])
                try:
                    poi = POI.objects.get(origin_id=srv_id)
                except POI.DoesNotExist:
                    poi = POI(origin_id=srv_id)
                poi.name = srv_info['name_fi']
                poi.category = cat
                if not 'address_city_fi' in srv_info:
                    print("No city!")
                    print(srv_info)
                    continue
                city_name = srv_info['address_city_fi']
                if not city_name in muni_dict:
                    city_name = city_name.encode('utf8')
                    post_code = srv_info.get('address_zip', '')
                    if post_code.startswith('00'):
                        print("%s: %s (%s)" % (srv_info['id'], poi.name.encode('utf8'), city_name))
                        city_name = "Helsinki"
                    elif post_code.startswith('01'):
                        print("%s: %s (%s)" % (srv_info['id'], poi.name.encode('utf8'), city_name))
                        city_name = "Vantaa"
                    elif post_code in ('02700', '02701', '02760'):
                        print("%s: %s (%s)" % (srv_info['id'], poi.name.encode('utf8'), city_name))
                        city_name = "Kauniainen"
                    elif post_code.startswith('02'):
                        print("%s: %s (%s)" % (srv_info['id'], poi.name.encode('utf8'), city_name))
                        city_name = "Espoo"
                    else:
                        print(srv_info)
                poi.municipality = muni_dict[city_name]
                poi.street_address = srv_info.get('street_address_fi', None)
                poi.zip_code = srv_info.get('address_zip', None)
                if not 'northing_etrs_gk25' in srv_info:
                    print("No location!")
                    print(srv_info)
                    continue
                poi.location = convert_from_gk25(srv_info['northing_etrs_gk25'], srv_info['easting_etrs_gk25'])
                poi.save()
