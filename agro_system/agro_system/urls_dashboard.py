from django.urls import path, include

from .views.dashboard_views import DashboardView
from .views.calendar_views import CalendarView
from .views.technical_plan_views import TechnicalPlanView
from .views.alert_views import AlertView, AlertOutcomeView
from .views.crop_monitoring_views import VineyardView
from .views.weather_views import WeatherView
from .views.user_views import ProducerProfileView
from .views.work_order_views import WorkOrderDetailView, WorkOrderCreateView, WorkOrderQuickStateView
from .views.phenology_views import PhenologyView
from .views.report_views import CampaignComparisonView
from .views.notification_views import NotificationsView, mark_notification_read, mark_all_notifications_read
from weather.views.open_mateo import weather_open_meteo

urlpatterns = [

    path('', view=DashboardView, name='dashboard'),

    path('calendarboard',view=CalendarView, name="calendarboard"),
    path('weather',view=WeatherView, name="weather"),
    path('alert',                              view=AlertView,        name="alert"),
    path('alert/<int:alert_id>/outcome/',      view=AlertOutcomeView, name="alert-outcome"),
    path('wines',view=VineyardView, name="vineyard"), # antes era wines 
    path('technical-plan', view=TechnicalPlanView, name="technical-plan"), # antes era kanbanboard
    path('profile/', view=ProducerProfileView.as_view(), name='producer_profile'),

    path('orders/new/',                    view=WorkOrderCreateView,      name='work-order-create'),
    path('orders/<int:pk>/',              view=WorkOrderDetailView,      name='work-order-detail'),
    path('orders/<int:pk>/quick-state/',  view=WorkOrderQuickStateView,  name='work-order-quick-state'),

    path('fenologia/', view=PhenologyView, name='fenologia'),
    path('reports/campaign-comparison/', view=CampaignComparisonView, name='report-campaign-comparison'),

    path('notifications/',                        view=NotificationsView,         name='notifications-list'),
    path('notifications/<int:pk>/read/',          view=mark_notification_read,    name='notification-read'),
    path('notifications/read-all/',               view=mark_all_notifications_read, name='notifications-read-all'),

    # TODO temporal — disparar ingesta Open-Meteo manualmente desde el dashboard
    path('dev/fetch-open-meteo', view=weather_open_meteo, name='fetch_open_meteo'),
]