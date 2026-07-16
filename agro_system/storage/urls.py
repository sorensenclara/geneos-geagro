from django.urls import path
from .views import (
    acopio_ledger_view, acopio_ledger_excel,
    stock_position_view, stock_position_excel,
    conciliation_view, conciliation_excel,
    storage_cost_view, storage_cost_excel,
    aging_view, aging_excel,
)

app_name = 'storage'

urlpatterns = [
    path('acopio/', acopio_ledger_view, name='acopio_ledger'),
    path('acopio/excel/', acopio_ledger_excel, name='acopio_ledger_excel'),
    path('posicion/', stock_position_view, name='stock_position'),
    path('posicion/excel/', stock_position_excel, name='stock_position_excel'),
    path('conciliacion/', conciliation_view, name='conciliation'),
    path('conciliacion/excel/', conciliation_excel, name='conciliation_excel'),
    path('costos/', storage_cost_view, name='storage_cost'),
    path('costos/excel/', storage_cost_excel, name='storage_cost_excel'),
    path('antiguedad/', aging_view, name='aging'),
    path('antiguedad/excel/', aging_excel, name='aging_excel'),
]
