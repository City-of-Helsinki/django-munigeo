"""
munigeo importer for Finnish nation-level data
"""

import re
import os

from django import db
from django.contrib.gis.gdal import DataSource, SpatialReference, CoordTransform
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon, Point

from munigeo.importer.base import Importer, register_importer
from munigeo.importer.sync import ModelSyncher
from munigeo.models import *
from munigeo import ocd

try:
    from concurrent.futures import ThreadPoolExecutor
except ImportError:
    ThreadPoolExecutor = None


@register_importer
class FinlandImporter(Importer):
    name = "finland"

    def __init__(self, options):
        self.data_path = options['data_path']
        self.options = options

    @db.transaction.atomic
    def _process_muni(self, syncher, feat):
        muni_id = str(feat.get('nationalCode'))
        t = feat.get('text')
        m = re.match(r'\(2:([\w\s:-]+),([\w\s:-]+)\)', t)
        name_fi = m.groups()[0]
        name_sv = m.groups()[1]
        print(name_fi)

        muni = syncher.get(muni_id)
        if not muni:
            muni = Municipality(origin_id=muni_id)
        muni.name_fi = name_fi
        muni.name_sv = name_sv
        muni.ocd_id = ocd.make_id(country='fi', kunta=name_fi)
        muni.save()
        syncher.mark(muni)

        try:
            geom_obj = muni.geometry
        except AdministrativeDivisionGeometry.DoesNotExist:
            geom_obj = AdministrativeDivisionGeometry(division=muni)
        geom = feat.geom
        geom.transform(PROJECTION_SRID)
        # Store only the land boundaries
        #geom = geom.geos.intersection(self.land_area)
        geom = geom.geos
        if geom.geom_type == 'Polygon':
            geom = MultiPolygon(geom)
        geom_obj.boundary = geom
        geom_obj.save()

    def _setup_land_area(self):
        fin_bbox = Polygon.from_bbox(FIN_GRID)
        fin_bbox.srid = TM35_SRID
        fin_bbox.transform(4326)
        print("Loading global land shape")
        path = os.path.join(self.data_path, 'global', 'ne_10m_land.shp')
        ds = DataSource(path)
        land = ds[0][0]
        self.land_area = fin_bbox.intersection(land.geom.geos)
        self.land_area.transform(PROJECTION_SRID)

    def import_municipalities(self):
        #self._setup_land_area()

        print("Loading municipality boundaries")
        path = os.path.join(self.data_path, 'fi', 'SuomenKuntajako_2013_10k.xml')
        ds = DataSource(path)
        lyr = ds[0]
        assert lyr.name == "AdministrativeUnit"

        syncher = ModelSyncher(Municipality.objects.all(), lambda obj: obj.origin_id)

        # If running under Python 3, parallelize the heavy lifting.
        if ThreadPoolExecutor:
            executor = ThreadPoolExecutor(max_workers=8)
            futures = []
        else:
            executor = None
        for idx, feat in enumerate(lyr):
            if feat.get('nationalLevel') != '4thOrder':
                continue
            # Process the first in a single-threaded way to catch
            # possible exceptions early.
            if executor and idx > 0:
                futures.append(executor.submit(self._process_muni, syncher, feat))
            else:
                self._process_muni(syncher, feat)
        if executor:
            for f in futures:
                res = f.result()
            executor.shutdown()
