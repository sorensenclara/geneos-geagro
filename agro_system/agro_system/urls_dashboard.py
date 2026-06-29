from django.urls import path, include

from .views.dashboard_views import DashboardView
from .views.calendar_views import CalendarView
from .views.technical_plan_views import TechnicalPlanView
from .views.alert_views import AlertView
from .views.vineyard_views import VineyardView
from .views.weather_views import WeatherView
from .views.user_views import ProducerProfileView
from .views.inputs_views import InputsView

urlpatterns = [

    path('', view=DashboardView, name='dashboard'),

    path('calendarboard',view=CalendarView, name="calendarboard"),
    path('weather',view=WeatherView, name="weather"),
    path('alert',view=AlertView, name="alert"),
    path('fields',view=VineyardView, name="vineyard"), # antes era wines 
    path('technical-plan', view=TechnicalPlanView, name="technical-plan"), # antes era kanbanboard
    path('profile/', view=ProducerProfileView.as_view(), name='producer_profile'),
    path('inputs', view=InputsView, name='inputs'),
]