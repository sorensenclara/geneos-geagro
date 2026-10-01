from django.contrib import admin
from user.admin.adminSite import adminSite  
from operation.models.variety import Variety
from operation.models.stage import Stage
from operation.models.service_type import ServiceType
from operation.models.service import Service

# Register your models here.




class StageAdmin(admin.ModelAdmin):
    list_display = ['order','name','variety']
    ordering = ['order']


adminSite.register(Variety)
adminSite.register(Stage, StageAdmin)
adminSite.register(ServiceType)
adminSite.register(Service)