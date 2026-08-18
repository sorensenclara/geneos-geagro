from django.contrib import admin
from user.admin.adminSite import adminSite
from weather.models.station_external import ExternalStation
from weather.models.station_external_variable import ExternalStationVariable


class ExternalStationVariableInline(admin.TabularInline):
    model = ExternalStationVariable
    extra = 0
    fields = ("variable", "source_field")
    autocomplete_fields = ("variable",)
    verbose_name = "Variable climática"
    verbose_name_plural = "Variables climáticas"


class LotInline(admin.TabularInline):
    model       = None   # se asigna abajo para evitar import circular
    fk_name     = "external_station"
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


class ExternalStationAdmin(admin.ModelAdmin):
    list_display  = ("name", "latitude", "longitude", "forecast_days")
    search_fields = ("name",)
    inlines       = [ExternalStationVariableInline, LotInline]

    fieldsets = [
        (None, {
            "fields": ["name"],
        }),
        ("Ubicación", {
            "fields": ["latitude", "longitude"],
        }),
        ("Configuración Open-Meteo", {
            "fields": ["forecast_days", "url"],
        }),
    ]


adminSite.register(ExternalStation, ExternalStationAdmin)
