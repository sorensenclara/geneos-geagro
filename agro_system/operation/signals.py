from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from operation.models.work_order import WorkOrder
from user.models.notification import Notification
from producer.models.staff import Staff


def _wo_recipients(wo, exclude_user=None):
    """
    Returns the set of UserExtend to notify for a given WorkOrder.
    Always includes: producer + assigned staff user (if exists) + all staff with users.
    Excludes `exclude_user` (the person who triggered the change).
    """
    users = set()
    # Producer (is a UserExtend subclass)
    if wo.producer:
        users.add(wo.producer)
    # Assigned staff user
    if wo.staff_id and wo.staff.user_id:
        users.add(wo.staff.user)
    # Crop responsible user
    if wo.crop and wo.crop.responsible and wo.crop.responsible.user_id:
        users.add(wo.crop.responsible.user)
    # All producer staff with user accounts
    for staff in Staff.objects.filter(producer=wo.producer, user__isnull=False).select_related("user"):
        users.add(staff.user)
    if exclude_user is not None:
        users.discard(exclude_user)
    return users


def _wo_detail(wo, change_summary=None):
    base = f"OT {wo.code} — {wo.service} / {wo.stage}. Cultivo: {wo.crop}."
    if change_summary:
        return f"{base} Cambios: {change_summary}."
    return base


@receiver(post_save, sender=WorkOrder)
def notify_work_order(sender, instance, created, **kwargs):
    wo = instance
    date = timezone.localdate()
    edited_by = getattr(wo, "_edited_by", None)

    if created:
        name   = f"Nueva OT: {wo.code} — {wo.service}"
        detail = _wo_detail(wo)
        for user in _wo_recipients(wo):
            Notification.objects.create(
                name=name,
                detail=detail,
                date=date,
                user=user,
                notification_type=Notification.TYPE_WORK_ORDER,
            )
    else:
        # Only notify on user-triggered saves (view sets _edited_by; system saves don't)
        if edited_by is None:
            return
        change_summary = getattr(wo, "_change_summary", None)
        name   = f"OT actualizada: {wo.code} — {wo.service}"
        detail = _wo_detail(wo, change_summary)
        for user in _wo_recipients(wo, exclude_user=edited_by):
            Notification.objects.create(
                name=name,
                detail=detail,
                date=date,
                user=user,
                notification_type=Notification.TYPE_WORK_ORDER,
            )
