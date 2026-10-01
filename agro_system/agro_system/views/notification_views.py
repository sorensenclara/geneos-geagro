from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from user.models.notification import Notification


def _unread_count(user):
    return Notification.objects.filter(user=user, read=False).count()


def _done(request):
    """Respuesta de las acciones: JSON para el JS (actualiza el contador sin recargar) o redirect."""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'unread_count': _unread_count(request.user)})
    # Solo se redirige a direcciones de este mismo sitio
    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                                   require_https=request.is_secure()):
        return redirect(next_url)
    return redirect('notifications')


@login_required
def NotificationsView(request):
    """Todas las notificaciones del usuario logueado, con filtro Todas / No leídas."""
    only_unread = request.GET.get('status') == 'unread'
    notifications = Notification.objects.filter(user=request.user)
    if only_unread:
        notifications = notifications.filter(read=False)

    page = Paginator(notifications, 25).get_page(request.GET.get('page'))
    return render(request, 'pages/notifications.html', {
        'page': page,
        'only_unread': only_unread,
        'total_count': Notification.objects.filter(user=request.user).count(),
    })


@login_required
@require_POST
def notification_mark_read(request, pk):
    # Filtra por usuario: nadie puede marcar notificaciones ajenas (404)
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if not notification.read:
        notification.read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['read', 'read_at'])
    return _done(request)


@login_required
@require_POST
def notification_mark_all_read(request):
    Notification.objects.filter(user=request.user, read=False).update(read=True, read_at=timezone.now())
    return _done(request)
