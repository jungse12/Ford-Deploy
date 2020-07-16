from django.db import models
import json
#import simplejson as json


# Create your models here.

class ClimateZone(models.Model):
    state = models.CharField(max_length=2)
    state_FIPS = models.IntegerField()
    county_FIPS = models.IntegerField()
    county_name = models.CharField(max_length=50)
    climate_zone = models.IntegerField()

    def __str__(self):
        return self.state+", "+self.county_name+": "+str(self.climate_zone)


class EGRID(models.Model):
    zip_code = models.IntegerField()
    state = models.CharField(max_length=2)
    eGRID_subregion = models.CharField(max_length=4)

    def __str__(self):
        return str(self.zip_code)+": "+self.eGRID_subregion

class ZipcodeCounty(models.Model):
    zip_code = models.IntegerField()
    county_name = models.CharField(max_length=50)

    def __str__(self):
        return str(self.zip_code)+": "+self.county_name

class GWP(models.Model):
    year = models.IntegerField()
    eGRID_subregion = models.CharField(max_length=4)
    gwp = models.DecimalField(max_digits=8, decimal_places=6)

    def __str__(self):
        return str(self.year)+", "+self.eGRID_subregion+": "+str(self.gwp)

class CED(models.Model):
    year = models.IntegerField()
    eGRID_subregion = models.CharField(max_length=4)
    ced = models.DecimalField(max_digits=8, decimal_places=6)

    def __str__(self):
        return str(self.year)+", "+self.eGRID_subregion+": "+str(self.ced)

class PVSoilingLoss(models.Model):
    climate_zone = models.IntegerField(null=True)
    loss_percent = models.FloatField()

    def __str__(self):
        return str(self.climate_zone)+", "+str(self.loss_percent)

class HomeESS(models.Model):
    zone_number = models.CharField(max_length=6,default='')
    array_list = models.CharField(max_length=120000, default='')


    #def get_foo(self):
    #    return json.loads(self.foo)

    def __str__(self):
        return str(self.zone_number)

class MicrogridESS(models.Model):
    zone_number = models.CharField(max_length=6,default='')
    array_list = models.CharField(max_length=120000, default='')

    def __str__(self):
        return str(self.zone_number)

class Fastcharger(models.Model):
    watt = models.CharField(max_length=120000,default='')
