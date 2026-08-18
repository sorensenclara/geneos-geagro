"""
Evaluador de Ventana óptima de aplicación (semáforo operativo).

Informa si las condiciones
permiten realizar aplicaciones fitosanitarias en este momento.

Niveles:
  None     → Verde  — condiciones óptimas (no se emite alerta)
  warning  → Amarillo — precaución, revisar antes de aplicar
  alert    → Rojo   — no aplicar

Lógica Verde (todas deben cumplirse):
  - Viento 5–15 km/h
  - Ráfagas < 20 km/h
  - Delta T 2–8 °C
  - T < 28 °C
  - HR 60–85 %

Lógica Amarillo (cualquiera):
  - Viento 15–20 km/h
  - Ráfagas 20–25 km/h
  - Delta T 0–2 °C (posible inversión) o 8–10 °C (aire seco)
  - Lluvia en 4–6 h

Lógica Rojo (cualquiera):
  - Viento > 20 km/h
  - Ráfagas > 25 km/h
  - Delta T < 0 °C (inversión térmica)
  - Delta T > 10 °C
  - Lluvia en < 4 h
  - Viento < 3 km/h de noche (20–06 h) → inversión radiativa

Delta T = T − Tw   (Tw = bulbo húmedo, fórmula de Stull 2011)

Fuente de datos: OpenMeteoHourly (ventana 06–12 h).
Fallback: DailySummary (tmax, hr_media, wind_max, wind_gusts_max).

Los umbrales son sobreescribibles desde IndicatorVariable (role='filter').
Si no están cargados en el admin, se usan los defaults definidos aquí.
"""

from __future__ import annotations
import math
from datetime import timedelta
from alert.evaluators.base import BaseEvaluator

# ── Defaults (km/h, °C, %) ────────────────────────────────────────────────────
DEFAULT_VIENTO_MIN_VERDE   =  5.0   # km/h  viento mínimo para buena cobertura
DEFAULT_VIENTO_MAX_VERDE   = 15.0   # km/h  límite verde→amarillo
DEFAULT_VIENTO_MAX_AMARI   = 20.0   # km/h  límite amarillo→rojo
DEFAULT_RAFAGA_MAX_VERDE   = 20.0   # km/h  ráfagas: límite verde→amarillo
DEFAULT_RAFAGA_MAX_AMARI   = 25.0   # km/h  ráfagas: límite amarillo→rojo
DEFAULT_DT_MIN_VERDE       =  2.0   # °C    Delta T mínimo óptimo
DEFAULT_DT_MAX_VERDE       =  8.0   # °C    Delta T máximo óptimo
DEFAULT_DT_MAX_AMARI       = 10.0   # °C    Delta T límite amarillo→rojo
DEFAULT_T_MAX_VERDE        = 28.0   # °C    temperatura máxima para verde
DEFAULT_HR_MIN_VERDE       = 60.0   # %
DEFAULT_HR_MAX_VERDE       = 85.0   # %
DEFAULT_VIENTO_NOCHE_MIN   =  3.0   # km/h  por debajo de noche → inversión → rojo

HORAS_APLICACION = set(range(6, 13))       # 06 h–12 h
HORAS_NOCHE      = set(range(20, 24)) | set(range(0, 6))


class VentanaAplicacionEvaluator(BaseEvaluator):

    def evaluate(self, indicator, daily_summary, bbch_code):
        # BBCH no aplica: la ventana de aplicación es independiente del estadio
        qs = list(self.hourly_qs(daily_summary))

        if not qs:
            return self._evaluate_from_daily(indicator, daily_summary)

        # Priorizar ventana de aplicación matutina; si no hay, usar todas las horas
        window = [h for h in qs if h.datetime.hour in HORAS_APLICACION] or qs

        worst = None
        for hour in window:
            level = self._evaluate_hour(indicator, daily_summary, hour)
            worst = self.highest_level(worst, level)

        return worst

    # ------------------------------------------------------------------

    def _evaluate_hour(self, indicator, daily_summary, hour):
        t     = float(hour.temperature or 0)
        hr    = float(hour.humidity    or 0)
        wind  = float(hour.wind_speed  or 0)
        gusts = float(hour.wind_gusts  or 0)

        tw      = self._wet_bulb_stull(t, hr)
        delta_t = t - tw

        v_amari  = self._umbral(indicator, "Viento máximo",    "alert",   DEFAULT_VIENTO_MAX_AMARI)
        r_amari  = self._umbral(indicator, "Ráfaga máxima",   "alert",   DEFAULT_RAFAGA_MAX_AMARI)
        dt_amari = self._umbral(indicator, "Delta T máximo",  "alert",   DEFAULT_DT_MAX_AMARI)
        v_noche  = self._umbral(indicator, "Viento mínimo noche", "alert", DEFAULT_VIENTO_NOCHE_MIN)

        # ── ROJO ──────────────────────────────────────────────────────
        if wind > v_amari:
            return "alert"
        if gusts > r_amari:
            return "alert"
        if delta_t < 0 or delta_t > dt_amari:
            return "alert"
        if hour.datetime.hour in HORAS_NOCHE and wind < v_noche:
            return "alert"
        if self._lluvia_proximas_horas(daily_summary, hour.datetime, 4):
            return "alert"

        # ── AMARILLO ──────────────────────────────────────────────────
        v_warn   = self._umbral(indicator, "Viento máximo",   "warning", DEFAULT_VIENTO_MAX_VERDE)
        r_warn   = self._umbral(indicator, "Ráfaga máxima",   "warning", DEFAULT_RAFAGA_MAX_VERDE)
        dt_min   = self._umbral(indicator, "Delta T mínimo",  "warning", DEFAULT_DT_MIN_VERDE)
        dt_max   = self._umbral(indicator, "Delta T máximo",  "warning", DEFAULT_DT_MAX_VERDE)

        if wind > v_warn:
            return "warning"
        if gusts > r_warn:
            return "warning"
        if delta_t < dt_min or delta_t > dt_max:
            return "warning"
        if self._lluvia_proximas_horas(daily_summary, hour.datetime, 6):
            return "warning"

        return None  # Verde

    def _evaluate_from_daily(self, indicator, daily_summary):
        """Fallback cuando no hay datos horarios disponibles."""
        wind  = float(daily_summary.wind_max       or 0)
        gusts = float(daily_summary.wind_gusts_max or 0)
        t     = float(daily_summary.tmax           or 0)
        hr    = float(daily_summary.hr_media       or 50)

        tw      = self._wet_bulb_stull(t, hr)
        delta_t = t - tw

        v_amari  = self._umbral(indicator, "Viento máximo",   "alert", DEFAULT_VIENTO_MAX_AMARI)
        r_amari  = self._umbral(indicator, "Ráfaga máxima",   "alert", DEFAULT_RAFAGA_MAX_AMARI)
        dt_amari = self._umbral(indicator, "Delta T máximo",  "alert", DEFAULT_DT_MAX_AMARI)

        if wind > v_amari or gusts > r_amari or delta_t < 0 or delta_t > dt_amari:
            return "alert"

        v_warn  = self._umbral(indicator, "Viento máximo",  "warning", DEFAULT_VIENTO_MAX_VERDE)
        r_warn  = self._umbral(indicator, "Ráfaga máxima",  "warning", DEFAULT_RAFAGA_MAX_VERDE)
        dt_min  = self._umbral(indicator, "Delta T mínimo", "warning", DEFAULT_DT_MIN_VERDE)
        dt_max  = self._umbral(indicator, "Delta T máximo", "warning", DEFAULT_DT_MAX_VERDE)

        if wind > v_warn or gusts > r_warn or delta_t < dt_min or delta_t > dt_max:
            return "warning"

        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _wet_bulb_stull(t: float, hr: float) -> float:
        """Temperatura de bulbo húmedo — fórmula de Stull (2011), error < 0.3 °C."""
        return (
            t * math.atan(0.151977 * math.sqrt(hr + 8.313659))
            + math.atan(t + hr)
            - math.atan(hr - 1.676331)
            + 0.00391838 * hr ** 1.5 * math.atan(0.023101 * hr)
            - 4.686035
        )

    def _lluvia_proximas_horas(self, daily_summary, dt_ref, horas: int) -> bool:
        """True si hay precipitación >0 en las próximas `horas` horas."""
        from weather.models.open_meteo_hourly import OpenMeteoHourly
        lot = daily_summary.lot
        if not hasattr(lot, "external_station") or not lot.external_station_id:
            return False
        return OpenMeteoHourly.objects.filter(
            station=lot.external_station,
            datetime__gt=dt_ref,
            datetime__lte=dt_ref + timedelta(hours=horas),
            precipitation__gt=0,
        ).exists()

    def _umbral(self, indicator, var_name: str, alert_level: str, default: float) -> float:
        """Lee el umbral desde IndicatorVariable filtrado por nombre y alert_level."""
        iv = (
            indicator.variables
            .filter(variable__name=var_name, role="filter", alert_level=alert_level)
            .select_related("variable")
            .first()
        )
        if iv is not None and iv.min_value is not None:
            return float(iv.min_value)
        return default
