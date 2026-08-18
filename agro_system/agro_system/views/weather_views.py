import logging
from datetime import timedelta

from django.shortcuts import render

logger = logging.getLogger(__name__)
from django.contrib.auth.decorators import login_required
from django.db.models import Min, Max, Sum, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone

from weather.models.weather_data import WeatherData
from weather.models.daily_summary import DailySummary
from weather.models.open_meteo_hourly import OpenMeteoHourly
from operation.models.crop import Crop
from producer.models.country_side import Countryside
from producer.models.lot import Lot
from parameter.models.campaign import Campaing
from producer.models.staff import Staff


@login_required
def WeatherView(request):

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

    today = timezone.now().date()

    # ── Estación interna (WeatherData) ───────────────────────────
    weather_data    = None
    station         = None
    weather_records = WeatherData.objects.none()

    if selected_crop and selected_crop.lot and selected_crop.lot.station:
        station = selected_crop.lot.station
        weather_records = WeatherData.objects.filter(station=station).order_by('-timestamp')
        weather_data = weather_records.first()

    # ── Estación externa (Open-Meteo) ────────────────────────────
    external_station   = None
    today_summary      = None
    past_summaries     = []
    future_weather     = []
    today_source_label = None
    weather_today_rt   = None   # lectura en tiempo real si no hay DailySummary de hoy

    if selected_crop and selected_crop.lot:
        _lot = selected_crop.lot
        external_station = _lot.external_station

        today_summary = DailySummary.objects.filter(lot=_lot, date=today).first()
        past_summaries = list(
            DailySummary.objects
            .filter(lot=_lot, date__gte=today - timedelta(days=3), date__lt=today)
            .order_by("-date")
        )

        if today_summary:
            if today_summary.fuente_predominante == DailySummary.SOURCE_STATION and station:
                today_source_label = station.name
            else:
                today_source_label = "Open-Meteo"
        elif weather_data:
            today_source_label = f"{station.name} · tiempo real" if station else "Estación"
            weather_today_rt = weather_data

        # Pronóstico: primero el resumen diario (ya consolidado por el ciclo)
        future_qs = (
            DailySummary.objects
            .filter(lot=_lot, date__gt=today)
            .order_by("date")[:7]
        )
        if future_qs.exists():
            future_weather = [
                {
                    "datetime__date": s.date,
                    "tmin":          s.tmin,
                    "tmax":          s.tmax,
                    "lluvia_mm":     s.lluvia_mm,
                    "eto_mm":        s.eto_mm,
                    "hr_media":      s.hr_media,
                    "wind_max":      s.wind_max,
                    "wind_gusts_max": s.wind_gusts_max,
                }
                for s in future_qs
            ]
        elif external_station:
           
            rows = (
                OpenMeteoHourly.objects
                .filter(station=external_station, datetime__date__gt=today)
                .annotate(day=TruncDate("datetime"))
                .values("day")
                .annotate(
                    tmin=Min("temperature"),
                    tmax=Max("temperature"),
                    lluvia_mm=Sum("precipitation"),
                    eto_mm=Sum("eto_mm"),
                    hr_media=Avg("humidity"),
                    wind_max=Max("wind_speed"),
                    wind_gusts_max=Max("wind_gusts"),
                )
                .order_by("day")[:7]
            )
            future_weather = [
                {
                    "datetime__date": r["day"],
                    "tmin":          r["tmin"],
                    "tmax":          r["tmax"],
                    "lluvia_mm":     r["lluvia_mm"],
                    "eto_mm":        r["eto_mm"],
                    "hr_media":      r["hr_media"],
                    "wind_max":      r["wind_max"],
                    "wind_gusts_max": r["wind_gusts_max"],
                }
                for r in rows
            ]

    data = {
        # Estación interna
        'weather_data':    weather_data,
        'weather_records': weather_records[:10],
        'station':         station,

        # Estación externa + resúmenes
        'external_station':   external_station,
        'today_summary':      today_summary,
        'past_summaries':     past_summaries,
        'future_weather':     future_weather,
        'today_source_label': today_source_label,
        'weather_today_rt':   weather_today_rt,
        'today':              today,

        # Selección
        'crop_main':       selected_crop,
        'selected_crop':   selected_crop,
        'crop_selected':   selected_crop,
        'crops':           crops,
        'country_sides':   country_sides,
        'lots':            lots,
        'campaings':       campaings,
        'selected_campaing': selected_campaing,
        'campaign_active': campaign_active,
    }

    return render(request, 'pages/weather.html', data)
