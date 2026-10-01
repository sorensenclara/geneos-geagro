from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from user.models.notification import Notification


@login_required
def NotificationsView(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-id")
    return render(request, "pages/notifications.html", {"notifications": notifications})


@login_required
@require_POST
def mark_notification_read(request, pk):
    Notification.objects.filter(pk=pk, user=request.user).update(is_read=True)
    return JsonResponse({"ok": True})


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"ok": True})
