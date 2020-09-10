"""
munigeo importer for Espoo data
"""

from munigeo.importer.base import register_importer
from munigeo.importer.helsinki import HelsinkiImporter


@register_importer
class EspooImporter(HelsinkiImporter):
    name = "espoo"
    wfs_output_format = None

    def __init__(self, *args, **kwargs):
        super(EspooImporter, self).__init__(*args, **kwargs)
        self.muni_data_path = 'fi/espoo'
