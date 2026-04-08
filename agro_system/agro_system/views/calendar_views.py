from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from operation.models.work_order import WorkOrder
from operation.models.input_work_order import InputWorkOrder
from operation.models.crop import Crop
from producer.models.country_side import Countryside
from producer.models.lot import Lot
from parameter.models.campaign import Campaing

@login_required
def CalendarView(request):
    
    # filtros desde GET
    countryside_id = request.GET.get('countryside')
    lot_id = request.GET.get('lot')
    campaing_id = request.GET.get('campaing')

    user = request.user
    if user.type == 'Producer':
        work_orders = WorkOrder.objects.filter(producer=user)  
        country_sides = Countryside.objects.filter(producer=user)

    elif user.type == 'Administration':
        work_orders = WorkOrder.objects.all()

    orders = []
    lots = Lot.objects.filter(countryside__in=country_sides)
    campaings = Campaing.objects.all()

    if countryside_id:
        crops = Crop.objects.filter(countryside__in=country_sides)
        work_orders = work_orders.filter(crops__in=crops)

    if lot_id:
        crops = Crop.objects.filter(lot=lot_id)
        work_orders = work_orders.filter(crops__in=crops)

    if campaing_id:
        work_orders = work_orders.filter(campaing_id=campaing_id)

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
        'campaings': campaings,
    }

    return render(request, 'pages/calendar.html', data)
