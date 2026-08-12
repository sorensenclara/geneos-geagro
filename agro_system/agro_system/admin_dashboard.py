from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone

from user.admin.adminSite import adminSite
from agro_system.utils.bcr import get_quotes_bcr

from producer.models.lot import Lot
from producer.models.country_side import Countryside
from producer.models.staff import Staff

from parameter.models.campaign import Campaing

from operation.models.work_order import WorkOrder
from operation.models.input_work_order import InputWorkOrder
from operation.models.crop import Crop

from weather.models.weather_data import WeatherData
from alert.models.alert import Alert


@staff_member_required
def custom_admin_dashboard(request):

    campaing_id = request.GET.get('campaing')
    crop_id = request.GET.get('crop')

    user = request.user
    today = timezone.now().date()

    context = adminSite.each_context(request)

    if user.is_superuser or getattr(user, 'type', None) == 'Administration':
        crops_base = Crop.objects.all()
        country_sides = Countryside.objects.all()

    elif getattr(user, 'type', None) == 'Staff':
        staff = Staff.objects.filter(user=user).first()

        if staff and staff.producer:
            crops_base = Crop.objects.filter(producer=staff.producer)
            country_sides = Countryside.objects.filter(producer=staff.producer)
        else:
            crops_base = Crop.objects.none()
            country_sides = Countryside.objects.none()

    elif getattr(user, 'type', None) == 'Producer':
        crops_base = Crop.objects.filter(producer=user)
        country_sides = Countryside.objects.filter(producer=user)

    else:
        crops_base = Crop.objects.none()
        country_sides = Countryside.objects.none()


    campaings = Campaing.objects.all().order_by('-date_init')
    campaign_active = campaings.filter(active=True).first() or campaings.first()

    if campaing_id:
        selected_campaing = campaings.filter(id=campaing_id).first()
    else:
        selected_campaing = campaign_active

    crops = crops_base

    if selected_campaing:
        crops = crops.filter(campaing=selected_campaing)

    selected_crop = None

    if crop_id:
        selected_crop = crops.filter(id=crop_id).first()
    else:
        selected_crop = crops.filter(is_main=True).first() or crops.order_by('-id').first()

    lots = Lot.objects.filter(countryside__in=country_sides)


    base_qs = WorkOrder.objects.none()

    if selected_crop:
        base_qs = WorkOrder.objects.filter(crop=selected_crop)

        if selected_campaing:
            base_qs = base_qs.filter(campaing=selected_campaing)

    elif selected_campaing and crops.exists():
        base_qs = WorkOrder.objects.filter(campaing=selected_campaing, crop__in=crops)

    finished_filter = (
        Q(stateOT__name__icontains='COMPLET') |
        Q(stateOT__name__icontains='FINALIZ') |
        Q(stateOT__name__icontains='REALIZ')
    )

    in_progress_filter = Q(stateOT__name__icontains='CURSO')
    pending_filter = Q(stateOT__name__icontains='PEND')


    current_or_next_order = base_qs.filter(
        in_progress_filter
    ).order_by('date_init').first()

    if not current_or_next_order:
        current_or_next_order = base_qs.filter(
            date_init__gte=today
        ).exclude(
            finished_filter
        ).order_by('date_init').first()

    if not current_or_next_order:
        current_or_next_order = base_qs.exclude(
            finished_filter
        ).order_by('date_init').first()

    orders_not_started_count = base_qs.filter(
        pending_filter
    ).count()

    orders_today_count = base_qs.filter(
        date_init=today
    ).exclude(
        finished_filter
    ).count()

    orders_overdue_count = base_qs.filter(
        date_init__lt=today
    ).exclude(
        finished_filter
    ).count()

    orders_next_count = base_qs.filter(
        date_init__gt=today
    ).exclude(
        finished_filter
    ).count()


    work_orders_total = base_qs.count()

    work_orders_completed = base_qs.filter(
        finished_filter
    ).count()

    work_orders_pending = work_orders_total - work_orders_completed

    campaign_execution_percent = 0

    if work_orders_total > 0:
        campaign_execution_percent = int(
            (work_orders_completed / work_orders_total) * 100
        )


    next_work_orders = base_qs.exclude(
        finished_filter
    ).order_by('date_init')[:6]

    alerts = Alert.objects.none()

    if selected_crop:
        alerts = Alert.objects.filter(
            crop=selected_crop
        ).order_by('-date')

    elif selected_campaing:
        alerts = Alert.objects.filter(
            crop__campaing=selected_campaing
        ).order_by('-date')

    alerts_count = alerts.count()
    recent_alerts = alerts[:5]


    weather_data = None
    station = None

    if selected_crop and selected_crop.lot and selected_crop.lot.station:
        station = selected_crop.lot.station
        weather_data = WeatherData.objects.filter(
            station=station
        ).order_by('-timestamp').first()

    weather_operational_status = "Sin datos"
    weather_operational_detail = "No hay datos meteorológicos disponibles para este cultivo."
    weather_operational_badge = "geagro-badge-primary"

    if weather_data:
        wind = weather_data.wind_speed or 0
        rain = weather_data.rain_total or 0
        humidity = weather_data.humidity or 0

        if wind >= 25:
            weather_operational_status = "No recomendable pulverizar"
            weather_operational_detail = f"Viento elevado ({wind} km/h)."
            weather_operational_badge = "geagro-badge-danger"

        elif rain > 0:
            weather_operational_status = "Precipitaciones registradas"
            weather_operational_detail = f"Lluvia acumulada: {rain} mm."
            weather_operational_badge = "geagro-badge-warning"

        elif humidity >= 90:
            weather_operational_status = "Humedad elevada"
            weather_operational_detail = "Posible riesgo sanitario."
            weather_operational_badge = "geagro-badge-warning"

        else:
            weather_operational_status = "Condiciones óptimas"
            weather_operational_detail = "Ventana favorable para labores."
            weather_operational_badge = "geagro-badge-success"


    required_inputs = InputWorkOrder.objects.filter(
        work_order__in=next_work_orders
    ).select_related(
        'input',
        'work_order',
        'work_order__service'
    )

    missing_inputs = []

    for item in required_inputs:
        stock = item.input.stock or 0
        dose = item.dose or 0

        if stock < dose:
            missing_inputs.append(item)

    missing_inputs_count = len(missing_inputs)


    try:
        precios = get_quotes_bcr()
    except Exception:
        precios = []

    context.update({
        'precios': precios,

        'campaings': campaings,
        'campaign_active': campaign_active,
        'selected_campaing': selected_campaing,

        'crops': crops,
        'selected_crop': selected_crop,

        'current_or_next_order': current_or_next_order,

        'orders_not_started_count': orders_not_started_count,
        'orders_today_count': orders_today_count,
        'orders_overdue_count': orders_overdue_count,
        'orders_next_count': orders_next_count,

        'work_orders_total': work_orders_total,
        'work_orders_completed': work_orders_completed,
        'work_orders_pending': work_orders_pending,
        'campaign_execution_percent': campaign_execution_percent,

        'next_work_orders': next_work_orders,

        'alerts': recent_alerts,
        'alerts_count': alerts_count,

        'weather_data': weather_data,
        'station': station,
        'weather_operational_status': weather_operational_status,
        'weather_operational_detail': weather_operational_detail,
        'weather_operational_badge': weather_operational_badge,

        'required_inputs': required_inputs,
        'missing_inputs': missing_inputs,
        'missing_inputs_count': missing_inputs_count,

        'today': today,
    })

    return render(request, 'admin/custom_dashboard.html', context)