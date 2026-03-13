from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required


@login_required
def WeatherView(request):
    
    data = {
    
    }

    return render(request, 'pages/weather.html', data)