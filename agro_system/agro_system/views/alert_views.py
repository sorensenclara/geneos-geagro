from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from user.models.notification import Notification

@login_required
def AlertView(request):
    
    user = request.user
    if user.type == 'Producer':
        notifications = Notification.objects.filter(user=user).order_by('-date')
    elif user.type == 'Administration':
        notifications = Notification.objects.all().order_by('-date')
    data = {
        'notifications': notifications  
    }

    return render(request, 'pages/alert.html', data)
