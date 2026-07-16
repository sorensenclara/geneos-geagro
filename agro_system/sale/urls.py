from django.urls import path
from .views import traceability_view, traceability_excel

app_name = 'sale'

urlpatterns = [
    path('trazabilidad/', traceability_view, name='traceability'),
    path('trazabilidad/excel/', traceability_excel, name='traceability_excel'),
]
