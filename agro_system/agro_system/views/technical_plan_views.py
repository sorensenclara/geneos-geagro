from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from operation.models.technical_plan import TechnicalPlan
from operation.models.technical_plan_input import TechnicalPlanInput
from operation.models.technical_plan_detail import TechnicalPlanDetail


@login_required
def TechnicalPlanView(request):

    user = request.user

    # Filtrado por tipo de usuario
    if user.type == 'Producer':
        technical_plans = TechnicalPlan.objects.filter(producer=user)
    elif user.type == 'Administration':
        technical_plans = TechnicalPlan.objects.all()
    else:
        technical_plans = TechnicalPlan.objects.none()

    if not technical_plans.exists():
        return redirect('dashboard')

    data = []

    for plan in technical_plans:

        technical_plan_details = TechnicalPlanDetail.objects.filter(technical_plan=plan)
        technical_plan_inputs = TechnicalPlanInput.objects.filter(technical_plan=plan)

        data_plan = {
            'technical_plan': plan,
            'technical_plan_details': technical_plan_details,
            'technical_plan_inputs': technical_plan_inputs,
        }

        data.append(data_plan)

    return render(request, 'pages/plan.html', {'data_plan': data})