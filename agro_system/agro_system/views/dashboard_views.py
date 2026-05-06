from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from producer.models.lot import Lot
from producer.models.country_side import Countryside
from producer.models.staff import Staff

from parameter.models.campaign import Campaing

from operation.models.technical_plan import TechnicalPlan
from operation.models.work_order import WorkOrder
from operation.models.crop import Crop

from weather.models.weather_data import WeatherData
from weather.models.station_weather import WeatherStation

from alert.models.alert import Alert


# Panel principal
@login_required
def DashboardView(request):

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


    work_orders = WorkOrder.objects.none()

    if selected_crop:
        work_orders = WorkOrder.objects.filter(crop=selected_crop)

        if selected_campaing:
            work_orders = work_orders.filter(campaing=selected_campaing)

        work_orders = work_orders.order_by('date_init')[:3]

    elif selected_campaing:
        work_orders = WorkOrder.objects.filter(campaing=selected_campaing)

        if lots.exists():
            work_orders = work_orders.filter(crop__lot__in=lots)

        work_orders = work_orders.order_by('date_init')[:3]

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
        crop_hectares_without_plant = (selected_crop.hectares_productive - selected_crop.hectares_planted) or 0
        crop_hectares_planted = selected_crop.hectares_planted or 0
        #crop_hectares_without_plant = selected_crop.hectares_without_plant or 0
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

        #crop_hectares_productive': crop_hectares_productive,
        #crop_hectares_total': crop_hectares_total,

        'weather_data': weather_data,
        'station': station,

        'lot_hectares_total': lot_hectares_total,
        'crop_hectares_planted': crop_hectares_planted,
        'crop_hectares_without_plant': crop_hectares_without_plant,
        'crop_hectares_harvested': crop_hectares_harvested,
        'crop_hectares_without_harvest': crop_hectares_without_harvest,
        'planted_percent': planted_percent,
        'harvested_percent': harvested_percent,
    }

    return render(request, 'pages/dashboard.html', data)