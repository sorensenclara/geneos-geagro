from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from producer.models.lot import Lot
from parameter.models.campaign import Campaing
from producer.models.country_side import Countryside
from django.views.generic import TemplateView
from operation.models.technical_plan import TechnicalPlan
from operation.models.work_order import WorkOrder
from producer.models.staff import Staff


@login_required
def VineyardView(request):
    

    user = request.user
    if user.type == 'Producer':
        country_sides = Countryside.objects.filter(producer=user)
        technical_plans = TechnicalPlan.objects.filter(producer=user)
        staff = Staff.objects.filter(producer=user)

    elif user.type == 'Administration':
        country_sides = Countryside.objects.all()
        technical_plans = TechnicalPlan.objects.all()
        staff = Staff.objects.all()
    else:
        country_sides = Countryside.objects.none()
        technical_plans = TechnicalPlan.objects.none()
        staff = Staff.objects.none()

    # Referencia a los lotes de un viñedo
    lots = Lot.objects.filter(countryside__in=country_sides)

    # TODO todas o la activa?
    # Referencia a las campañas
    campaings = Campaing.objects.all()
    

    
    data = {
        'technical_plans': technical_plans,
        'staff': staff,
        'country_sides': country_sides,
        'lots': lots,
        'campaings' : campaings,
    }

    return render(request, 'pages/vineyard.html', data)