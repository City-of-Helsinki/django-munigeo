import pytest  # noqa: F401;

from rest_framework.reverse import reverse

from munigeo.tests.endpoint_tests.utils import get
from munigeo.tests.endpoint_tests.fixtures import *  # noqa: F403, F401;


def get_administrativedivision_list(api_client, data=None, query_string=None):
    url = reverse('administrativedivision-list')
    if query_string:
        url = '%s?%s' % (url, query_string)
        print(url)
    res = get(api_client, url, data=data).data['results']
    res.sort(key=lambda r: r['id'])
    return res


@pytest.mark.django_db
def test_page_filter(administrative_divisions, api_client):
    res = get_administrativedivision_list(api_client, query_string='page=1')
    assert len(res) == 6
    assert res[0]['id'] == 0
    assert res[3]['id'] == 3
    assert res[5]['id'] == 5

    res = get_administrativedivision_list(api_client, query_string='page=1&page_size=2')
    assert len(res) == 2
    assert res[0]['id'] == 4
    assert res[1]['id'] == 5

    res = get_administrativedivision_list(api_client, query_string='page=2&page_size=3')
    assert len(res) == 3
    assert res[0]['id'] == 0
    assert res[2]['id'] == 2


@pytest.mark.django_db
def test_ocd_id_filter(administrative_divisions, api_client):
    ad = [administrative_divisions[0], administrative_divisions[1], administrative_divisions[2],
          administrative_divisions[3], administrative_divisions[4], administrative_divisions[5]]
    res = get_administrativedivision_list(api_client, query_string='ocd_id=' + ad[1])
    assert len(res) == 1
    assert res[0]['id'] == 1
    assert res[0]['ocd_id'] == ad[1].get('ocd_id')

    res = get_administrativedivision_list(api_client, query_string='ocd_id={0},{1}'.format(ad[3], ad[5]))
    assert len(res) == 2
    assert res[0]['id'] == 3
    assert res[0]['ocd_id'] == 'ocd-division/country:fi/peruspiiri:district_0'
    assert res[1]['id'] == 5
    assert res[0]['ocd_id'] == 'ocd-division/country:fi/peruspiiri:district_2'


@pytest.mark.skip(reason="waiting for implementation, temporary disabled")
@pytest.mark.django_db
def test_geometry_filter(administrative_divisions, api_client):
    res = get_administrativedivision_list(api_client, query_string='geometry=true')
    assert len(res) == 6
    assert len(res[0]['boundary']['coordinates']) == 0
    assert res[0]['boundary']['coordinates'] == 0


@pytest.mark.skip(reason="waiting for implementation, temporary disabled")
@pytest.mark.django_db
def test_input_filter(administrative_divisions, api_client):
    res = get_administrativedivision_list(api_client, query_string='input=municipality')
    assert len(res) == 6


@pytest.mark.skip(reason="waiting for implementation, temporary disabled")
@pytest.mark.django_db
def test_origin_id_filter(administrative_divisions, api_client):
    res = get_administrativedivision_list(api_client, query_string='origin_id=origin_muni_0')
    assert len(res) == 1
    assert res[0]['origin_id'] == 0


@pytest.mark.skip(reason="waiting for implementation, temporary disabled")
@pytest.mark.django_db
def test_date_filter(administrative_divisions, api_client):
    res = get_administrativedivision_list(api_client, query_string='date=2019-7')
    assert len(res) == 1
    assert res[0]['id'] == 0

