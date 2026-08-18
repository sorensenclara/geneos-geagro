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
from alert.models.indicator import Indicator


@login_required
def TechnicalPlanView(request):

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
        crops = Crop.objects.filter(campaing_id=selected_campaing.id)

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


    _completed_q = (
        Q(stateOT__name__icontains='COMPLET') |
        Q(stateOT__name__icontains='FINALIZ') |
        Q(stateOT__name__icontains='REALIZ')
    )

    work_orders = WorkOrder.active.none()

    if selected_crop:
        work_orders = WorkOrder.active.filter(crop=selected_crop)
        if selected_campaing:
            work_orders = work_orders.filter(campaing_id=selected_campaing.id)

    def _inputs_str(order):
        parts = []
        for iwo in InputWorkOrder.objects.filter(work_order=order).select_related("input__unit_measure"):
            unit = str(iwo.input.unit_measure) if iwo.input.unit_measure_id else ""
            parts.append(f"{iwo.input.name} — {iwo.dose} {unit}".strip())
        return " | ".join(parts) if parts else "Sin insumos"

    def _order_row(order):
        return {
            "order": order,
            "inputs_str": _inputs_str(order),
        }

    pending_orders  = [_order_row(o) for o in work_orders.exclude(_completed_q).order_by("date_init")]
    completed_orders = [_order_row(o) for o in work_orders.filter(_completed_q).order_by("-date_init")]

    # ID del registro Staff del usuario logueado (para highlight de "mis órdenes")
    current_staff_id = None
    if user.type == 'Staff':
        _my_staff = Staff.objects.filter(user=user).first()
        if _my_staff:
            current_staff_id = _my_staff.pk

    today = date.today()

    next_work_order = work_orders.filter(
        date_init__gte=today
    ).exclude(_completed_q).order_by('date_init').first()

    if not next_work_order:
        next_work_order = work_orders.exclude(_completed_q).order_by('date_init').first()


    work_orders_total = work_orders.count()
    work_orders_completed = work_orders.filter(_completed_q).count()
    work_orders_pending = work_orders_total - work_orders_completed
    work_orders_completed_percent = (
        round((work_orders_completed / work_orders_total) * 100) if work_orders_total else 0
    )


    alerts = Alert.active.none()

    if selected_crop:
        alerts = Alert.active.filter(
            crop=selected_crop
        ).order_by('-date')

    alerts_count = alerts.count()

    next_alert = alerts.first()

    # Ventana de aplicación: muestra verde si no hay alerta activa del indicador
    ventana_nivel = None
    if selected_crop:
        ventana_ind = Indicator.objects.filter(name="ventana_aplicacion").first()
        if ventana_ind:
            ventana_alert = Alert.active.filter(
                crop=selected_crop,
                indicator=ventana_ind,
            ).order_by("-date").first()
            ventana_nivel = ventana_alert.level if ventana_alert else "verde"

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
            activity=selected_crop.activity,
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
        'pending_orders':   pending_orders,
        'completed_orders': completed_orders,
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

        'current_staff_id': current_staff_id,
        'ventana_nivel': ventana_nivel,
    }

    return render(request, 'pages/plan.html', data)