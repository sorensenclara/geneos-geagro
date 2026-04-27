from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from weather.models import WeatherData

@login_required
def WeatherView(request):
    
    crop_id = request.GET.get('crop')
    from operation.models.crop import Crop
    from producer.models.lot import Lot
    from weather.models.station_weather import WeatherStation

    user = request.user
    if user.type == 'Producer':
        crops = Crop.objects.filter(producer=user)
    elif user.type == 'Staff':
        crops = Crop.objects.filter(responsible__user=user)
    elif user.type == 'Administration':
        crops = Crop.objects.all()
    else:
        crops = Crop.objects.none()

    crop_selected = None
    if crop_id:
        crop_selected = crops.filter(id=crop_id).first()
    else:
        crop_selected = crops.filter(is_main=True).first() or crops.first()

    weather = None
    station = None
    if crop_selected and crop_selected.lot and crop_selected.lot.station:
        station = crop_selected.lot.station
        weather = WeatherData.objects.filter(station=station).last()

    data = {
        'weather_data': weather,
        'station': station,
        'crop_main': crop_selected,
        'crops': crops,
    }

    return render(request, 'pages/weather.html', data)