from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from user.admin.adminSite import adminSite
from agro_system.utils.bcr import get_quotes_bcr


@staff_member_required
def custom_admin_dashboard(request):
    precios = get_quotes_bcr()
    context = adminSite.each_context(request)
    context['precios'] = precios
    return render(request, 'admin/custom_dashboard.html', context)