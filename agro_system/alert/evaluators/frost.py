"""
Evaluador de helada.

Configurar en el indicador:
    evaluator = "alert.evaluators.frost.FrostEvaluator"

No requiere IndicatorVariable ni IndicatorBand — toda la lógica es interna:
  - Umbral depende del BBCH (tabla Poni et al. 2022)
  - Temperatura efectiva es Tw (bulbo húmedo, Stull 2011), no T seca
  - Nivel depende de cuánto se supera el umbral
  - Helada radiativa (viento < 8 km/h) agrava el nivel

Fuente de datos: OpenMeteoHourly (temperature, humidity, wind_speed por hora).
Se evalúa hora a hora y se devuelve el nivel más grave del día.
"""

import math
from alert.evaluators.base import BaseEvaluator

# Umbral de viento para clasificar tipo de helada
WIND_RADIATIVE_KMH = 8.0

# Tabla BBCH → umbral crítico de temperatura (Poni et al. 2022)
# Cada tupla: (bbch_desde, bbch_hasta, umbral_°C)
# Si el BBCH no cae en ningún rango → sin riesgo (retorna None)
BBCH_THRESHOLDS = [
    (1,  5,  -3.5),   # yema hinchada, pre-brotación
    (6,  9,  -2.5),   # puntas verdes
    (9,  27, -1.0),   # Brotacion / hojas visibles
    (28, 53, -1.0),   # inflorescencias visibles
    (54, 65, -0.5),   # plena floración
    # BBCH 66–80: sin riesgo significativo (cuaje → envero)
    (81, 99, -1.5),   # maduración / envero en adelante
]

FALLBACK_THRESHOLD = -2.0   # sin BBCH conocido


def _stull_tw(t: float, hr: float) -> float:
    """
    Temperatura de bulbo húmedo (Tw) según Stull (2011).
    Válida para T ∈ [-20, 50] °C y HR ∈ [5, 99] %.
    Tw ≤ T siempre; la diferencia crece cuanto más seco el aire.
    """
    tw = (
        t * math.atan(0.151977 * math.sqrt(hr + 8.313659))
        + math.atan(t + hr)
        - math.atan(hr - 1.676331)
        + 0.00391838 * hr ** 1.5 * math.atan(0.023101 * hr)
        - 4.686035
    )
    return tw


def _get_threshold(bbch_code: int | None) -> float | None:
    """Umbral de T para el BBCH dado. None = sin riesgo (no está en ningún rango)."""
    if bbch_code is None:
        return FALLBACK_THRESHOLD
    for bbch_from, bbch_to, threshold in BBCH_THRESHOLDS:
        if bbch_from <= bbch_code <= bbch_to:
            return threshold
    return None


def _level_from_diff(diff: float, is_radiative: bool) -> str:
    """
    diff = min(T - umbral_T, Tw - umbral_Tw)
    Negativo significa que está por debajo del umbral.
    La helada radiativa sube un escalón por ser más peligrosa.
    """
    if diff > -1.0:
        level = "warning"
    elif diff > -2.0:
        level = "alert"
    else:
        level = "critical"

    if is_radiative and level == "warning":
        level = "alert"

    return level


class FrostEvaluator(BaseEvaluator):

    def evaluate(self, _indicator, daily_summary, bbch_code):
        threshold = _get_threshold(bbch_code)
        if threshold is None:
            return None   # post-floración, sin riesgo

        tw_threshold = threshold - 1.0   # Tw dispara 1 °C antes que T seca
        worst_level = None

        for row in self.hourly_qs(daily_summary):
            if row.temperature is None or row.humidity is None:
                continue

            t  = float(row.temperature)
            hr = float(row.humidity)
            wind = float(row.wind_speed) if row.wind_speed is not None else 0.0

            tw = _stull_tw(t, hr)
            is_radiative = wind < WIND_RADIATIVE_KMH

            triggered = (t <= threshold) or (tw <= tw_threshold)
            if not triggered:
                continue

            diff = min(t - threshold, tw - tw_threshold)
            level = _level_from_diff(diff, is_radiative)
            worst_level = self.highest_level(worst_level, level)

        return worst_level
