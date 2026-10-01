from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import date

from operation.models.work_order import WorkOrder
from operation.models.input_work_order import InputWorkOrder
from operation.models.crop import Crop
from operation.models.technical_plan import TechnicalPlan
from operation.models.technical_plan_detail import TechnicalPlanDetail

from producer.models.country_side import Countryside
from producer.models.lot import Lot

from parameter.models.campaign import Campaing
from producer.models.staff import Staff

from alert.models.alert import Alert
from agro_system.views.filter_helpers import read_filter, build_user_scope


@login_required
def TechnicalPlanView(request):

    countryside_id = request.GET.get('countryside')
    lot_id = request.GET.get('lot')
    campaing_id, crop_id = read_filter(request)

    user = request.user
    crops_base, country_sides = build_user_scope(user)

    campaings = Campaing.objects.all()
    campaign_active = campaings.filter(active=True).first()

    if campaing_id:
        selected_campaing = campaings.filter(id=campaing_id).first()
    else:
        selected_campaing = campaign_active or campaings.first()

    lots = Lot.objects.filter(countryside__in=country_sides)
    crops = crops_base

    if selected_campaing:
        crops = crops.filter(campaing_id=selected_campaing.id)

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


    work_orders = WorkOrder.objects.none()

    if selected_crop:
        work_orders = WorkOrder.objects.filter(crop=selected_crop)

        if selected_campaing:
            work_orders = work_orders.filter(campaing_id=selected_campaing.id)


    orders = []

    for order in work_orders:
        input_work_orders = InputWorkOrder.objects.filter(work_order=order)

        orders.append({
            'work_order': order,
            'input_work_orders': input_work_orders,
        })


    today = date.today()

    next_work_order = work_orders.filter(
        date_init__gte=today
    ).order_by('date_init').first()

    if not next_work_order:
        next_work_order = work_orders.exclude(
            Q(stateOT__name__icontains='COMPLET') |
            Q(stateOT__name__icontains='FINALIZ') |
            Q(stateOT__name__icontains='REALIZ')
        ).order_by('date_init').first()


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


    alerts = Alert.objects.none()

    if selected_crop:
        alerts = Alert.objects.filter(
            crop=selected_crop
        ).order_by('-date')

    alerts_count = alerts.count()

    next_alert = alerts.first()
    why_now_title = "Según planificación técnica"
    why_now_text = "Esta acción está programada dentro del plan técnico del cultivo."

    if next_alert:
        why_now_title = next_alert.name
        why_now_text = next_alert.detail

    elif next_work_order:
        why_now_title = "Orden planificada"
        why_now_text = (
            f"La labor {next_work_order.service} está prevista para el estadio "
            f"{next_work_order.stage} y tiene fecha de inicio "
            f"{next_work_order.date_init.strftime('%d/%m/%Y')}."
        )


    timeline = []
    technical_plan = None

    if selected_crop:
        technical_plan = TechnicalPlan.objects.filter(
            variety=selected_crop.variety,
            area=selected_crop.area,
            active=True
        ).first()

    if technical_plan:
        plan_details = TechnicalPlanDetail.objects.filter(
            technical_plan=technical_plan,
            active=True
        ).select_related(
            'stage',
            'service'
        ).order_by('secuence')

        for detail in plan_details:

            stage_orders = work_orders.filter(
                stage=detail.stage,
                service=detail.service
            )

            total_orders = stage_orders.count()

            completed_orders = stage_orders.filter(
                Q(stateOT__name__icontains='COMPLET') |
                Q(stateOT__name__icontains='FINALIZ') |
                Q(stateOT__name__icontains='REALIZ')
            ).count()

            if total_orders > 0 and completed_orders == total_orders:
                status = 'completed'

            elif completed_orders > 0:
                status = 'active'

            else:
                status = 'pending'

            timeline.append({
                'detail': detail,
                'stage': detail.stage,
                'service': detail.service,
                'status': status,
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'orders': stage_orders,
            })

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

        'alerts': alerts[:5],
        'alerts_count': alerts_count,

        'timeline': timeline,
        'technical_plan': technical_plan,

        'next_work_order': next_work_order,
        'today': today,

        'next_alert': next_alert,
        'why_now_title': why_now_title,
        'why_now_text': why_now_text,
    }

    return render(request, 'pages/plan.html', data)