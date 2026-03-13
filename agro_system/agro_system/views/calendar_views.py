from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required


@login_required
def CalendarView(request):
    
    data = {
    
    }

    return render(request, 'pages/calendar.html', data)
