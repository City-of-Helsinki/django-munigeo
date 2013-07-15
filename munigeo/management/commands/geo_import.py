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
        make_option('--district', action='store_true', dest='district', help='Import muni districts'),
        make_option('--plan', action='store_true', dest='plan', help='Import muni plan'),
        make_option('--address', action='store_true', dest='address', help='Import addresses'),
        make_option('--poi', action='store_true', dest='poi', help='Import POIs'),
        make_option('--all', action='store_true', dest='all', help='Import all entities.'),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Enter the name of the geo importer module.")
        module = __import__('munigeo.importer.%s' % args[0], globals(), locals(), ['Importer'])
        importer = module.Importer()
        importer.data_path = os.path.join(settings.PROJECT_ROOT, 'data')
        if options['all'] or options['municipality']:
            print "Importing municipalities"
            importer.import_municipalities()
        if options['all'] or options['district']:
            print "Importing districts"
            importer.import_districts()
        if options['all'] or options['plan']:
            print "Importing plans"
            importer.import_plans()
        if options['all'] or options['address']:
            print "Importing addresses"
            importer.import_addresses()
        if options['all'] or options['poi']:
            print "Importing POIs"
            importer.import_pois()
