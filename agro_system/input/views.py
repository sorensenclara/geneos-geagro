import json
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.shortcuts import render
from django.db.models import F
from user.models.user_producer import UserProducer
from input.models.purchase_order_detail import PurchaseOrderDetail
from input.models.purchase_order import PurchaseOrder
from input.models.input import Input
from input.models.purchase_reception_detail import PurchaseReceptionDetail
from operation.models.input_work_order import InputWorkOrder
from django.contrib import messages 
from django.utils.translation import gettext_lazy as _

def input_charts_view(request):
    # Muestra gráficos de stock e historial de movimientos para los insumos del usuario.
    # Filtra los insumos según el tipo de usuario (Administración, Organización o Productor).
    # Si se recibe un input_id por GET, genera también un gráfico de evolución acumulada del stock.
    extra_context = {}

    # Filtro de privacidad por productor (mismo criterio que el Admin)
    queryset = Input.objects.all()
    if not request.user.is_superuser and request.user.type != 'Administration':
        if request.user.type == 'Organization':
            user_producers = UserProducer.objects.filter(association=request.user)
            if user_producers.exists():
                queryset = queryset.filter(producer__in=user_producers)
            else:
                queryset = queryset.none()
        elif request.user.type == 'Producer':
            user_producer = UserProducer.objects.filter(email=request.user.email).first()
            if user_producer:
                queryset = queryset.filter(producer=user_producer)
            else:
                queryset = queryset.none()
        else:
            queryset = queryset.none()

    all_inputs = queryset.order_by('name')

    # Gráfico General (Barras)
    chart_data_qs = queryset.order_by('-stock')[:15] # Limit to 15 for readability
    extra_context['chart_data_json'] = json.dumps({
        'labels': [i.name for i in chart_data_qs],
        'stock': [i.stock for i in chart_data_qs],
        'projected': [i.stock + i.pending for i in chart_data_qs],
        'min_stock': [getattr(i, 'min_stock', 0) for i in chart_data_qs],
    })

    # Gráfico de Evolución (Solo si se filtra un insumo específico)
    input_id = request.GET.get('input_id')
    extra_context['selected_input_id'] = input_id
    extra_context['selected_input_name'] = _("Select an input") # Default value

    if input_id:
        input_obj = Input.objects.filter(id=input_id).first()
        if input_obj:
            extra_context['selected_input_name'] = input_obj.name
            
            receptions = PurchaseReceptionDetail.objects.filter(input=input_obj, purchase_reception__state='confirm').values('amount', date=F('purchase_reception__delivery_date'))
            usages = InputWorkOrder.objects.filter(input=input_obj, work_order__stateOT__name="Finalizada").values(amount=F('dose_applied'), date=F('work_order__date_init'))
            
            all_movements = list(receptions)
            for u in usages:
                u['amount'] = float(u['amount'] or 0) * -1
                all_movements.append(u)
            
            movements = sorted([m for m in all_movements if m['date']], key=lambda x: x['date'])
            
            history_labels = [m['date'].strftime('%d/%m/%Y') for m in movements]
            history_values = [sum(float(mov['amount'] or 0) for mov in movements[:i+1]) for i in range(len(movements))] # Calculate cumulative sum
            
            extra_context['timeline_data_json'] = json.dumps({
                'labels': history_labels,
                'data': history_values,
                'name': input_obj.name,
                'min_stock': getattr(input_obj, 'min_stock', 0)
            })
    
    extra_context['all_inputs'] = all_inputs

    return render(request, 'admin/input/charts.html', extra_context)

def InputPendingPDFView(request):
    # Genera un PDF con los detalles de órdenes de compra que tienen cantidades pendientes de recepción.
    # Filtra las órdenes según el tipo de usuario y descarga el archivo directamente como adjunto.
    # Si no hay pendientes, redirige a la página anterior con un mensaje de error.

    # Recupera los registros de lineas de ordenes con pendientes
   pendings = []
   purchase = PurchaseOrder.objects.filter(state="pending")
   if request.user.is_superuser:
            pendings = PurchaseOrderDetail.objects.filter(pending_amount__gt=0,purchase_order__in=purchase)
   if request.user.type == 'Administration':
            pendings = PurchaseOrderDetail.objects.filter(pending_amount__gt=0, purchase_order__in=purchase)
   if request.user.type == 'Organization':
      userProducer = UserProducer.objects.filter(association=request.user)
      if userProducer.exists():
            purchase = purchase.filter(producer__in=userProducer)
            pendings = PurchaseOrderDetail.objects.filter(pending_amount__gt=0, purchase_order__in=purchase)
   if request.user.type == 'Producer':
         userProducer = UserProducer.objects.filter(email=request.user.email).first()
         if userProducer:
            purchase = purchase.filter(producer__in=userProducer)
            pendings = PurchaseOrderDetail.objects.filter(pending_amount__gt=0, purchase_order__in=purchase)
    
   if pendings:
      # Renderiza la plantilla HTML y pasa el queryset como contexto
      context = {'pendientes': pendings}

      template_path = 'purchase/report_purchase_pending.html'
      # Create a Django response object, and specify content_type as pdf
      response = HttpResponse(content_type='application/pdf')
      response['Content-Disposition'] = 'attachment; filename="reporte-compras-pendientes.pdf"'
      # find the template and render it.
      template = get_template(template_path)
      html = template.render(context)

      # create a pdf
      pisa_status = pisa.CreatePDF(html, dest=response)
      # if error then show some funny view
      if pisa_status.err:
         return HttpResponse('Errores: <pre>' + html + '</pre>')
      return response
   else:
      messages.error(request, "No hay pendientes para generar el reporte.")
      return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def exchange_rate_api(request):
    # API JSON que devuelve la tasa de conversión de una moneda a la moneda base.
    # Recibe currency_id por GET. Si la moneda ya es la base, devuelve rate=1.0.
    # Usado por el JS del formulario de orden de compra para autocompletar la tasa.
    currency_id = request.GET.get('currency_id')
    if not currency_id:
        return JsonResponse({'error': 'missing currency_id'}, status=400)
    try:
        from parameter.models.currency import Currency
        from parameter.models.exchange_rate import exchangeRate
        currency = Currency.objects.get(pk=currency_id)
        if currency.is_base:
            return JsonResponse({'rate': 1.0, 'is_base': True})
        rate = exchangeRate.get_rate(currency)
        return JsonResponse({'rate': rate, 'is_base': False})
    except Currency.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)


def input_cost_api(request):
    # API JSON que devuelve el costo unitario y la moneda de un insumo dado su ID.
    # Recibe id por GET. Usado por el JS de la orden de trabajo para autocompletar el valor estimado.
    input_id = request.GET.get('id')
    if not input_id:
        return JsonResponse({'error': 'missing id'}, status=400)
    try:
        inp = Input.objects.select_related('currency').get(pk=input_id)
        return JsonResponse({
            'cost': inp.cost,
            'currency': str(inp.currency) if inp.currency else '',
            'currency_id': inp.currency_id,
        })
    except Input.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)