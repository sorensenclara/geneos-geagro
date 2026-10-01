from django.contrib import admin
from user.admin.adminSite import adminSite
from alert.models.alert import Alert
from alert.models.alert_outcome import AlertOutcome


class AlertOutcomeInline(admin.StackedInline):
    model   = AlertOutcome
    extra   = 0
    max_num = 1
    fields  = (
        "damage_occurred", "damage_severity",
        "area_affected_pct", "estimated_loss_kg_ha", "estimated_loss_ars",
        "intervention_effective", "notes", "registered_by",
    )


class AlertAdmin(admin.ModelAdmin):
    list_display  = ("name", "level", "date", "crop", "bbch_stage", "is_forecast", "is_aborted", "has_work_order", "has_outcome")
    search_fields = ("name", "crop__name", "crop__lot__name")
    list_filter   = ("level", "is_forecast", "is_aborted", "date", "crop__campaing")
    ordering      = ("-date",)
    readonly_fields = ("work_orders_display",)
    inlines       = [AlertOutcomeInline]

    def has_work_order(self, obj):
        return obj.work_orders.exists()
    has_work_order.boolean = True
    has_work_order.short_description = "OT"

    def has_outcome(self, obj):
        return hasattr(obj, "outcome")
    has_outcome.boolean = True
    has_outcome.short_description = "Impacto"

    def work_orders_display(self, obj):
        wos = obj.work_orders.all()
        if not wos:
            return "—"
        return ", ".join(str(wo) for wo in wos)
    work_orders_display.short_description = "Órdenes de trabajo"


class AlertOutcomeAdmin(admin.ModelAdmin):
    list_display  = ("alert", "damage_occurred", "damage_severity", "area_affected_pct", "estimated_loss_ars", "intervention_effective", "registered_at")
    list_filter   = ("damage_severity", "intervention_effective", "damage_occurred", "alert__crop__campaing")
    search_fields = ("alert__name", "notes")
    ordering      = ("-registered_at",)
    raw_id_fields = ("alert",)


adminSite.register(Alert, AlertAdmin)
adminSite.register(AlertOutcome, AlertOutcomeAdmin)
