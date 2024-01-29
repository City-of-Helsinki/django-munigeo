# -*- coding: utf-8 -*-
import csv
import io
import json
import os

# import unicodecsv
import requests
import requests_cache
from django import db
from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, DataSource, SpatialReference
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Point

from munigeo import ocd
from munigeo.importer.base import Importer, register_importer
from munigeo.importer.sync import ModelSyncher
from munigeo.models import *

CITADEL_LIST = [
    {
        "url": "http://www.citadelonthemove.eu/Portals/0/PropertyAgent/517/Files/11/hospitals.json",
        "cat_map": {
            "hospital": {
                "category": "hospital",
                "category_desc": "Hospital",
            }
        },
    },
    {
        "url": "http://www.citadelonthemove.eu/Portals/0/PropertyAgent/517/Files/14/museums-galleries.json",
        "cat_map": {
            "galleries": {
                "category": "gallery",
                "category_desc": "Gallery",
            },
            "museums": {
                "category": "museum",
                "category_desc": "Museum",
            },
        },
    },
    {
        "url": "http://www.citadelonthemove.eu/Portals/0/PropertyAgent/517/Files/12/hotel_conventioncenter.json",
        "cat_map": {
            "hotels": {
                "category": "hotel",
                "category_desc": "Hotel",
            },
            "hotel": {
                "category": "hotel",
                "category_desc": "Hotel",
            },
            "convention center": {
                "category": "convention center",
                "category_desc": "Convention center",
            },
        },
    },
    {
        "url": "http://www.citadelonthemove.eu/Portals/0/PropertyAgent/517/Files/5/ParkingAthens.json",
        "cat_map": {
            "Parking": {
                "category": "parking",
                "category_desc": "Parking lot",
            }
        },
    },
]


def convert_from_wgs84(coords):
    pnt = Point(coords[1], coords[0], srid=4326)
    pnt.transform(PROJECTION_SRID)
    return pnt


@register_importer
class AthensImporter(Importer):
    name = "athens"

    def __init__(self, *args, **kwargs):
        super(AthensImporter, self).__init__(*args, **kwargs)
        self.data_path = self.options["data_path"]
        self.muni_data_path = os.path.join(self.data_path, "gr", "athens")

    def import_municipalities(self):
        muni, c = Municipality.objects.get_or_create(id=30001, name="Athens")
        self.logger.info("Athens municipality added.")

    def import_pois_from_citadel(self):
        muni = Municipality.objects.get(id=30001)
        for d in CITADEL_LIST:
            self._import_citadel(muni, d)

    def import_pois(self):
        requests_cache.install_cache("geo_import_athens")
        self.logger.info("Importing POIs from Citadel")
        self.import_pois_from_citadel()
