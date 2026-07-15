from django.urls import path
from .views import WorkOrderPDFView, input_report_view, budget_vs_real_view, input_report_excel, budget_vs_real_excel, work_orders_report_view, work_orders_report_excel

app_name = 'operation'

urlpatterns = [
    path('', WorkOrderPDFView, name='work_orders_pdf'),
    path('informe-insumos/', input_report_view, name='input_report'),
    path('informe-insumos/excel/', input_report_excel, name='input_report_excel'),
    path('informe-presupuesto/', budget_vs_real_view, name='budget_vs_real'),
    path('informe-presupuesto/excel/', budget_vs_real_excel, name='budget_vs_real_excel'),
    path('ordenes/', work_orders_report_view, name='work_orders_report'),
    path('ordenes/excel/', work_orders_report_excel, name='work_orders_report_excel'),
]
