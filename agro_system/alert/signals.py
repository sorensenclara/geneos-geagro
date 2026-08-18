"""
Motor de evaluación de alertas.

Puntos de entrada:
  1. post_save en DailySummary (fecha <= hoy)
       → evalúa indicadores de la zona (AlertProfile) para todos los cultivos del lote
       → luego evalúa indicadores propios del cultivo (Crop.indicators) no cubiertos por zona

  2. post_save en TechnicalCropDetail
       → evalúa solo los indicadores del cultivo que usen esa variable técnica

  3. evaluate_indicators_forecast(lot, today)  — llamado explícitamente desde run_daily_cycle
       → evalúa indicadores para días futuros (hoy+1 … hoy+N) usando DailySummary de pronóstico
       → proyecta GDD para derivar el BBCH correcto por día futuro
       → respeta indicator.max_forecast_days para limitar el horizonte por indicador
       → crea Alert con is_forecast=True; si el evento se confirma se actualiza a False

Fuentes de datos para las variables:
  - VarCropTechnique.is_climatic=True  → DailySummary (por nombre de campo)
  - VarCropTechnique.is_climatic=False → TechnicalCropDetail (última lectura hasta la fecha)
"""

import logging
from datetime import timedelta

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from alert.models.alert import Alert
from alert.models.indicator import Indicator
from alert.models.indicator_variable import IndicatorVariable
from user.models.notification import Notification
from weather.models.daily_summary import DailySummary
from weather.models.open_meteo_hourly import OpenMeteoHourly
from weather.models.weather_data import WeatherData
from operation.models.technical_crop_detail import TechnicalCropDetail

logger = logging.getLogger(__name__)

DAILY_SUMMARY_FIELDS = {
    "tmin", "tmax", "hr_media", "lluvia_mm",
    "eto_mm", "horas_hr_alta", "horas_banda_oidio",
    "wind_max", "wind_gusts_max",
}

_LEVEL_ORDER = {"warning": 0, "alert": 1, "critical": 2}

DEFAULT_FORECAST_DAYS = 7


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _highest_level(*levels):
    valid = [l for l in levels if l in _LEVEL_ORDER]
    return max(valid, key=lambda l: _LEVEL_ORDER[l]) if valid else None


def _bbch_int(stage):
    """Convierte el primer código BBCH de la etapa (ej. '07-09' → 7, '65' → 65)."""
    if stage is None:
        return None
    return int(stage.bbch.split("-")[0])


def _get_bbch_for_crop(crop):
    from crop_monitoring.models.gdd_accumulator import GDDAccumulator
    from crop_monitoring.models.phenological_state import PhenologicalState
    from crop_monitoring.models.biofix import Biofix

    acc = (
        GDDAccumulator.objects
        .filter(biofix__crop=crop, biofix__counter=Biofix.COUNTER_VINE)
        .order_by("-calculation_date")
        .first()
    )
    if acc is None:
        return None
    stage = PhenologicalState.current_stage(acc.accumulated_gdd)
    return _bbch_int(stage)


def _get_bbch_stage_label(crop):
    from crop_monitoring.models.gdd_accumulator import GDDAccumulator
    from crop_monitoring.models.phenological_state import PhenologicalState
    from crop_monitoring.models.biofix import Biofix

    acc = (
        GDDAccumulator.objects
        .filter(biofix__crop=crop, biofix__counter=Biofix.COUNTER_VINE)
        .order_by("-calculation_date")
        .first()
    )
    if acc is None:
        return ""
    stage = PhenologicalState.current_stage(acc.accumulated_gdd)
    return f"BBCH {stage.bbch} — {stage.stage_name}" if stage else ""


def _get_value_for_variable(iv, crop, daily_summary, date=None):
    """
    Resuelve el valor de una variable según su origen:
      - is_climatic=True  → DailySummary (campo por nombre)
      - is_climatic=False → TechnicalCropDetail (última lectura hasta la fecha)

    daily_summary puede ser None para evaluaciones puramente técnicas.
    """
    variable = iv.variable

    if variable.is_climatic:
        if daily_summary is None:
            return None
        field = variable.field_name or variable.name
        if field not in DAILY_SUMMARY_FIELDS:
            logger.debug("Variable climática '%s' no mapeada en DailySummary.", field)
            return None
        raw = getattr(daily_summary, field, None)
        return float(raw) if raw is not None else None

    # Variable técnica del cultivo
    ref_date = date or (daily_summary.date if daily_summary else None)
    if ref_date is None:
        return None
    tech = (
        TechnicalCropDetail.objects
        .filter(crop=crop, varTechnique=variable, date__lte=ref_date)
        .order_by("-date", "-id")
        .first()
    )
    return float(tech.value) if tech is not None else None


# ──────────────────────────────────────────────────────────────────────────────
# Evaluador genérico
# ──────────────────────────────────────────────────────────────────────────────

def _evaluate_generic(indicator, crop, daily_summary, bbch_code, date=None):
    """
    Paso 1 — Filtros puros (role=filter, alert_level=""):
      Todas deben estar en rango [min_value, max_value] (AND).
      Si alguna falla o no tiene dato → no dispara.

    Paso 2 — Variables de nivel (role=filter, alert_level!=""):
      Si el valor está en [min_value, max_value] → contribuye con su alert_level.
      Si no hay dato → se ignora (no bloquea).

    Paso 3 — Nivel por bandas BBCH (IndicatorBand):
      Variable role=graduated → su valor se compara contra las bandas.
      Sin graduada → bandas solo por BBCH (threshold=NULL).

    Nivel final: el más severo entre Paso 2 y Paso 3.
    """
    # ── Paso 1: filtros puros — AND gate ─────────────────────────────────────
    for iv in (
        indicator.variables
        .filter(role=IndicatorVariable.ROLE_FILTER, alert_level="")
        .select_related("variable")
    ):
        value = _get_value_for_variable(iv, crop, daily_summary, date)
        if value is None:
            return None
        if iv.min_value is not None and value < iv.min_value:
            return None
        if iv.max_value is not None and value > iv.max_value:
            return None

    # ── Paso 2: variables que determinan nivel ───────────────────────────────
    level_from_vars = None
    for iv in (
        indicator.variables
        .filter(role=IndicatorVariable.ROLE_FILTER)
        .exclude(alert_level="")
        .select_related("variable")
    ):
        value = _get_value_for_variable(iv, crop, daily_summary, date)
        if value is None:
            continue  # sin dato → se ignora, no bloquea
        in_range = (
            (iv.min_value is None or value >= iv.min_value) and
            (iv.max_value is None or value <= iv.max_value)
        )
        if in_range:
            level_from_vars = _highest_level(level_from_vars, iv.alert_level)

    # ── Paso 3: nivel por bandas BBCH ────────────────────────────────────────
    graduated = list(
        indicator.variables.filter(role=IndicatorVariable.ROLE_GRADUATED).select_related("variable")
    )
    if not graduated:
        level_from_bands = _level_from_bands(indicator, bbch_code, value=None)
    else:
        grad_value = _get_value_for_variable(graduated[0], crop, daily_summary, date)
        level_from_bands = None if grad_value is None else _level_from_bands(indicator, bbch_code, value=grad_value)

    return _highest_level(level_from_vars, level_from_bands)


def _level_from_bands(indicator, bbch_code, value):
    if bbch_code is None:
        return None
    bands = indicator.bands.filter(bbch_from__lte=bbch_code, bbch_to__gte=bbch_code)
    triggered = [b.level for b in bands if b.crosses(value)]
    return _highest_level(*triggered)


# ──────────────────────────────────────────────────────────────────────────────
# Órdenes de trabajo desde alertas
# ──────────────────────────────────────────────────────────────────────────────

def _confirm_forecast_work_orders(alert):
    """Mueve las OTs 'Contingente' de esta alerta a 'Pendiente' al confirmar el pronóstico."""
    from parameter.models.ot_state import OTState
    contingent = OTState.objects.filter(name="Contingente").first()
    pending    = OTState.objects.filter(name="Pendiente").first()
    if contingent and pending:
        alert.work_orders.filter(stateOT=contingent).update(stateOT=pending)


def _abort_forecast_alert(alert):
    """
    Marca la alerta como abortada y cancela sus OTs Contingentes.

    Casos:
      1. La fecha de la alerta llegó pero no se confirmó con datos reales.
      2. El pronóstico cambió y el evento ya no se predice para esa fecha.
    """
    from parameter.models.ot_state import OTState
    alert.is_aborted = True
    alert.save(update_fields=["is_aborted"])
    cancelada = OTState.objects.filter(name="Cancelada").first()
    if cancelada:
        updated = alert.work_orders.filter(stateOT__name="Contingente").update(stateOT=cancelada)
        if updated:
            logger.info("Cancelled %d WO(s) for aborted alert pk=%s", updated, alert.pk)
    logger.info("Alert pk=%s aborted (indicator=%s date=%s)", alert.pk, alert.indicator_id, alert.date)


def _abort_unconfirmed_for_date(lot, date):
    """
    Al final de la evaluación con datos reales para `date`, aborta cualquier alerta
    de pronóstico de ese lote/fecha que no fue confirmada (sigue con is_forecast=True).
    """
    from operation.models.crop import Crop
    crop_ids = list(Crop.objects.filter(lot=lot).values_list("id", flat=True))
    stale = Alert.objects.filter(
        crop_id__in=crop_ids,
        date=date,
        is_forecast=True,
        is_aborted=False,
    )
    for alert in stale:
        _abort_forecast_alert(alert)


def _abort_stale_forecast(lot, today, emitted_ids):
    """
    Al final de la evaluación de pronóstico, aborta las alertas forecast de la ventana
    que NO fueron regeneradas en este ciclo (el pronóstico cambió).

    `emitted_ids` es el conjunto de Alert.pk emitidos/tocados en este ciclo de pronóstico.
    """
    from operation.models.crop import Crop
    crop_ids = list(Crop.objects.filter(lot=lot).values_list("id", flat=True))
    stale = Alert.objects.filter(
        crop_id__in=crop_ids,
        date__gt=today,
        date__lte=today + timedelta(days=DEFAULT_FORECAST_DAYS),
        is_forecast=True,
        is_aborted=False,
    ).exclude(id__in=emitted_ids)
    for alert in stale:
        _abort_forecast_alert(alert)


def _maybe_create_work_order(alert, indicator, level, bbch_code, is_forecast):
    """
    Crea una WorkOrder por cada IndicatorAction que coincida con el nivel y BBCH actuales.

    Cuando hay múltiples actions que aplican (ej. dos tareas distintas para la misma alerta),
    se crea una OT por cada una. El código de la OT incluye el id del action para evitar
    duplicados en re-ejecuciones (get_or_create por code).

    Para alertas de pronóstico: solo crea la OT si la acción tiene create_on_forecast=True;
    la OT queda en estado 'Contingente'. Cuando el pronóstico se confirma,
    _confirm_forecast_work_orders la mueve a 'Pendiente'.
    """
    from operation.models.work_order import WorkOrder
    from operation.models.input_work_order import InputWorkOrder
    from parameter.models.ot_state import OTState

    matching_actions = [
        a for a in (
            indicator.actions
            .select_related("service", "stage")
            .prefetch_related("inputs__input")
            .order_by(
                models.Case(models.When(alert_level='', then=1), default=0, output_field=models.IntegerField()),
                models.Case(models.When(bbch_from=None, then=1), default=0, output_field=models.IntegerField()),
            )
        )
        if a.matches(level, bbch_code)
        and (not is_forecast or a.create_on_forecast)
    ]
    if not matching_actions:
        return

    # Resolver staff una sola vez para todas las acciones
    staff = None
    for user in indicator.report_user.all():
        try:
            s = user.staff_user
            if s.state == "active":
                staff = s
                break
        except Exception:
            pass
    staff = staff or alert.crop.responsible

    if not staff:
        logger.warning("No staff found for indicator '%s' — WorkOrders not created", indicator.name)
        return

    if is_forecast:
        state = OTState.objects.filter(name="Contingente").first()
    else:
        state = OTState.objects.filter(name="Pendiente").first()

    if not state:
        logger.warning("OTState not configured for WO creation (indicator '%s')", indicator.name)
        return

    crop  = alert.crop
    today = timezone.localdate()
    start = alert.date if is_forecast else today

    # Etapa actual del cultivo (fallback cuando la acción no la especifica)
    _current_crop_stage_cache = None

    def _current_crop_stage():
        nonlocal _current_crop_stage_cache
        if _current_crop_stage_cache is not None:
            return _current_crop_stage_cache
        from crop_monitoring.models.gdd_accumulator import GDDAccumulator
        from crop_monitoring.models.biofix import Biofix
        from crop_monitoring.models.phenological_state import PhenologicalState
        acc = (
            GDDAccumulator.objects
            .filter(biofix__crop=crop, biofix__counter=Biofix.COUNTER_VINE)
            .order_by("-calculation_date")
            .first()
        )
        if acc:
            ps = PhenologicalState.current_stage(acc.accumulated_gdd)
            _current_crop_stage_cache = ps.stage if (ps and ps.stage_id) else None
        return _current_crop_stage_cache

    for action in matching_actions:
        # Si la acción no especifica etapa, usar la etapa actual del cultivo
        wo_stage = action.stage if action.stage_id else _current_crop_stage()

        # Código único por alerta + acción — evita duplicar si se re-evalúa
        code = f"ALRT-{indicator.name[:6].upper()}-{today:%Y%m%d}-{alert.pk}-{action.pk}"
        wo, wo_created = WorkOrder.objects.get_or_create(
            code=code,
            defaults=dict(
                date_emission = today,
                date_init     = start,
                date_fin      = start + timedelta(days=action.days_to_complete),
                campaing      = crop.campaing,
                crop          = crop,
                area          = crop.area,
                stage         = wo_stage,
                service       = action.service,
                stateOT       = state,
                type          = "OW",
                staff         = staff,
                producer      = crop.producer,
                alert         = alert,
            ),
        )
        if wo_created:
            for ai in action.inputs.select_related("input").all():
                InputWorkOrder.objects.create(work_order=wo, input=ai.input, dose=ai.dose)
            logger.info(
                "WorkOrder %s created — alert=%s action=%s level=%s forecast=%s",
                wo.code, alert.pk, action.pk, level, is_forecast,
            )


# ──────────────────────────────────────────────────────────────────────────────
# Emisión de alerta y notificaciones
# ──────────────────────────────────────────────────────────────────────────────

def _build_alert_detail(level, bbch_label, is_forecast, rec_text="") -> str:
    """Arma el texto completo del campo detail de Alert y Notification."""
    header = f"Nivel: {level}"
    if bbch_label:
        header += f" | {bbch_label}"
    if is_forecast:
        header += "  [pronóstico]"
    return f"{header}\n\n{rec_text}" if rec_text else header


def _recommendation_detail(indicator, level, bbch_code) -> str:
    """Texto de acciones recomendadas para este nivel y BBCH. Vacío si no hay."""
    recs = [r.text for r in indicator.recommendations.all() if r.matches(level, bbch_code)]
    if not recs:
        return ""
    lines = ["Acciones recomendadas:"] + [f"• {r}" for r in recs]
    return "\n".join(lines)


def _emit_alert(crop, indicator, date, level, bbch_label, status, is_forecast=False, bbch_code=None):
    # is_aborted=False en el lookup: si la alerta anterior fue abortada, se crea una nueva
    alert, created = Alert.objects.get_or_create(
        crop=crop,
        indicator=indicator,
        date=date,
        is_aborted=False,
        defaults={
            "name":        f"Alerta {indicator.name} — {date} — {crop.name}",
            "detail":      _build_alert_detail(level, bbch_label, is_forecast,
                                               _recommendation_detail(indicator, level, bbch_code)),
            "bbch_stage":  bbch_label,
            "is_forecast": is_forecast,
            "level":       level or "",
        },
    )

    level_changed = False
    if not created:
        updates = {}
        # Pronóstico confirmado por dato real
        if alert.is_forecast and not is_forecast:
            updates["is_forecast"] = False
            _confirm_forecast_work_orders(alert)
        # Nivel escalado (warning → alert → critical)
        if level and alert.level != level:
            updates["level"] = level
            level_changed = True
        if updates:
            for k, v in updates.items():
                setattr(alert, k, v)
            alert.save(update_fields=list(updates.keys()))

    # Crear OT: en primera emisión o cuando el nivel escala
    if status != "vigilance" and (created or level_changed):
        _maybe_create_work_order(alert, indicator, level, bbch_code, is_forecast)

    # Si no hubo cambio relevante, no repetir notificación
    if not created and not level_changed:
        return alert

    logger.info(
        "Alert: %s [%s] forecast=%s status=%s created=%s level_changed=%s",
        indicator.name, level, is_forecast, status, created, level_changed,
    )

    if status == "vigilance":
        return alert  # solo registrar, no notificar

    escalated = level_changed and not created
    users = set()
    users.add(crop.producer)
    if crop.responsible and crop.responsible.user_id:
        users.add(crop.responsible.user)
    for user in indicator.report_user.all():
        users.add(user)

    prefix = "[ESCALADA] " if escalated else ""
    for user in users:
        Notification.objects.create(
            name   = f"{prefix}Notificación {indicator.name} — {date} — {crop.name}",
            detail = _build_alert_detail(level, bbch_label, is_forecast,
                                     _recommendation_detail(indicator, level, bbch_code)),
            date   = date,
            user   = user,
        )
    return alert


# ──────────────────────────────────────────────────────────────────────────────
# Evaluación por cultivo (datos observados)
# ──────────────────────────────────────────────────────────────────────────────

def _run_indicator(indicator, crop, daily_summary, bbch_code, date, status):
    """Evalúa un indicador y emite alerta si corresponde."""
    try:
        evaluator = indicator.get_evaluator()
        if evaluator and daily_summary is not None:
            level = evaluator.evaluate(indicator, daily_summary, bbch_code)
        elif evaluator:
            return  # custom evaluators requieren daily_summary
        else:
            level = _evaluate_generic(indicator, crop, daily_summary, bbch_code, date)
    except Exception:
        logger.exception("Error evaluando '%s' para cultivo '%s'", indicator, crop)
        return

    if level:
        bbch_label = _get_bbch_stage_label(crop)
        _emit_alert(crop, indicator, date, level, bbch_label, status, is_forecast=False, bbch_code=bbch_code)


def _evaluate_crop(crop, daily_summary, skip_indicator_ids=None, date=None):
    """
    Evalúa los indicadores propios del cultivo (Crop.indicators),
    excluyendo los ya cubiertos por la zona (skip_indicator_ids).
    """
    skip_ids = skip_indicator_ids or set()
    ref_date = date or (daily_summary.date if daily_summary else None)
    if ref_date is None:
        return

    bbch_code = _get_bbch_for_crop(crop)

    from alert.models.indicator import Indicator
    for indicator in (
        crop.indicators
        .exclude(id__in=skip_ids)
        .exclude(review_mode=Indicator.REVIEW_PER_READING)
        .prefetch_related("variables", "bands")
    ):
        _run_indicator(indicator, crop, daily_summary, bbch_code, ref_date, status="on")


# ──────────────────────────────────────────────────────────────────────────────
# Proyección GDD (efímera, no persiste)
# ──────────────────────────────────────────────────────────────────────────────

def _gdd_proyectado_por_dia(accumulator, forecast_summaries):
    """
    Parte del GDD real acumulado y proyecta día a día con los resúmenes de pronóstico.
    Devuelve {date: gdd_proyectado}. NO modifica el acumulador real.
    """
    base = float(accumulator.biofix.base_temp)
    lot = accumulator.biofix.crop.lot
    cutoff = float(lot.area.gdd_upper_cutoff) if (lot.area and lot.area.gdd_upper_cutoff) else None
    current = float(accumulator.accumulated_gdd)

    result = {}
    for summary in sorted(forecast_summaries, key=lambda s: s.date):
        tmin = float(summary.tmin)
        tmax = float(summary.tmax)
        if cutoff is not None:
            tmax = min(tmax, cutoff)
            tmin = min(tmin, cutoff)
        current += max(0.0, (tmax + tmin) / 2 - base)
        result[summary.date] = round(current, 1)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Evaluación por registro (sub-diaria)
# ──────────────────────────────────────────────────────────────────────────────

def _get_value_from_record(iv, record):
    """Lee el valor de una variable directamente desde el registro (OpenMeteoHourly o WeatherData)."""
    field_name = iv.variable.field_name or iv.variable.name
    val = getattr(record, field_name, None)
    return float(val) if val is not None else None


def _evaluate_generic_per_reading(indicator, crop, record, bbch_code):
    """
    AND logic sobre un único registro: todos los filtros deben cumplirse en el mismo objeto.
    Idéntico a _evaluate_generic pero lee del registro en lugar del DailySummary.
    """
    for iv in indicator.variables.filter(role=IndicatorVariable.ROLE_FILTER).select_related("variable"):
        value = _get_value_from_record(iv, record)
        if value is None:
            return None
        if iv.min_value is not None and value < iv.min_value:
            return None
        if iv.max_value is not None and value > iv.max_value:
            return None

    graduated = list(
        indicator.variables.filter(role=IndicatorVariable.ROLE_GRADUATED).select_related("variable")
    )
    if not graduated:
        return _level_from_bands(indicator, bbch_code, value=None)

    value = _get_value_from_record(graduated[0], record)
    if value is None:
        return None
    return _level_from_bands(indicator, bbch_code, value=value)


def _run_indicator_per_reading(indicator, crop, record, bbch_code, date, status):
    """Evalúa un indicador per_reading y emite alerta si corresponde."""
    try:
        level = _evaluate_generic_per_reading(indicator, crop, record, bbch_code)
    except Exception:
        logger.exception("Error evaluando per_reading '%s' cultivo '%s'", indicator, crop)
        return

    if level:
        bbch_label = _get_bbch_stage_label(crop)
        _emit_alert(crop, indicator, date, level, bbch_label, status, is_forecast=False, bbch_code=bbch_code)


def evaluate_indicators_per_reading(lot, record):
    """
    Disparado por OpenMeteoHourly.post_save o WeatherData.post_save.

    Evalúa solo indicadores con review_mode='per_reading' para todos los cultivos del lote.
    AND logic: todos los filtros del indicador deben pasar en el MISMO registro.
    No aplica a pronóstico (los datos horarios son siempre observados).

    Nombres de campo útiles por fuente:
      OpenMeteoHourly: temperature, humidity, wind_speed, wind_gusts, precipitation, cape, eto_mm, delta_t_1h
      WeatherData:     temp, humidity, wind_speed, wind_gust, rain_rate, rain_total, solar_radiation
    """
    from alert.models.alert_profile_indicator import AlertProfileIndicator
    from alert.models.indicator import Indicator
    from operation.models.crop import Crop

    # Fecha del registro
    record_dt = getattr(record, 'datetime', None) or getattr(record, 'timestamp', None)
    if record_dt is None:
        return
    record_date = record_dt.date() if hasattr(record_dt, 'date') else record_dt
    if record_date > timezone.localdate():
        return

    crops = Crop.objects.filter(lot=lot).select_related("area__alert_profile", "responsible")

    for crop in crops:
        zone_indicator_ids = set()
        bbch_code = _get_bbch_for_crop(crop)

        try:
            profile = crop.area.alert_profile
            profile_indicators = (
                AlertProfileIndicator.objects
                .filter(
                    profile=profile,
                    status__in=["on", "vigilance"],
                    indicator__review_mode=Indicator.REVIEW_PER_READING,
                )
                .select_related("indicator")
                .prefetch_related("indicator__variables", "indicator__bands")
            )
            for pi in profile_indicators:
                zone_indicator_ids.add(pi.indicator_id)
                _run_indicator_per_reading(pi.indicator, crop, record, bbch_code, record_date, pi.status)
        except Exception:
            pass

        for indicator in (
            crop.indicators
            .filter(review_mode=Indicator.REVIEW_PER_READING)
            .exclude(id__in=zone_indicator_ids)
            .prefetch_related("variables", "bands")
        ):
            _run_indicator_per_reading(indicator, crop, record, bbch_code, record_date, status="on")


# ──────────────────────────────────────────────────────────────────────────────
# Evaluación por cultivo (pronóstico)
# ──────────────────────────────────────────────────────────────────────────────

def _run_indicator_forecast(indicator, crop, daily_summary, bbch_code, date, status, emitted_ids=None):
    """Igual que _run_indicator pero emite alertas con is_forecast=True.

    Si se pasa `emitted_ids`, agrega el pk de la alerta emitida al set
    para que evaluate_indicators_forecast pueda detectar pronósticos obsoletos.
    """
    try:
        evaluator = indicator.get_evaluator()
        if evaluator and daily_summary is not None:
            level = evaluator.evaluate(indicator, daily_summary, bbch_code)
        elif evaluator:
            return
        else:
            level = _evaluate_generic(indicator, crop, daily_summary, bbch_code, date)
    except Exception:
        logger.exception("Error evaluando forecast '%s' cultivo '%s' fecha %s", indicator, crop, date)
        return

    if level:
        bbch_label = _get_bbch_stage_label(crop)
        alert = _emit_alert(crop, indicator, date, level, bbch_label, status, is_forecast=True, bbch_code=bbch_code)
        if alert is not None and emitted_ids is not None:
            emitted_ids.add(alert.pk)


def _evaluate_crop_forecast(crop, summary_by_date, gdd_by_date, today, skip_indicator_ids=None, emitted_ids=None):
    from crop_monitoring.models.phenological_state import PhenologicalState

    skip_ids = skip_indicator_ids or set()

    from alert.models.indicator import Indicator as _Indicator
    for indicator in (
        crop.indicators
        .exclude(id__in=skip_ids)
        .exclude(review_mode=_Indicator.REVIEW_PER_READING)
        .prefetch_related("variables", "bands")
    ):
        horizon = indicator.max_forecast_days or DEFAULT_FORECAST_DAYS
        for i in range(1, horizon + 1):
            target_date = today + timedelta(days=i)
            daily_summary = summary_by_date.get(target_date)
            if daily_summary is None:
                break
            projected_gdd = gdd_by_date.get(target_date)
            bbch_code = _bbch_int(PhenologicalState.current_stage(projected_gdd)) if projected_gdd is not None else None
            _run_indicator_forecast(indicator, crop, daily_summary, bbch_code, target_date, status="on", emitted_ids=emitted_ids)


# ──────────────────────────────────────────────────────────────────────────────
# Puntos de entrada
# ──────────────────────────────────────────────────────────────────────────────

def evaluate_indicators_for_lot(lot, date):
    """
    Disparado por DailySummary post_save (solo fechas <= hoy).

    Para cada cultivo del lote:
      1. Evalúa indicadores de la zona (AlertProfile) → status on/vigilance
      2. Evalúa indicadores propios del cultivo no cubiertos por la zona → status on
    """
    from alert.models.alert_profile_indicator import AlertProfileIndicator
    from operation.models.crop import Crop

    try:
        daily_summary = DailySummary.objects.get(lot=lot, date=date)
    except DailySummary.DoesNotExist:
        return

    crops = Crop.objects.filter(lot=lot).select_related("area__alert_profile", "responsible")

    for crop in crops:
        zone_indicator_ids = set()

        # — Indicadores de la zona (solo revisión diaria) —
        try:
            from alert.models.indicator import Indicator as _Ind
            profile = crop.area.alert_profile
            profile_indicators = (
                AlertProfileIndicator.objects
                .filter(profile=profile, status__in=["on", "vigilance"])
                .exclude(indicator__review_mode=_Ind.REVIEW_PER_READING)
                .select_related("indicator")
                .prefetch_related("indicator__variables", "indicator__bands")
            )
            bbch_code = _get_bbch_for_crop(crop)

            for pi in profile_indicators:
                zone_indicator_ids.add(pi.indicator_id)
                _run_indicator(pi.indicator, crop, daily_summary, bbch_code, date, pi.status)

        except Exception:
            pass  # área sin perfil configurado

        # — Indicadores propios del cultivo no cubiertos por la zona —
        _evaluate_crop(crop, daily_summary, skip_indicator_ids=zone_indicator_ids, date=date)

    # Caso 1: pronósticos que no se confirmaron hoy → abortar
    _abort_unconfirmed_for_date(lot, date)


def evaluate_indicators_for_technical(crop, variable, date):
    """
    Disparado por TechnicalCropDetail post_save.

    Evalúa solo los indicadores de crop.indicators que usen esa variable.
    No evalúa indicadores de zona (esos se cubren vía DailySummary).
    """
    indicators = (
        crop.indicators
        .filter(variables__variable=variable)
        .distinct()
        .prefetch_related("variables", "bands")
    )
    if not indicators.exists():
        return

    try:
        daily_summary = DailySummary.objects.get(lot=crop.lot, date=date)
    except DailySummary.DoesNotExist:
        daily_summary = None

    bbch_code = _get_bbch_for_crop(crop)

    for indicator in indicators:
        _run_indicator(indicator, crop, daily_summary, bbch_code, date, status="on")


def evaluate_indicators_forecast(lot, today):
    """
    Llamado explícitamente desde run_daily_cycle después de consolidar el pronóstico.

    Para cada cultivo del lote:
      1. Proyecta el GDD día a día sobre el acumulado real de hoy.
      2. Deriva el BBCH proyectado para cada día futuro.
      3. Evalúa indicadores (zona + cultivo) con el DailySummary de pronóstico y el BBCH proyectado.
      4. Emite Alert con is_forecast=True; si el evento ya existía como forecast, no lo duplica.

    Solo usa DailySummary con fecha > today (pronósticos); los de hoy y anteriores
    son datos observados y se evalúan vía el signal normal.
    """
    from alert.models.alert_profile_indicator import AlertProfileIndicator
    from crop_monitoring.models.gdd_accumulator import GDDAccumulator
    from crop_monitoring.models.biofix import Biofix
    from crop_monitoring.models.phenological_state import PhenologicalState
    from operation.models.crop import Crop

    forecast_summaries = list(
        DailySummary.objects.filter(
            lot=lot,
            date__gt=today,
            date__lte=today + timedelta(days=DEFAULT_FORECAST_DAYS),
        ).order_by("date")
    )
    if not forecast_summaries:
        return

    summary_by_date = {s.date: s for s in forecast_summaries}

    crops = Crop.objects.filter(lot=lot).select_related("area__alert_profile", "responsible")

    # Acumula todos los pks de alertas emitidas en este ciclo (todos los cultivos del lote)
    emitted_ids: set[int] = set()

    for crop in crops:
        # GDD real del contador vid para este cultivo
        try:
            acc = GDDAccumulator.objects.get(biofix__crop=crop, biofix__counter=Biofix.COUNTER_VINE)
        except GDDAccumulator.DoesNotExist:
            continue

        gdd_by_date = _gdd_proyectado_por_dia(acc, forecast_summaries)

        zone_indicator_ids = set()

        # — Indicadores de la zona con su horizonte —
        try:
            profile = crop.area.alert_profile
            profile_indicators = (
                AlertProfileIndicator.objects
                .filter(profile=profile, status__in=["on", "vigilance"])
                .exclude(indicator__review_mode=Indicator.REVIEW_PER_READING)
                .select_related("indicator")
                .prefetch_related("indicator__variables", "indicator__bands")
            )
            for pi in profile_indicators:
                zone_indicator_ids.add(pi.indicator_id)
                indicator = pi.indicator
                horizon = indicator.max_forecast_days or DEFAULT_FORECAST_DAYS
                for i in range(1, horizon + 1):
                    target_date = today + timedelta(days=i)
                    daily_summary = summary_by_date.get(target_date)
                    if daily_summary is None:
                        break
                    projected_gdd = gdd_by_date.get(target_date)
                    bbch_code = _bbch_int(PhenologicalState.current_stage(projected_gdd)) if projected_gdd is not None else None
                    _run_indicator_forecast(indicator, crop, daily_summary, bbch_code, target_date, pi.status, emitted_ids=emitted_ids)
        except Exception:
            pass

        # — Indicadores propios del cultivo —
        _evaluate_crop_forecast(crop, summary_by_date, gdd_by_date, today, skip_indicator_ids=zone_indicator_ids, emitted_ids=emitted_ids)

    # Caso 2: pronósticos que ya no se generaron en este ciclo → abortar
    _abort_stale_forecast(lot, today, emitted_ids)


# ──────────────────────────────────────────────────────────────────────────────
# Señales
# ──────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=DailySummary)
def evaluate_from_daily_summary(sender, instance, **kwargs):
    # Las fechas futuras se evalúan explícitamente desde run_daily_cycle con BBCH proyectado
    if instance.date > timezone.localdate():
        return
    evaluate_indicators_for_lot(lot=instance.lot, date=instance.date)


@receiver(post_save, sender=TechnicalCropDetail)
def evaluate_from_technical(sender, instance, **kwargs):
    evaluate_indicators_for_technical(
        crop=instance.crop,
        variable=instance.varTechnique,
        date=instance.date,
    )


@receiver(post_save, sender=OpenMeteoHourly)
def evaluate_from_open_meteo_hourly(sender, instance, **kwargs):
    """Evalúa indicadores per_reading cuando llega una lectura horaria de Open-Meteo."""
    from producer.models.lot import Lot
    for lot in Lot.objects.filter(external_station=instance.station).select_related("external_station"):
        evaluate_indicators_per_reading(lot=lot, record=instance)


@receiver(post_save, sender=WeatherData)
def evaluate_from_weather_data(sender, instance, **kwargs):
    """Evalúa indicadores per_reading cuando llega una lectura de la estación propia."""
    from producer.models.lot import Lot
    if instance.station is None:
        return
    for lot in Lot.objects.filter(station=instance.station).select_related("station"):
        evaluate_indicators_per_reading(lot=lot, record=instance)
