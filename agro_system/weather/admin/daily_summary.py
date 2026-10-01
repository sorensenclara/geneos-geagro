from django.contrib import admin
from user.admin.adminSite import adminSite
from user.admin.producer_scope import producers_for_user, ReadOnlyForProducersMixin
from weather.models.daily_summary import DailySummary


class DailySummaryAdmin(ReadOnlyForProducersMixin, admin.ModelAdmin):
    list_display  = ("lot", "date", "tmin", "tmax", "hr_media", "lluvia_mm", "horas_hr_alta", "horas_banda_oidio", "fuente_predominante")
    # RelatedOnlyFieldListFilter: el filtro solo ofrece los lotes que el usuario puede ver
    list_filter   = (("lot", admin.RelatedOnlyFieldListFilter), "fuente_predominante")
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

    def get_queryset(self, request):
        # Productor / Staff / Organización: solo el resumen diario de sus lotes
        qs = super().get_queryset(request)
        producers = producers_for_user(request)
        return qs if producers is None else qs.filter(lot__countryside__producer__in=producers)


adminSite.register(DailySummary, DailySummaryAdmin)
