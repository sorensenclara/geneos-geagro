from django.contrib import admin
from user.admin.adminSite import adminSite
from alert.models.alert import Alert


class AlertAdmin(admin.ModelAdmin):
    list_display  = ("name", "level", "date", "crop", "bbch_stage", "is_forecast", "is_aborted", "has_work_order")
    search_fields = ("name", "crop__name", "crop__lot__name")
    list_filter   = ("level", "is_forecast", "is_aborted", "date", "crop__campaing")
    ordering      = ("-date",)
    readonly_fields = ("work_orders_display",)

    def has_work_order(self, obj):
        return obj.work_orders.exists()
    has_work_order.boolean = True
    has_work_order.short_description = "OT"

    def work_orders_display(self, obj):
        wos = obj.work_orders.all()
        if not wos:
            return "—"
        return ", ".join(str(wo) for wo in wos)
    work_orders_display.short_description = "Órdenes de trabajo"


adminSite.register(Alert, AlertAdmin)
