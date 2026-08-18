from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .biofix import Biofix
from weather.models.daily_summary import DailySummary

class GDDAccumulator(models.Model):
    """
    Estado recalculable, NO append-only.
    recalculate() re-suma desde el biofix leyendo DailySummary por lote.
    DailySummary se puebla desde la estación propia o desde OpenMeteoHourly.
    """

    biofix = models.OneToOneField(
        Biofix,
        on_delete=models.CASCADE,
        related_name="accumulator",
        verbose_name=_("biofix"),
    )
    accumulated_gdd  = models.DecimalField(max_digits=7, decimal_places=1, default=0, verbose_name=_("accumulated GDD"))
    calculation_date = models.DateField(null=True, blank=True, verbose_name=_("calculation date"))

    def __str__(self):
        return f"{self.biofix}: {self.accumulated_gdd} GDD"

    def recalculate(self, until=None):
        """
        Lee DailySummary del lote para cada día desde el biofix hasta `until`.
        DailySummary tiene fuente_predominante='station' o 'open_meteo' según
        qué se consolidó — el acumulador no distingue, usa lo que haya.
        Días sin DailySummary contribuyen 0 GDD.

        Cadena de acceso al techo: biofix → crop → lot → area → gdd_upper_cutoff
        """
        until  = until or timezone.localdate()
        base   = float(self.biofix.base_temp)
        lot    = self.biofix.crop.lot
        cutoff = float(lot.area.gdd_upper_cutoff) if (lot.area and lot.area.gdd_upper_cutoff) else None
        start  = self.biofix.date

        summary_by_date = {
            s.date: (float(s.tmin), float(s.tmax))
            for s in DailySummary.objects.filter(
                lot=lot,
                date__gte=start,
                date__lte=until,
            )
        }

        def _day_gdd(tmin, tmax):
            if cutoff is not None:
                tmax = min(tmax, cutoff)
                tmin = min(tmin, cutoff)
            return max(0.0, (tmax + tmin) / 2 - base)

        total   = 0.0
        current = start
        while current <= until:
            if current in summary_by_date:
                tmin, tmax = summary_by_date[current]
                total += _day_gdd(tmin, tmax)
            # sin DailySummary ese día → contribuye 0
            current += timedelta(days=1)

        self.accumulated_gdd  = round(total, 1)
        self.calculation_date = until
        self.save()
        return self.accumulated_gdd
