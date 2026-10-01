from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from user.admin.adminSite import adminSite
from alert.models.alert_profile import AlertProfile
from alert.models.alert_profile_indicator import AlertProfileIndicator


class AlertProfileIndicatorInline(admin.TabularInline):
    model   = AlertProfileIndicator
    extra   = 0
    fields  = ("indicator", "status")
    autocomplete_fields = ("indicator",)
    verbose_name        = _("active indicator")
    verbose_name_plural = _("active indicators")


class AlertProfileAdmin(admin.ModelAdmin):
    list_display  = ("area", "active_count", "vigilance_count", "off_count")
    search_fields = ("area__name",)
    inlines       = [AlertProfileIndicatorInline]

    fieldsets = [
        (None, {"fields": ["area"]}),
        (_("Data sources"), {
            "fields": ["priority_sources"],
            "description": _(
                'Priority order of meteorological data sources. '
                'Example: ["open_meteo_eto", "soil_moisture_station", "station"].'
            ),
        }),
    ]

    def _count_by_status(self, obj, status):
        return obj.profile_indicators.filter(status=status).count()

    def active_count(self, obj):
        return self._count_by_status(obj, "on")
    active_count.short_description = _("On")

    def vigilance_count(self, obj):
        return self._count_by_status(obj, "vigilance")
    vigilance_count.short_description = _("Vigilance")

    def off_count(self, obj):
        return self._count_by_status(obj, "off")
    off_count.short_description = _("Off")


adminSite.register(AlertProfile, AlertProfileAdmin)
