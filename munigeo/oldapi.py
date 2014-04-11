import json
import re

from django.db.models import Q
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from django.contrib.gis.gdal import SRSException, SpatialReference, CoordTransform
from tastypie.http import HttpBadRequest
from tastypie.resources import ModelResource
from tastypie.exceptions import InvalidFilterError, ImmediateHttpResponse
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.cache import SimpleCache
from tastypie import fields
from munigeo.models import *
from modeltranslation.translator import translator, NotRegistered

# Use the GPS coordinate system by default
DEFAULT_SRID = 4326

def poly_from_bbox(bbox_val):
    points = bbox_val.split(',')
    if len(points) != 4:
        raise InvalidFilterError("bbox must be in format 'left,bottom,right,top'")
    try:
        points = [float(p) for p in points]
    except ValueError:
        raise InvalidFilterError("bbox values must be floating point or integers")
    poly = Polygon.from_bbox(points)
    return poly

def srid_to_srs(srid):
    if not srid:
        srid = DEFAULT_SRID
    try:
        srid = int(srid)
    except ValueError:
        raise InvalidFilterError("'srid' must be an integer")
    try:
        srs = SpatialReference(srid)
    except SRSException:
        raise InvalidFilterError("SRID %d not found (try 4326 for GPS coordinate system)" % srid)
    return srs

def build_bbox_filter(srid, bbox_val, field_name):
    poly = poly_from_bbox(bbox_val)
    srs = srid_to_srs(srid)
    poly.set_srid(srs.srid)

    if srid != settings.PROJECTION_SRID:
        source_srs = SpatialReference(settings.PROJECTION_SRID)
        ct = CoordTransform(srs, source_srs)
        poly.transform(ct)

    return {"%s__within" % field_name: poly}


LANGUAGES = [x[0] for x in settings.LANGUAGES]

class TranslatableCachedResource(ModelResource):
    def __init__(self, api_name=None):
        super(TranslatableCachedResource, self).__init__(api_name)
        self._meta.cache = SimpleCache(timeout=300)

    def dehydrate(self, bundle):
        bundle = super(TranslatableCachedResource, self).dehydrate(bundle)
        obj = bundle.obj
        try:
            trans_opts = translator.get_options_for_model(type(obj))
        except NotRegistered:
            return bundle

        for field_name in trans_opts.fields.keys():
            if field_name in bundle.data:
                del bundle.data[field_name]

            # Remove the pre-existing data in the bundle.
            for lang in LANGUAGES:
                key = "%s_%s" % (field_name, lang)
                if key in bundle.data:
                    del bundle.data[key]

            d = {}
            default_lang = LANGUAGES[0]
            d[default_lang] = getattr(obj, field_name)
            for lang in LANGUAGES[1:]:
                key = "%s_%s" % (field_name, lang)
                val = getattr(bundle.obj, key, None)
                if val == None:
                    continue
                d[lang] = val

            # If no text provided, leave the field as null
            for key, val in d.items():
                if val != None:
                    break
            else:
                d = None
            bundle.data[field_name] = d

        return bundle
    #_meta.translatable_fields


class AdministrativeDivisionTypeResource(TranslatableCachedResource):
    class Meta:
        queryset = AdministrativeDivisionType.objects.order_by('pk')
        resource_name = 'administrative_division_type'
        filtering = {
            'type': ALL,
            'name': ALL
        }

class AdministrativeDivisionResource(TranslatableCachedResource):
    parent = fields.ForeignKey('munigeo.api.AdministrativeDivisionResource', 'parent', null=True)
    type = fields.ForeignKey(AdministrativeDivisionTypeResource, 'type')

    def _convert_to_geojson(self, bundle):
        obj = bundle.obj
        data = {'type': 'Feature'}
        data['properties'] = bundle.data
        data['id'] = bundle.obj.pk
        geom = obj.geometry.boundary
        data['geometry'] = json.loads(geom.geojson)
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
        obj_list = super(AdministrativeDivisionResource, self).apply_filters(request, filters)
        if request.GET.get('format') == 'geojson':
            obj_list = obj_list.select_related('geometry')
        return obj_list

    def query_to_filters(self, query):
        filters = {}
        filters['name__icontains'] = query
        return filters
    def build_filters(self, filters=None):
        if 'type' in filters:
            type_str = filters['type']
            # If the given type is not digits, assume it's a type name
            if re.match(type_str, r'$[\d]+^'):
                del filters['type']
                filters['type__type'] = type_str

        orm_filters = super(AdministrativeDivisionResource, self).build_filters(filters)
        if filters and 'input' in filters:
            orm_filters.update(self.query_to_filters(filters['input']))
        return orm_filters


    def dehydrate(self, bundle):
        if bundle.request.GET.get('geometry', '').lower() in ('true', '1'):
            srid = bundle.request.GET.get('srid', None)
            srs = srid_to_srs(srid)
            geom = bundle.obj.geometry.boundary
            if srs.srid != geom.srid:
                ct = CoordTransform(geom.srs, srs)
                geom.transform(ct)
            geom_str = geom.geojson
            bundle.data['boundary'] = json.loads(geom_str)

        return super(AdministrativeDivisionResource, self).dehydrate(bundle)

    def determine_format(self, request):
        if request.GET.get('format') == 'geojson':
            return 'application/json'
        return super(AdministrativeDivisionResource, self).determine_format(request)

    class Meta:
        queryset = AdministrativeDivision.objects.order_by('ocd_id').select_related('geometry').select_related('type__type')
        resource_name = 'administrative_division'
        filtering = {
            'type': ALL_WITH_RELATIONS,
            'ocd_id': ALL,
            'begin': ALL,
            'end': ALL,
            'name': ALL,
            'parent': ALL_WITH_RELATIONS,
            'type': ALL_WITH_RELATIONS,
        }
        excludes = ['lft', 'rght', 'tree_id']
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']


class MunicipalityResource(AdministrativeDivisionResource):
    class Meta:
        queryset = Municipality.objects.all()
        resource_name = 'municipality'
        filtering = {
            'administrative_division': ALL_WITH_RELATIONS,
            'ocd_id': ALL,
            'begin': ALL,
            'end': ALL,
            'name': ALL,
            'parent': ALL_WITH_RELATIONS,
            'type': ALL_WITH_RELATIONS,
        }
        excludes = ['lft', 'rght', 'tree_id']
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

class AddressResource(ModelResource):
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

class POICategoryResource(TranslatableCachedResource):
    class Meta:
        queryset = POICategory.objects.all()
        filtering = {
            'type': ALL,
            'description': ALL,
        }
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

class POIResource(TranslatableCachedResource):
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
        srid = bundle.request.GET.get('srid', None)
        srs = srid_to_srs(srid)
        geom = bundle.obj.location
        if srs.srid != geom.srid:
            ct = CoordTransform(geom.srs, srs)
            geom.transform(ct)
        geom_str = geom.geojson
        return json.loads(geom_str)

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


class PlanResource(ModelResource):
    #municipality = fields.ToOneField(MunicipalityResource, 'municipality',
        #help_text="ID of the municipality that this plan belongs to")

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
    AdministrativeDivisionResource, AdministrativeDivisionTypeResource,
    AddressResource, POICategoryResource, POIResource, MunicipalityResource, PlanResource,
]
