from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from producer.models.lot import Lot
from parameter.models.campaign import Campaing
from producer.models.country_side import Countryside
from django.views.generic import TemplateView
from operation.models.technical_plan import TechnicalPlan
from operation.models.work_order import WorkOrder
from producer.models.staff import Staff
from operation.models.crop import Crop

@login_required
def VineyardView(request):
    

    user = request.user
  
    if user.type == 'Producer':
        country_sides = Countryside.objects.filter(producer=user)
        technical_plans = TechnicalPlan.objects.filter(producer=user)
        staff = Staff.objects.filter(producer=user)
        crops = Crop.objects.filter(producer=user)
    elif user.type == 'Staff':
        # Buscar el productor asociado al staff
        staff_instance = Staff.objects.filter(user=user).first()
        if staff_instance and staff_instance.producer:
            producer = staff_instance.producer
            country_sides = Countryside.objects.filter(producer=producer)
            technical_plans = TechnicalPlan.objects.filter(producer=producer)
            staff = Staff.objects.filter(producer=producer)
            crops = Crop.objects.filter(producer=producer)
        else:
            country_sides = Countryside.objects.none()
            technical_plans = TechnicalPlan.objects.none()
            staff = Staff.objects.none()
            crops = Crop.objects.none()
    elif user.type == 'Administration':
        country_sides = Countryside.objects.all()
        technical_plans = TechnicalPlan.objects.all()
        staff = Staff.objects.all()
        crops = Crop.objects.all()
    else:
        country_sides = Countryside.objects.none()
        technical_plans = TechnicalPlan.objects.none()
        staff = Staff.objects.none()
        crops = Crop.objects.none()

    # Referencia a los lotes de un viñedo
    lots = Lot.objects.filter(countryside__in=country_sides)

    # Referencia a las campañas
    campaings = Campaing.objects.all()

    data = {
        'technical_plans': technical_plans,
        'staff': staff,
        'country_sides': country_sides,
        'lots': lots,
        'crops': crops,
        'campaings': campaings,
    }

    return render(request, 'pages/vineyard.html', data)