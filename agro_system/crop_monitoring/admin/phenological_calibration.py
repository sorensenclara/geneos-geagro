from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from user.admin.adminSite import adminSite
from crop_monitoring.models.phenological_calibration import (
    PhenologicalCalibration,
    seed_phenological_calibrations,
)
from parameter.models.specie import Specie
from parameter.models.area import Area


class PhenologicalCalibrationAdmin(admin.ModelAdmin):
    list_display  = (
        "state", "specie", "area",
        "gdd_from", "gdd_to", "amplitud",
        "origen_calibracion", "sample_count", "last_calibrated",
    )
    list_filter   = ("specie", "area", "is_auto_calibrated")
    list_select_related = ("state", "specie", "area")
    search_fields = ("state__bbch", "state__stage_name", "specie__name", "area__name")
    ordering      = ("area", "specie", "state__order")

    readonly_fields = (
        "is_auto_calibrated", "sample_count", "last_calibrated",
        "origen_calibracion",
    )

    fieldsets = [
        ("Combinación", {
            "fields": ["specie", "area", "state"],
        }),
        ("Rango de GDD", {
            "fields": ["gdd_from", "gdd_to"],
            "description": (
                "Rango en el que este estadio BBCH es válido para esta especie+zona. "
                "Se ajusta automáticamente con cada observación de campo registrada."
            ),
        }),
        ("Estado de calibración", {
            "fields": ["origen_calibracion", "sample_count", "last_calibrated"],
            "classes": ["collapse"],
        }),
    ]

    actions = ["action_seed_mendoza", "action_recalibrate"]

    # ------------------------------------------------------------------

    def amplitud(self, obj):
        return f"{obj.gdd_to - obj.gdd_from} GDD"
    amplitud.short_description = "Amplitud"

    def origen_calibracion(self, obj):
        if obj.is_auto_calibrated:
            return format_html(
                '<span style="color:#1565c0;">Auto · {} observaciones · {}</span>',
                obj.sample_count,
                obj.last_calibrated or "—",
            )
        return format_html('<span style="color:#555;">Base (seed)</span>')
    origen_calibracion.short_description = "Origen"

    # ------------------------------------------------------------------

    def action_seed_mendoza(self, request, queryset):
        """Crea calibraciones base copiando los GDD actuales de PhenologicalState."""
        total = 0
        for specie in Specie.objects.all():
            for area in Area.objects.all():
                total += seed_phenological_calibrations(specie, area)
        self.message_user(
            request,
            f"Se crearon {total} calibraciones base (existentes no fueron pisadas).",
            messages.SUCCESS,
        )
    action_seed_mendoza.short_description = "Cargar calibraciones base para todas las combinaciones"

    def action_recalibrate(self, request, queryset):
        """Recalibra manualmente las calibraciones seleccionadas desde observaciones."""
        recalibradas = 0
        sin_datos = 0
        for cal in queryset:
            prev_from = cal.gdd_from
            cal.recalibrate_from_observations()
            cal.refresh_from_db()
            if cal.gdd_from != prev_from:
                recalibradas += 1
            else:
                sin_datos += 1
        msg = f"{recalibradas} recalibrada(s)."
        if sin_datos:
            msg += f" {sin_datos} sin observaciones suficientes (sin cambios)."
        self.message_user(request, msg, messages.SUCCESS)
    action_recalibrate.short_description = "Recalibrar desde observaciones de campo"


adminSite.register(PhenologicalCalibration, PhenologicalCalibrationAdmin)
