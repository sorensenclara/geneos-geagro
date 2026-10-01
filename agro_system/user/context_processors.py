from user.models.notification import Notification


def user_notifications(request):
    if not request.user.is_authenticated:
        return {}
    qs = Notification.objects.filter(user=request.user).order_by("-id")
    unread = qs.filter(is_read=False)
    return {
        "user_notifications":       unread[:5],
        "user_notifications_count": unread.count(),
    }
