# -*- coding: utf-8 -*-
import os
from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    args = '<module>'
    help = "Import geo data"
    option_list = BaseCommand.option_list + (
        make_option('--municipality', action='store_true', dest='municipality', help='Import municipalities'),
        make_option('--division', action='store_true', dest='division', help='Import administrative divisions'),
        make_option('--address', action='store_true', dest='address', help='Import addresses'),
        make_option('--poi', action='store_true', dest='poi', help='Import POIs'),
        make_option('--all', action='store_true', dest='all', help='Import all entities.'),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Enter the name of the geo importer module.")
        module = __import__('munigeo.importer.%s' % args[0], globals(), locals(), ['Importer'])

        if hasattr(settings, 'PROJECT_ROOT'):
            root_dir = settings.PROJECT_ROOT
        else:
            root_dir = settings.BASE_DIR
        importer = module.Importer(data_path=os.path.join(root_dir, 'data'))

        if options['all'] or options['municipality']:
            print("Importing municipalities")
            importer.import_municipalities()
        if options['all'] or options['division']:
            print("Importing administrative divisions")
            importer.import_divisions()
        if options['all'] or options['address']:
            print("Importing addresses")
            importer.import_addresses()
        if options['all'] or options['poi']:
            print("Importing POIs")
            importer.import_pois()
