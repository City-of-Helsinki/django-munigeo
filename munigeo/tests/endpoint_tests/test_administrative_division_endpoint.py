import pytest  # noqa: F401;

from rest_framework.reverse import reverse

from munigeo.tests.endpoint_tests.utils import get
from munigeo.tests.endpoint_tests.fixtures import *  # noqa: F403, F401;
from munigeo.tests.endpoint_tests.fixtures import bbox_muni, bbox_dist


def get_administrativedivision_list(api_client, data=None, query_string=None):
    url = reverse('administrativedivision-list')
    if query_string:
        url = '%s?%s' % (url, query_string)
        print(url)
    res = get(api_client, url, data=data).data
    res.sort(key=lambda r: r['id'])
    return res


@pytest.mark.django_db
def test_ocd_id_filter(administrative_divisions, api_client):
    ad = administrative_divisions

    res = get_administrativedivision_list(api_client, query_string='ocd_id=' + ad[1].ocd_id)
    assert len(res) == 1
    assert res[0]['id'] == 1
    assert res[0]['ocd_id'] == 'ocd-division/country:fi/kunta:muni_1'

    res = get_administrativedivision_list(api_client, query_string='ocd_id={0},{1}'.format(ad[3].ocd_id,
                                                                                           ad[5].ocd_id))
    assert len(res) == 2
    assert res[0]['id'] == 3
    assert res[0]['ocd_id'] == 'ocd-division/country:fi/peruspiiri:district_0'
    assert res[1]['id'] == 5
    assert res[1]['ocd_id'] == 'ocd-division/country:fi/peruspiiri:district_2'


@pytest.mark.django_db
def test_geometry_filter(administrative_divisions, api_client):
    bbox = bbox_muni + bbox_dist
    res = get_administrativedivision_list(api_client, query_string='geometry=true')
    assert len(res) == 6
    for i in range(len(res)):
        for j in range(0, 5, 2):
            if j == 2:
                assert res[i]['boundary']['coordinates'][0][0][j] == [bbox[i][2], bbox[i][3]]
            else:
                assert res[i]['boundary']['coordinates'][0][0][j] == [bbox[i][0], bbox[i][1]]


@pytest.mark.django_db
@pytest.mark.parametrize("test_input,expected", [('muni_', ['muni_0', 'muni_1', 'muni_2']),
                                                 ('district_', ['district_0', 'district_1', 'district_2']),
                                                 ('_0', ['muni_0', 'district_0'])])
def test_input_filter_param(administrative_divisions, api_client, test_input, expected):
    res = get_administrativedivision_list(api_client, query_string='input=' + test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['name'] == e


@pytest.mark.django_db
@pytest.mark.parametrize("test_input,expected", [('origin_muni_0', [0, 'origin_muni_0']),
                                                 ('origin_muni_2', [2, 'origin_muni_2']),
                                                 ('origin_district_1', [4, 'origin_district_1']),
                                                 ('origin_district_2', [5, 'origin_district_2'])])
def test_origin_id_filter(administrative_divisions, api_client, test_input, expected):
    res = get_administrativedivision_list(api_client, query_string='origin_id=' + test_input)
    assert len(res) == 1
    assert res[0]['id'] == expected[0]
    assert res[0]['origin_id'] == expected[1]


@pytest.mark.django_db
@pytest.mark.parametrize("test_input,expected", [('2020-06-16', list(range(0, 4))),
                                                 ('2020-08-7', list(range(0, 6))),
                                                 ('2020-5-4', list(range(0, 3))),
                                                 ('2019-12-01', list(range(0, 3))),
                                                 ('2022-12-01', list(range(0, 3)))])
def test_date_filter(administrative_divisions, api_client, test_input, expected):
    res = get_administrativedivision_list(api_client, query_string='date=' + test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == e
