"""
This management command updates parking areas according to new desired specification.
"""
from time import time
from typing import List

from django.core.management.base import BaseCommand
from munigeo.models import AdministrativeDivision, Municipality

PARKING_CLASS_NAME_MAP = {
    0: {"fi": "Muu", "sv": "Något annat", "en": "Other"},
    1: {
        "fi": "Ilmainen, pysäköinti sallittu 30 min, 1 h, 2 h tai 4 h",
        "sv": "Gratis, parkering tillåten 30 minuter, 1 timme, 2 timmar eller 4 timmar",
        "en": "Free, parking allowed for 30 minute, 1 hour, 2 hours or 4 hours",
    },
    2: {
        "fi": "Ilmainen, pysäköinti sallittu 24 h tai ilman aikarajoitusta",
        "sv": "Gratis, parkering tillåten 24/7 utan tidsbegränsning",
        "en": "Free, parking allowed for 24/7 without time limit",
    },
    3: {
        "fi": "Ilmainen, useimmilla paikoilla pysäköinti kielletty ma–pe 7–18, la 9–15",
        "sv": "Gratis, parkering är förbjuden på de flesta platser må-fre 7-18, lö 9-15",
        "en": "Free, parking forbidden in most places mon-fri 7–18, sat 9–15",
    },
    4: {
        "fi": "Maksullinen, pysäköinti sallittu 1 h tai 2 h",
        "sv": "Avgiftsbelagd, parkering tillåten 1 timme eller 2 timmar",
        "en": "Paid, parking allowed for 1 hour or 2 hours",
    },
    5: {
        "fi": "Maksullinen, pysäköinti sallittu 4 h",
        "sv": "Avgiftsbelagd, parkering tillåten 4 timmar",
        "en": "Paid, parking allowed for 4 hours",
    },
    6: {
        "fi": "Maksullinen, ei aikarajoitusta",
        "sv": "Avgiftsbelagd, ingen tidsbegränsning",
        "en": "Paid, without time limit",
    },
    7: {
        "fi": "Pysäköintikielto",
        "sv": "Parkeringsförbud",
        "en": "Parking ban",
    },
}


class Command(BaseCommand):
    help = "Update parking areas according to new desired specification."

    def handle(self, *args, **options) -> None:
        start_time = time()
        num_parking_areas_updated = 0
        municipality = Municipality.objects.get(name_fi="Vantaa")
        parking_areas = AdministrativeDivision.objects.filter(
            type__type="parking_area"
        ).exclude(municipality=municipality)
        for parking_area in parking_areas:
            extra = parking_area.extra
            parking_area.name_fi = PARKING_CLASS_NAME_MAP[int(extra["class"])]["fi"]
            parking_area.name_sv = PARKING_CLASS_NAME_MAP[int(extra["class"])]["sv"]
            parking_area.name_en = PARKING_CLASS_NAME_MAP[int(extra["class"])]["en"]

            new_periods = []  # type: List[str]
            prefix_days = ""
            validity_period = extra["validity_period"]
            # prevent validity period data overriding for already converted data
            if validity_period and not validity_period.islower():
                period_parts = (
                    validity_period.replace("(", "").replace(")", "").split(",")
                )
                period_parts_count = 1
                for period_part in period_parts:
                    if period_parts_count == 1:
                        prefix_days = "ma-pe "
                    if period_parts_count == 2:
                        prefix_days = "la "
                    if period_parts_count == 3:
                        prefix_days = "su "
                    new_periods.append(prefix_days + period_part.strip())
                    period_parts_count += 1
                parking_area.extra["validity_period"] = ", ".join(new_periods)
            parking_area.save()
            num_parking_areas_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{num_parking_areas_updated} parking areas updated "
                f"in {time() - start_time:.0f} seconds."
            )
        )
