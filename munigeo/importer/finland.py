"""
munigeo importer for Finnish nation-level data
"""

import re
import os
import zipfile
import requests
import io

from django import db
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon, Polygon

from munigeo.importer.base import Importer, register_importer
from munigeo.importer.sync import ModelSyncher
from munigeo.models import AdministrativeDivision, AdministrativeDivisionGeometry, AdministrativeDivisionType, \
    Municipality, PROJECTION_SRID
from munigeo import ocd
from .helsinki import FIN_GRID, TM35_SRID

try:
    from concurrent.futures import ThreadPoolExecutor
except ImportError:
    ThreadPoolExecutor = None
# Disable threaded mode for now
ThreadPoolExecutor = None

MUNI_DATA_URL = 'http://kartat.kapsi.fi/files/kuntajako/kuntajako_1000k/etrs89/gml/TietoaKuntajaosta_2016_1000k.zip'


@register_importer
class FinlandImporter(Importer):
    name = "finland"

    def _process_muni(self, syncher, feat):
        muni_id = str(feat.get('nationalCode'))
        t = feat.get('text')
        m = re.match(r'\(2:([\w\s:-]+),([\w\s:-]+)\)', t)
        name_fi = m.groups()[0]
        name_sv = m.groups()[1]
        self.logger.debug(name_fi)

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
        # geom = geom.geos.intersection(self.land_area)
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
        self.logger.debug("Loading global land shape")
        path = self.find_data_file('global/ne_10m_land.shp')
        ds = DataSource(path)
        land = ds[0][0]
        self.land_area = fin_bbox.intersection(land.geom.geos)
        self.land_area.transform(PROJECTION_SRID)

    def load_muni_data(self):
        self.logger.info("Loading Finnish municipalities")
        resp = requests.get(MUNI_DATA_URL)
        with io.BytesIO(resp.content) as f:
            zf = zipfile.ZipFile(f)
            for name in zf.namelist():
                if name.endswith('.xml'):
                    break
            else:
                raise Exception('XML file not found in %s' % MUNI_DATA_URL)
            out_path = os.path.join(self.data_paths[0], 'fi')
            try:
                os.makedirs(out_path)
            except OSError:
                pass
            zf.extract(name, out_path)
            return os.path.join(out_path, name)

    def find_muni_data(self):
        for root_path in self.data_paths:
            base_path = os.path.join(root_path, 'fi')
            if not os.path.exists(base_path):
                os.makedirs(base_path)
            paths = os.listdir(base_path)
            for p in paths:
                if 'Kuntajaosta' in p:
                    break
            else:
                return self.load_muni_data()
            xml_dir = p
            base_path = os.path.join(base_path, xml_dir)
            paths = os.listdir(base_path)
            for p in paths:
                if p.endswith('.xml'):
                    break
            else:
                return self.load_muni_data()
            return os.path.join(base_path, p)

    def import_municipalities(self):
        # self._setup_land_area()

        self.logger.info("Loading municipality boundaries")
        path = self.find_muni_data()
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
