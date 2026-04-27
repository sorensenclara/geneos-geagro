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
from weather.models.weather_data import WeatherData
from weather.models.station_weather import WeatherStation

# Panel principal
@login_required
def DashboardView(request):

    # filtros desde GET
    countryside_id = request.GET.get('countryside')
    lot_id = request.GET.get('lot')
    campaing_id = request.GET.get('campaing')
    crop_id = request.GET.get('crop')

    user = request.user
    staff = None
    if user.type == 'Staff':
        staff = Staff.objects.filter(user=user).first()
        country_sides = Countryside.objects.filter(producer=user.producer)
        crops = Crop.objects.filter(responsible=staff)
    elif user.type == 'Producer':
        country_sides = Countryside.objects.filter(producer=user)
        crops = Crop.objects.filter(producer=user)
    elif user.type == 'Administration':
        country_sides = Countryside.objects.all()
        crops = Crop.objects.all()
    else:
        country_sides = Countryside.objects.none()
        crops = Crop.objects.none()

    lots = Lot.objects.filter(countryside__in=country_sides)

    # Filtros de campañas
    campaings = Campaing.objects.all()

    # Filtro de cultivos por campaña, viñedo, lote
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
        # Filtro de campaña en work_orders
        if campaing_id:
            work_orders = work_orders.filter(campaing_id=campaing_id)
        # Solo próximas 3 órdenes
        today = timezone.now().date()
        work_orders = work_orders.filter(date_init__gte=today).order_by('date_init')[:3]

    # Clima de la estación del lote del cultivo seleccionado
    weather_data = None
    station = None
    if crop_selected and crop_selected.lot and crop_selected.lot.station:
        station = crop_selected.lot.station
        weather_data = WeatherData.objects.filter(station=station).last()

    data = {
        'country_sides': country_sides, # Viñedos
        'lots': lots,  # Lotes
        'crop_main': crop_selected, # Cultivo principal o seleccionado
        'crops': crops, # Cultivos filtrados
        'campaings': campaings,
        'campaing_active': campaings.filter(active=True).first(),
        'work_orders': work_orders,
        'selected_countryside': countryside_id,
        'selected_lot': lot_id,
        'selected_campaing': campaing_id,
        'weather_data': weather_data,
        'station': station,
    }
    return render(request, 'pages/dashboard.html', data)




#kanbanboard_view = DashboardView.as_view(template_name = "pages/plan.html")
#calendar_front_view = DashboardView.as_view(template_name = "pages/calendar.html")
#weather_view = DashboardView.as_view(template_name = "pages/weather.html")
#alert_view = DashboardView.as_view(template_name = "pages/alert.html")
#wines_view = DashboardView.as_view(template_name = "pages/wines.html") #vineyard