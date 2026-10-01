from django.contrib import admin
from django.utils.html import format_html
from user.admin.adminSite import adminSite
from crop_monitoring.models.phenological_observation import PhenologicalObservation
from crop_monitoring.models.gdd_accumulator import GDDAccumulator
from crop_monitoring.models.biofix import Biofix


class PhenologicalObservationAdmin(admin.ModelAdmin):
    list_display  = (
        "date", "crop", "observed_state", "observed_gdd",
        "calculated_state_display", "coincide", "registered_by",
    )
    list_filter   = ("observed_state", "crop__area", "crop__activity__specie")
    search_fields = ("crop__name", "crop__lot__name", "notes")
    date_hierarchy = "date"
    list_select_related = ("crop", "observed_state", "calculated_state", "registered_by")

    readonly_fields = ("calculated_state", "gdd_acumulador_referencia", "coincide_display")

    fieldsets = [
        ("Cultivo", {
            "fields": ["crop", "date", "registered_by"],
        }),
        ("Observación de campo", {
            "fields": ["observed_state", "observed_gdd", "gdd_acumulador_referencia"],
            "description": (
                "Seleccioná el BBCH que observaste en campo. "
                "El GDD se completa automáticamente del acumulador si lo dejás vacío; "
                "podés corregirlo si creés que el valor del acumulador está mal."
            ),
        }),
        ("Estado calculado por el sistema", {
            "fields": ["calculated_state", "coincide_display"],
            "classes": ["collapse"],
            "description": "Se guarda automáticamente al registrar la observación.",
        }),
        ("Notas", {
            "fields": ["notes"],
        }),
    ]

    # ------------------------------------------------------------------

    def gdd_acumulador_referencia(self, obj):
        """Muestra el GDD actual del acumulador como referencia al editar."""
        if not obj or not obj.crop_id:
            return "—"
        try:
            biofix = obj.crop.biofixes.get(counter=Biofix.COUNTER_VINE)
            gdd = biofix.accumulator.accumulated_gdd
            return format_html(
                '<span style="color:#555;">GDD actual del acumulador: <strong>{}</strong> '
                '(calculado al {})</span>',
                gdd,
                biofix.accumulator.calculation_date or "—",
            )
        except Exception:
            return "Sin acumulador vine para este cultivo"
    gdd_acumulador_referencia.short_description = "Referencia del acumulador"

    def calculated_state_display(self, obj):
        if not obj.calculated_state:
            return "—"
        return f"BBCH {obj.calculated_state.bbch} — {obj.calculated_state.stage_name}"
    calculated_state_display.short_description = "Sistema calculaba"

    def coincide(self, obj):
        if obj.calculated_state is None:
            return "—"
        if obj.matches_calculated:
            return format_html('<span style="color:#2e7d32;">✓ Coincide</span>')
        return format_html('<span style="color:#c62828;">✗ Difiere</span>')
    coincide.short_description = "¿Coincide?"

    def coincide_display(self, obj):
        return self.coincide(obj)
    coincide_display.short_description = "¿Observado coincide con calculado?"


adminSite.register(PhenologicalObservation, PhenologicalObservationAdmin)
