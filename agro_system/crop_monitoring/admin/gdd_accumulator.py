from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from user.admin.adminSite import adminSite
from crop_monitoring.models.gdd_accumulator import GDDAccumulator


class GDDAccumulatorAdmin(admin.ModelAdmin):
    list_display  = ("biofix", "accumulated_gdd", "calculation_date")
    readonly_fields = ("biofix", "accumulated_gdd", "calculation_date")

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:pk>/recalculate/",
                self.admin_site.admin_view(self.recalculate_view),
                name="crop_monitoring_gddaccumulator_recalculate",
            ),
        ]
        return custom + urls

    def recalculate_view(self, request, pk):
        try:
            acc = GDDAccumulator.objects.get(pk=pk)
            acc.recalculate()
            self.message_user(
                request,
                f"GDD recalculado: {acc.accumulated_gdd} GDD (hasta {acc.calculation_date})",
            )
        except GDDAccumulator.DoesNotExist:
            self.message_user(request, "Acumulador no encontrado.", level="error")

        referer = request.META.get("HTTP_REFERER")
        if referer:
            return HttpResponseRedirect(referer)
        return HttpResponseRedirect(
            reverse("admin:crop_monitoring_biofix_changelist", current_app=self.admin_site.name)
        )


adminSite.register(GDDAccumulator, GDDAccumulatorAdmin)
