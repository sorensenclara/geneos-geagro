"""
Management command: seed_climate_demo

Carga datos climáticos sintéticos para probar el motor de alertas sin depender
de Open-Meteo real. Requiere que seed_test_data haya corrido antes.

Genera:
  - ExternalStation "Open-Meteo Luján de Cuyo" ligada al lote
  - 15 días de OpenMeteoHourly con clima normal (acumula ~105 GDD → BBCH 11-15)
  - Hoy y mañana con helada a la madrugada (T=-3°C, HR=85%, viento 2 km/h)
  - DailySummary consolidado para cada día
  - GDDAccumulator recalculado desde los datos reales
  - Indicador Helada configurado con FrostEvaluator (max 5 días de anticipación)
  - AlertProfileIndicator: Helada ON para zona Mendoza
  - Evaluación de alertas hoy + pronóstico mañana

Idempotente: se puede correr varias veces.
"""

from datetime import date as date_cls, timedelta, datetime, time, timezone as dt_timezone
from django.core.management.base import BaseCommand
from django.utils import timezone

# ── Clima normal (días pasados) ────────────────────────────────────────────────
# Perfil horario: T sube de tmin a tmax y vuelve a bajar.
# base 10, cutoff 30 → GDD/día ≈ (12+22)/2 - 10 = 7
NORMAL_TMIN   = 12.0
NORMAL_TMAX   = 22.0
NORMAL_HR     = 60.0
NORMAL_WIND   = 8.0
DAYS_HISTORY  = 15   # días de clima normal antes de hoy

# ── Helada (madrugada de hoy y mañana) ────────────────────────────────────────
# T=-3°C, HR=85%, viento 2 km/h → activa FrostEvaluator (BBCH 11, umbral -2°C)
# diff = -3 - (-2) = -1 → nivel "alert" (radiativa por viento bajo)
FROST_HOURS   = list(range(0, 6))   # 0h a 5h
FROST_TEMP    = -3.0
FROST_HR      = 85.0
FROST_WIND    = 2.0


def _hourly_temp(hour, tmin, tmax):
    """Perfil de temperatura horario simplificado (sinusoidal día/noche)."""
    import math
    # mínimo a las 6h, máximo a las 14h
    angle = math.pi * (hour - 6) / 8
    factor = max(0.0, math.sin(angle)) if 6 <= hour <= 22 else 0.0
    return round(tmin + (tmax - tmin) * factor, 1)


def _make_hourly_rows(station, day, is_frost_day):
    """Genera 24 filas OpenMeteoHourly para un día."""
    from weather.models.open_meteo_hourly import OpenMeteoHourly
    rows = []
    for hour in range(24):
        dt = datetime.combine(day, time(hour, 0), tzinfo=dt_timezone.utc)
        if is_frost_day and hour in FROST_HOURS:
            temp, hr, wind = FROST_TEMP, FROST_HR, FROST_WIND
        else:
            temp = _hourly_temp(hour, NORMAL_TMIN, NORMAL_TMAX)
            hr   = NORMAL_HR
            wind = NORMAL_WIND
        rows.append({
            "station":     station,
            "datetime":    dt,
            "temperature": temp,
            "humidity":    hr,
            "wind_speed":  wind,
            "precipitation": 0.0,
        })
    return rows


class Command(BaseCommand):
    help = "Carga datos climáticos de prueba y configura la alerta de helada"

    def handle(self, *args, **options):
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)

        self._step("Verificar datos base (seed_test_data)")
        lot, crop = self._get_base_data()
        if lot is None:
            return

        self._step("ExternalStation — Luján de Cuyo")
        station = self._seed_station(lot)

        self._step("Biofix vine — ajustar fecha de cero")
        self._fix_biofix(crop, today)

        self._step(f"OpenMeteoHourly — {DAYS_HISTORY} días historia (clima normal)")
        self._seed_hourly_history(station, today)

        self._step("OpenMeteoHourly — hoy (helada a la madrugada)")
        self._seed_hourly_day(station, today, is_frost=True)

        self._step("OpenMeteoHourly — mañana (pronóstico con helada)")
        self._seed_hourly_day(station, tomorrow, is_frost=True)

        self._step("DailySummary — consolidar historia")
        self._consolidate_history(lot, station, today)

        self._step("GDD — recalcular desde datos reales")
        gdd = self._recalculate_gdd(crop, today)
        self._ok(f"GDD acumulado: {gdd} → {self._bbch_label(gdd)}")

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Datos climáticos cargados.\n"
            f"  GDD: {gdd} | BBCH: {self._bbch_label(gdd)}\n"
            f"  Hoy y mañana tienen helada a la madrugada (T={FROST_TEMP}°C, HR={FROST_HR}%, viento {FROST_WIND} km/h).\n"
            f"  Configurá el indicador y el perfil de zona en el admin,\n"
            f"  luego corré run_daily_cycle para que se evalúen las alertas."
        ))

    # ── Helpers de output ──────────────────────────────────────────────────────

    def _step(self, msg):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n→ {msg}"))

    def _ok(self, msg):
        self.stdout.write(f"   {msg}")

    def _bbch_label(self, gdd):
        from crop_monitoring.models.phenological_state import PhenologicalState
        stage = PhenologicalState.current_stage(gdd)
        return f"BBCH {stage.bbch} — {stage.stage_name}" if stage else "sin etapa"

    # ── 1. Datos base ──────────────────────────────────────────────────────────

    def _get_base_data(self):
        from producer.models.lot import Lot
        from operation.models.crop import Crop

        lot = Lot.objects.filter(name="Lote Norte — Malbec").first()
        if not lot:
            self.stderr.write(self.style.ERROR(
                "No se encontró 'Lote Norte — Malbec'. "
                "Ejecutá seed_test_data primero."
            ))
            return None, None

        crop = Crop.objects.filter(name="Malbec 2026/27 — Lote Norte").first()
        if not crop:
            self.stderr.write(self.style.ERROR(
                "No se encontró el cultivo Malbec. "
                "Ejecutá seed_test_data primero."
            ))
            return None, None

        self._ok(f"Lot: {lot} (id={lot.id})")
        self._ok(f"Crop: {crop} (id={crop.id})")
        return lot, crop

    # ── 2. ExternalStation ─────────────────────────────────────────────────────

    def _seed_station(self, lot):
        from weather.models.station_external import ExternalStation

        station, created = ExternalStation.objects.get_or_create(
            name="Open-Meteo Luján de Cuyo",
            defaults={
                "latitude":     -33.05,
                "longitude":    -68.88,
                "forecast_days": 7,
                "variable":     "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
                "url":          "https://api.open-meteo.com/v1/forecast",
            },
        )
        action = "creada" if created else "ya existía"
        self._ok(f"ExternalStation: {station.name} ({action}, id={station.id})")

        if lot.external_station_id != station.id:
            lot.external_station = station
            lot.save(update_fields=["external_station"])
            self._ok("Lote vinculado a la estación")

        return station

    # ── 3. Biofix ──────────────────────────────────────────────────────────────

    def _fix_biofix(self, crop, today):
        from crop_monitoring.models.biofix import Biofix
        from crop_monitoring.models.gdd_accumulator import GDDAccumulator

        # Cero en today - DAYS_HISTORY - 5 → primeros 5 días sin DailySummary → 0 GDD
        # Luego DAYS_HISTORY días con datos → ~105 GDD → BBCH 11-15
        biofix_date = today - timedelta(days=DAYS_HISTORY + 5)
        biofix, created = Biofix.objects.get_or_create(
            crop=crop,
            counter=Biofix.COUNTER_VINE,
            defaults={
                "base_temp":    10.0,
                "date":         biofix_date,
                "origin":       Biofix.ORIGIN_MANUAL,
                "is_confirmed": True,
            },
        )
        if not created and biofix.date != biofix_date:
            biofix.date         = biofix_date
            biofix.is_confirmed = True
            biofix.save(update_fields=["date", "is_confirmed"])
            self._ok(f"Biofix vine actualizado → {biofix_date}")
        else:
            self._ok(f"Biofix vine: {biofix.date} ({'creado' if created else 'sin cambios'})")

        GDDAccumulator.objects.get_or_create(biofix=biofix)

    # ── 4. OpenMeteoHourly historia ───────────────────────────────────────────

    def _seed_hourly_history(self, station, today):
        count = 0
        for delta in range(DAYS_HISTORY, 0, -1):
            day = today - timedelta(days=delta)
            count += self._seed_hourly_day(station, day, is_frost=False)
        self._ok(f"{count} registros horarios creados/actualizados (clima normal)")

    def _seed_hourly_day(self, station, day, is_frost):
        from weather.models.open_meteo_hourly import OpenMeteoHourly
        rows = _make_hourly_rows(station, day, is_frost)
        count = 0
        for r in rows:
            _, created = OpenMeteoHourly.objects.update_or_create(
                station=r["station"],
                datetime=r["datetime"],
                defaults={k: v for k, v in r.items() if k not in ("station", "datetime")},
            )
            count += 1
        label = "helada" if is_frost else "normal"
        self._ok(f"{day} [{label}]: {count} horas")
        return count

    # ── 5. DailySummary historia ───────────────────────────────────────────────

    def _consolidate_history(self, lot, station, today):
        from weather.models.daily_summary import DailySummary
        count = 0
        for delta in range(DAYS_HISTORY, 0, -1):
            day = today - timedelta(days=delta)
            obj = DailySummary.consolidate_from_open_meteo(lot, day, station)
            if obj:
                count += 1
        self._ok(f"{count} resúmenes diarios consolidados")

    def _consolidate_day(self, lot, station, day):
        from weather.models.daily_summary import DailySummary
        obj = DailySummary.consolidate_from_open_meteo(lot, day, station)
        if obj:
            self._ok(f"DailySummary {day}: tmin={obj.tmin} tmax={obj.tmax}")
        else:
            self._ok(f"DailySummary {day}: sin datos")

    # ── 6. GDD recalculate ────────────────────────────────────────────────────

    def _recalculate_gdd(self, crop, today):
        from crop_monitoring.models.biofix import Biofix
        from crop_monitoring.models.gdd_accumulator import GDDAccumulator

        try:
            biofix = Biofix.objects.get(crop=crop, counter=Biofix.COUNTER_VINE)
            acc, _ = GDDAccumulator.objects.get_or_create(biofix=biofix)
            return acc.recalculate(until=today)
        except Biofix.DoesNotExist:
            self._ok("Biofix vine no encontrado")
            return 0

