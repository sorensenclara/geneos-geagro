from django.db import models
from django.utils.translation import gettext_lazy as _
from .indicator import Indicator


class ActiveAlertManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_aborted=False)


class Alert(models.Model):

    objects = models.Manager()
    active  = ActiveAlertManager()
    """
    Registro de una alerta disparada, asociada al cultivo (Crop) que la originó.
    El lote y la campaña se derivan via crop.lot y crop.campaing.
    """

    name      = models.CharField(max_length=200, unique=True, verbose_name=_("nombre"))
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, null=True, verbose_name=_("indicador"))
    date      = models.DateField(verbose_name=_("fecha"))
    detail    = models.TextField(verbose_name=_("detalle"))

    # Cultivo que originó la alerta (tiene lot, campaing, activity, area)
    crop = models.ForeignKey(
        "operation.Crop",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="alerts",
        verbose_name=_("crop"),
    )

    # Etapa fenológica al momento del disparo (ej: "BBCH 65 — Plena floración")
    bbch_stage = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("BBCH stage"))

    LEVEL_CHOICES = [
        ("warning",  _("Warning")),
        ("alert",    _("Alert")),
        ("critical", _("Critical")),
    ]

    level = models.CharField(
        max_length=10,
        blank=True,
        choices=LEVEL_CHOICES,
        verbose_name=_("level"),
        help_text=_("Severity level returned by the evaluator: warning / alert / critical."),
    )

    is_forecast = models.BooleanField(
        default=False,
        verbose_name=_("is forecast"),
        help_text=_("True when generated from forecast data; False when confirmed by observed data."),
    )

    is_aborted = models.BooleanField(
        default=False,
        verbose_name=_("is aborted"),
        help_text=_(
            "True when the forecast expired without confirmation or the forecast changed and the event "
            "is no longer predicted. Associated WOs are moved to 'Cancelada'."
        ),
    )

    def __str__(self):
        return f"{self.name} - {self.date}"

    class Meta:
        verbose_name = _("alert")
        verbose_name_plural = _("alerts")
