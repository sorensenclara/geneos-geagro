from django.db import models
from django.utils.translation import gettext_lazy as _
from user.models.user_extend import UserExtend
import importlib

class Indicator(models.Model):
    """
    Cabecera del indicador. Las variables se almacenan en IndicatorVariable
    (detalle, N por indicador) en lugar de columnas fijas variable_one/two/three.
    """

    REVIEW_DAILY       = "daily"
    REVIEW_PER_READING = "per_reading"

    CRITICALITY_CHOICES = [
        ("low",    _("Low")),
        ("medium", _("Medium")),
        ("high",   _("High")),
    ]

    REVIEW_CHOICES = [
        (REVIEW_DAILY,       _("Revisión diaria")),
        (REVIEW_PER_READING, _("Revisión por registro")),
    ]

    name              = models.CharField(max_length=200, unique=True, verbose_name=_("name"))
    report_user       = models.ManyToManyField(UserExtend, blank=True, verbose_name=_("user alert"))
    report_mails      = models.TextField(blank=True, null=True, verbose_name=_("report mails"))
    criticality_level = models.CharField(
        max_length=6,
        choices=CRITICALITY_CHOICES,
        default="low",
        verbose_name=_("criticality level"),
    )
    evaluator = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("evaluator"),
        help_text=_(
            "Optional Python path to a custom evaluator class "
            "(e.g. 'alert.evaluators.storm_front.StormFrontEvaluator'). "
            "When set, overrides the generic filter + band logic."
        ),
    )
    review_mode = models.CharField(
        max_length=20,
        choices=REVIEW_CHOICES,
        default=REVIEW_DAILY,
        verbose_name=_("review mode"),
        help_text=_(
            "Revisión diaria: se evalúa una vez por día con el resumen diario. "
            "Revisión por registro: se evalúa en cada lectura horaria u de estación; "
            "todos los filtros deben cumplirse simultáneamente en el mismo registro. "
            "No aplica a pronóstico (los pronósticos son siempre diarios)."
        ),
    )

    max_forecast_days = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("max forecast days"),
        help_text=_(
            "How many days ahead this alert is emitted from forecast data. "
            "Frost → 5, hail → 2, heat → 3. Leave blank to use the global default (7)."
        ),
    )

    def get_evaluator(self):
        """Returns an instantiated custom evaluator, or None if not configured."""
        if not self.evaluator:
            return None 
        module_path, class_name = self.evaluator.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("indicator")
        verbose_name_plural = _("indicators")
