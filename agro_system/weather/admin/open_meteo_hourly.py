from django.contrib import admin
from user.admin.adminSite import adminSite
from weather.models.open_meteo_hourly import OpenMeteoHourly


class OpenMeteoHourlyAdmin(admin.ModelAdmin):
    list_display    = ("station", "datetime", "temperature", "humidity", "wind_speed", "wind_gusts", "precipitation", "cape", "eto_mm")
    list_filter     = ("station",)
    search_fields   = ("station__name",)
    readonly_fields = ("station", "datetime", "temperature", "humidity", "wind_speed",
                       "wind_direction", "wind_gusts", "precipitation", "cape", "eto_mm", "extra_data")
    date_hierarchy  = "datetime"
    ordering        = ("-datetime",)

    def has_add_permission(self, request):
        return False


adminSite.register(OpenMeteoHourly, OpenMeteoHourlyAdmin)
