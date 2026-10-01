from django.contrib import admin
from user.admin.adminSite import adminSite
from user.admin.producer_scope import producers_for_user, ReadOnlyForProducersMixin
from weather.models.open_meteo_hourly import OpenMeteoHourly


class OpenMeteoHourlyAdmin(ReadOnlyForProducersMixin, admin.ModelAdmin):
    list_display    = ("station", "datetime", "temperature", "humidity", "wind_speed", "wind_gusts", "precipitation", "cape", "eto_mm")
    # RelatedOnlyFieldListFilter: el filtro solo ofrece las estaciones que el usuario puede ver
    list_filter     = (("station", admin.RelatedOnlyFieldListFilter),)
    search_fields   = ("station__name",)
    readonly_fields = ("station", "datetime", "temperature", "humidity", "wind_speed",
                       "wind_direction", "wind_gusts", "precipitation", "cape", "eto_mm", "extra_data")
    date_hierarchy  = "datetime"
    ordering        = ("-datetime",)

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        # Productor / Staff / Organización: solo el clima de la estación externa asignada a sus lotes
        qs = super().get_queryset(request)
        producers = producers_for_user(request)
        if producers is None:
            return qs
        return qs.filter(station__lots__countryside__producer__in=producers).distinct()


adminSite.register(OpenMeteoHourly, OpenMeteoHourlyAdmin)
