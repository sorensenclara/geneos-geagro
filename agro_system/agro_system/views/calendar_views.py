from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import date
import json

from operation.models.work_order import WorkOrder
from operation.models.input_work_order import InputWorkOrder
from operation.models.crop import Crop

from producer.models.country_side import Countryside
from producer.models.lot import Lot

from parameter.models.campaign import Campaing
from producer.models.staff import Staff

@login_required
def CalendarView(request):

    # =========================================================
    # CLARA - filtros desde topbar/dashboard
    # =========================================================
    countryside_id = request.GET.get('countryside')
    lot_id = request.GET.get('lot')
    campaing_id = request.GET.get('campaing')
    crop_id = request.GET.get('crop')

    user = request.user

    if user.type == 'Producer':
        country_sides = Countryside.objects.filter(producer=user)
        crops_base = Crop.objects.filter(producer=user)

    elif user.type == 'Staff':
        staff = Staff.objects.filter(user=user).first()
        country_sides = Countryside.objects.filter(producer=staff.producer)
        crops_base = Crop.objects.filter(producer=staff.producer)

    elif user.type == 'Administration':
        country_sides = Countryside.objects.all()
        crops_base = Crop.objects.all()

    else:
        country_sides = Countryside.objects.none()
        crops_base = Crop.objects.none()

  
    campaings = Campaing.objects.all()
    campaign_active = campaings.filter(active=True).first()


    if campaing_id:
        selected_campaing = campaings.filter(id=campaing_id).first()
    else:
        selected_campaing = campaign_active or campaings.first()

    if not crops_base.exists():
        crops_base = Crop.objects.all()

    if not country_sides.exists():
        country_sides = Countryside.objects.all()

    lots = Lot.objects.filter(countryside__in=country_sides)

    crops = crops_base

    if selected_campaing:
        crops = crops.filter(campaing_id=selected_campaing.id)

    if selected_campaing and not crops.exists():
        crops = Crop.objects.filter(
            campaing_id=selected_campaing.id
        )

    if countryside_id:
        crops = crops.filter(countryside_id=countryside_id)
        lots = lots.filter(countryside_id=countryside_id)

    if lot_id:
        crops = crops.filter(lot_id=lot_id)
        lots = lots.filter(id=lot_id)

    if crop_id:
        selected_crop = crops.filter(id=crop_id).first()
    else:
        selected_crop = crops.filter(is_main=True).first() or crops.order_by('-id').first()

    if not selected_crop and selected_campaing:

        selected_crop = Crop.objects.filter(
            campaing_id=selected_campaing.id
        ).order_by('-id').first()

    # =========================================================
    # órdenes reales del cultivo seleccionado
    # =========================================================
    work_orders = WorkOrder.active.none()

    if selected_crop:

        work_orders = WorkOrder.active.filter(
            crop=selected_crop
        )

        if selected_campaing:
            work_orders = work_orders.filter(
                campaing_id=selected_campaing.id
            )

    # =========================================================
    # filtros calendario
    # =========================================================
    state_filter = request.GET.get('state')
    service_filter = request.GET.get('service')

    if state_filter:
        work_orders = work_orders.filter(
            stateOT__name__icontains=state_filter
        )

    if service_filter:
        work_orders = work_orders.filter(
            service_id=service_filter
        )  

    # =========================================================
    # DEV ORIGINAL - armado órdenes + insumos
    # =========================================================
    orders = []

    for order in work_orders:

        input_work_orders = InputWorkOrder.objects.filter(
            work_order=order
        )

        orders.append({
            'work_order': order,
            'input_work_orders': input_work_orders,
        })

    # =========================================================
    #  eventos reales FullCalendar
    # =========================================================
    calendar_events = []

    for order in work_orders:

        color_class = "bg-warning"

        state_name = str(order.stateOT).upper() if order.stateOT else ""

        if "CURSO" in state_name:
            color_class = "bg-primary"

        elif (
            "COMPLET" in state_name
            or "FINALIZ" in state_name
            or "REALIZ" in state_name
        ):
            color_class = "bg-success"

        elif "VENC" in state_name:
            color_class = "bg-danger"

        calendar_events.append({

            'title': (
                str(order.service)
                if order.service
                else 'Orden de trabajo'
            ),

            'start': (
                order.date_init.strftime('%Y-%m-%d')
                if order.date_init
                else None
            ),

            'end': (
                order.date_fin.strftime('%Y-%m-%d')
                if order.date_fin
                else None
            ),

            'className': color_class,
        })

    # =========================================================
    # próximas actividades sidebar
    # Mostrar primero EN CURSO / fecha actual, luego próximas pendientes
    # =========================================================
    today = date.today()

    work_orders_current = work_orders.filter(
        Q(stateOT__name__icontains='CURSO') |
        Q(date_init__lte=today, date_fin__gte=today)
    ).exclude(
        Q(stateOT__name__icontains='COMPLET') |
        Q(stateOT__name__icontains='FINALIZ') |
        Q(stateOT__name__icontains='REALIZ')
    ).order_by('date_init')

    work_orders_next = work_orders.filter(
        date_init__gte=today
    ).exclude(
        Q(stateOT__name__icontains='CURSO') |
        Q(stateOT__name__icontains='COMPLET') |
        Q(stateOT__name__icontains='FINALIZ') |
        Q(stateOT__name__icontains='REALIZ')
    ).order_by('date_init')

    recent_activities = list(work_orders_current[:3])

    for order in work_orders_next:
        if order not in recent_activities:
            recent_activities.append(order)

        if len(recent_activities) >= 5:
            break
    
    services = set(order.service for order in work_orders if order.service)
    # =========================================================
    # data template
    # =========================================================
    data = {

        'data_work_orders': orders,

        'country_sides': country_sides,
        'lots': lots,
        'crops': crops,
        'campaings': campaings,

        'crop_main': selected_crop,
        'crop_selected': selected_crop,
        'selected_crop': selected_crop,

        'selected_campaing': selected_campaing,
        'campaign_active': campaign_active,

        'calendar_events_json': json.dumps(calendar_events),

        'recent_activities': recent_activities,

        'today': date.today(),

        'selected_state': state_filter,
        'selected_service': service_filter,
        'services': list(services),
    }

    return render(
        request,
        'pages/calendar.html',
        data
    )