# -*- coding: utf-8 -*-
import os
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import activate, get_language

from munigeo.importer.base import get_importers


class Command(BaseCommand):
    help = "Import geo data"

    importer_types = ["municipalities", "divisions", "addresses", "pois"]

    def add_arguments(self, parser):
        parser.add_argument("module", type=str)
        parser.add_argument(
            "--all", action="store_true", dest="all", help="Import all entities"
        )
        for imp in self.importer_types:
            parser.add_argument(
                "--%s" % imp, dest=imp, action="store_true", help="import %s" % imp
            )

    def __init__(self):
        super(Command, self).__init__()

    def handle(self, *args, **options):
        importers = get_importers()
        imp_list = ", ".join(sorted(importers.keys()))
        imp_name = options.get("module")
        if not imp_name:
            raise CommandError(
                "Enter the name of the geo importer module. Valid importers: %s"
                % imp_list
            )
        if imp_name not in importers:
            raise CommandError(
                "Importer %s not found. Valid importers: %s" % (args[0], imp_list)
            )
        imp_class = importers[imp_name]
        importer = imp_class(options)

        # Activate the default language for the duration of the import
        # to make sure translated fields are populated correctly.
        old_lang = get_language()
        activate(settings.LANGUAGES[0][0])

        for imp_type in self.importer_types:
            name = "import_%s" % imp_type
            method = getattr(importer, name, None)
            if options[imp_type]:
                if not method:
                    raise CommandError(
                        "Importer %s does not support importing %s" % (name, imp_type)
                    )
            else:
                if not options["all"]:
                    continue

            if method:
                method()

        activate(old_lang)
