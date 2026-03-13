from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from xhtml2pdf import pisa
from user.models.user_producer import UserProducer
from input.models.purchase_order_detail import PurchaseOrderDetail
from input.models.purchase_order import PurchaseOrder
from django.contrib import messages 

def InputPendingPDFView(request):

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