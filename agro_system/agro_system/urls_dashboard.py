from django.urls import path, include

from .views.dashboard_views import dashboardView
from .views.calendar_views import CalendarView
from .views.technical_plan_views import TechnicalPlanView
from .views.alert_views import AlertView
from .views.vineyard_views import VineyardView
from .views.weather_views import WeatherView


urlpatterns = [

    path('', view=dashboardView, name='dashboard'),

    path('calendarboard',view=CalendarView, name="calendarboard"),
    path('weather',view=WeatherView, name="weather"),
    path('alert',view=AlertView, name="alert"),
    path('wines',view=VineyardView, name="vineyard"), # antes era wines 
    path('technical-plan', view=TechnicalPlanView, name="technical-plan") # antes era kanbanboard

]