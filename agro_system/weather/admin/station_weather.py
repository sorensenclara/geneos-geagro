from django.contrib import admin
from weather.models.station_weather import WeatherStation
from user.admin.adminSite import adminSite


class LotInline(admin.TabularInline):
    model       = None   # se asigna abajo para evitar import circular
    fk_name     = "station"
    fields      = ("name", "countryside", "area")
    readonly_fields = ("name", "countryside", "area")
    extra       = 0
    can_delete  = False
    verbose_name        = "Lote asignado"
    verbose_name_plural = "Lotes asignados"

    def has_add_permission(self, request, obj=None):
        return False


def _lot_model():
    from producer.models.lot import Lot
    return Lot

LotInline.model = _lot_model()


class WeatherStationAdmin(admin.ModelAdmin):
    list_display  = ("name", "latitude", "longitude", "save_interval")
    search_fields = ("name",)
    inlines       = [LotInline]


adminSite.register(WeatherStation, WeatherStationAdmin)