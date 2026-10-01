"""
Alcance por productor para los admins: cada usuario ve solo los datos de su(s) productor(es).

    producers_for_user(request) -> None (sin filtro: superusuario / Administración)
                                 | queryset de UserProducer del usuario (Producer, Staff, Organización)
"""
from user.models.user_producer import UserProducer


def producers_for_user(request):
    return producers_for(request.user)


def accessible_crops(user):
    """Cultivos que el usuario puede ver: todos (superusuario / Administración) o los de su(s) productor(es)."""
    from operation.models.crop import Crop
    producers = producers_for(user)
    return Crop.objects.all() if producers is None else Crop.objects.filter(producer__in=producers)


def visible_stores(user):
    """Almacenes del usuario: todos (superusuario / Administración); si no, los de su productor y los sin productor."""
    from django.db.models import Q
    from producer.models.store import Store
    producers = producers_for(user)
    if producers is None:
        return Store.objects.all()
    return Store.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))


def producers_for(user):
    user_type = getattr(user, 'type', None)
    if user.is_superuser or user_type == 'Administration':
        return None
    if user_type == 'Organization':
        return UserProducer.objects.filter(organization=user)
    if user_type == 'Producer':
        return UserProducer.objects.filter(email=user.email)
    if user_type == 'Staff':
        from producer.models.staff import Staff
        staff = Staff.objects.filter(user=user).first()
        if staff:
            return UserProducer.objects.filter(pk=staff.producer_id)
    return UserProducer.objects.none()


class ReadOnlyForProducersMixin:
    """Solo lectura para todos salvo superusuario / Administración (ver depende del permiso view_)."""

    def _can_edit(self, request):
        return producers_for_user(request) is None

    def has_add_permission(self, request, *args, **kwargs):
        return self._can_edit(request) and super().has_add_permission(request, *args, **kwargs)

    def has_change_permission(self, request, obj=None):
        return self._can_edit(request) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self._can_edit(request) and super().has_delete_permission(request, obj)
