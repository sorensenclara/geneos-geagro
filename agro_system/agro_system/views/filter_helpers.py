def get_producer_ref(user):
    """
    Devuelve la instancia UserProducer del usuario logueado, o None.
    Necesario porque AUTH_USER_MODEL=UserExtend y las FKs apuntan a UserProducer.
    """
    from user.models.user_producer import UserProducer
    from producer.models.staff import Staff

    if user.type == 'Producer':
        return UserProducer.objects.filter(pk=user.pk).first()
    elif user.type == 'Staff':
        staff = Staff.objects.filter(user=user).first()
        return staff.producer if staff else None
    return None


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
