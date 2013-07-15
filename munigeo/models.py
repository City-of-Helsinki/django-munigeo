from django.contrib.gis.db import models

PROJECTION_SRID = 900913

class Municipality(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

# For municipality names in other languages
class MunicipalityName(models.Model):
    municipality = models.ForeignKey(Municipality)
    language = models.CharField(max_length=8)
    name = models.CharField(max_length=50)

class MunicipalityBoundary(models.Model):
    municipality = models.OneToOneField(Municipality)
    borders = models.MultiPolygonField()

    objects = models.GeoManager()

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
