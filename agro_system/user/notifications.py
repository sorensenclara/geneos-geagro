"""Helpers para crear notificaciones a usuarios (productor y su personal)."""
from django.utils.timezone import localdate

# Estados de personal que ya no deben recibir notificaciones
INACTIVE_STAFF_STATES = ('inactive', 'discharged')


def active_staff_users(producer):
    """Usuarios del personal activo del productor (el personal sin usuario no puede recibir notificaciones)."""
    from producer.models.staff import Staff
    if producer is None:
        return []
    staff = (Staff.objects
             .filter(producer=producer, user__isnull=False)
             .exclude(state__in=INACTIVE_STAFF_STATES)
             .select_related('user'))
    return [s.user for s in staff]


def notify(users, name, detail, date=None):
    """Crea una notificación por usuario, sin repetir usuarios ni crear para usuarios vacíos."""
    from user.models.notification import Notification
    unique = {}
    for user in users:
        if user is not None and user.pk is not None:
            unique[user.pk] = user
    Notification.objects.bulk_create([
        Notification(user_id=pk, name=name[:200], detail=detail, date=date or localdate())
        for pk in unique
    ])
    return len(unique)
