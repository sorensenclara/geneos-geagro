from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import localdate

from operation.models.work_order import WorkOrder
from user.notifications import active_staff_users, notify


# NOTIFICACIONES CUANDO SE CREA UNA ORDEN DE TRABAJO
# Si la orden tiene personal asignado, se avisa solo a esa persona;
# si no, a todo el personal activo del productor. El productor no recibe esta notificación.
@receiver(post_save, sender=WorkOrder)
def notify_work_order_created(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.staff_id:
        users = [instance.staff.user]  # el personal sin usuario no puede recibir notificaciones
    else:
        users = active_staff_users(instance.producer)

    parts = [f'Cultivo: {instance.crop}', f'Inicio: {instance.date_init:%d/%m/%Y}']
    if instance.service_id:
        parts.insert(0, f'Servicio: {instance.service}')
    if instance.surface is not None:
        parts.append(f'Superficie: {instance.surface:g} ha')
    if instance.staff_id:
        parts.append(f'Asignada a: {instance.staff}')

    notify(
        users,
        name=f'Nueva orden de trabajo {instance.code}',
        detail='. '.join(parts),
        date=localdate(),
    )
