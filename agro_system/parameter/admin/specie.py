from django.contrib import admin
from user.admin.adminSite import adminSite
from parameter.models.specie import Specie


class SpecieAdmin(admin.ModelAdmin):
    list_display  = ("name", "gdd_harvest_min", "gdd_harvest_max", "es_vid")
    search_fields = ("name",)
    list_filter   = ("name",)

    fieldsets = [
        (None, {
            "fields": ["name"],
        }),
        ("Datos vitivinícolas (solo variedades de vid)", {
            "fields": ["gdd_harvest_min", "gdd_harvest_max"],
            "description": (
                "GDD acumulado desde brotación (base 10°C) al momento de cosecha. "
                "gdd_harvest_min: umbral de inicio de ventana. "
                "gdd_harvest_max: umbral de sobre-maduración. "
                "Dejar vacío para especies no-vid."
            ),
        }),
    ]

    def es_vid(self, obj):
        return obj.gdd_harvest_min is not None
    es_vid.boolean = True
    es_vid.short_description = "¿Es vid?"


adminSite.register(Specie, SpecieAdmin)
