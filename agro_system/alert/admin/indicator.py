from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from user.admin.adminSite import adminSite
from alert.models.indicator import Indicator
from alert.models.indicator_variable import IndicatorVariable
from alert.models.indicator_band import IndicatorBand
from alert.models.indicator_action import IndicatorAction
from alert.models.indicator_action_input import IndicatorActionInput
from alert.models.indicator_recommendation import IndicatorRecommendation


class IndicatorVariableInline(admin.TabularInline):
    model   = IndicatorVariable
    extra   = 1
    fields  = ("variable", "role", "min_value", "max_value", "alert_level", "order")
    ordering = ("order",)
    verbose_name        = _("indicator variable")
    verbose_name_plural = _("indicator variables")


class IndicatorBandInline(admin.TabularInline):
    model   = IndicatorBand
    extra   = 1
    fields  = ("bbch_from", "bbch_to", "threshold", "direction", "level", "order")
    ordering = ("bbch_from", "order")
    verbose_name        = _("indicator band")
    verbose_name_plural = _("indicator bands")


class IndicatorActionInline(admin.TabularInline):
    model   = IndicatorAction
    extra   = 1
    fields  = ("alert_level", "bbch_from", "bbch_to", "service", "stage", "days_to_complete", "create_on_forecast")
    verbose_name        = _("indicator action")
    verbose_name_plural = _("indicator actions — work order templates")
    show_change_link    = True  # permite ir al detail de IndicatorAction para agregar insumos


class IndicatorRecommendationInline(admin.TabularInline):
    model   = IndicatorRecommendation
    extra   = 1
    fields  = ("alert_level", "bbch_from", "bbch_to", "text", "order")
    ordering = ("order",)
    verbose_name        = _("recommendation")
    verbose_name_plural = _("recommendations — informative (no work order)")


class IndicatorAdmin(admin.ModelAdmin):
    list_display  = ("name", "review_mode", "criticality_level", "variable_count", "band_count", "action_count", "has_custom_evaluator")
    search_fields = ("name",)
    list_filter   = ("criticality_level", "review_mode")
    inlines       = [IndicatorVariableInline, IndicatorBandInline, IndicatorActionInline, IndicatorRecommendationInline]
    fieldsets = [
        (None, {"fields": ["name", "criticality_level", "review_mode", "max_forecast_days", "report_user", "report_mails"]}),
        (_("Custom evaluator"), {
            "fields": ["evaluator"],
            "description": _(
                "Only set this if the generic filter + band logic cannot express the condition. "
                "When filled, the generic engine is bypassed entirely for this indicator."
            ),
        }),
    ]

    def variable_count(self, obj):
        return obj.variables.count()
    variable_count.short_description = "Variables"

    def band_count(self, obj):
        return obj.bands.count()
    band_count.short_description = "Bands"

    def action_count(self, obj):
        return obj.actions.count()
    action_count.short_description = _("Actions")

    def has_custom_evaluator(self, obj):
        return bool(obj.evaluator)
    has_custom_evaluator.boolean = True
    has_custom_evaluator.short_description = _("Custom")


class IndicatorActionInputInline(admin.TabularInline):
    model   = IndicatorActionInput
    extra   = 1
    fields  = ("input", "dose")
    verbose_name        = _("input")
    verbose_name_plural = _("inputs / insumos")


class IndicatorActionAdmin(admin.ModelAdmin):
    list_display  = ("indicator", "alert_level", "bbch_from", "bbch_to", "service", "stage", "days_to_complete", "create_on_forecast")
    list_filter   = ("alert_level", "create_on_forecast", "indicator")
    search_fields = ("indicator__name", "service__name")
    inlines       = [IndicatorActionInputInline]
    fieldsets = [
        (None, {"fields": ["indicator", "alert_level", "bbch_from", "bbch_to"]}),
        (_("Work order"), {"fields": ["service", "stage", "days_to_complete"]}),
        (_("Forecast"), {"fields": ["create_on_forecast"]}),
    ]


adminSite.register(Indicator, IndicatorAdmin)
adminSite.register(IndicatorAction, IndicatorActionAdmin)
