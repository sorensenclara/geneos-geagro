def get_producer_ref(user):
    """
    Devuelve la instancia UserProducer del usuario logueado, o None.
    Necesario porque AUTH_USER_MODEL=UserExtend y las FKs apuntan a UserProducer.
    """
    from user.models.user_producer import UserProducer
    from producer.models.staff import Staff

    if getattr(user, 'type', None) == 'Producer':
        return UserProducer.objects.filter(email=user.email).first()
    elif getattr(user, 'type', None) == 'Staff':
        staff = Staff.objects.filter(user=user).first()
        return staff.producer if staff else None
    return None


def build_user_scope(user):
    """
    Devuelve (crops_qs, country_sides_qs) filtrados según tipo de usuario.
    Nunca aplica fallback a 'todo': si el usuario no tiene datos, devuelve none().
    """
    from operation.models.crop import Crop
    from producer.models.country_side import Countryside
    from user.models.user_producer import UserProducer

    user_type = getattr(user, 'type', None)

    if user.is_superuser or user_type == 'Administration':
        return Crop.objects.all(), Countryside.objects.all()

    if user_type == 'Producer':
        producer = get_producer_ref(user)
        if producer:
            return (
                Crop.objects.filter(producer=producer),
                Countryside.objects.filter(producer=producer),
            )
        return Crop.objects.none(), Countryside.objects.none()

    if user_type == 'Organization':
        producers = UserProducer.objects.filter(organization=user)
        return (
            Crop.objects.filter(producer__in=producers),
            Countryside.objects.filter(producer__in=producers),
        )

    if user_type == 'Staff':
        producer = get_producer_ref(user)
        if producer:
            return (
                Crop.objects.filter(producer=producer),
                Countryside.objects.filter(producer=producer),
            )
        return Crop.objects.none(), Countryside.objects.none()

    return Crop.objects.none(), Countryside.objects.none()


def read_filter(request):
    """
    Lee campaing_id y crop_id desde GET params o sesión (en ese orden).
    Persiste en sesión cuando vienen desde GET.
    """
    if 'campaing' in request.GET:
        request.session['filter_campaing_id'] = request.GET.get('campaing') or None
    if 'crop' in request.GET:
        request.session['filter_crop_id'] = request.GET.get('crop') or None

    return (
        request.GET.get('campaing') or request.session.get('filter_campaing_id'),
        request.GET.get('crop') or request.session.get('filter_crop_id'),
    )
