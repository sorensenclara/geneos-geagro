from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from producer.models.lot import Lot
from parameter.models.campaign import Campaing
from producer.models.country_side import Countryside
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from operation.models.technical_plan import TechnicalPlan
from operation.models.work_order import WorkOrder
from operation.models.crop import Crop
from producer.models.staff import Staff
from django.utils import timezone
from weather.models import WeatherData


# Panel principal
@login_required
def DashboardView(request):

    # filtros desde GET
    countryside_id = request.GET.get('countryside')
    lot_id = request.GET.get('lot')
    campaing_id = request.GET.get('campaing')
    lot = None
    user = request.user
    if user.type == 'Staff':
        staff = Staff.objects.filter(user=user).first()
        country_sides = Countryside.objects.filter(producer=user.producer)
        work_orders = WorkOrder.objects.filter(producer=user.producer)
        lot = Lot.objects.filter(countryside__in=country_sides, staffuser__id=staff.id)
    if user.type == 'Producer':
        country_sides = Countryside.objects.filter(producer=user)
        work_orders = WorkOrder.objects.filter(producer=user)

    elif user.type == 'Administration':
        country_sides = Countryside.objects.all()
        work_orders = WorkOrder.objects.all()

    else:
        country_sides = Countryside.objects.none()
        work_orders = WorkOrder.objects.none()

    lots = Lot.objects.filter(countryside__in=country_sides)

    # Busco lote principal  del staff para mostrarlo por defecto en el dashboard
    if lot: 
        for l in lots:
            if l.is_main:
                lot = l
                break
            else:
                lot = lots.first()

    # Filtros

    if countryside_id:
       lots = lots.filter(countryside=countryside_id)
       crops = Crop.objects.filter(countryside__in=country_sides)
       work_orders = work_orders.filter(crops__in=crops)
   
    if lot_id:
        crops = Crop.objects.filter(lot=lot_id)
        work_orders = work_orders.filter(crops__in=crops)

    # TODO todas o la activa?
    # Referencia a las campañas
    campaings = Campaing.objects.all()
    if campaing_id:
        work_orders = work_orders.filter(campaing_id=campaing_id)
    elif campaings.filter(active=True).first():
        work_orders = work_orders.filter(campaing=campaings.filter(active=True).first())

    # Las proximas 3 ordenes a realizar
    today = timezone.now().date()
    work_orders = work_orders.filter(date_init__gte=today).order_by('date_init')[:3]

    weather_data = WeatherData.objects.last() 
    data = {
        'country_sides': country_sides,
        'lots': lots,
        'lot_main': lot,    
        'campaings': campaings,
        'campaing_active': campaings.filter(active=True).first(),
        'work_orders': work_orders,
        'selected_countryside': countryside_id,
        'selected_lot': lot_id,
        'selected_campaing': campaing_id,
        'weather_data': weather_data
    }
    return render(request, 'pages/dashboard.html', data)




#kanbanboard_view = DashboardView.as_view(template_name = "pages/plan.html")
#calendar_front_view = DashboardView.as_view(template_name = "pages/calendar.html")
#weather_view = DashboardView.as_view(template_name = "pages/weather.html")
#alert_view = DashboardView.as_view(template_name = "pages/alert.html")
#wines_view = DashboardView.as_view(template_name = "pages/wines.html") #vineyard