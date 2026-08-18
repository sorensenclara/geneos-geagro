from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from producer.models.lot import Lot
from parameter.models.campaign import Campaing
from producer.models.country_side import Countryside
from operation.models.technical_plan import TechnicalPlan
from operation.models.work_order import WorkOrder
from producer.models.staff import Staff
from operation.models.crop import Crop


@login_required
def VineyardView(request):

    # =========================================================
    # filtros desde topbar/dashboard
    # =========================================================
    campaing_id = request.GET.get('campaing')
    crop_id = request.GET.get('crop')

    user = request.user

    # =========================================================
    # DEV ORIGINAL - visibilidad según tipo usuario
    # =========================================================
    if user.type == 'Producer':
        country_sides = Countryside.objects.filter(producer=user)
        technical_plans = TechnicalPlan.objects.filter(producer=user)
        staff = Staff.objects.filter(producer=user)
        crops_base = Crop.objects.filter(producer=user)

    elif user.type == 'Staff':
        staff_instance = Staff.objects.filter(user=user).first()

        if staff_instance and staff_instance.producer:
            producer = staff_instance.producer
            country_sides = Countryside.objects.filter(producer=producer)
            technical_plans = TechnicalPlan.objects.filter(producer=producer)
            staff = Staff.objects.filter(producer=producer)
            crops_base = Crop.objects.filter(producer=producer)
        else:
            country_sides = Countryside.objects.none()
            technical_plans = TechnicalPlan.objects.none()
            staff = Staff.objects.none()
            crops_base = Crop.objects.none()

    elif user.type == 'Administration':
        country_sides = Countryside.objects.all()
        technical_plans = TechnicalPlan.objects.all()
        staff = Staff.objects.all()
        crops_base = Crop.objects.all()

    else:
        country_sides = Countryside.objects.none()
        technical_plans = TechnicalPlan.objects.none()
        staff = Staff.objects.none()
        crops_base = Crop.objects.none()

    # =========================================================
    # campaña seleccionada / activa
    # =========================================================
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

    # =========================================================
    #  cultivo principal / seleccionado
    # =========================================================
    if crop_id:
        main_crop = crops.filter(id=crop_id).first()
    else:
        main_crop = crops.filter(is_main=True).first() or crops.order_by('-id').first()

    if not main_crop and selected_campaing:
        main_crop = Crop.objects.filter(
            campaing_id=selected_campaing.id
        ).order_by('-id').first()

    # =========================================================
    # métricas reales
    # =========================================================
    total_productive_hectares = lots.aggregate(
        total=Sum('hectares_productive')
    )['total'] or 0

    data = {
        'technical_plans': technical_plans,
        'staff': staff,
        'country_sides': country_sides,
        'lots': lots,
        'crops': crops,
        'campaings': campaings,

        'selected_campaing': selected_campaing,
        'campaign_active': campaign_active,

        'selected_crop': main_crop,
        'crop_selected': main_crop,
        'crop_main': main_crop,
        'main_crop': main_crop,

        'total_productive_hectares': total_productive_hectares,
    }

    return render(request, 'pages/vineyard.html', data)