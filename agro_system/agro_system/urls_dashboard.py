from django.urls import path, include

from .views.dashboard_views import DashboardView
from .views.calendar_views import CalendarView
from .views.technical_plan_views import TechnicalPlanView
from .views.alert_views import AlertView
from .views.crop_monitoring_views import VineyardView
from .views.weather_views import WeatherView
from .views.user_views import ProducerProfileView
from .views.work_order_views import WorkOrderDetailView, WorkOrderCreateView
from weather.views.open_mateo import weather_open_meteo

urlpatterns = [

    path('', view=DashboardView, name='dashboard'),

    path('calendarboard',view=CalendarView, name="calendarboard"),
    path('weather',view=WeatherView, name="weather"),
    path('alert',view=AlertView, name="alert"),
    path('wines',view=VineyardView, name="vineyard"), # antes era wines 
    path('technical-plan', view=TechnicalPlanView, name="technical-plan"), # antes era kanbanboard
    path('profile/', view=ProducerProfileView.as_view(), name='producer_profile'),

    path('orders/new/',      view=WorkOrderCreateView,  name='work-order-create'),
    path('orders/<int:pk>/', view=WorkOrderDetailView,  name='work-order-detail'),

    # TODO temporal — disparar ingesta Open-Meteo manualmente desde el dashboard
    path('dev/fetch-open-meteo', view=weather_open_meteo, name='fetch_open_meteo'),
]