from django.urls import path, include

from .views.dashboard_views import DashboardView
from .views.calendar_views import CalendarView
from .views.technical_plan_views import TechnicalPlanView
from .views.alert_views import AlertView
from .views.vineyard_views import VineyardView
from .views.weather_views import WeatherView
from .views.user_views import ProducerProfileView
from .views.inputs_views import InputsView
from .views.notification_views import NotificationsView, notification_mark_read, notification_mark_all_read

urlpatterns = [

    path('', view=DashboardView, name='dashboard'),

    path('calendarboard',view=CalendarView, name="calendarboard"),
    path('weather',view=WeatherView, name="weather"),
    path('alert',view=AlertView, name="alert"),
    path('fields',view=VineyardView, name="vineyard"), # antes era wines 
    path('technical-plan', view=TechnicalPlanView, name="technical-plan"), # antes era kanbanboard
    path('profile/', view=ProducerProfileView.as_view(), name='producer_profile'),
    path('inputs', view=InputsView, name='inputs'),
    path('notifications', view=NotificationsView, name='notifications'),
    path('notifications/<int:pk>/read', view=notification_mark_read, name='notification_mark_read'),
    path('notifications/read-all', view=notification_mark_all_read, name='notification_mark_all_read'),
]