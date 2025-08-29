from django.urls import path
from .views import WorkOrderPDFView

app_name = 'operation'

urlpatterns = [
    path('', WorkOrderPDFView, name='work_orders_pdf'),
    #path('estadisticas/', EstadisticasView, name='estadisticas'),

]


