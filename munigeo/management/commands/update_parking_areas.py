"""
This management command updates parking areas according to new desired specification.
"""
from time import time
from typing import List

from django.core.management.base import BaseCommand
from munigeo.models import AdministrativeDivision

PARKING_CLASS_NAME_MAP = {
    0: "Muu",
    1: "Ilmainen, pysäköinti sallittu 30 min, 1 h, 2 h tai 4 h",
    2: "Ilmainen, pysäköinti sallittu 24 h tai ilman aikarajoitusta",
    3: "Ilmainen, pysäköinti kielletty useimmilla paikoilla ma–pe 7–18, la 9–15",
    4: "Maksullinen, pysäköinti sallittu 1 h tai 2 h",
    5: "Maksullinen, pysäköinti sallittu 4 h",
    6: "Maksullinen, ei aikarajoitusta",
}


class Command(BaseCommand):
    help = "Update parking areas according to new desired specification."

    def handle(self, *args, **options) -> None:
        start_time = time()
        num_parking_areas_updated = 0
        parking_areas = AdministrativeDivision.objects.filter(type__type="parking_area")
        for parking_area in parking_areas:
            extra = parking_area.extra
            parking_area.name_fi = PARKING_CLASS_NAME_MAP[int(extra["class"])]

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
