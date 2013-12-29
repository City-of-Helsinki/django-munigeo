import json
import re

from django.db.models import Q
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from tastypie.http import HttpBadRequest
from tastypie.resources import ModelResource
from tastypie.exceptions import InvalidFilterError, ImmediateHttpResponse
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.contrib.gis.resources import ModelResource as GeometryModelResource
from tastypie import fields
from munigeo.models import *

class MunicipalityResource(ModelResource):
    def _convert_to_geojson(self, bundle):
        muni = bundle.obj
        data = {'type': 'Feature'}
        data['properties'] = bundle.data
        data['id'] = bundle.obj.pk
        borders = muni.municipalityboundary.borders
        data['geometry'] = json.loads(borders.geojson)
        bundle.data = data
        return bundle
    def alter_detail_data_to_serialize(self, request, bundle):
        if request.GET.get('format') == 'geojson':
            return self._convert_to_geojson(bundle)
        return bundle
    def alter_list_data_to_serialize(self, request, bundles):
        if request.GET.get('format') != 'geojson':
            return bundles
        data = {'type': 'FeatureCollection'}
        data['meta'] = bundles['meta']
        data['features'] = [self._convert_to_geojson(bundle) for bundle in bundles['objects']]
        return data
    def apply_filters(self, request, filters):
        obj_list = super(MunicipalityResource, self).apply_filters(request, filters)
        if request.GET.get('format') == 'geojson':
            obj_list = obj_list.select_related('municipalityboundary')
        return obj_list
    def dehydrate(self, bundle):
        alt_names = bundle.obj.municipalityname_set.all()
        for an in alt_names:
            bundle.data['name_%s' % an.language] = an.name
        return bundle
    def determine_format(self, request):
        if request.GET.get('format') == 'geojson':
            return 'application/json'
        return super(MunicipalityResource, self).determine_format(request)
    class Meta:
        queryset = Municipality.objects.all().order_by('name').select_related('municipalityboundary')
        resource_name = 'municipality'
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

class MunicipalityBoundaryResource(GeometryModelResource):
    municipality = fields.ToOneField('munigeo.api.MunicipalityResource', 'municipality')
    class Meta:
        queryset = MunicipalityBoundary.objects.all()
        resource_name = 'municipality_boundary'
        filtering = {
            'municipality': ALL
        }
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

class AddressResource(GeometryModelResource):
    municipality = fields.ToOneField('munigeo.api.MunicipalityResource', 'municipality',
        help_text="ID of the municipality that this address belongs to")

    def apply_sorting(self, objects, options=None):
        if options and 'lon' in options and 'lat' in options:
            try:
                lat = float(options['lat'])
                lon = float(options['lon'])
            except ValueError:
                raise InvalidFilterError("'lon' and 'lat' need to be floats")
            pnt = Point(lon, lat, srid=4326)
            pnt.transform(PROJECTION_SRID)
            objects = objects.distance(pnt).order_by('distance')
        return super(AddressResource, self).apply_sorting(objects, options)

    def apply_filters(self, request, applicable_filters):
        if 'distinct_streets' in applicable_filters:
            ds = applicable_filters.pop('distinct_streets')
        else:
            ds = None
        queryset = (super(AddressResource, self)
                    .apply_filters(request, applicable_filters))
        if ds:
            queryset = (queryset.order_by(*ds['order_by'])
                                .distinct(*ds['distinct']))
        return queryset

    def distinct_streets(self, ds):
        filters = {}
        if ds == 'true':
            filters['distinct_streets'] = {
                'order_by': ['municipality', 'street'],
                'distinct': ['municipality', 'street']}
        elif ds != 'false':
            raise ImmediateHttpResponse(
                response=HttpBadRequest(
                    content="{\"error\": \"If given, the option "
                            "distinct_streets must be either 'true' or "
                            "'false'.\"}",
                    content_type='application/json'))
        return filters

    def query_to_filters(self, query):
        filters = {}
        m = re.search(r'(\D+)(\d+)', query, re.U)
        if m:
            number = m.groups()[1]
            street = m.groups()[0].strip()
        else:
            number = None
            street = query.strip()
        filters['street__istartswith'] = street
        if number:
            filters['number'] = int(number)
        return filters
        
    def build_filters(self, filters=None):
        orm_filters = super(AddressResource, self).build_filters(filters)
        if filters:
            if 'name' in filters:
                orm_filters.update(self.query_to_filters(filters['name']))
            if 'distinct_streets' in filters:
                orm_filters.update(self.distinct_streets(
                    filters['distinct_streets']))
        return orm_filters            

    def dehydrate_location(self, bundle):
        loc = bundle.data['location']
        coords = loc['coordinates']
        pnt = Point(coords[0], coords[1], srid=PROJECTION_SRID)
        pnt.transform(4326)
        loc['coordinates'] = [pnt.x, pnt.y]
        return loc

    def dehydrate(self, bundle):
        distance = getattr(bundle.obj, 'distance', None)
        if distance is not None:
            distance = str(distance)
            bundle.data['distance'] = float(distance.strip(' m'))
        bundle.data['name'] = str(bundle.obj)
        return bundle

    class Meta:
        queryset = Address.objects.all()
        filtering = {
            'municipality': ALL,
            'street': ALL,
            'number': ALL,
            'number_end': ALL,
            'letter': ALL,
            'location': ALL,
        }
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

class POICategoryResource(ModelResource):
    class Meta:
        queryset = POICategory.objects.all()
        filtering = {
            'type': ALL,
            'description': ALL,
        }
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

class POIResource(GeometryModelResource):
    category = fields.ToOneField(POICategoryResource, 'category')

    def apply_sorting(self, objects, options=None):
        if options and 'lon' in options and 'lat' in options:
            try:
                lat = float(options['lat'])
                lon = float(options['lon'])
            except ValueError:
                raise InvalidFilterError("'lon' and 'lat' need to be floats")
            pnt = Point(lon, lat, srid=4326)
            pnt.transform(PROJECTION_SRID)
            objects = objects.distance(pnt).order_by('distance')
        return super(POIResource, self).apply_sorting(objects, options)

    def dehydrate_location(self, bundle):
        loc = bundle.data['location']
        coords = loc['coordinates']
        pnt = Point(coords[0], coords[1], srid=PROJECTION_SRID)
        pnt.transform(4326)
        loc['coordinates'] = [pnt.x, pnt.y]
        return loc

    def dehydrate(self, bundle):
        distance = getattr(bundle.obj, 'distance', None)
        if distance is not None:
            distance = str(distance)
            bundle.data['distance'] = float(distance.strip(' m'))
        bundle.data['category_type'] = str(bundle.obj.category.type)
        return bundle

    class Meta:
        queryset = POI.objects.all()
        filtering = {
            'municipality': ALL,
            'category': ALL_WITH_RELATIONS,
        }
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

class DistrictResource(GeometryModelResource):
    municipality = fields.ToOneField(MunicipalityResource, 'municipality',
        help_text="ID of the municipality that this district belongs to")

    def query_to_filters(self, query):
        filters = {}
        filters['name__icontains'] = query
        return filters

    def build_filters(self, filters=None):
        orm_filters = super(DistrictResource, self).build_filters(filters)
        if filters and 'input' in filters:
            orm_filters.update(self.query_to_filters(filters['input']))
        return orm_filters            

    class Meta:
        queryset = District.objects.all()
        filtering = {
            'municipality': ALL,
            'name': ALL,
        }
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

def build_bbox_filter(bbox_val, field_name):
    points = bbox_val.split(',')
    if len(points) != 4:
        raise InvalidFilterError("bbox must be in format 'left,bottom,right,top'")
    try:
        points = [float(p) for p in points]
    except ValueError:
        raise InvalidFilterError("bbox values must be floating point")
    poly = Polygon.from_bbox(points)
    poly.srid = 4326
    poly.transform(PROJECTION_SRID)
    return {"%s__intersects" % field_name: poly}

class PlanResource(GeometryModelResource):
    municipality = fields.ToOneField(MunicipalityResource, 'municipality',
        help_text="ID of the municipality that this plan belongs to")

    def build_filters(self, filters=None):
        orm_filters = super(PlanResource, self).build_filters(filters)
        if filters and 'bbox' in filters:
            bbox_filter = build_bbox_filter(filters['bbox'], 'geometry')
            orm_filters.update(bbox_filter)
        return orm_filters

    def full_dehydrate(self, bundle, for_list=False):
        # Convert to WGS-84 before outputting.
        bundle.obj.geometry.transform(4326)
        return super(PlanResource, self).full_dehydrate(bundle, for_list)

    class Meta:
        queryset = Plan.objects.all()
        filtering = {
            'municipality': ALL,
            'origin_id': ['exact'],
            'in_effect': ['exact'],
            'geometry': ALL,
        }
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

all_resources = [
    MunicipalityResource, MunicipalityBoundaryResource, AddressResource, POICategoryResource,
    POIResource, DistrictResource, PlanResource,
]
