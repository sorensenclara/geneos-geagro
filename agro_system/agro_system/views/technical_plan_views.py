from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from operation.models.work_order import WorkOrder
from operation.models.input_work_order import InputWorkOrder
from operation.models.crop import Crop

from producer.models.country_side import Countryside
from producer.models.lot import Lot

from parameter.models.campaign import Campaing

from django.db.models import Q

@login_required
def TechnicalPlanView(request):

    # =========================================================
    # CLARA - filtros desde topbar/dashboard
    # =========================================================
    countryside_id = request.GET.get('countryside')
    lot_id = request.GET.get('lot')
    campaing_id = request.GET.get('campaing')
    crop_id = request.GET.get('crop')

    user = request.user

    # =========================================================
    # DEV ORIGINAL - visibilidad según tipo de usuario
    # =========================================================
    if user.type == 'Producer':
        country_sides = Countryside.objects.filter(producer=user)
        crops_base = Crop.objects.filter(producer=user)

    elif user.type == 'Staff':
        country_sides = Countryside.objects.filter(producer=user.producer)
        crops_base = Crop.objects.filter(producer=user.producer)

    elif user.type == 'Administration':
        country_sides = Countryside.objects.all()
        crops_base = Crop.objects.all()

    else:
        country_sides = Countryside.objects.none()
        crops_base = Crop.objects.none()

    campaings = Campaing.objects.all()
    campaign_active = campaings.filter(active=True).first()

    # =========================================================
    # CLARA - campaña seleccionada / activa
    # =========================================================
    if campaing_id:
        selected_campaing = campaings.filter(id=campaing_id).first()
    else:
        selected_campaing = campaign_active or campaings.first()

    # =========================================================
    # CLARA - fallback para desarrollo/local
    # Si por permisos no trae cultivos, no romper topbar.
    # =========================================================
    if not crops_base.exists():
        crops_base = Crop.objects.all()

    if not country_sides.exists():
        country_sides = Countryside.objects.all()

    lots = Lot.objects.filter(countryside__in=country_sides)

    # =========================================================
    # CLARA - cultivos disponibles para topbar
    # =========================================================
    crops = crops_base

    if selected_campaing:
        crops = crops.filter(campaing_id=selected_campaing.id)

    # fallback si el cruce campaña/usuario no devuelve nada
    if selected_campaing and not crops.exists():
        crops = Crop.objects.filter(campaing_id=selected_campaing.id)

    if countryside_id:
        crops = crops.filter(countryside_id=countryside_id)
        lots = lots.filter(countryside_id=countryside_id)

    if lot_id:
        crops = crops.filter(lot_id=lot_id)
        lots = lots.filter(id=lot_id)

    # =========================================================
    # CLARA - cultivo seleccionado
    # 1. Si viene desde Dashboard/topbar, usar ese.
    # 2. Si no viene, tomar último cultivo de la campaña.
    # =========================================================
    if crop_id:
        selected_crop = crops.filter(id=crop_id).first()
    else:
        selected_crop = crops.order_by('-id').first()

    if not selected_crop and selected_campaing:
        selected_crop = Crop.objects.filter(
            campaing_id=selected_campaing.id
        ).order_by('-id').first()

    # =========================================================
    # CLARA - órdenes de trabajo reales del cultivo seleccionado
    # =========================================================
    work_orders = WorkOrder.objects.none()

    if selected_crop:
        work_orders = WorkOrder.objects.filter(crop=selected_crop)

        if selected_campaing:
            work_orders = work_orders.filter(campaing_id=selected_campaing.id)

    # =========================================================
    # DEV ORIGINAL - armado de órdenes
    # =========================================================
    orders = []

    for order in work_orders:
        input_work_orders = InputWorkOrder.objects.filter(work_order=order)

        orders.append({
            'work_order': order,
            'input_work_orders': input_work_orders,
        })


    # =========================================================
    # CLARA - métricas de órdenes para Plan Técnico
    # =========================================================
    work_orders_total = work_orders.count()

    work_orders_completed = work_orders.filter(
        stateOT__name__icontains='COMPLET'
    ).count()

    work_orders_pending = work_orders_total - work_orders_completed

    if work_orders_total > 0:
        work_orders_completed_percent = round(
            (work_orders_completed / work_orders_total) * 100
        )
    else:
        work_orders_completed_percent = 0


    # =========================================================
    # CLARA - métricas de órdenes como Dashboard
    # =========================================================
    work_orders_total = work_orders.count()

    work_orders_completed = work_orders.filter(
        Q(stateOT__name__icontains='COMPLET') |
        Q(stateOT__name__icontains='FINALIZ') |
        Q(stateOT__name__icontains='REALIZ')
    ).count()

    work_orders_pending = work_orders_total - work_orders_completed

    if work_orders_total > 0:
        work_orders_completed_percent = round(
            (work_orders_completed / work_orders_total) * 100
        )
    else:
        work_orders_completed_percent = 0

    data = {
        'data_work_orders': orders,
        'work_orders': work_orders,

        'country_sides': country_sides,
        'lots': lots,
        'crops': crops,
        'campaings': campaings,

        'crop_main': selected_crop,
        'selected_crop': selected_crop,
        'selected_campaing': selected_campaing,
        'campaign_active': campaign_active,

        'work_orders_total': work_orders_total,
        'work_orders_completed': work_orders_completed,
        'work_orders_pending': work_orders_pending,
        'work_orders_completed_percent': work_orders_completed_percent,

        'work_orders_total': work_orders_total,
        'work_orders_completed': work_orders_completed,
        'work_orders_pending': work_orders_pending,
        'work_orders_completed_percent': work_orders_completed_percent,
    }

    return render(request, 'pages/plan.html', data)