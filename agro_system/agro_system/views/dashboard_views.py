import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

logger = logging.getLogger(__name__)

from producer.models.lot import Lot
from producer.models.country_side import Countryside
from producer.models.staff import Staff

from parameter.models.campaign import Campaing

from operation.models.technical_plan import TechnicalPlan
from operation.models.work_order import WorkOrder
from operation.models.crop import Crop

from weather.models.weather_data import WeatherData
from weather.models.station_weather import WeatherStation

from alert.models.alert import Alert
from alert.models.alert_profile_indicator import AlertProfileIndicator
from user.admin.producer_scope import accessible_crops
from alert.models.indicator import Indicator
from operation.models.input_work_order import InputWorkOrder

from crop_monitoring.models.phenological_state import PhenologicalState
from crop_monitoring.models.biofix import Biofix

# Alertas relevantes por etapa BBCH — informa el panel del dashboard
_ALERTS_BY_BBCH = {
    "07-09": ["helada", "zonda", "ventana_aplicacion"],
    "11-15": ["helada", "zonda", "ventana_aplicacion"],
    "53-55": ["helada", "mildiu_primario", "lobesia", "ventana_aplicacion"],
    "57":    ["helada", "mildiu_primario", "lobesia", "ventana_aplicacion"],
    "60":    ["helada", "golpe_calor", "lobesia", "mildiu_primario", "ventana_aplicacion"],
    "65":    ["helada", "golpe_calor", "lobesia", "botrytis", "mildiu_primario", "ventana_aplicacion"],
    "69":    ["golpe_calor", "lobesia", "botrytis", "ventana_aplicacion"],
    "71-73": ["estres_hidrico", "lobesia", "botrytis", "ventana_aplicacion"],
    "75":    ["estres_hidrico", "lobesia", "botrytis", "ventana_aplicacion"],
    "77-79": ["estres_hidrico", "lobesia", "botrytis", "ventana_aplicacion"],
    "81":    ["estres_hidrico", "golpe_calor", "lobesia", "gdd_cosecha", "ventana_aplicacion"],
    "83":    ["estres_hidrico", "golpe_calor", "lobesia", "gdd_cosecha", "ventana_aplicacion"],
    "85":    ["estres_hidrico", "gdd_cosecha", "botrytis"],
    "89":    ["estres_hidrico", "gdd_cosecha", "botrytis"],
}

_ALERT_LABELS = {
    "helada":             "Helada",
    "zonda":              "Zonda",
    "ventana_aplicacion": "Ventana de aplicación",
    "mildiu_primario":    "Mildiu primario",
    "mildiu_secundario":  "Mildiu secundario",
    "lobesia":            "Lobesia botrana",
    "golpe_calor":        "Golpe de calor",
    "botrytis":           "Botrytis",
    "estres_hidrico":     "Estrés hídrico",
    "granizo":            "Granizo",
    "oidio":              "Oídio",
    "gdd_cosecha":        "Ventana de cosecha",
}

# Panel principal
@login_required
def DashboardView(request):

    countryside_id = request.GET.get('countryside')
    lot_id = request.GET.get('lot')
    campaing_id = request.GET.get('campaing')
    crop_id = request.GET.get('crop')

    user = request.user
    staff = None

    if user.type == 'Staff':
        staff = Staff.objects.filter(user=user).first()
        country_sides = Countryside.objects.filter(producer=staff.producer)
        crops = Crop.objects.filter(responsible=staff)

    elif user.type == 'Producer':
        country_sides = Countryside.objects.filter(producer=user)
        crops = Crop.objects.filter(producer=user)

    elif user.type == 'Administration' or user.is_superuser:
        country_sides = Countryside.objects.all()
        crops = Crop.objects.all()

    else:
        country_sides = Countryside.objects.none()
        crops = Crop.objects.none()

    lots = Lot.objects.filter(countryside__in=country_sides)

    campaings = Campaing.objects.all().order_by('-date_init')
    campaign_active = campaings.filter(active=True).first() or campaings.first()

    if campaing_id:
        selected_campaing = campaings.filter(id=campaing_id).first()
    else:
        selected_campaing = campaign_active


    if selected_campaing:
        crops = crops.filter(campaing=selected_campaing)

    if countryside_id:
        country_side_selected = country_sides.filter(id=countryside_id).first()
        crops = crops.filter(countryside_id=countryside_id)
        lots = lots.filter(countryside_id=countryside_id)
    else:
        country_side_selected = None

    if lot_id:
        selected_lot = lots.filter(id=lot_id).first()
        crops = crops.filter(lot_id=lot_id)
        lots = lots.filter(id=lot_id)
    else:
        selected_lot = None


    if crop_id:
        selected_crop = crops.filter(id=crop_id).first()
    else:
        selected_crop = crops.filter(is_main=True).first() or crops.order_by('-id').first()

    if not selected_lot and selected_crop and selected_crop.lot:
        selected_lot = selected_crop.lot

    if not selected_crop and selected_lot:
        selected_crop = crops.filter(lot=selected_lot).order_by('-id').first()

    if selected_lot:
        lot_main = selected_lot
    elif selected_crop and selected_crop.lot:
        lot_main = selected_crop.lot
    else:
        lot_main = lots.order_by('-id').first()


    today = timezone.now().date()

    work_orders = WorkOrder.objects.none()
    next_work_order = None
    base_qs = WorkOrder.objects.none()

    if selected_crop:
        base_qs = WorkOrder.active.filter(crop=selected_crop)

        if selected_campaing:
            base_qs = base_qs.filter(campaing=selected_campaing)

    elif selected_campaing:
        # Siempre acotado a los cultivos visibles para el usuario (antes, sin lotes, traía las de todos)
        base_qs = WorkOrder.active.filter(campaing=selected_campaing, crop__in=accessible_crops(user))

        if lots.exists():
            base_qs = base_qs.filter(crop__lot__in=lots)

    # =========================
    # Próximas actividades — pendientes (incluyendo vencidas no finalizadas)
    # =========================
    work_orders = base_qs.exclude(stateOT__name__iexact="Finalizada").order_by('date_init')[:3]


    # =========================
    #  Métricas reales de ejecución
    # Se calculan sobre TODAS las órdenes del cultivo/campaña,
    # no solo sobre las 3 que se muestran en la timeline.
    # =========================
    work_orders_total = base_qs.count()

    work_orders_completed = base_qs.filter(
        stateOT__name__iexact="Finalizada"
    ).count()

    work_orders_pending = base_qs.exclude(
        stateOT__name__iexact="Finalizada"
    ).count()

    work_orders_completed_percent = 0

    if work_orders_total > 0:
        work_orders_completed_percent = int(
            (work_orders_completed / work_orders_total) * 100
        )


    # =========================
    #  Días restantes de campaña
    # =========================
    campaign_days_remaining = 0
    campaign_reference = selected_campaing or campaign_active

    if campaign_reference and campaign_reference.date_final:
        campaign_days_remaining = (campaign_reference.date_final - today).days

        if campaign_days_remaining < 0:
            campaign_days_remaining = 0

    # Próxima acción: solo desde hoy en adelante, sin fallback al pasado
    next_work_order = base_qs.filter(
        date_init__gte=today
    ).exclude(
        stateOT__name__iexact="Finalizada"
    ).order_by('date_init').first()


    insumos_faltantes = []
    total_cost = 0

    if work_orders:
        next_orders = work_orders[:3]

        for order in next_orders:
            insumos_ot = InputWorkOrder.objects.filter(work_order=order)

            for io in insumos_ot:
                input_obj = io.input
                requerido = io.dose or 0
                stock = input_obj.stock or 0

                if stock < requerido:
                    faltante = requerido - stock
                    costo = (input_obj.cost or 0) * faltante

                    insumos_faltantes.append({
                        'name': input_obj.name,
                        'faltante': faltante,
                        'costo': costo,
                        'currency': input_obj.currency,
                    })

                    total_cost += costo


    # =========================
    # Si hay órdenes, usar el cultivo real de la primera orden
    # Esto corrige cuando selected_crop queda vacío pero work_orders sí trae datos.
    # =========================
    if not selected_crop and work_orders:
        first_work_order = work_orders.first()

        if first_work_order and first_work_order.crop:
            selected_crop = first_work_order.crop

            if selected_crop.lot:
                selected_lot = selected_crop.lot
                lot_main = selected_crop.lot

            if selected_crop.countryside:
                country_side_selected = selected_crop.countryside

            # Asegurar que el listado de cultivos no quede vacío (solo cultivos visibles para el usuario)
            crops = accessible_crops(user).filter(campaing=selected_campaing)

    alerts = Alert.active.none()

    if selected_crop:
        alerts = Alert.active.filter(crop=selected_crop).order_by('-date')
    elif selected_campaing:
        alerts = Alert.active.filter(crop__in=crops, crop__campaing=selected_campaing).order_by('-date')
    alerts_today    = alerts.filter(date=today, is_forecast=False)
    alerts_forecast = alerts.filter(date__gt=today, is_forecast=True).order_by('date')
    alerts_count    = alerts_today.count()

    # Ventana de aplicación: verde si no hay alerta confirmada HOY del indicador
    ventana_nivel = None
    if selected_crop:
        _ventana_ind = Indicator.objects.filter(name="ventana_aplicacion").first()
        if _ventana_ind:
            _ventana_alert = Alert.active.filter(
                crop=selected_crop,
                indicator=_ventana_ind,
                date=today,
                is_forecast=False,
            ).first()
            ventana_nivel = _ventana_alert.level if _ventana_alert else "verde"

    # ── Fenología ────────────────────────────────────────────────
    vine_gdd               = None
    current_stage          = None
    next_stage             = None
    phenological_timeline  = []
    gdd_stage_percent      = 0
    current_stage_alerts   = []
    next_stage_alerts      = []

    if selected_crop:
        biofix_vine = Biofix.objects.filter(crop=selected_crop, counter=Biofix.COUNTER_VINE).first()
        if biofix_vine is None:
            logger.warning("Dashboard: sin biofix vine para crop %s", selected_crop.pk)
        else:
            try:
                vine_gdd = float(biofix_vine.accumulator.accumulated_gdd)
            except Exception as e:
                logger.warning("Dashboard: sin acumulador para biofix %s → %s", biofix_vine.pk, e)

        if vine_gdd is not None:
            try:
                current_stage = biofix_vine.accumulator.effective_state
                next_stage = (
                    PhenologicalState.objects
                    .filter(order__gt=current_stage.order)
                    .order_by('order')
                    .first()
                ) if current_stage else None

                current_order = current_stage.order if current_stage else 0
                for stage in PhenologicalState.objects.all():
                    if stage.order < current_order:
                        status = "past"
                    elif stage.order == current_order:
                        status = "current"
                    else:
                        status = "future"
                    phenological_timeline.append({"stage": stage, "status": status})

                if current_stage:
                    stage_range = current_stage.gdd_to - current_stage.gdd_from
                    if stage_range > 0:
                        gdd_stage_percent = min(100, int(
                            (vine_gdd - current_stage.gdd_from) / stage_range * 100
                        ))

                # Alertas del área (via AlertProfileIndicator) + indicadores propios del cultivo
                area_alerts = {}
                lot = selected_crop.lot
                if lot and lot.area:
                    try:
                        profile = lot.area.alert_profile
                        area_alerts = {
                            pi.indicator.name: pi.status
                            for pi in AlertProfileIndicator.objects.filter(
                                profile=profile, status__in=("on", "vigilance")
                            ).select_related("indicator")
                        }
                    except Exception:
                        pass
                # Crop-level indicators override/add with status "on"
                for ind in selected_crop.indicators.all():
                    area_alerts[ind.name] = "on"

                def _alerts_for_bbch(bbch):
                    return [
                        {"key": k, "label": _ALERT_LABELS.get(k, k), "level": area_alerts.get(k)}
                        for k in _ALERTS_BY_BBCH.get(bbch, [])
                        if area_alerts.get(k) in ("on", "vigilance")
                    ]

                if current_stage:
                    current_stage_alerts = _alerts_for_bbch(current_stage.bbch)

                if next_stage:
                    current_keys = {a["key"] for a in current_stage_alerts}
                    next_stage_alerts = [
                        a for a in _alerts_for_bbch(next_stage.bbch)
                        if a["key"] not in current_keys
                    ]

            except Exception as e:
                logger.exception("Dashboard: error en fenología para crop %s", selected_crop.pk)

    # BBCH numérico para filtrar recomendaciones
    bbch_code = None
    if current_stage and current_stage.bbch:
        try:
            bbch_code = int(current_stage.bbch.split("-")[0])
        except (ValueError, AttributeError):
            pass

    # Alertas de hoy + sus recomendaciones que aplican al nivel y BBCH actual
    alerts_with_recs = []
    for alert in alerts_today.select_related("indicator").prefetch_related("indicator__recommendations"):
        recs = [r for r in alert.indicator.recommendations.all() if r.matches(alert.level, bbch_code)]
        alerts_with_recs.append({"alert": alert, "recommendations": recs})

    lot_hectares_total = 0
    crop_hectares_planted = 0
    crop_hectares_without_plant = 0
    crop_hectares_harvested = 0
    crop_hectares_without_harvest = 0

    planted_percent = 0
    harvested_percent = 0

    if selected_crop:
        # Superficie total del lote
        if selected_crop.lot:
            lot_hectares_total = selected_crop.lot.hectares or 0

        # Datos propios del cultivo / campaña
        crop_hectares_planted = selected_crop.hectares_planted or 0
        crop_hectares_without_plant = selected_crop.hectares_unplanted or 0
        crop_hectares_harvested = selected_crop.hectares_harvested or 0
        crop_hectares_without_harvest = selected_crop.hectares_not_harvested or 0

        # % plantado sobre total del lote
        if lot_hectares_total:
            planted_percent = round((crop_hectares_planted / lot_hectares_total) * 100)

        # % cosechado sobre lo plantado
        if crop_hectares_planted:
            harvested_percent = round((crop_hectares_harvested / crop_hectares_planted) * 100)


    weather_data = None
    station = None

    if selected_crop and selected_crop.lot and selected_crop.lot.station:
        station = selected_crop.lot.station
        weather_data = WeatherData.objects.filter(station=station).last()

    data = {
        'country_sides': country_sides,
        'lots': lots,
        'lot_main': lot_main,

        'crops': crops,
        'crop_main': selected_crop,
        'selected_crop': selected_crop,

        'campaings': campaings,
        'campaign_active': campaign_active,
        'campaing_active': campaign_active,
        'selected_campaing': selected_campaing,

        'work_orders': work_orders,

        'alerts': alerts,
        'alerts_today': alerts_today,
        'alerts_forecast': alerts_forecast,
        'alerts_count': alerts_count,
        'alerts_with_recs': alerts_with_recs,

        'selected_countryside': country_side_selected,
        'selected_lot': selected_lot,

        'weather_data': weather_data,
        'station': station,

        'lot_hectares_total': lot_hectares_total,
        'crop_hectares_planted': crop_hectares_planted,
        'crop_hectares_without_plant': crop_hectares_without_plant,
        'crop_hectares_harvested': crop_hectares_harvested,
        'crop_hectares_without_harvest': crop_hectares_without_harvest,
        'planted_percent': planted_percent,
        'harvested_percent': harvested_percent,

        'next_work_order': next_work_order,

        'insumos_faltantes': insumos_faltantes,
        'insumos_count': len(insumos_faltantes),
        'insumos_total_cost': total_cost,

        'today': today,

        'work_orders_total': work_orders_total,
        'work_orders_completed': work_orders_completed,
        'work_orders_pending': work_orders_pending,
        'work_orders_completed_percent': work_orders_completed_percent,
        'campaign_days_remaining': campaign_days_remaining,

        # Fenología
        'vine_gdd':              vine_gdd,
        'current_stage':         current_stage,
        'next_stage':            next_stage,
        'phenological_timeline': phenological_timeline,
        'gdd_stage_percent':     gdd_stage_percent,
        'current_stage_alerts':  current_stage_alerts,
        'next_stage_alerts':     next_stage_alerts,

        'ventana_nivel': ventana_nivel,
    }

    return render(request, 'pages/dashboard.html', data)