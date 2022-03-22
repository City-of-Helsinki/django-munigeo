import re
import json
import logging
from django.db.models import Q
from datetime import datetime
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.measure import D
from rest_framework import serializers, viewsets, generics
from rest_framework.exceptions import ParseError
from django.contrib.gis.gdal import SRSException, CoordTransform, SpatialReference
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis import gdal
from munigeo.models import AdministrativeDivisionType, AdministrativeDivision,\
    AdministrativeDivisionGeometry, Municipality, Street, Address, PostalCodeArea
from modeltranslation import models as mt_models # workaround for init problem
from modeltranslation.translator import translator, NotRegistered

# Use the GPS coordinate system by default
DEFAULT_SRID = 4326
DATABASE_SRID = getattr(settings, 'PROJECTION_SRID', 4326)
DEFAULT_SRS = SpatialReference(DEFAULT_SRID)
ADDRESS_SEARCH_RADIUS = getattr(settings, 'ADDRESS_SEARCH_RADIUS', None)

logger = logging.getLogger(__name__)

all_views = []


def register_view(klass, name):
    all_views.append({'class': klass, 'name': name})


def poly_from_bbox(bbox_val):
    points = bbox_val.split(',')
    if len(points) != 4:
        raise ParseError("bbox must be in format 'left,bottom,right,top'")
    try:
        points = [float(p) for p in points]
    except ValueError:
        raise ParseError("bbox values must be floating points or integers")
    poly = Polygon.from_bbox(points)
    return poly


def srid_to_srs(srid):
    if not srid:
        srid = DEFAULT_SRID
    try:
        srid = int(srid)
    except ValueError:
        raise ParseError("'srid' must be an integer")
    try:
        srs = SpatialReference(srid)
    except SRSException:
        raise ParseError("SRID %d not found (try 4326 for GPS coordinate system)" % srid)
    return srs


def build_bbox_filter(srs, bbox_val, field_name):
    poly = poly_from_bbox(bbox_val)
    poly.srid = srs.srid

    return {"%s__within" % field_name: poly}


def make_muni_ocd_id(name, rest=None):
    country = getattr(settings, 'DEFAULT_COUNTRY', None)
    muni = getattr(settings, 'DEFAULT_OCD_MUNICIPALITY', None)
    if country and muni:
        s = 'ocd-division/country:%s/%s:%s' % (settings.DEFAULT_COUNTRY, settings.DEFAULT_OCD_MUNICIPALITY, name)
    else:
        s = name
    if rest:
        s += '/' + rest
    return s


class TranslatedModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(TranslatedModelSerializer, self).__init__(*args, **kwargs)
        model = self.Meta.model
        try:
            trans_opts = translator.get_options_for_model(model)
        except NotRegistered:
            self.translated_fields = []
            return

        self.translated_fields = trans_opts.fields.keys()
        lang_codes = [x[0] for x in settings.LANGUAGES]
        remove_fields = []
        # Remove the pre-existing data in the bundle.
        for field_name in self.translated_fields:
            for lang in lang_codes:
                key = "%s_%s" % (field_name, lang)
                if key in self.fields:
                    del self.fields[key]
            del self.fields[field_name]
            remove_fields.append(field_name)
        for field_name in remove_fields:
            if field_name in self.fields:
                del self.fields[field_name]

    def to_representation(self, obj):
        ret = super(TranslatedModelSerializer, self).to_representation(obj)
        if obj is None:
            return ret
        return self.translated_fields_to_representation(obj, ret)

    def translated_fields_to_representation(self, obj, ret):
        for field_name in self.translated_fields:
            d = {}
            for lang in [x[0] for x in settings.LANGUAGES]:
                key = "%s_%s" % (field_name, lang)
                val = getattr(obj, key, None)
                if val is None:
                    continue
                d[lang] = val

            # If no text provided, leave the field as null
            for key, val in d.items():
                if val is not None:
                    break
            else:
                d = None
            ret[field_name] = d

        return ret


class MPTTModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(MPTTModelSerializer, self).__init__(*args, **kwargs)
        for field_name in 'lft', 'rght', 'tree_id', 'level':
            if field_name in self.fields:
                del self.fields[field_name]


# Maintain a cache of different coordinate transformations for performance
# reasons.
srs_cache = {}
coord_transforms = {}


def geom_to_json(geom, target_srs):
    srs = srs_cache.get(geom.srid, None)
    if not srs:
        srs = geom.srs
        srs_cache[geom.srid] = srs

    if target_srs:
        ct_id = '%s-%s' % (geom.srid, target_srs.srid)
        ct = coord_transforms.get(ct_id, None)
        if not ct:
            ct = CoordTransform(srs, target_srs)
            coord_transforms[ct_id] = ct
    else:
        ct = None

    if ct:
        wkb = geom.wkb
        geom = gdal.OGRGeometry(wkb, srs)
        geom.transform(ct)
        geom_name = geom.geom_name.lower()
    else:
        geom_name = geom.geom_type.lower()

    # Accelerated path for points
    if geom_name == 'point':
        if target_srs.projected:
            digits = 2
        else:
            digits = 7
        coords = [round(n, digits) for n in [geom.x, geom.y]]
        return {'type': 'Point', 'coordinates': coords}

    s = geom.geojson
    return json.loads(s)


class GeoModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(GeoModelSerializer, self).__init__(*args, **kwargs)
        model = self.Meta.model
        self.geo_fields = []
        model_fields = [f.name for f in model._meta.fields]
        remove_fields = []
        for field_name in self.fields:
            if field_name not in model_fields:
                continue
            field = model._meta.get_field(field_name)
            if not isinstance(field, models.GeometryField):
                continue
            self.geo_fields.append(field_name)
            remove_fields.append(field_name)
        for field_name in remove_fields:
            del self.fields[field_name]

    def to_representation(self, obj):
        # SRS is deduced in ViewSet and passed from there
        self.srs = self.context.get('srs', DEFAULT_SRS)
        ret = super(GeoModelSerializer, self).to_representation(obj)
        if obj is None:
            return ret
        for field_name in self.geo_fields:
            val = getattr(obj, field_name)
            if val is None:
                ret[field_name] = None
                continue
            ret[field_name] = geom_to_json(val, self.srs)
        return ret


class GeoModelAPIView(generics.GenericAPIView):
    def initial(self, request, *args, **kwargs):
        super(GeoModelAPIView, self).initial(request, *args, **kwargs)
        srid = request.query_params.get('srid', None)
        self.srs = srid_to_srs(srid)

    def get_serializer_context(self):
        ret = super(GeoModelAPIView, self).get_serializer_context()
        ret['srs'] = self.srs
        return ret


class AdministrativeDivisionTypeSerializer(TranslatedModelSerializer):
    class Meta:
        model = AdministrativeDivisionType
        fields = '__all__'


class AdministrativeDivisionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AdministrativeDivisionType.objects.all()
    serializer_class = AdministrativeDivisionTypeSerializer


register_view(AdministrativeDivisionTypeViewSet, 'administrative_division_type')


class AdministrativeDivisionSerializer(GeoModelSerializer, TranslatedModelSerializer,
                                       MPTTModelSerializer):
    def to_representation(self, obj):
        ret = super(AdministrativeDivisionSerializer, self).to_representation(obj)
        if not 'request' in self.context:
            return ret
        qparams = self.context['request'].query_params
        if qparams.get('geometry', '').lower() in ('true', '1'):
            try:
                geom = obj.geometry.boundary
                ret['boundary'] = geom_to_json(geom, self.srs)
            except AdministrativeDivisionGeometry.DoesNotExist:
                logger.warning('AdministrativeDivisionGeometry does not exist for division with ocd_id: %s'
                               % ret.get('ocd_id'))
        ret['type'] = obj.type.type
        return ret

    class Meta:
        model = AdministrativeDivision
        fields = '__all__'


def parse_lat_lon(query_params):
    lat = query_params.get('lat', None)
    lon = query_params.get('lon', None)
    if not lat and not lon:
        return None

    if not lat or not lon:
        raise ParseError("you must supply both 'lat' and 'lon'")
    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        raise ParseError("'lat' and 'lon' must be floating point numbers")

    point = Point(lon, lat, srid=DEFAULT_SRID)
    if DEFAULT_SRID != DATABASE_SRID:
        ct = CoordTransform(SpatialReference(DEFAULT_SRID),
                            SpatialReference(DATABASE_SRID))
        point.transform(ct)
    return point


class AdministrativeDivisionViewSet(GeoModelAPIView, viewsets.ReadOnlyModelViewSet):
    queryset = AdministrativeDivision.objects.all()
    serializer_class = AdministrativeDivisionSerializer

    def get_queryset(self):
        queryset = super(AdministrativeDivisionViewSet, self).get_queryset()
        filters = self.request.query_params

        if 'type' in filters:
            types = filters['type'].strip().split(',')
            is_name = False
            for t in types:
                # If the given type is not digits, assume it's a type name
                if not re.match(r'^[\d]+$', t):
                    is_name = True
                    break
            if is_name:
                queryset = queryset.filter(type__type__in=types)
            else:
                queryset = queryset.filter(type__in=types)

        point = parse_lat_lon(filters)
        if point:
            geometries = AdministrativeDivisionGeometry.objects.filter(boundary__contains=point)
            queryset = queryset.filter(geometry__in=geometries).distinct()

        if 'input' in filters:
            queryset = queryset.filter(name__icontains=filters['input'].strip())

        for filter in filters:
            if filter.startswith('extra__'):
                queryset = queryset.filter(**{filter: filters[filter].strip()})

        if 'ocd_id' in filters:
            # Divisions can be specified with form:
            # division=helsinki/kaupunginosa:kallio,vantaa/äänestysalue:5
            d_list = filters['ocd_id'].lower().split(',')
            ocd_id_list = []
            for division_path in d_list:
                if division_path.startswith('ocd-division'):
                    muni_ocd_id = division_path
                else:
                    ocd_id_base = r'[\w0-9~_.-]+'
                    match_re = r'(%s)/([\w_-]+):(%s)' % (ocd_id_base, ocd_id_base)
                    m = re.match(match_re, division_path, re.U)
                    if not m:
                        raise ParseError("'ocd_id' must be of form 'muni/type:id'")

                    arr = division_path.split('/')
                    muni_ocd_id = make_muni_ocd_id(arr.pop(0), '/'.join(arr))
                ocd_id_list.append(muni_ocd_id)

            queryset = queryset.filter(ocd_id__in=ocd_id_list)

        if 'geometry' in filters:
            queryset = queryset.select_related('geometry')

        if 'origin_id' in filters:
            queryset = queryset.filter(origin_id=filters['origin_id'])

        if 'date' in filters:
            try:
                date = datetime.strptime(filters['date'], '%Y-%m-%d').date()
            except ValueError:
                raise ParseError('Invalid date. The required format is YYYY-MM-DD.')
            queryset = queryset.filter(
                (Q(start__lte=date) | Q(start__isnull=True)) &
                (Q(end__gte=date)   | Q(end__isnull=True)))

        queryset = queryset.select_related('type')

        return queryset


register_view(AdministrativeDivisionViewSet, 'administrative_division')


class PostalCodeSerializer(TranslatedModelSerializer):
    class Meta:
        model = PostalCodeArea
        fields = '__all__'


class PostalCodeAreaViewSet(GeoModelAPIView, viewsets.ReadOnlyModelViewSet):
    queryset = PostalCodeArea.objects.all()
    serializer_class = PostalCodeSerializer

    def get_queryset(self):
        queryset = super(PostalCodeAreaViewSet, self).get_queryset()
        filters = self.request.query_params
        if 'language' in filters:
            self.lang_code = filters['language']
            if self.lang_code not in LANG_CODES:
                raise ParseError("Invalid language supplied. Supported languages: %s" %
                                    ', '.join([x[0] for x in settings.LANGUAGES]))
        else:
            self.lang_code = LANG_CODES[0]

        if 'name' in filters:         
            name = filters['name'].strip() 
            args = {'name_%s' % self.lang_code: name}
            try:
                postal_code_area = PostalCodeArea.objects.get(**args)
            except PostalCodeArea.DoesNotExist:
                raise ParseError("postalcodearea with name '%s' not found" % name)
            queryset = queryset.filter(id=postal_code_area.id)
        
        if 'postal_code' in filters:            
            postal_code = filters["postal_code"].strip()
            try:
                postal_code_area = PostalCodeArea.objects.get(postal_code=postal_code)
            except PostalCodeArea.DoesNotExist:
                raise ParseError("postalcode with postal_code '%s' not found" % postal_code)
            queryset = queryset.filter(id=postal_code_area.id)
        return queryset


register_view(PostalCodeAreaViewSet, 'postalcodearea')


class StreetSerializer(TranslatedModelSerializer):
    class Meta:
        model = Street
        fields = '__all__'


LANG_CODES = [x[0] for x in settings.LANGUAGES]


class StreetViewSet(GeoModelAPIView, viewsets.ReadOnlyModelViewSet):
    queryset = Street.objects.all()
    serializer_class = StreetSerializer

    def get_queryset(self):
        queryset = super(StreetViewSet, self).get_queryset()
        default_lang = LANG_CODES[0]
        self.lang_code = self.request.query_params.get('language', default_lang)
        if self.lang_code not in LANG_CODES:
            raise ParseError("Invalid language supplied. Supported languages: %s" %
                             ', '.join([x[0] for x in settings.LANGUAGES]))

        filters = self.request.query_params

        if 'municipality' in filters:
            val = filters['municipality'].lower()
            if val.startswith('ocd-division'):
                ocd_id = val
            else:
                ocd_id = make_muni_ocd_id(val)
            try:
                muni = Municipality.objects.get(division__ocd_id=ocd_id)
            except Municipality.DoesNotExist:
                raise ParseError("municipality with ID '%s' not found" % ocd_id)

            queryset = queryset.filter(municipality=muni)

        if 'input' in filters:
            args = {}
            args['name_%s__istartswith' % self.lang_code] = filters['input'].strip()
            queryset = queryset.filter(**args)

        return queryset


register_view(StreetViewSet, 'street')


class AddressSerializer(GeoModelSerializer):
    # Reverse geocoding
    def to_representation(self, obj):
        ret = super(AddressSerializer, self).to_representation(obj)
        if not ret['number_end']:
            ret['number_end'] = None
        if not ret['letter']:
            ret['letter'] = None
        if hasattr(obj, 'distance'):
            ret['distance'] = obj.distance.m
        ret['street'] = StreetSerializer(obj.street).data
        div_qs = AdministrativeDivisionGeometry.objects.select_related(
            "division", "division__type"
        ).filter(boundary__contains=obj.location, division__type__type="postcode_area")
        if obj.postal_code_area:
            ret['postal_code'] = obj.postal_code_area.postal_code
        else:
            ret['postal_code'] = div_qs.first().division.name if div_qs else None
        ret['postal_code_area'] = PostalCodeSerializer(obj.postal_code_area).data
        return ret

    class Meta:
        model = Address
        exclude = ('id', 'street')


class AddressViewSet(GeoModelAPIView, viewsets.ReadOnlyModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_queryset(self):
        filters = self.request.query_params

        default_lang = LANG_CODES[0]
        self.lang_code = filters.get('language', default_lang)
        if self.lang_code not in LANG_CODES:
            raise ParseError("Invalid language supplied. Supported languages: %s" %
                             ', '.join([x[0] for x in settings.LANGUAGES]))

        queryset = super(AddressViewSet, self).get_queryset()

        street = filters.get('street', None)
        if street is not None:
            if street.isnumeric():
                queryset = queryset.filter(street=street)
            else:
                args = {}
                args['street__name_%s__iexact' % self.lang_code] = street.strip()
                queryset = queryset.filter(**args)

        if 'municipality' in filters:
            val = filters['municipality'].lower()
            if val.startswith('ocd-division'):
                ocd_id = val
            else:
                ocd_id = make_muni_ocd_id(val)
            try:
                muni = Municipality.objects.get(division__ocd_id=ocd_id)
            except Municipality.DoesNotExist:
                raise ParseError("municipality with ID '%s' not found" % ocd_id)

            queryset = queryset.filter(street__municipality=muni)
        elif 'municipality_name' in filters:
            val = filters['municipality_name'].lower()
            args = {}
            args['name_%s__iexact' % self.lang_code] = val
            try:
                muni = Municipality.objects.get(**args)
                queryset = queryset.filter(street__municipality=muni)
            except Municipality.DoesNotExist:
                queryset = queryset.none()

        number = filters.get('number', None)
        if number is not None:
            queryset = queryset.filter(number=number)

        query_point = parse_lat_lon(self.request.query_params)
        if query_point:
            distance = filters.get('distance', None)
            if distance is None and ADDRESS_SEARCH_RADIUS:
                distance = ADDRESS_SEARCH_RADIUS
            if distance:
                queryset = queryset.filter(location__distance_lte=(query_point, D(m=distance)))
            queryset = queryset.annotate(distance=Distance('location', query_point)).order_by('distance')

        if "bbox" in filters:
            val = filters.get("bbox", None)
            if "bbox_srid" in filters:
                ref = SpatialReference(filters.get("bbox_srid", None))
            else:
                ref = self.srs
            if val:
                bbox_filter = build_bbox_filter(ref, val, "location")
                queryset = queryset.filter(Q(**bbox_filter))

        return queryset


register_view(AddressViewSet, 'address')


class MunicipalitySerializer(TranslatedModelSerializer):
    class Meta:
        model = Municipality
        fields = '__all__'
