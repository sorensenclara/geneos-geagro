from django.contrib import admin
from user.admin.adminSite import adminSite
from parameter.models.area import Area


class AreaAdmin(admin.ModelAdmin):
    list_display  = ("name", "climate", "gdd_upper_cutoff", "tiene_perfil_alertas")
    search_fields = ("name",)
    list_filter   = ("climate",)

    fieldsets = [
        (None, {
            "fields": ["name", "climate"],
        }),
        ("GDD y método de cálculo", {
            "fields": ["gdd_upper_cutoff"],
            "description": (
                "Techo de temperatura para el método Winkler. "
                "Mendoza: 30.0 (temperaturas recortadas a 30°C antes de promediar). "
                "Tandil / zonas no-vid: dejar vacío (promedio simple sin techo). "
                "La configuración de alertas y umbrales se edita en Perfil de alertas."
            ),
        }),
    ]

    def tiene_perfil_alertas(self, obj):
        return hasattr(obj, 'alert_profile')
    tiene_perfil_alertas.boolean = True
    tiene_perfil_alertas.short_description = "Perfil alertas"


adminSite.register(Area, AreaAdmin)
