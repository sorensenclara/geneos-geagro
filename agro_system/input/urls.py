from django.urls import path
from .views import InputPendingPDFView, input_charts_view

app_name = 'input'

urlpatterns = [
    path('pending-pdf/', InputPendingPDFView, name='input_pending_pdf'),
    path('charts/', input_charts_view, name='input_charts'),
]
