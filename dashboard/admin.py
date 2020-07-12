from django.contrib import admin

from .models import ClimateZone, EGRID, ZipcodeCounty, GWP, CED, PVSoilingLoss, MicrogridESS, Fastcharger, HomeESS, ElectricConsumption, TouMatrix, CustomESS

# Register your models here.
admin.site.register(ClimateZone)
admin.site.register(EGRID)
admin.site.register(ZipcodeCounty)
admin.site.register(GWP)
admin.site.register(CED)
admin.site.register(PVSoilingLoss)
admin.site.register(HomeESS)
admin.site.register(MicrogridESS)
admin.site.register(Fastcharger)
admin.site.register(ElectricConsumption)
admin.site.register(TouMatrix)
admin.site.register(CustomESS)
