import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Avg

from producer.models.lot import Lot
from producer.models.country_side import Countryside
from producer.models.staff import Staff

from parameter.models.campaign import Campaing

from operation.models.technical_plan import TechnicalPlan
from operation.models.work_order import WorkOrder
from operation.models.crop import Crop
from operation.models.crop_yields import CropYields

from weather.models.weather_data import WeatherData
from weather.models.station_weather import WeatherStation

from alert.models.alert import Alert
from operation.models.input_work_order import InputWorkOrder

from storage.models.silo_movement import SiloMovement
from storage.models.silo_stock import SiloStock
from storage.models.storage_certificate import StorageCertificate
from storage.models.storage_movement import StorageMovement

from agro_system.views.filter_helpers import get_producer_ref

# Panel principal
@login_required
def DashboardView(request):

    countryside_id = request.GET.get('countryside')
    lot_id = request.GET.get('lot')

    # Persistir selección en sesión
    if 'campaing' in request.GET:
        request.session['filter_campaing_id'] = request.GET.get('campaing') or None
    if 'crop' in request.GET:
        request.session['filter_crop_id'] = request.GET.get('crop') or None

    campaing_id = request.GET.get('campaing') or request.session.get('filter_campaing_id')
    crop_id = request.GET.get('crop') or request.session.get('filter_crop_id')

    user = request.user
    staff = None

    if user.type == 'Staff':
        staff = Staff.objects.filter(user=user).first()
        country_sides = Countryside.objects.filter(producer=staff.producer)
        crops = Crop.objects.filter(responsible=staff)

    elif user.type == 'Producer':
        _p = get_producer_ref(user)
        country_sides = Countryside.objects.filter(producer=_p)
        crops = Crop.objects.filter(producer=_p)

    elif user.type == 'Administration':
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
        base_qs = WorkOrder.objects.filter(crop=selected_crop)

        if selected_campaing:
            base_qs = base_qs.filter(campaing=selected_campaing)

    elif selected_campaing:
        base_qs = WorkOrder.objects.filter(campaing=selected_campaing)

        if lots.exists():
            base_qs = base_qs.filter(crop__lot__in=lots)

    # =========================
    # ine próximas actividades
    # Solo muestra 3 órdenes en la card central
    # =========================
    work_orders = base_qs.order_by('date_init')[:3]


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

    # Próxima acción:
    # 1. Pendiente desde hoy en adelante
    next_work_order = base_qs.filter(
        date_init__gte=today
    ).exclude(
        stateOT__name__iexact="Finalizada"
    ).order_by('date_init').first()

    # 2. Si no hay, cualquier pendiente
    if not next_work_order:
        next_work_order = base_qs.exclude(
            stateOT__name__iexact="Finalizada"
        ).order_by('date_init').first()

    # 3. Si no hay, última finalizada
    if not next_work_order:
        next_work_order = base_qs.order_by('-date_init').first()


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

            # Asegurar que el listado de cultivos no quede vacío
            crops = Crop.objects.filter(campaing=selected_campaing)

    alerts = Alert.objects.none()

    if selected_crop:
        alerts = Alert.objects.filter(crop=selected_crop).order_by('-date')

    elif selected_campaing:
        alerts = Alert.objects.filter(crop__campaing=selected_campaing).order_by('-date')

    alerts_count = alerts.count()

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

    # =========================================================
    # ACOPIO
    # =========================================================
    producer_ref = get_producer_ref(user)

    sf = {'producer': producer_ref} if producer_ref else {}

    # SiloStock ya tiene quantity_tons calculado y actualizado automáticamente
    sf_stock = {'silo__producer': producer_ref} if producer_ref else {}
    acopio_silo_stock = round(
        SiloStock.objects.filter(**sf_stock).aggregate(t=Sum('quantity_tons'))['t'] or 0, 2
    )

    # Chart: stock por silo y especie (horizontal bar apilado)
    stock_items = (
        SiloStock.objects.filter(quantity_tons__gt=0, **sf_stock)
        .select_related('silo', 'specie')
        .order_by('silo__name', 'specie__name')
    )

    _silo_names, _species_set, _silo_sp_map = [], [], {}
    for item in stock_items:
        sn, sp = item.silo.name, item.specie.name
        if sn not in _silo_names:
            _silo_names.append(sn)
        if sp not in _species_set:
            _species_set.append(sp)
        # Acumular: puede haber varios SiloStock por silo+especie (distintas campañas)
        _silo_sp_map[(sn, sp)] = round(_silo_sp_map.get((sn, sp), 0) + item.quantity_tons, 2)

    _COLORS = [
        'rgba(52,120,246,0.8)', 'rgba(52,195,143,0.8)',
        'rgba(241,180,76,0.8)', 'rgba(244,106,106,0.8)',
        'rgba(85,110,230,0.8)',
    ]
    chart_silo_datasets = [
        {
            'label': sp,
            'data': [_silo_sp_map.get((sn, sp), 0) for sn in _silo_names],
            'backgroundColor': _COLORS[i % len(_COLORS)],
        }
        for i, sp in enumerate(_species_set)
    ]

    sf_cert = {'certificate__producer': producer_ref} if producer_ref else {}
    cert_entries = StorageMovement.objects.filter(type='entry', **sf_cert).aggregate(t=Sum('quantity_tons'))['t'] or 0
    cert_exits   = StorageMovement.objects.filter(
        type__in=['sale_exit', 'withdrawal', 'transfer'], **sf_cert
    ).aggregate(t=Sum('quantity_tons'))['t'] or 0
    acopio_externo_stock = round(max(0, cert_entries - cert_exits), 2)

    # =========================================================
    # CHART: Acopiado vs Vendido por campaña (últimas 5)
    # =========================================================
    recent_campaigns = Campaing.objects.order_by('-date_init')[:5]
    recent_campaigns = list(reversed(list(recent_campaigns)))

    chart_labels   = []
    chart_acopiado = []
    chart_vendido  = []

    for camp in recent_campaigns:
        chart_labels.append(camp.name)

        date_fin = camp.date_final

        silo_in_c = SiloMovement.objects.filter(type='entry', date__gte=camp.date_init, **sf)
        if date_fin:
            silo_in_c = silo_in_c.filter(date__lte=date_fin)
        silo_in_c = silo_in_c.aggregate(t=Sum('quantity_tons'))['t'] or 0

        cert_in_c = StorageCertificate.objects.filter(campaing=camp, **sf).aggregate(t=Sum('quantity_entry'))['t'] or 0

        silo_out_c = SiloMovement.objects.filter(type='exit', date__gte=camp.date_init, **sf)
        if date_fin:
            silo_out_c = silo_out_c.filter(date__lte=date_fin)
        silo_out_c = silo_out_c.aggregate(t=Sum('quantity_tons'))['t'] or 0

        cert_out_c = StorageMovement.objects.filter(
            type='sale_exit',
            **({'certificate__campaing': camp, 'certificate__producer': producer_ref} if producer_ref else {'certificate__campaing': camp})
        ).aggregate(t=Sum('quantity_tons'))['t'] or 0

        chart_acopiado.append(round(silo_in_c + cert_in_c, 2))
        chart_vendido.append(round(silo_out_c + cert_out_c, 2))

    # =========================================================
    # RENDIMIENTO: estimado vs real del cultivo seleccionado (card)
    # =========================================================
    yield_estimate = None
    yield_real = None
    if selected_crop:
        cy = CropYields.objects.filter(crop=selected_crop).first()
        if cy:
            yield_estimate = cy.yields_estimate
            yield_real = cy.yields_real

    # =========================================================
    # CHART RENDIMIENTO: por especie a través de campañas (Opción A)
    # Promedio tn/ha de cada especie en cada una de las últimas 5 campañas
    # =========================================================
    from parameter.models.specie import Specie

    species_filter = {'crop__cropYields__isnull': False}
    if producer_ref:
        species_filter['crop__producer'] = producer_ref

    active_species = Specie.objects.filter(
        activity__crop__campaing__in=recent_campaigns,
        **({'activity__crop__producer': producer_ref} if producer_ref else {})
    ).distinct()

    chart_species = []
    SPECIES_COLORS = [
        ('rgba(52,195,143,0.8)',  'rgba(52,195,143,1)'),   # verde — soja
        ('rgba(241,180,76,0.8)', 'rgba(241,180,76,1)'),    # amarillo — trigo
        ('rgba(244,106,106,0.8)','rgba(244,106,106,1)'),   # rojo — maíz
        ('rgba(85,110,230,0.8)', 'rgba(85,110,230,1)'),    # azul — girasol
        ('rgba(52,195,195,0.8)', 'rgba(52,195,195,1)'),    # turquesa
    ]

    for idx, specie in enumerate(active_species[:5]):
        color_fill, color_border = SPECIES_COLORS[idx % len(SPECIES_COLORS)]
        est_per_camp  = []
        real_per_camp = []

        for camp in recent_campaigns:
            f = {'crop__campaing': camp, 'crop__activity__specie': specie}
            if producer_ref:
                f['crop__producer'] = producer_ref

            est  = CropYields.objects.filter(**f).aggregate(v=Avg('yields_estimate'))['v']
            real = CropYields.objects.filter(**f).aggregate(v=Avg('yields_real'))['v']

            est_per_camp.append(round(est, 2) if est is not None else None)
            real_per_camp.append(round(real, 2) if real is not None else None)

        chart_species.append({
            'name':      specie.name,
            'estimado':  est_per_camp,
            'real':      real_per_camp,
            'color':     color_fill,
            'border':    color_border,
        })

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
        'alerts_count': alerts_count,

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

        # Acopio
        'acopio_silo_stock': acopio_silo_stock,
        'acopio_externo_stock': acopio_externo_stock,
        'acopio_total': round(acopio_silo_stock + acopio_externo_stock, 2),

        # Chart acopiado vs vendido
        'chart_labels_json': json.dumps(chart_labels),
        'chart_acopiado_json': json.dumps(chart_acopiado),
        'chart_vendido_json': json.dumps(chart_vendido),

        # Chart stock silo por especie
        'chart_silo_labels_json': json.dumps(_silo_names),
        'chart_silo_datasets_json': json.dumps(chart_silo_datasets),

        # Chart rendimiento por especie y campaña
        'chart_species_json': json.dumps(chart_species),

        # Rendimiento del cultivo seleccionado (para la card)
        'yield_estimate': yield_estimate,
        'yield_real': yield_real,
    }

    return render(request, 'pages/dashboard.html', data)