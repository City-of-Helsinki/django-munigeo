import os
import requests
import json
from django.utils.text import slugify
from django.contrib.gis.gdal import DataSource, SpatialReference, CoordTransform
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Point

from munigeo.models import *
from munigeo.importer.sync import ModelSyncher

def convert_from_wgs84(coords):
    pnt = Point(coords[1], coords[0], srid=4326)
    pnt.transform(PROJECTION_SRID)
    return pnt

class Importer(object):
    def _import_citadel(self, muni, info):
        muni_slug = slugify(muni.name)

        print("\tImporting from Citadel")
        resp = requests.get(info['url'])
        assert resp.status_code == 200
        s = resp.content.decode('utf8')
        resp_json = json.loads(s)

        for d in resp_json['dataset']['poi']:
            citadel_type = d['category'][0]
            cat_info = info['cat_map'][citadel_type]
            cat, _ = POICategory.objects.get_or_create(type=cat_info['category'],
                    defaults={'description': cat_info['category_desc']})

            origin_id = "%s-%s-%s" % (muni_slug, cat.type, d['id'])

            try:
                poi = POI.objects.get(origin_id=origin_id)
            except POI.DoesNotExist:
                poi = POI(origin_id=origin_id)
            poi.name = d['title'].strip()
            coords = d['location']['point']['pos']['posList']
            if not coords:
                continue
            coords = [float(x) for x in coords.split(' ')]
            if coords[0] > 180 or coords[0] < -180:
                print("Skipping invalid coords for %s" % poi.name)
                continue
            poi.category = cat
            poi.municipality = muni
            poi.location = convert_from_wgs84(coords)
            poi.save()
            print(poi)

    def __init__(self, options):
        super(Importer, self).__init__()
        self.options = options

importers = {}

def register_importer(klass):
    importers[klass.name] = klass
    return klass

def get_importers():
    if importers:
        return importers
    # Importing the packages will cause their register_importer() methods
    # being called.
    for fname in os.listdir(os.path.dirname(__file__)):
        module, ext = os.path.splitext(fname)
        if ext.lower() != '.py':
            continue
        if module in ('__init__', 'base'):
            continue
        full_path = "%s.%s" % (__package__, module)
        ret = __import__(full_path, locals(), globals())
    return importers
