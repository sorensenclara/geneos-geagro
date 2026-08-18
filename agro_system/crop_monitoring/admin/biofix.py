from django.contrib import admin
from django.utils.html import format_html
from user.admin.adminSite import adminSite
from crop_monitoring.models.biofix import Biofix
from crop_monitoring.models.gdd_accumulator import GDDAccumulator
from crop_monitoring.models.phenological_state import PhenologicalState


class GDDAccumulatorInline(admin.TabularInline):
    model         = GDDAccumulator
    extra         = 0
    can_delete    = False
    readonly_fields = ("accumulated_gdd", "calculation_date", "estado_fenologico", "recalculate_link")
    fields          = ("accumulated_gdd", "calculation_date", "estado_fenologico", "recalculate_link")

    def recalculate_link(self, obj):
        if obj and obj.pk:
            return format_html(
                '<a class="button" href="{}">Recalcular</a>',
                f"/admin/crop_monitoring/gddaccumulator/{obj.pk}/recalculate/",
            )
        return "—"
    recalculate_link.short_description = "Acción"

    def estado_fenologico(self, obj):
        if not obj or not obj.pk:
            return "—"
        if obj.biofix.counter != Biofix.COUNTER_VINE:
            return "—"
        gdd = float(obj.accumulated_gdd)
        stage = PhenologicalState.current_stage(gdd)
        if not stage:
            return "—"
        next_s = PhenologicalState.next_stage(gdd)
        text = f"BBCH {stage.bbch} — {stage.stage_name}"
        if next_s:
            faltan = next_s.gdd_from - gdd
            text += f" (faltan ~{faltan:.0f} GDD para {next_s.stage_name})"
        return text
    estado_fenologico.short_description = "Estado fenológico"


class BiofixAdmin(admin.ModelAdmin):
    list_display   = ("crop", "counter", "date", "is_confirmed", "origin", "base_temp", "gdd_acumulado", "estado_fenologico")
    list_filter    = ("counter", "is_confirmed", "origin")
    search_fields  = ("crop__name", "crop__lot__name")
    readonly_fields = ("gdd_acumulado", "estado_fenologico")
    inlines        = [GDDAccumulatorInline]

    fieldsets = [
        (None, {
            "fields": ["crop", "counter", "base_temp"],
        }),
        ("Fecha de anclaje", {
            "fields": ["date", "origin", "is_confirmed"],
            "description": "La fecha es el cero biológico del contador. "
                           "Para 'vine': día de brotación observado en campo. "
                           "Para 'lobesia': día del primer vuelo en trampa.",
        }),
        ("Estado actual", {
            "fields": ["gdd_acumulado", "estado_fenologico"],
        }),
    ]

    def gdd_acumulado(self, obj):
        try:
            return f"{obj.accumulator.accumulated_gdd} GDD"
        except GDDAccumulator.DoesNotExist:
            return "Sin acumulador"
    gdd_acumulado.short_description = "GDD acumulado"

    def estado_fenologico(self, obj):
        if obj.counter != Biofix.COUNTER_VINE:
            return "Solo aplica al contador vid"
        try:
            gdd = float(obj.accumulator.accumulated_gdd)
        except GDDAccumulator.DoesNotExist:
            return "Sin GDD calculado"
        stage = PhenologicalState.current_stage(gdd)
        if not stage:
            return f"Sin etapa para {gdd} GDD"
        next_s = PhenologicalState.next_stage(gdd)
        text = f"BBCH {stage.bbch} — {stage.stage_name} ({gdd:.1f} GDD)"
        if next_s:
            faltan = next_s.gdd_from - gdd
            text += f" · próxima: {next_s.stage_name} en ~{faltan:.0f} GDD"
        return text
    estado_fenologico.short_description = "Estado fenológico"

    actions = ["action_recalculate"]

    def action_recalculate(self, request, queryset):
        recalculados = 0
        for biofix in queryset:
            try:
                biofix.accumulator.recalculate()
                recalculados += 1
            except GDDAccumulator.DoesNotExist:
                GDDAccumulator.objects.create(biofix=biofix).recalculate()
                recalculados += 1
        self.message_user(request, f"{recalculados} acumulador(es) recalculado(s).")
    action_recalculate.short_description = "Recalcular GDD acumulado"


adminSite.register(Biofix, BiofixAdmin)
