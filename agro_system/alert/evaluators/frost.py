"""
Evaluador de helada.

Configurar en el indicador:
    evaluator = "alert.evaluators.frost.FrostEvaluator"

No requiere IndicatorVariable ni IndicatorBand — toda la lógica es interna:
  - Umbral depende del BBCH (tabla Poni et al. 2022)
  - Temperatura efectiva es Tw (bulbo húmedo, Stull 2011), no T seca
  - Los umbrales BBCH son el piso de critical; hay dos escalones por encima:
      critical → T o Tw en o por debajo del umbral
      alert    → dentro de 0.5 °C sobre el umbral
      warning  → dentro de 1.0 °C sobre el umbral
  - Helada radiativa (viento < 8 km/h): sube un escalón (warning→alert, alert→critical)

Fuente de datos: OpenMeteoHourly (temperature, humidity, wind_speed por hora).
Se evalúa hora a hora y se devuelve el nivel más grave del día.
"""

import math
from alert.evaluators.base import BaseEvaluator

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

FALLBACK_THRESHOLD   = -2.0  # sin BBCH conocido
WIND_RADIATIVE_KMH   = 8.0   # por debajo de este viento → helada radiativa

# Márgenes por encima del umbral crítico BBCH
ALERT_MARGIN   = 0.5   # °C sobre el umbral → alert
WARNING_MARGIN = 1.0   # °C sobre el umbral → warning


def _bump_level(level: str | None) -> str | None:
    """Sube un escalón de severidad (helada radiativa). critical no cambia."""
    if level == "warning":
        return "alert"
    if level == "alert":
        return "critical"
    return level


def _level_from_excess(excess: float) -> str | None:
    """
    excess = temperatura - umbral_crítico_BBCH.
    <= 0  → critical  (en o por debajo del umbral de daño)
    <= 0.5 → alert    (dentro de medio grado del umbral)
    <= 1.0 → warning  (dentro de un grado del umbral)
    > 1.0  → None     (sin riesgo por esta variable)
    """
    if excess <= 0:
        return "critical"
    elif excess <= ALERT_MARGIN:
        return "alert"
    elif excess <= WARNING_MARGIN:
        return "warning"
    return None


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



class FrostEvaluator(BaseEvaluator):

    def evaluate(self, _indicator, daily_summary, bbch_code):
        threshold = _get_threshold(bbch_code)
        if threshold is None:
            return None   # post-floración, sin riesgo

        worst_level = None

        for row in self.hourly_qs(daily_summary):
            if row.temperature is None or row.humidity is None:
                continue

            t    = float(row.temperature)
            hr   = float(row.humidity)
            wind = float(row.wind_speed) if row.wind_speed is not None else 0.0
            tw   = _stull_tw(t, hr)

            # Tw y T se comparan contra el mismo umbral crítico BBCH;
            # Tw es siempre <= T, así que en aire seco dispara antes.
            hour_level = self.highest_level(
                _level_from_excess(t  - threshold),
                _level_from_excess(tw - threshold),
            )
            # Helada radiativa (noche calma): sube un escalón de severidad.
            if wind < WIND_RADIATIVE_KMH:
                hour_level = _bump_level(hour_level)
            worst_level = self.highest_level(worst_level, hour_level)
            if worst_level == "critical":
                break  # ya no puede empeorar

        return worst_level
