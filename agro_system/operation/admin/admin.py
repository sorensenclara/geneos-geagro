from django.contrib import admin
from user.admin.adminSite import adminSite  
from operation.models.activity import Activity
from operation.models.stage import Stage
from operation.models.serviceType import ServiceType
from operation.models.service import Service

# Register your models here.

adminSite.register(Activity)
adminSite.register(Stage)
adminSite.register(ServiceType)
adminSite.register(Service)