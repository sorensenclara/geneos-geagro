from parameter.models.campaign import Campaing
from operation.models.crop import Crop
from producer.models.staff import Staff


def topbar_filter(request):
    """
    Hace disponibles en todos los templates los datos del filtro global
    (campaña y cultivo seleccionados). Persiste la selección en la sesión.
    """
    if not request.user.is_authenticated:
        return {}

    # Actualizar sesión si vienen parámetros GET del filtro
    if 'campaing' in request.GET:
        request.session['filter_campaing_id'] = request.GET.get('campaing') or None
    if 'crop' in request.GET:
        request.session['filter_crop_id'] = request.GET.get('crop') or None

    campaing_id = request.session.get('filter_campaing_id')
    crop_id = request.session.get('filter_crop_id')

    user = request.user

    # Queryset de cultivos según tipo de usuario
    if user.type == 'Staff':
        staff = Staff.objects.filter(user=user).first()
        crops_qs = Crop.objects.filter(responsible=staff) if staff else Crop.objects.none()
    elif user.type == 'Producer':
        crops_qs = Crop.objects.filter(producer=user)
    elif user.type in ('Administration', 'Organization'):
        crops_qs = Crop.objects.all()
    else:
        crops_qs = Crop.objects.none()

    campaings = Campaing.objects.all().order_by('-date_init')
    campaign_active = campaings.filter(active=True).first() or campaings.first()

    # Campaña seleccionada
    if campaing_id:
        selected_campaing = campaings.filter(id=campaing_id).first() or campaign_active
    else:
        selected_campaing = campaign_active

    if selected_campaing:
        crops_qs = crops_qs.filter(campaing=selected_campaing)

    # Cultivo seleccionado
    if crop_id:
        selected_crop = crops_qs.filter(id=crop_id).first()
    else:
        selected_crop = crops_qs.filter(is_main=True).first() or crops_qs.order_by('-id').first()

    return {
        'campaings': campaings,
        'crops': crops_qs,
        'selected_campaing': selected_campaing,
        'selected_crop': selected_crop,
        'campaign_active': campaign_active,
    }
