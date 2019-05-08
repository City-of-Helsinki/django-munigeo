import pytest
from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.gis.geos import Point, Polygon, MultiPolygon
from rest_framework.test import APIClient

from munigeo.models import AdministrativeDivisionType, AdministrativeDivision, AdministrativeDivisionGeometry, \
    Municipality, Address, Street


TODAY = datetime.now()
bbox_0 = MultiPolygon(Polygon.from_bbox((24.916821, 60.163376, 24.960937, 60.185233)), srid=4326)
bbox_00 = MultiPolygon(Polygon.from_bbox((24.92, 60.17, 24.95, 60.18)), srid=4326)
bbox_1 = MultiPolygon(Polygon.from_bbox((24.818115, 60.179770, 24.840045, 60.190695)), srid=4326)
bbox_11 = MultiPolygon(Polygon.from_bbox((24.82, 60.18, 24.83, 60.185)), srid=4326)
bbox_2 = MultiPolygon(Polygon.from_bbox((24.785500, 60.272642, 25.004797, 60.342920)), srid=4326)
bbox_22 = MultiPolygon(Polygon.from_bbox((24.80, 60.28, 24.85, 60.30)), srid=4326)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
@pytest.mark.django_db
def administrative_divisions():
    bbox_muni = [bbox_0, bbox_1, bbox_2]
    bbox_dist = [bbox_00, bbox_11, bbox_22]

    start = datetime(year=2020, month=6, day=1)
    end = datetime(year=2020, month=9, day=1)

    t_0, _ = AdministrativeDivisionType.objects.get_or_create(id=1, type='muni', defaults={'name': 'Municipality'})
    t_1, _ = AdministrativeDivisionType.objects.get_or_create(id=2, type='district', defaults={'name': 'Peruspiiri'})
    a_munis = []

    # municipalities
    for i in range(3):
        n = str(i)
        a, _ = AdministrativeDivision.objects.get_or_create(id=i, type=t_0, name_fi='muni_' + n,
                                                            origin_id='origin_muni_' + n,
                                                            ocd_id='ocd-division/country:fi/kunta:muni_' + n)
        a_munis.append(a)
        AdministrativeDivisionGeometry.objects.get_or_create(division=a, boundary=bbox_muni[i])

    # districts
    for i in range(3):
        n = str(i)
        a, _ = AdministrativeDivision.objects.get_or_create(id=i + 3, type=t_1, name_fi='district_' + n,
                                                            origin_id='origin_district_' + n,
                                                            ocd_id='ocd-division/country:fi/peruspiiri:district_' + n,
                                                            parent=a_munis[i],
                                                            start=start + relativedelta(months=i),
                                                            end=end + relativedelta(months=i))
        AdministrativeDivisionGeometry.objects.get_or_create(division=a, boundary=bbox_dist[i])
    print('ADMIN_DIVS', AdministrativeDivision.objects.values())
    return AdministrativeDivision.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def municipalities(administrative_divisions):
    ad = [administrative_divisions[0], administrative_divisions[1], administrative_divisions[2]]
    for i in range(3):
        n = str(i)
        Municipality.objects.get_or_create(id='muni_' + n, name_fi='muni_' + n, division=ad[i])
    return Municipality.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def addresses(municipalities):
    pnt = Point(24.948475627, 60.180769286, srid=4326)
    t, _ = Street.objects.get_or_create(name='Porthaninrinne', municipality=municipalities[0])
    Address.objects.get_or_create(street=t, location=pnt)
    return Address.objects.all().order_by('pk')
