from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from operation.models.technical_plan import TechnicalPlan
from operation.models.technical_plan_input import TechnicalPlanInput
from operation.models.technical_plan_detail import TechnicalPlanDetail
from operation.models.work_order import WorkOrder
from operation.models.input_work_order import InputWorkOrder
from operation.models.crop import Crop
from producer.models.country_side import Countryside
from producer.models.lot import Lot
from parameter.models.campaign import Campaing


@login_required
def TechnicalPlanView(request):

    # filtros desde GET
    countryside_id = request.GET.get('countryside')
    lot_id = request.GET.get('lot')
    campaing_id = request.GET.get('campaing')
    crop_id = request.GET.get('crop')

    user = request.user
    if user.type == 'Producer':
        country_sides = Countryside.objects.filter(producer=user)
        crops = Crop.objects.filter(producer=user)
    elif user.type == 'Staff':
        country_sides = Countryside.objects.filter(producer=user.producer)
        crops = Crop.objects.filter(responsible__user=user)
    elif user.type == 'Administration':
        country_sides = Countryside.objects.all()
        crops = Crop.objects.all()
    else:
        country_sides = Countryside.objects.none()
        crops = Crop.objects.none()

    lots = Lot.objects.filter(countryside__in=country_sides)
    campaings = Campaing.objects.all()

    # Filtros de cultivos por campaña, viñedo, lote
    if campaing_id:
        crops = crops.filter(campaing_id=campaing_id)
    if countryside_id:
        crops = crops.filter(countryside_id=countryside_id)
        lots = lots.filter(countryside_id=countryside_id)
    if lot_id:
        crops = crops.filter(lot_id=lot_id)
        lots = lots.filter(id=lot_id)

    # Cultivo seleccionado o principal
    crop_selected = None
    if crop_id:
        crop_selected = crops.filter(id=crop_id).first()
    else:
        crop_selected = crops.filter(is_main=True).first() or crops.first()

    # Filtrar work_orders solo del cultivo seleccionado
    work_orders = WorkOrder.objects.none()
    if crop_selected:
        work_orders = WorkOrder.objects.filter(crop=crop_selected)
        if campaing_id:
            work_orders = work_orders.filter(campaing_id=campaing_id)

    orders = []
    for order in work_orders:
        input_work_orders = InputWorkOrder.objects.filter(work_order=order)
        data_order = {
            'work_order': order,
            'input_work_orders': input_work_orders,
        }
        orders.append(data_order)

    data = {
        'data_work_orders': orders,
        'country_sides': country_sides,
        'lots': lots,
        'crops': crops,
        'crop_main': crop_selected,
        'campaings': campaings,
    }

    return render(request, 'pages/plan.html', data)