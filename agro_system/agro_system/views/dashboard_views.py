from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from producer.models.lot import Lot
from parameter.models.campaign import Campaing
from producer.models.country_side import Countryside
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required


# Panel principal
@login_required
def dashboardView(request):
    user = request.user
    # Referencia a los viñedos o campos 

    # TODO CONTROLA EL USUARIO   producter=user
    country_sides = Countryside.objects.all()
    
    # Referencia a los lotes de un viñedo
    lots = Lot.objects.all()
    # Referencia a las campañas
    campaings = Campaing.objects.filter()
    
    
    data = {
        'country_sides' : country_sides,
        'lots': lots,
        'campaings' : campaings
    }

    return render(request, 'pages/dashboard.html', data)



class DashboardView(LoginRequiredMixin,TemplateView):
    pass


#kanbanboard_view = DashboardView.as_view(template_name = "pages/plan.html")
#calendar_front_view = DashboardView.as_view(template_name = "pages/calendar.html")
#weather_view = DashboardView.as_view(template_name = "pages/weather.html")
#alert_view = DashboardView.as_view(template_name = "pages/alert.html")
#wines_view = DashboardView.as_view(template_name = "pages/wines.html") #vineyard