# -*- coding: utf-8 -*-
import os
import csv
import requests
import requests_cache
import StringIO
import urllib
import json

from django.core.management.base import BaseCommand
from munigeo.models import *
from utils.http import HttpFetcher
from django.conf import settings
from django import db
from django.contrib.gis.gdal import DataSource, SpatialReference, CoordTransform
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Point

POI_LIST = [
    {
        'category': 'park', 'category_desc': 'Park',
        'url': 'http://opendata.manchesterdda.com/data-files/parks_and_open_spaces_20121116.csv',
        'name_col': 0,
        'address_col': 1,
        'desc_col': 5,
        'location_col': 18,
    }, {
        'category': 'library', 'category_desc': 'Library',
        'url': 'http://opendata.manchesterdda.com/data-files/libraries20121113.csv',
        'name_col': 0,
        'address_col': 6, 
        'desc_col': 1,
        'location_col': 20,
    }
]

SERVICE_CATEGORY_MAP = {
    50: ("toilet", "Toilet"),
    9: ("recycling", "Recycling points"),
    #87: ("attractions", "Tourist attractions"),
}

def convert_from_wgs84(coords):
    pnt = Point(coords[1], coords[0], srid=4326)
    pnt.transform(PROJECTION_SRID)
    return pnt

class Command(BaseCommand):
    help = "Manage stats app"

    def import_municipalities(self):
        muni, c = Municipality.objects.get_or_create(id=44001, name="Manchester")
        print "Manchester municipality added."

    def import_pois_from_csv(self):
        muni = Municipality.objects.get(id=44001)
        for poi_info in POI_LIST:
            print "\tImporting %s" % poi_info['category']
            s = self.http.open_url(poi_info['url'], "manchester")
            cat, c = POICategory.objects.get_or_create(type=poi_info['category'], defaults={'description': poi_info['category_desc']})
            f = StringIO.StringIO(s)
            reader = csv.reader(f, delimiter=',', quotechar='"')
            # skip header
            reader.next()

            for idx, row in enumerate(reader):
                origin_id = "man-%s-%d" % (poi_info['category'], idx)
                try:
                    poi = POI.objects.get(origin_id=origin_id)
                except POI.DoesNotExist:
                    poi = POI(origin_id=origin_id)
                poi.name = row[poi_info['name_col']].strip()
                if not poi.name:
                    continue
                coords = row[poi_info['location_col']].strip()
                if not coords:
                    continue
                coords = [float(x) for x in coords.split(',')]
                if coords[0] > 180 or coords[0] < -180:
                    print "Skipping invalid coords for %s" % poi.name
                    continue
                poi.category = cat
                poi.municipality = muni
                poi.location = convert_from_wgs84(coords)
                poi.save()

    def import_pois_from_rest(self):
        URL_BASE = 'http://www.manchester.gov.uk/site/api/getdirectorylocationsbycategory.php?service=%d&postcode=M2+5DB&count=10000&format=json'

        muni = Municipality.objects.get(id=44001)
        for srv_id in SERVICE_CATEGORY_MAP.keys():
            cat_type, cat_desc = SERVICE_CATEGORY_MAP[srv_id]
            cat, c = POICategory.objects.get_or_create(type=cat_type, defaults={'description': cat_desc})

            print "\tImporting %s" % cat_type
            ret = requests.get(URL_BASE % srv_id)
            if ret.status_code != 200:
                raise Exception("HTTP request failed with %d" % ret.status_code)
            # Fix quoting bug
            s = ret.content.replace("\\'", "'")
            ret_json = json.loads(s)
            count = 0
            for srv_info in ret_json['items']:
                srv_id = "man-%s" % unicode(srv_info['uid'])
                try:
                    poi = POI.objects.get(origin_id=srv_id)
                except POI.DoesNotExist:
                    poi = POI(origin_id=srv_id)
                poi.name = urllib.unquote(srv_info['name'].replace('+', ' '))
                poi.category = cat
                poi.municipality = muni
                if 'address' in srv_info:
                    poi.street_address = srv_info['address']
                else:
                    poi.street_address = ''
                coords = srv_info['latlon'].strip()
                if not coords:
                    continue
                coords = [float(x) for x in coords.split(',')]
                poi.location = convert_from_wgs84(coords)
                poi.save()
                count = count + 1
            print "\t%d imported" % count

    def handle(self, **options):
        http = HttpFetcher()
        http.set_cache_dir(os.path.join(settings.PROJECT_ROOT, ".cache"))
        requests_cache.install_cache('geo_import_man')
        self.data_path = os.path.join(settings.PROJECT_ROOT, 'data')
        self.http = http
        print "Importing municipalities"
        self.import_municipalities()
        print "Importing POIs"
        self.import_pois_from_csv()
        self.import_pois_from_rest()
