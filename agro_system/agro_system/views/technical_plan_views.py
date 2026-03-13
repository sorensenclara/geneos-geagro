from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from operation.models.technical_plan import TechnicalPlan
from operation.models.technical_plan_input import TechnicalPlanInput
from operation.models.technical_plan_detail import TechnicalPlanDetail

@login_required
def TechnicalPlanView(request):
    
    # TODO CONTROLA EL USUARIO   producter=user
    technical_plan = TechnicalPlan.objects.all()
    technical_plan_inputs = TechnicalPlanInput.objects.filter(technical_plan__in=technical_plan)
    technical_plan_details = TechnicalPlanDetail.objects.filter(technical_plan__in=technical_plan)
    data = {
        'technical_plan': technical_plan,
        'technical_plan_inputs': technical_plan_inputs,
        'technical_plan_details': technical_plan_details

    }

    return render(request, 'pages/plan.html', data)