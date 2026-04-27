from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from user.models.notification import Notification
from producer.models.staff import Staff
from operation.models.crop import Crop
from alert.models.alert import Alert

@login_required
def AlertView(request):
    
    crop_id = request.GET.get('crop')
    user = request.user
    staff = None
    if user.type == 'Producer':
        staff = Staff.objects.filter(producer=user)
        crops = Crop.objects.filter(producer=user)
    elif user.type == 'Staff':
        crops = Crop.objects.filter(responsible__user=user)
    elif user.type == 'Administration':
        crops = Crop.objects.all()
    else:
        crops = Crop.objects.none()

    # Cultivo seleccionado o principal
    crop_selected = None
    if crop_id:
        crop_selected = crops.filter(id=crop_id).first()
    else:
        crop_selected = crops.filter(is_main=True).first() or crops.first()

    # Filtrar alertas y notificaciones por cultivo
    alerts = Alert.objects.none()
    notifications = Notification.objects.none()
    if crop_selected:
        alerts = Alert.objects.filter(crop=crop_selected).order_by('-date')
        if user.type == 'Producer':
            staff_users = staff.values('user') if staff is not None else []
            notifications = Notification.objects.filter(user__in=staff_users).order_by('-date')
        elif user.type == 'Staff':
            notifications = Notification.objects.filter(user=user).order_by('-date')
        elif user.type == 'Administration':
            notifications = Notification.objects.all().order_by('-date')
    elif user.type == 'Administration':
        alerts = Alert.objects.all().order_by('-date')
        notifications = Notification.objects.all().order_by('-date')

    data = {
        'notifications': notifications,
        'alerts': alerts,
        'crop_main': crop_selected,
        'crops': crops,
    }

    return render(request, 'pages/alert.html', data)
