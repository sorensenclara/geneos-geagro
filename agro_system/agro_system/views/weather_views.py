from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from weather.models import WeatherData
from operation.models.crop import Crop
from producer.models.country_side import Countryside
from producer.models.lot import Lot
from parameter.models.campaign import Campaing
from producer.models.staff import Staff
from agro_system.views.filter_helpers import read_filter, build_user_scope

@login_required
def WeatherView(request):

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

 
    weather = None
    station = None
    weather_records = WeatherData.objects.none()

    if selected_crop and selected_crop.lot and selected_crop.lot.station:
        station = selected_crop.lot.station

        weather_records = WeatherData.objects.filter(
            station=station
        ).order_by('-timestamp')

        weather = weather_records.first()

    data = {
        'weather_data': weather,
        'weather_records': weather_records[:10],
        'station': station,

        'crop_main': selected_crop,
        'selected_crop': selected_crop,
        'crop_selected': selected_crop,

        'crops': crops,
        'country_sides': country_sides,
        'lots': lots,
        'campaings': campaings,

        'selected_campaing': selected_campaing,
        'campaign_active': campaign_active,
    }

    return render(request, 'pages/weather.html', data)