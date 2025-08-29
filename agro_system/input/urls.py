from django.urls import path
from .views import InputPendingPDFView

app_name = 'input'

urlpatterns = [
    path('', InputPendingPDFView, name='input_pending_pdf'),
]
