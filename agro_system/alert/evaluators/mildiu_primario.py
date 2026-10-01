"""
Evaluador de Mildiu primario (Plasmopara viticola) — ventana horaria 48h.

Configurar en el indicador:
    evaluator = "alert.evaluators.mildiu_primario.MildiuPrimarioEvaluator"

Lógica de infección (basada en Goidanich / Mills adaptado):
  Una "hora de infección" ocurre cuando simultáneamente:
    - temperature >= T_MIN  (condición mínima de germinación)
    - precipitation > 0  O  humidity >= HR_WETNESS  (follaje mojado)
  Se evalúan las últimas 48 horas (hoy + ayer en OpenMeteoHourly).

  Filtros obligatorios (AND — si alguno falla, no hay alerta):
    1. Lluvia total en 48h  >= LLUVIA_MIN mm
    2. Horas de infección   >= HORAS_INF_MIN

  Nivel base por BBCH (IndicatorBand):
    - BBCH 14–59  → warning
    - BBCH 60–69  → critical   (floración — máximo riesgo)
    - BBCH 70–79  → alert

  Escalada adicional por intensidad de condiciones:
    - horas de infección >= HORAS_INF_CRITICAL  → sube un escalón

Umbrales configurables vía IndicatorVariable (role='filter'):
  "Temperatura mínima"   min_value → T_MIN         (default 10 °C)
  "Lluvia mínima (mm)"   min_value → LLUVIA_MIN     (default 10 mm)
  "Horas de infección"   min_value → HORAS_INF_MIN  (default 4 h)
  "Humedad relativa"     min_value → HR_WETNESS      (default 90 %)

Fuente de datos: OpenMeteoHourly (temperature, precipitation, humidity).
Si el lote no tiene external_station cae a None (sin alerta).
"""

from __future__ import annotations
from datetime import timedelta

from weather.models.open_meteo_hourly import OpenMeteoHourly
from alert.evaluators.base import BaseEvaluator

# Defaults — sobreescribibles desde IndicatorVariable en el admin
DEFAULT_T_MIN        = 10.0   # °C — mínimo para germinación de oosporas
DEFAULT_LLUVIA_MIN   = 10.0   # mm — lluvia acumulada en 48 h
DEFAULT_HORAS_MIN    =  4     # h  — horas de infección mínimas para disparar
DEFAULT_HORAS_CRIT   = 12     # h  — horas de infección para escalar un nivel
DEFAULT_HR_WETNESS   = 90.0   # %  — HR que considera follaje mojado (sin lluvia)


class MildiuPrimarioEvaluator(BaseEvaluator):

    def evaluate(self, indicator, daily_summary, bbch_code):
        lot = daily_summary.lot
        if not hasattr(lot, "external_station") or lot.external_station is None:
            return None

        # ── umbrales desde IndicatorVariable ──────────────────────────────
        t_min       = self._umbral(indicator, "Temperatura mínima", DEFAULT_T_MIN)
        lluvia_min  = self._umbral(indicator, "Lluvia mínima (mm)", DEFAULT_LLUVIA_MIN)
        horas_min   = int(self._umbral(indicator, "Horas de infección", DEFAULT_HORAS_MIN))
        horas_crit  = int(self._umbral(indicator, "Horas escalada",    DEFAULT_HORAS_CRIT))
        hr_wetness  = self._umbral(indicator, "Humedad relativa",    DEFAULT_HR_WETNESS)

        # ── ventana 48 h: hoy + ayer ───────────────────────────────────────
        ayer = daily_summary.date - timedelta(days=1)
        rows = (
            OpenMeteoHourly.objects
            .filter(
                station=lot.external_station,
                datetime__date__in=[ayer, daily_summary.date],
            )
            .order_by("datetime")
            .values("temperature", "precipitation", "humidity")
        )

        if not rows:
            return None

        lluvia_total   = 0.0
        horas_infeccion = 0

        for row in rows:
            t    = float(row["temperature"])  if row["temperature"]  is not None else None
            prec = float(row["precipitation"]) if row["precipitation"] is not None else 0.0
            hr   = float(row["humidity"])      if row["humidity"]      is not None else 0.0

            lluvia_total += prec

            if t is None:
                continue

            follaje_mojado = prec > 0 or hr >= hr_wetness
            if t >= t_min and follaje_mojado:
                horas_infeccion += 1

        # ── filtros obligatorios ───────────────────────────────────────────
        if lluvia_total < lluvia_min:
            return None
        if horas_infeccion < horas_min:
            return None

        # ── nivel base por BBCH ───────────────────────────────────────────
        level = self.level_from_bands(indicator, bbch_code)
        if level is None:
            return None

        # ── escalar por intensidad ────────────────────────────────────────
        if horas_infeccion >= horas_crit:
            level = self._escalar(level)

        return level

    # ── helpers ───────────────────────────────────────────────────────────

    def _umbral(self, indicator, var_name: str, default: float) -> float:
        iv = (
            indicator.variables
            .filter(variable__name=var_name, role="filter")
            .select_related("variable")
            .first()
        )
        if iv is not None and iv.min_value is not None:
            return float(iv.min_value)
        return default

    def _escalar(self, level: str) -> str:
        escala = ("warning", "alert", "critical")
        idx = escala.index(level) if level in escala else 0
        return escala[min(idx + 1, len(escala) - 1)]
