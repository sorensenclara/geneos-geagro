from django.contrib import admin
from user.admin.adminSite import adminSite
from user.admin.producer_scope import producers_for_user
from alert.models.alert import Alert
from alert.models.alert_outcome import AlertOutcome


def _registered_by_field(db_field, request, kwargs):
    """'Registrado por': solo el personal del productor del usuario."""
    if db_field.name == "registered_by":
        producers = producers_for_user(request)
        if producers is not None:
            from producer.models.staff import Staff
            kwargs["queryset"] = Staff.objects.filter(producer__in=producers)


class AlertOutcomeInline(admin.StackedInline):
    model   = AlertOutcome
    extra   = 0
    max_num = 1
    fields  = (
        "damage_occurred", "damage_severity",
        "area_affected_pct", "estimated_loss_kg_ha", "estimated_loss_ars",
        "intervention_effective", "notes", "registered_by",
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        _registered_by_field(db_field, request, kwargs)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AlertAdmin(admin.ModelAdmin):
    list_display  = ("name", "level", "date", "crop", "bbch_stage", "is_forecast", "is_aborted", "has_work_order", "has_outcome")
    search_fields = ("name", "crop__name", "crop__lot__name")
    list_filter   = ("level", "is_forecast", "is_aborted", "date", "crop__campaing")
    ordering      = ("-date",)
    readonly_fields = ("work_orders_display",)
    inlines       = [AlertOutcomeInline]

    def get_queryset(self, request):
        # Productor / Staff / Organización: solo las alertas de sus cultivos
        qs = super().get_queryset(request)
        producers = producers_for_user(request)
        return qs if producers is None else qs.filter(crop__producer__in=producers)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "crop":
            producers = producers_for_user(request)
            if producers is not None:
                from operation.models.crop import Crop
                kwargs["queryset"] = Crop.objects.filter(producer__in=producers)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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

    def get_queryset(self, request):
        # Productor / Staff / Organización: solo los resultados de alertas de sus cultivos
        qs = super().get_queryset(request)
        producers = producers_for_user(request)
        return qs if producers is None else qs.filter(alert__crop__producer__in=producers)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        _registered_by_field(db_field, request, kwargs)
        if db_field.name == "alert":
            # raw_id: aunque se escriba el ID a mano, solo valida alertas de sus cultivos
            producers = producers_for_user(request)
            if producers is not None:
                kwargs["queryset"] = Alert.objects.filter(crop__producer__in=producers)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


adminSite.register(Alert, AlertAdmin)
adminSite.register(AlertOutcome, AlertOutcomeAdmin)
