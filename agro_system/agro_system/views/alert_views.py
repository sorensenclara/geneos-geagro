from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import date

from alert.models.alert import Alert
from operation.models.crop import Crop
from producer.models.country_side import Countryside
from producer.models.lot import Lot
from parameter.models.campaign import Campaing


@login_required
def AlertView(request):

    # =========================================================
    # CLARA - filtros desde topbar/dashboard
    # =========================================================
    countryside_id = request.GET.get('countryside')
    lot_id = request.GET.get('lot')
    campaing_id = request.GET.get('campaing')
    crop_id = request.GET.get('crop')
    selected_status = request.GET.get('status')
    search_query = request.GET.get('q')

    user = request.user

    # =========================================================
    # DEV ORIGINAL - visibilidad según tipo usuario
    # =========================================================
    if user.type == 'Producer':
        country_sides = Countryside.objects.filter(producer=user)
        crops_base = Crop.objects.filter(producer=user)

    elif user.type == 'Staff':
        country_sides = Countryside.objects.filter(producer=user.producer)
        crops_base = Crop.objects.filter(producer=user.producer)

    elif user.type == 'Administration':
        country_sides = Countryside.objects.all()
        crops_base = Crop.objects.all()

    else:
        country_sides = Countryside.objects.none()
        crops_base = Crop.objects.none()

    campaings = Campaing.objects.all()
    campaign_active = campaings.filter(active=True).first()

    # =========================================================
    # CLARA - campaña seleccionada / activa
    # =========================================================
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
        selected_crop = crops.order_by('-id').first()

    if not selected_crop and selected_campaing:
        selected_crop = Crop.objects.filter(
            campaing_id=selected_campaing.id
        ).order_by('-id').first()

    # =========================================================
    # CLARA - alertas reales
    # =========================================================
    alerts = Alert.objects.none()

    if selected_crop:
        alerts = Alert.objects.filter(
            crop=selected_crop
        ).order_by('-date')

    if selected_status == 'active':
        alerts = alerts.filter(date__gte=date.today())

    elif selected_status == 'history':
        alerts = alerts.filter(date__lt=date.today())

    if search_query:
        alerts = alerts.filter(
            Q(name__icontains=search_query) |
            Q(detail__icontains=search_query)
        )

    alerts_count = alerts.count()
    featured_alert = alerts.first()

    data = {
        'country_sides': country_sides,
        'lots': lots,
        'crops': crops,
        'campaings': campaings,

        'selected_crop': selected_crop,
        'crop_main': selected_crop,
        'selected_campaing': selected_campaing,
        'campaign_active': campaign_active,

        'alerts': alerts,
        'alerts_count': alerts_count,
        'featured_alert': featured_alert,

        'selected_status': selected_status,
        'search_query': search_query,
        'today': date.today(),
    }

    return render(request, 'pages/alert.html', data)