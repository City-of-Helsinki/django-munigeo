import pytest
from django.contrib.gis.geos import Point
from django.http import QueryDict
from rest_framework.exceptions import ParseError
from unittest.mock import patch
from munigeo.api import parse_lat_lon, DATABASE_SRID


@pytest.mark.django_db
class TestParseLatLon:
    def test_parse_lat_lon_valid_coordinates(self):
        """Test parsing valid latitude and longitude"""
        query_params = QueryDict('lat=60.1699&lon=24.9384')
        point = parse_lat_lon(query_params)

        assert isinstance(point, Point)
        assert point.srid == DATABASE_SRID

    def test_parse_lat_lon_no_parameters(self):
        """Test returns None when no lat/lon provided"""
        query_params = QueryDict('')
        result = parse_lat_lon(query_params)

        assert result is None

    def test_parse_lat_lon_missing_lat(self):
        """Test raises error when only lon is provided"""
        query_params = QueryDict('lon=24.9384')

        with pytest.raises(ParseError) as exc:
            parse_lat_lon(query_params)

        assert "both 'lat' and 'lon'" in str(exc.value)

    def test_parse_lat_lon_missing_lon(self):
        """Test raises error when only lat is provided"""
        query_params = QueryDict('lat=60.1699')

        with pytest.raises(ParseError) as exc:
            parse_lat_lon(query_params)

        assert "both 'lat' and 'lon'" in str(exc.value)

    def test_parse_lat_lon_invalid_lat_format(self):
        """Test raises error for non-numeric latitude"""
        query_params = QueryDict('lat=invalid&lon=24.9384')

        with pytest.raises(ParseError) as exc:
            parse_lat_lon(query_params)

        assert "floating point numbers" in str(exc.value)

    def test_parse_lat_lon_invalid_lon_format(self):
        """Test raises error for non-numeric longitude"""
        query_params = QueryDict('lat=60.1699&lon=invalid')

        with pytest.raises(ParseError) as exc:
            parse_lat_lon(query_params)

        assert "floating point numbers" in str(exc.value)

    def test_parse_lat_lon_lat_out_of_range_high(self):
        """Test raises error when latitude > 90"""
        query_params = QueryDict('lat=91.0&lon=24.9384')

        with pytest.raises(ParseError) as exc:
            parse_lat_lon(query_params)

        assert "between -90 and 90" in str(exc.value)

    def test_parse_lat_lon_lat_out_of_range_low(self):
        """Test raises error when latitude < -90"""
        query_params = QueryDict('lat=-91.0&lon=24.9384')

        with pytest.raises(ParseError) as exc:
            parse_lat_lon(query_params)

        assert "between -90 and 90" in str(exc.value)

    def test_parse_lat_lon_lon_out_of_range_high(self):
        """Test raises error when longitude > 180"""
        query_params = QueryDict('lat=60.1699&lon=181.0')

        with pytest.raises(ParseError) as exc:
            parse_lat_lon(query_params)

        assert "between -180 and 180" in str(exc.value)

    def test_parse_lat_lon_lon_out_of_range_low(self):
        """Test raises error when longitude < -180"""
        query_params = QueryDict('lat=60.1699&lon=-181.0')

        with pytest.raises(ParseError) as exc:
            parse_lat_lon(query_params)

        assert "between -180 and 180" in str(exc.value)

    @pytest.mark.skipif(
        DATABASE_SRID != 3067,
        reason="Only applies to Finnish coordinate systems"
    )
    def test_parse_lat_lon_outside_finland_bounds(self):
        """Test raises error for coordinates outside Finland"""
        query_params = QueryDict('lat=40.0&lon=10.0')

        with pytest.raises(ParseError) as exc:
            parse_lat_lon(query_params)

        assert "outside the valid area for Finland" in str(exc.value)

    @pytest.mark.skipif(
        DATABASE_SRID != 3067,
        reason="Only applies to Finnish coordinate systems"
    )
    def test_parse_lat_lon_within_finland_bounds(self):
        """Test valid coordinates within Finland bounds"""
        query_params = QueryDict('lat=60.1699&lon=24.9384')
        point = parse_lat_lon(query_params)

        assert point is not None
        assert isinstance(point, Point)

    @patch('munigeo.api.DATABASE_SRID', 4326)
    def test_parse_lat_lon_boundary_values(self):
        """Test coordinates at valid boundaries"""
        query_params = QueryDict('lat=90&lon=180')
        point = parse_lat_lon(query_params)
        assert point is not None

        query_params = QueryDict('lat=-90&lon=-180')
        point = parse_lat_lon(query_params)
        assert point is not None

    def test_parse_lat_lon_coordinate_transformation(self):
        """Test coordinate transformation when DEFAULT_SRID != DATABASE_SRID"""
        query_params = QueryDict('lat=60.1699&lon=24.9384')
        point = parse_lat_lon(query_params)

        assert point.srid == DATABASE_SRID

    def test_parse_lat_lon_zero_coordinates(self):
        """Test that 0 is treated as a valid coordinate value"""
        query_params = QueryDict('lat=0&lon=0')

        with patch('munigeo.api.DATABASE_SRID', 4326):
            point = parse_lat_lon(query_params)

        assert point is not None
        assert point.x == pytest.approx(0.0)
        assert point.y == pytest.approx(0.0)
