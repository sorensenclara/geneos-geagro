"""
Ciclo diario del motor agro.

Flujo recomendado:
  08:00  → python manage.py run_daily_cycle              (Open-Meteo disponible, GDD estimado)
  23:45  → python manage.py run_daily_cycle --eod        (consolida estación real, GDD definitivo)

Backfill de días anteriores:
  python manage.py run_daily_cycle --from-date 2026-07-01   (desde esa fecha hasta hoy)

El comando es idempotente: se puede correr N veces por día sin efectos secundarios.
La estación propia siempre gana sobre Open-Meteo cuando tiene datos.

# ---------------------------------------------------------------------------
# CRON — descomentar y ajustar rutas cuando se quiera automatizar
# ---------------------------------------------------------------------------
# Editar con:  crontab -e
#
# VENV=/home/florencia/trabajo_final/venv_vid_alertas
# DJ=/home/florencia/trabajo_final/django-agro/agro_system
# MANAGE=$DJ/manage.py
# LOG=/var/log/agro_daily_cycle.log
#
# # 08:00 — ciclo mañana (GDD estimado con Open-Meteo)
# 0 8 * * *  $VENV/bin/python $MANAGE run_daily_cycle >> $LOG 2>&1
#
# # 23:45 — ciclo fin de día (GDD definitivo con estación real)
# 45 23 * * *  $VENV/bin/python $MANAGE run_daily_cycle --eod >> $LOG 2>&1
# ---------------------------------------------------------------------------
"""
import logging
from datetime import date as date_type, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from crop_monitoring.models.biofix import Biofix
from crop_monitoring.models.gdd_accumulator import GDDAccumulator
from producer.models.lot import Lot
from weather.models.daily_summary import DailySummary

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Consolida DailySummary y recalcula GDD para todos los lotes con cultivos activos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            type=str,
            default=None,
            metavar="YYYY-MM-DD",
            help="Fecha a procesar. Por defecto: hoy.",
        )
        parser.add_argument(
            "--from-date",
            type=str,
            default=None,
            metavar="YYYY-MM-DD",
            help="Backfill: procesa desde esta fecha hasta hoy (o hasta --date si se combinan).",
        )
        parser.add_argument(
            "--eod",
            action="store_true",
            help="Modo fin de día: consolida desde la estación propia (pisa Open-Meteo si hay datos).",
        )

    def handle(self, *args, **options):
        today = timezone.localdate()

        # --- Rango de fechas ---
        if options["from_date"]:
            try:
                start_date = date_type.fromisoformat(options["from_date"])
            except ValueError:
                self.stderr.write(self.style.ERROR(f"Fecha inválida: {options['from_date']}"))
                return
            end_date = date_type.fromisoformat(options["date"]) if options["date"] else today
            dates = []
            current = start_date
            while current <= end_date:
                dates.append(current)
                current += timedelta(days=1)
        elif options["date"]:
            try:
                dates = [date_type.fromisoformat(options["date"])]
            except ValueError:
                self.stderr.write(self.style.ERROR(f"Fecha inválida: {options['date']}"))
                return
        else:
            dates = [today]

        eod = options["eod"]

        for target_date in dates:
            self._process_date(target_date, eod)

    def _process_date(self, target_date, eod):
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"{'[EOD]' if eod else '[MORNING]'} Ciclo diario — {target_date}"
            )
        )

        # --- Lotes que tienen al menos un biofix (activos en el motor GDD) ---
        lots = Lot.objects.filter(
            crop__biofixes__isnull=False
        ).distinct().select_related("station", "external_station")

        if not lots.exists():
            self.stdout.write(self.style.WARNING("Sin lotes con biofixes. Nada que procesar."))
            return

        # --- Ciclo por lote ---
        totals = {"lots": 0, "summaries_om": 0, "summaries_st": 0, "recalc": 0, "forecast": 0}

        for lot in lots:
            totals["lots"] += 1
            lot_ext = lot.external_station  # cada lote usa su propia estación externa

            # 1. Consolidar desde Open-Meteo usando la estación del lote
            if lot_ext:
                summary = DailySummary.consolidate_from_open_meteo(
                    lot, target_date, lot_ext
                )
                if summary:
                    totals["summaries_om"] += 1
            else:
                self.stdout.write(self.style.WARNING(
                    f"  {lot.name}: sin estación externa configurada — "
                    "Open-Meteo omitido. Asigná una ExternalStation al lote."
                ))

            # 2. Consolidar desde estación propia
            #    - En modo --eod siempre lo intenta (fin del día, datos completos)
            #    - Sin --eod solo intenta si el lote tiene estación (datos parciales del día)
            if eod or lot.station_id:
                station_summary = DailySummary.consolidate_from_station(lot, target_date)
                if station_summary:
                    totals["summaries_st"] += 1

            # 3. Recalcular GDD para todos los biofixes del lote
            biofixes = Biofix.objects.filter(crop__lot=lot).select_related("crop")
            for biofix in biofixes:
                acc, _ = GDDAccumulator.objects.get_or_create(biofix=biofix)
                gdd = acc.recalculate()
                totals["recalc"] += 1
                self.stdout.write(
                    f"  {lot.name} / {biofix.counter}: {gdd} GDD "
                    f"(desde {biofix.date})"
                )

            # 4. Consolidar pronóstico (hoy+1 … hoy+7) y evaluar alertas anticipadas
            if lot_ext:
                forecast_days = 0
                for delta in range(1, 8):
                    forecast_date = target_date + timedelta(days=delta)
                    fs = DailySummary.consolidate_from_open_meteo(
                        lot, forecast_date, lot_ext
                    )
                    if fs:
                        forecast_days += 1
                if forecast_days:
                    from alert.signals import evaluate_indicators_forecast
                    evaluate_indicators_forecast(lot=lot, today=target_date)
                    totals["forecast"] += forecast_days

        # --- Resumen ---
        self.stdout.write(
            self.style.SUCCESS(
                f"\nListo: {totals['lots']} lotes · "
                f"{totals['summaries_om']} resúmenes Open-Meteo · "
                f"{totals['summaries_st']} resúmenes estación · "
                f"{totals['recalc']} acumuladores recalculados · "
                f"{totals['forecast']} días de pronóstico evaluados"
            )
        )
