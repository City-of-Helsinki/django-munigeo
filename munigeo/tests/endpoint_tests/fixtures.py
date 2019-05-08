import pytest
from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.gis.geos import Point, Polygon, MultiPolygon
from rest_framework.test import APIClient

from munigeo.models import AdministrativeDivisionType, AdministrativeDivision, AdministrativeDivisionGeometry, \
    Municipality, Address, Street


TODAY = datetime.now()

bbox_muni = [
    [24.916821, 60.163376, 24.960937, 60.185233],
    [24.818115, 60.179770, 24.840045, 60.190695],
    [24.785500, 60.272642, 25.004797, 60.342920]
]
bbox_dist = [
    [24.92, 60.17, 24.95, 60.18],
    [24.82, 60.18, 24.83, 60.185],
    [24.80, 60.28, 24.85, 60.30]
]


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
@pytest.mark.django_db
def administrative_divisions():
    geo_muni = [MultiPolygon(Polygon.from_bbox(tuple(bbox))) for bbox in bbox_muni]
    geo_dist = [MultiPolygon(Polygon.from_bbox(tuple(bbox))) for bbox in bbox_dist]

    start = datetime(year=2020, month=6, day=1)
    end = datetime(year=2020, month=9, day=1)

    t_0, _ = AdministrativeDivisionType.objects.get_or_create(id=1, type='muni', defaults={'name': 'Municipality'})
    t_1, _ = AdministrativeDivisionType.objects.get_or_create(id=2, type='district', defaults={'name': 'Peruspiiri'})
    a_munis = []

    # municipalities
    for i in range(3):
        n = str(i)
        a, _ = AdministrativeDivision.objects.get_or_create(id=i, type=t_0, name='muni_' + n,
                                                            origin_id='origin_muni_' + n,
                                                            ocd_id='ocd-division/country:fi/kunta:muni_' + n)
        a_munis.append(a)
        AdministrativeDivisionGeometry.objects.get_or_create(division=a, boundary=geo_muni[i])

    # districts
    for i in range(3):
        n = str(i)
        a, _ = AdministrativeDivision.objects.get_or_create(id=i + 3, type=t_1, name='district_' + n,
                                                            origin_id='origin_district_' + n,
                                                            ocd_id='ocd-division/country:fi/peruspiiri:district_' + n,
                                                            parent=a_munis[i],
                                                            start=start + relativedelta(months=i),
                                                            end=end + relativedelta(months=i))
        AdministrativeDivisionGeometry.objects.get_or_create(division=a, boundary=geo_dist[i])
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
