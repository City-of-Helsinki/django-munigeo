# -*- coding: utf-8 -*-
import os
from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import activate, get_language

from munigeo.importer.base import get_importers

class Command(BaseCommand):
    args = '<module>'
    help = "Import geo data"
    option_list = list(BaseCommand.option_list + (
        make_option('--all', action='store_true', dest='all', help='Import all entities'),
    ))

    importer_types = ['municipalities', 'divisions', 'addresses', 'pois']

    def __init__(self):
        super(Command, self).__init__()
        for imp in self.importer_types:
            opt = make_option('--%s' % imp, dest=imp, action='store_true', help='import %s' % imp)
            self.option_list.append(opt)

    def handle(self, *args, **options):
        importers = get_importers()
        imp_list = ', '.join(sorted(importers.keys()))
        if len(args) != 1:
            raise CommandError("Enter the name of the geo importer module. Valid importers: %s" % imp_list)
        if not args[0] in importers:
            raise CommandError("Importer %s not found. Valid importers: %s" % imp_list)
        imp_class = importers[args[0]]

        if hasattr(settings, 'PROJECT_ROOT'):
            root_dir = settings.PROJECT_ROOT
        else:
            root_dir = settings.BASE_DIR
        importer = imp_class({'data_path': os.path.join(root_dir, 'data')})

        # Activate the default language for the duration of the import
        # to make sure translated fields are populated correctly.
        old_lang = get_language()
        activate(settings.LANGUAGES[0][0])

        for imp_type in self.importer_types:
            name = "import_%s" % imp_type
            method = getattr(importer, name, None)
            if options[imp_type]:
                if not method:
                    raise CommandError("Importer %s does not support importing %s" % (name, imp_type))
            else:
                if not options['all']:
                    continue

            if method:
                method()

        activate(old_lang)
