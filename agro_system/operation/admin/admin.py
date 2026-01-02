from django.contrib import admin
from user.admin.adminSite import adminSite  
from operation.models.activity import Activity
from operation.models.stage import Stage
from operation.models.serviceType import ServiceType
from operation.models.service import Service

# Register your models here.




class StageAdmin(admin.ModelAdmin):
    list_display = ['order','name','activity']
    ordering = ['order']


adminSite.register(Activity)
adminSite.register(Stage, StageAdmin)
adminSite.register(ServiceType)
adminSite.register(Service)