from django.contrib import admin
from user.admin.adminSite import adminSite
from operation.models.variety import Variety
from operation.models.stage import Stage
from operation.models.service_type import ServiceType
from operation.models.service import Service


class StageAdmin(admin.ModelAdmin):
    list_display  = ['order', 'name', 'activity', 'bbch_range_display']
    list_select_related = ['activity']
    ordering      = ['order']
    fields        = ['name', 'activity', 'order']

    def bbch_range_display(self, obj):
        return obj.bbch_range_display
    bbch_range_display.short_description = "Rango BBCH"


adminSite.register(Variety)
adminSite.register(Stage, StageAdmin)
adminSite.register(ServiceType)
adminSite.register(Service)
