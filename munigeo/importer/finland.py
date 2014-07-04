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
# Disable threaded mode for now
ThreadPoolExecutor = None


@register_importer
class FinlandImporter(Importer):
    name = "finland"

    def _process_muni(self, syncher, feat):
        muni_id = str(feat.get('nationalCode'))
        t = feat.get('text')
        m = re.match(r'\(2:([\w\s:-]+),([\w\s:-]+)\)', t)
        name_fi = m.groups()[0]
        name_sv = m.groups()[1]
        print(name_fi)

        munidiv = syncher.get(muni_id)
        if not munidiv:
            munidiv = AdministrativeDivision(origin_id=muni_id)
        munidiv.name_fi = name_fi
        munidiv.name_sv = name_sv
        munidiv.ocd_id = ocd.make_id(country='fi', kunta=name_fi)
        munidiv.type = self.muni_type
        munidiv.save()
        syncher.mark(munidiv)

        try:
            geom_obj = munidiv.geometry
        except AdministrativeDivisionGeometry.DoesNotExist:
            geom_obj = AdministrativeDivisionGeometry(division=munidiv)
        geom = feat.geom
        geom.transform(PROJECTION_SRID)
        # Store only the land boundaries
        #geom = geom.geos.intersection(self.land_area)
        geom = geom.geos
        if geom.geom_type == 'Polygon':
            geom = MultiPolygon(geom)
        geom_obj.boundary = geom
        geom_obj.save()

        try:
            muni = Municipality.objects.get(division=munidiv)
        except Municipality.DoesNotExist:
            muni = Municipality(division=munidiv)
        muni.name_fi = name_fi
        muni.name_sv = name_sv
        muni.id = munidiv.ocd_id.split('/')[-1].split(':')[-1]
        muni.save()

    def _setup_land_area(self):
        fin_bbox = Polygon.from_bbox(FIN_GRID)
        fin_bbox.srid = TM35_SRID
        fin_bbox.transform(4326)
        print("Loading global land shape")
        path = self.find_data_file('global/ne_10m_land.shp')
        ds = DataSource(path)
        land = ds[0][0]
        self.land_area = fin_bbox.intersection(land.geom.geos)
        self.land_area.transform(PROJECTION_SRID)

    def import_municipalities(self):
        #self._setup_land_area()

        print("Loading municipality boundaries")
        path = self.find_data_file('fi/SuomenKuntajako_2013_10k.xml')
        ds = DataSource(path)
        lyr = ds[0]
        assert lyr.name == "AdministrativeUnit"

        defaults = {'name': 'Municipality'}
        muni_type, _ = AdministrativeDivisionType.objects.get_or_create(type='muni', defaults=defaults)
        self.muni_type = muni_type

        syncher = ModelSyncher(AdministrativeDivision.objects.filter(type=muni_type), lambda obj: obj.origin_id)

        # If running under Python 3, parallelize the heavy lifting.
        if ThreadPoolExecutor:
            executor = ThreadPoolExecutor(max_workers=8)
            futures = []
        else:
            executor = None

        with db.transaction.atomic():
            with AdministrativeDivision.objects.disable_mptt_updates():
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

            AdministrativeDivision.objects.rebuild()
