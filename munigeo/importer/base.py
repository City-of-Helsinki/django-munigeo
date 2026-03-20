import json
import logging
import os
from functools import cached_property

import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from django.utils.text import slugify

from munigeo.models import POI, PROJECTION_SRID, POICategory


def convert_from_wgs84(coords):
    pnt = Point(coords[1], coords[0], srid=4326)
    pnt.transform(PROJECTION_SRID)
    return pnt


class Importer(object):
    def __init__(self, options):
        self.logger = logging.getLogger("import")
        self.options = options

    @cached_property
    def data_paths(self):
        data_paths = []
        if getattr(settings, "IMPORT_DATA_PATH", None):
            data_paths.append(settings.IMPORT_DATA_PATH)

        if hasattr(settings, "PROJECT_ROOT"):
            root_dir = settings.PROJECT_ROOT
        else:
            root_dir = settings.BASE_DIR
        data_paths.append(os.path.join(root_dir, "data"))

        module_path = os.path.dirname(__file__)
        app_path = os.path.abspath(os.path.join(module_path, "..", "data"))
        data_paths.append(app_path)

        return data_paths

    @property
    def import_data_path(self):
        """
        Path for storing temporary data for imports.

        If set, uses IMPORT_DATA_PATH. Otherwise, uses the first data path
        set in data_paths (which should be either PROJECT_ROOT or BASE_DIR).
        """
        if getattr(settings, "IMPORT_DATA_PATH", None):
            return settings.IMPORT_DATA_PATH
        return self.data_paths[0]

    def _import_citadel(self, muni, info):
        muni_slug = slugify(muni.name)

        self.logger.info("Importing from Citadel")
        resp = requests.get(info["url"])
        assert resp.status_code == 200
        s = resp.content.decode("utf8")
        resp_json = json.loads(s)

        for d in resp_json["dataset"]["poi"]:
            citadel_type = d["category"][0]
            cat_info = info["cat_map"][citadel_type]
            cat, _ = POICategory.objects.get_or_create(
                type=cat_info["category"],
                defaults={"description": cat_info["category_desc"]},
            )

            origin_id = "%s-%s-%s" % (muni_slug, cat.type, d["id"])

            try:
                poi = POI.objects.get(origin_id=origin_id)
            except POI.DoesNotExist:
                poi = POI(origin_id=origin_id)
            poi.name = d["title"].strip()
            coords = d["location"]["point"]["pos"]["posList"]
            if not coords:
                continue
            coords = [float(x) for x in coords.split(" ")]
            if coords[0] > 180 or coords[0] < -180:
                self.logger.info("Skipping invalid coords for %s" % poi.name)
                continue
            poi.category = cat
            poi.municipality = muni
            poi.location = convert_from_wgs84(coords)
            poi.save()
            self.logger.info(poi)

    def find_data_file(self, data_file):
        for path in self.data_paths:
            full_path = os.path.join(path, data_file)
            if os.path.exists(full_path):
                return full_path
        raise FileNotFoundError("Data file '%s' not found" % data_file)


importers = {}


def register_importer(klass):
    importers[klass.name] = klass
    return klass


def get_importers():
    if importers:
        return importers
    module_path = __name__.rpartition(".")[0]
    # Importing the packages will cause their register_importer() methods
    # being called.
    for fname in os.listdir(os.path.dirname(__file__)):
        module, ext = os.path.splitext(fname)
        if ext.lower() != ".py":
            continue
        if module in ("__init__", "base"):
            continue
        full_path = "%s.%s" % (module_path, module)
        ret = __import__(full_path, locals(), globals())
    return importers
