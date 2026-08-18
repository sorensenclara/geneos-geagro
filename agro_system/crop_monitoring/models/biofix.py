from django.db import models
from django.utils.translation import gettext_lazy as _


class Biofix(models.Model):
    """
    El cero biológico de CADA contador. Una fila por contador por cultivo.

    Dos contadores paralelos con bases y ceros distintos — NUNCA mezclar:
      - vine:    base 10°C, cero en brotación.
      - lobesia: base 7°C,  cero en primer vuelo / primera captura de trampa.

    El reanclaje (productor confirma brotación tarde) es trivial:
    confirm() cambia la fecha y recalcula el acumulado desde cero. Idempotente.
    """

    COUNTER_VINE = "vine"
    COUNTER_LOBESIA = "lobesia"
    COUNTER_CHOICES = [
        (COUNTER_VINE,    _("Vine phenology (base 10°C)")),
        (COUNTER_LOBESIA, _("Lobesia botrana (base 7°C)")),
    ]

    ORIGIN_MANUAL   = "manual"
    ORIGIN_AUTO     = "auto"
    ORIGIN_FALLBACK = "fallback"
    ORIGIN_CHOICES = [
        (ORIGIN_MANUAL,   _("Confirmed by producer")),
        (ORIGIN_AUTO,     _("Detected by system")),
        (ORIGIN_FALLBACK, _("Fixed provisional date (~Sep 1)")),
    ]

    # String FK: vineyard → operation evita import circular
    crop = models.ForeignKey(
        "operation.Crop",
        on_delete=models.CASCADE,
        related_name="biofixes",
        verbose_name=_("crop"),
    )
    counter = models.CharField(max_length=10, choices=COUNTER_CHOICES, verbose_name=_("counter"))
    base_temp = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        verbose_name=_("base temperature"),
        help_text=_("10.0 para vid, 7.0 para Lobesia."),
    )
    date = models.DateField(
        verbose_name=_("date"),
        help_text=_("Cero del contador. Brotación (vid) o primer vuelo (Lobesia)."),
    )
    origin = models.CharField(
        max_length=10,
        choices=ORIGIN_CHOICES,
        default=ORIGIN_FALLBACK,
        verbose_name=_("origin"),
    )
    is_confirmed = models.BooleanField(default=False, verbose_name=_("is confirmed"))

    class Meta:
        unique_together = ("crop", "counter")
        verbose_name = _("biofix")
        verbose_name_plural = _("biofixes")

    def __str__(self):
        estado = "confirmed" if self.is_confirmed else "provisional"
        return f"Biofix {self.counter} {self.crop} ({estado})"

    def confirm(self, real_date, origin=ORIGIN_MANUAL):
        """
        Reancla el cero a la fecha real observada y recalcula el GDD desde cero.
        Idempotente: se puede llamar N veces sin efecto secundario.
        """
        # Import local para evitar circular: biofix → gdd_accumulator → biofix
        from .gdd_accumulator import GDDAccumulator

        self.date = real_date
        self.origin = origin
        self.is_confirmed = True
        self.save()

        acc, _ = GDDAccumulator.objects.get_or_create(biofix=self)
        return acc.recalculate()
