"""
Evaluador personalizado para granizo / frente tormentoso.

Configurar en el indicador:
    evaluator = "alert.evaluators.storm_hail.StormHailEvaluator"

Lógica: dispara si ALGUNA hora del día cumple:
  1. Todos los filtros configurados en IndicatorVariable (ej: wind_gusts >= 50)
  2. Caída de temperatura >= 5 °C en esa hora (delta_t_1h <= -5)
  3. Precipitación >= 10 mm en esa hora (proxy de 5 mm/15 min)

Las condiciones 2 y 3 son tiempo-dependientes y van hardcodeadas aquí.
La condición 1 (ráfagas u otras simples) se configura desde el admin
via IndicatorVariable (role=filter) para poder ajustar por zona.

Severidad: determinada por IndicatorBand según BBCH (sin threshold,
solo por etapa). Configurar en el admin.
"""

from alert.evaluators.base import BaseEvaluator

DELTA_T_1H  = -5.0   # °C/h — caída mínima para considerar frente
RAIN_MMH    = 10.0   # mm/h — proxy de 5 mm/15 min


class StormHailEvaluator(BaseEvaluator):

    def evaluate(self, indicator, daily_summary, bbch_code):
        triggered = (
            self.hourly_filtered(indicator, daily_summary)  # filtros del admin (ej: wind_gusts)
            .filter(
                delta_t_1h__lte=DELTA_T_1H,       # tiempo-dependiente: hardcodeado
                precipitation__gte=RAIN_MMH,        # tiempo-dependiente: hardcodeado
            )
            .exists()
        )
        if not triggered:
            return None
        return self.level_from_bands(indicator, bbch_code)
