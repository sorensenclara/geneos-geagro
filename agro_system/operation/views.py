from django.shortcuts import render
from operation.models.work_order import WorkOrder
from django.http import HttpResponse, HttpResponseRedirect
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages 


def WorkOrderPDFView(request):

    # Recupera los registros correspondientes a las ordenes

    ids = request.GET.get('ids')
    ids_list = ids.split(',') if ids else []
    orders = WorkOrder.objects.filter(id__in=ids_list)
    if orders:
        # Renderiza la plantilla HTML y pasa el queryset como contexto
        context = {'orders': orders}

        template_path = 'operations/report_work_order.html'
        # Create a Django response object, and specify content_type as pdf
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte-ordenes-trabajo.pdf"'
        # find the template and render it.
        template = get_template(template_path)
        html = template.render(context)

        # create a pdf
        pisa_status = pisa.CreatePDF(
        html, dest=response)
        # if error then show some funny view
        if pisa_status.err:
            return HttpResponse('Errores: <pre>' + html + '</pre>')
        return response

    else:
        messages.error(request, "No hay pendientes para generar el reporte.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def calendar_json(request):
    orders = WorkOrder.objects.all()
    data = []
    for order in orders:
        data.append({
            'title': f"{order.code} ({order.producer} - {order.campaing})",
            'start': order.init_order.isoformat(),
            'url': f'/admin/operations/workorder/{order.id}/change/',  # Opcional: enlace al admin
        })
    return JsonResponse(data, safe=False)


@login_required
def calendar_view(request):
    return render(request, 'operations/calendar.html')
