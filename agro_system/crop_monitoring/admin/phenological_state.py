from django.contrib import admin
from django.contrib import messages
from user.admin.adminSite import adminSite
from crop_monitoring.models.phenological_state import PhenologicalState, seed_phenological_stages


class PhenologicalStateAdmin(admin.ModelAdmin):
    list_display  = ("order", "bbch", "stage_name", "gdd_from", "gdd_to", "gdd_range", "stage")
    list_display_links = ("bbch",)
    list_select_related = ("stage",)
    ordering      = ("order",)
    search_fields = ("bbch", "stage_name")

    fieldsets = [
        (None, {
            "fields": ["order", "bbch", "stage_name", "stage"],
        }),
        ("Rango de GDD (base 10°C desde brotación)", {
            "fields": ["gdd_from", "gdd_to"],
        }),
    ]

    actions = ["action_seed"]

    def gdd_range(self, obj):
        return f"{obj.gdd_to - obj.gdd_from} GDD"
    gdd_range.short_description = "Amplitud"

    def action_seed(self, request, queryset):
        seed_phenological_stages()
        self.message_user(
            request,
            "Tabla fenológica recargada con los valores base (14 estadios).",
            messages.SUCCESS,
        )
    action_seed.short_description = "Recargar tabla base (seed)"


adminSite.register(PhenologicalState, PhenologicalStateAdmin)
