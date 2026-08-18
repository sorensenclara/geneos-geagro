"""
Evaluador de Mildiu primario (Plasmopara viticola).

Configurar en el indicador:
    evaluator = "alert.evaluators.mildiu_primario.MildiuPrimarioEvaluator"

Diseño híbrido: el código maneja solo la lógica estructural que no puede
expresarse con el motor genérico; los umbrales y los niveles viven en el admin.

Lógica estructural (en código):
  - T_media = (tmin + tmax) / 2  (campo no disponible en DailySummary)
  - Ventana 24–48 h: se suma lluvia de hoy + lluvia de ayer

Umbrales (IndicatorVariable, role='filter'):
  - "Temperatura media"  min_value=10  → T_media mínima para infección (bloquea si no se cumple)
  - "Lluvia (mm)"        min_value=10  → lluvia mínima en 24–48 h (bloquea si no se cumple)
  - "Humedad relativa"   min_value=80  → HR alta sube un nivel de criticidad (NO bloquea)
  Si una variable no está configurada en el admin, se usa el DEFAULT_* interno.

Niveles (IndicatorBand, sin threshold — solo por BBCH):
  - BBCH 14–59  → alert    (pre-floración)
  - BBCH 60–69  → critical (floración — riesgo máximo, siempre crítico)
  - BBCH 70–79  → alert    (cuaje → envero)

  Si HR ≥ umbral: sube un escalón adicional (alert → critical).
  En floración ya es critical, así que HR no cambia nada ahí.

Fuente de datos: DailySummary (tmin, tmax, lluvia_mm, hr_media)
                 + DailySummary del día anterior (lluvia_mm).
"""

from __future__ import annotations
from datetime import timedelta
from alert.evaluators.base import BaseEvaluator

# Defaults si no hay IndicatorVariable configuradas en el admin
DEFAULT_T_MEDIA_MIN  = 10.0   # °C
DEFAULT_LLUVIA_MM    = 10.0   # mm en 24–48 h
DEFAULT_HR_MIN       = 80.0   # %


class MildiuPrimarioEvaluator(BaseEvaluator):

    def evaluate(self, indicator, daily_summary, bbch_code):
        # 1. Leer umbrales desde IndicatorVariable (fallback a defaults)
        t_umbral   = self._umbral(indicator, "Temperatura media", DEFAULT_T_MEDIA_MIN)
        lluvia_min = self._umbral(indicator, "Lluvia (mm)",       DEFAULT_LLUVIA_MM)
        hr_min     = self._umbral(indicator, "Humedad relativa",  DEFAULT_HR_MIN)

        # 2. T media > umbral  (lógica estructural: no existe t_media en DailySummary)
        if daily_summary.tmin is None or daily_summary.tmax is None:
            return None
        t_media = (float(daily_summary.tmin) + float(daily_summary.tmax)) / 2.0
        if t_media <= t_umbral:
            return None

        # 3. Lluvia ≥ umbral en ventana 24–48 h  (lógica estructural: dos días)
        lluvia_hoy  = float(daily_summary.lluvia_mm or 0)
        lluvia_ayer = self._lluvia_dia_anterior(daily_summary)
        lluvia_max  = max(lluvia_hoy, lluvia_ayer)
        if lluvia_max < lluvia_min:
            return None

        # 4. Nivel base solo por BBCH (bandas sin threshold)
        level = self.level_from_bands(indicator, bbch_code)
        if level is None:
            return None

        # 5. HR alta → sube un escalón de criticidad (no bloquea, solo agrava)
        if daily_summary.hr_media is not None and float(daily_summary.hr_media) >= hr_min:
            level = self._escalar_nivel(level)

        return level

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _umbral(self, indicator, var_name: str, default: float) -> float:
        """Lee min_value del IndicatorVariable con ese nombre. Fallback al default."""
        iv = (
            indicator.variables
            .filter(variable__name=var_name, role="filter")
            .select_related("variable")
            .first()
        )
        if iv is not None and iv.min_value is not None:
            return float(iv.min_value)
        return default

    def _escalar_nivel(self, level: str) -> str:
        """Sube un nivel: warning→alert, alert→critical, critical→critical."""
        escala = ("warning", "alert", "critical")
        idx = escala.index(level) if level in escala else 0
        return escala[min(idx + 1, len(escala) - 1)]

    def _lluvia_dia_anterior(self, daily_summary) -> float:
        """Lluvia del DailySummary del día anterior para el mismo lote."""
        from weather.models.daily_summary import DailySummary
        prev = DailySummary.objects.filter(
            lot=daily_summary.lot,
            date=daily_summary.date - timedelta(days=1),
        ).first()
        return float(prev.lluvia_mm or 0) if prev else 0.0
