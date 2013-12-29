from six import with_metaclass
from django.utils.encoding import python_2_unicode_compatible

from django.contrib.gis.db import models
from linguo.models import MultilingualModel, MultilingualModelBase
from linguo.managers import MultilingualManager
from django.conf import settings
from mptt.models import MPTTModel, MPTTModelBase, TreeForeignKey
from mptt.managers import TreeManager

from django.utils.translation import ugettext as _

# If SRID not configured in settings, use the global Spherical
# Mercator projection.
if hasattr(settings, 'PROJECTION_SRID'):
    PROJECTION_SRID = settings.PROJECTION_SRID
else:
    PROJECTION_SRID = 3857

@python_2_unicode_compatible
class AdministrativeDivisionType(models.Model):
    type = models.CharField(max_length=30, unique=True, db_index=True,
                            help_text=_("Type name of the division (e.g. muni, school_district)"))
    name = models.CharField(max_length=50,
                            help_text=_("Human-readable name for the division"))

    def __str__(self):
        return "%s (%s)" % (self.name, self.type)

class AdministrativeDivisionMeta(MultilingualModelBase, MPTTModelBase):
    pass

@python_2_unicode_compatible
class AdministrativeDivision(with_metaclass(AdministrativeDivisionMeta, MultilingualModel, MPTTModel)):
    type = models.ForeignKey(AdministrativeDivisionType, db_index=True)
    name = models.CharField(max_length=100, null=True, db_index=True)
    parent = TreeForeignKey('self', null=True, related_name='children')
    origin_id = models.CharField(max_length=50, db_index=True)
    ocd_id = models.CharField(max_length=50, unique=True, db_index=True, null=True,
                              help_text=_("Open Civic Data identifier"))

    # Some divisions might be only valid during some time period.
    # (E.g. yearly school districts in Helsinki)
    start = models.DateField(null=True)
    end = models.DateField(null=True)

    last_modified_time = models.DateTimeField(help_text='Time when the information last changed', auto_now_add=True)

    objects = MultilingualManager()
    tree_objects = TreeManager()

    def __str__(self):
        return "%s (%s)" % (self.name, self.type.type)

    class Meta:
        unique_together = (('origin_id', 'type', 'parent'),)
        translate = ('name',)

class AdministrativeDivisionGeometry(models.Model):
    division = models.OneToOneField(AdministrativeDivision, related_name='geometry')
    boundary = models.MultiPolygonField(srid=PROJECTION_SRID)

    objects = models.GeoManager()

class Municipality(AdministrativeDivision):
    def save(self, *args, **kwargs):
        defaults = {'name': 'Municipality'}
        type_obj, c = AdministrativeDivisionType.objects.get_or_create(type='muni', defaults=defaults)
        self.type = type_obj
        return super(Municipality, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name


class District(models.Model):
    municipality = models.ForeignKey(Municipality)
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=20)
    borders = models.PolygonField()
    origin_id = models.CharField(max_length=20)

    objects = models.GeoManager()

    class Meta:
        unique_together = (('municipality', 'origin_id'))

class Plan(models.Model):
    municipality = models.ForeignKey(Municipality)
    geometry = models.MultiPolygonField(srid=PROJECTION_SRID)
    origin_id = models.CharField(max_length=20)
    in_effect = models.BooleanField()

    objects = models.GeoManager()

    class Meta:
        unique_together = (('municipality', 'origin_id'),)

class Address(models.Model):
    street = models.CharField(max_length=50, db_index=True,
        help_text="Name of the street")
    number = models.PositiveIntegerField(
        help_text="Building number")
    number_end = models.PositiveIntegerField(blank=True, null=True,
        help_text="Building number end (if range specified)")
    letter = models.CharField(max_length=2, blank=True, null=True,
        help_text="Building letter if applicable")
    location = models.PointField(srid=PROJECTION_SRID,
        help_text="Coordinates of the address in GeoJSON")
    municipality = models.ForeignKey(Municipality, db_index=True)

    objects = models.GeoManager()

    def __unicode__(self):
        s = "%s %d" % (self.street, self.number)
        if self.letter:
            s += "%s" % self.letter
        s += ", %s" % self.municipality
        return s

    class Meta:
        unique_together = (('municipality', 'street', 'number', 'number_end', 'letter'),)
        ordering = ['municipality', 'street', 'number']

class POICategory(models.Model):
    type = models.CharField(max_length=50, db_index=True)
    description = models.CharField(max_length=100)

class POI(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(POICategory, db_index=True)
    description = models.TextField(null=True, blank=True)
    location = models.PointField(srid=PROJECTION_SRID)
    municipality = models.ForeignKey(Municipality, db_index=True)
    street_address = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    origin_id = models.CharField(max_length=40, db_index=True, unique=True)

    objects = models.GeoManager()
