from django.urls import path
from .views import InputPendingPDFView, input_charts_view, input_cost_api, exchange_rate_api

app_name = 'input'

urlpatterns = [
    path('pending-pdf/', InputPendingPDFView, name='input_pending_pdf'),
    path('charts/', input_charts_view, name='input_charts'),
    path('api/cost/', input_cost_api, name='input_cost_api'),
    path('api/exchange-rate/', exchange_rate_api, name='exchange_rate_api'),
]
