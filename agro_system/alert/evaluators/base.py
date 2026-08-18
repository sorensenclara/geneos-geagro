"""
Base class for custom alert evaluators (Option B escape hatch).

Use when the generic filter + IndicatorBand system can't express the logic —
typically when the condition involves time-based rates, cross-variable calculations,
or multi-step aggregations.

Usage
-----
1. Subclass BaseEvaluator in a module under alert/evaluators/.
2. Implement evaluate().
3. Set indicator.evaluator = "alert.evaluators.my_module.MyEvaluator" in the admin.

The engine calls get_evaluator() on the Indicator, then evaluate() with the same
context it would pass to the generic engine.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from weather.models.open_meteo_hourly import OpenMeteoHourly


if TYPE_CHECKING:
    from weather.models.daily_summary import DailySummary
    from alert.models.indicator import Indicator


LEVELS = ("warning", "alert", "critical")


class BaseEvaluator:
    """
    Subclass this and implement evaluate().
    Return one of 'warning', 'alert', 'critical', or None (no alert).
    """

    def evaluate(
        self,
        indicator: "Indicator",
        daily_summary: "DailySummary",
        bbch_code: int,
    ) -> str | None:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Helpers available to subclasses
    # ------------------------------------------------------------------

    def hourly_qs(self, daily_summary: "DailySummary"):
        """Queryset de OpenMeteoHourly para el lote y fecha del resumen."""
        lot = daily_summary.lot
        if not hasattr(lot, "external_station") or lot.external_station is None:
            return OpenMeteoHourly.objects.none()
        return OpenMeteoHourly.objects.filter(
            station=lot.external_station,
            datetime__date=daily_summary.date,
        ).order_by("datetime")

    def hourly_filtered(self, indicator: "Indicator", daily_summary: "DailySummary"):
        """
        Aplica los IndicatorVariable (role='filter') del indicador como filtros
        sobre la queryset horaria.

        El nombre de la variable (VarCropTechnique.name) debe coincidir exactamente
        con un campo de OpenMeteoHourly (ej: 'wind_gusts', 'delta_t_1h').

        min_value → __gte, max_value → __lte. Si alguno es None, se omite.
        """
        qs = self.hourly_qs(daily_summary)
        for iv in indicator.variables.filter(role="filter").select_related("variable"):
            field = iv.variable.field_name or iv.variable.name
            if iv.min_value is not None:
                qs = qs.filter(**{f"{field}__gte": iv.min_value})
            if iv.max_value is not None:
                qs = qs.filter(**{f"{field}__lte": iv.max_value})
        return qs

    def level_from_bands(self, indicator: "Indicator", bbch_code: int, value=None) -> str | None:
        """
        Devuelve el nivel más alto disparado por las IndicatorBand para el BBCH actual.

        - Si la banda tiene threshold=NULL (banda solo-BBCH), dispara siempre que el BBCH coincida.
        - Si tiene threshold, llama band.crosses(value) para verificar.

        Pasar value=None es correcto para bandas sin threshold (granizo, granizo por BBCH).
        Pasar el valor de la variable graduada para bandas con threshold (helada, oídio).
        """
        bands = indicator.bands.filter(
            bbch_from__lte=bbch_code,
            bbch_to__gte=bbch_code,
        )
        triggered = [b.level for b in bands if b.crosses(value)]
        return self.highest_level(*triggered)

    def level_from_variable_thresholds(
        self,
        indicator: "Indicator",
        var_name: str,
        value: float,
    ) -> str | None:
        """
        Evalúa IndicatorVariable con alert_level configurado para una variable dada.

        El umbral se cumple si el valor está dentro del rango [min_value, max_value]
        (igual que la lógica de filtro existente). None en cualquiera de los extremos
        significa sin límite por ese lado.

        Solo procesa variables con alert_level no vacío — las existentes (alert_level="")
        no se tocan y siguen funcionando como filtros en el motor genérico.

        Retorna el nivel más severo de los umbrales que se cumplen, o None.

        Ejemplo:
            # Indicador configurado con:
            #   "Viento" | alert_level="alert"    | min_value=25
            #   "Viento" | alert_level="critical" | min_value=40
            wind = 35.0
            level = self.level_from_variable_thresholds(indicator, "Viento", wind)
            # → "alert"  (25 ≤ 35, pero 35 < 40)
        """
        ivs = (
            indicator.variables
            .filter(variable__name=var_name, role="filter")
            .exclude(alert_level="")
            .select_related("variable")
        )
        triggered = []
        for iv in ivs:
            in_range = True
            if iv.min_value is not None and value < iv.min_value:
                in_range = False
            if iv.max_value is not None and value > iv.max_value:
                in_range = False
            if in_range:
                triggered.append(iv.alert_level)
        return self.highest_level(*triggered)

    def highest_level(self, *levels: str | None) -> str | None:
        """Devuelve el nivel más severo entre los recibidos."""
        for lvl in reversed(LEVELS):
            if lvl in levels:
                return lvl
        return None
