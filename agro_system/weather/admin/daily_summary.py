from django.contrib import admin
from user.admin.adminSite import adminSite
from weather.models.daily_summary import DailySummary


class DailySummaryAdmin(admin.ModelAdmin):
    list_display  = ("lot", "date", "tmin", "tmax", "hr_media", "lluvia_mm", "horas_hr_alta", "horas_banda_oidio", "fuente_predominante")
    list_filter   = ("lot", "fuente_predominante")
    search_fields = ("lot__name",)
    date_hierarchy = "date"
    ordering       = ("-date",)
    readonly_fields = (
        "lot", "date",
        "tmin", "tmax",
        "hr_media", "lluvia_mm", "eto_mm",
        "horas_hr_alta", "horas_banda_oidio",
        "fuente_predominante",
    )

    def has_add_permission(self, request):
        return False


adminSite.register(DailySummary, DailySummaryAdmin)
