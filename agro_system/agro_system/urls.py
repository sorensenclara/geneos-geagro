"""
URL configuration for agro_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from agro_system import views
from user.admin.adminSite import adminSite
from agro_system.admin_dashboard import custom_admin_dashboard
from django.views.generic import RedirectView
from operation.views import calendar_json, calendar_view
from django.contrib.auth.decorators import login_required
from .views.user_views import MyPasswordChangeView, MyPasswordSetView
from weather.views import weather_ingest


urlpatterns = [
    path('admin/dashboard/', custom_admin_dashboard, name='custom_admin_dashboard'),  # Usa la vista correcta
    path('admin/', RedirectView.as_view(url='/admin/dashboard/')),
    path('admin/', adminSite.urls),
    path('api/', include('agro_system.api_urls'), name='apisUrls'), # urls de las apis
    path('user/', include('user.urls'), name='userUrls'), # urls de usuario
    path('input/', include('input.urls'), name='inputUrls'), # urls de insumos
    path('operation/', include('operation.urls'), name='operationsUrls'), # urls de operaciones
    path('json/', calendar_json, name='calendar_json'),
    path('calendar/', calendar_view, name='calendar_view'),
    #path('dashboard/', views.dashboard, name='dashboard'),
    


    path("api/report/", weather_ingest),  #OBTENER CLIMA DESDE LA API EXTERNA Y GUARDARLO EN LA BASE DE DATOS


    # Dashboard
    path('', include('agro_system.urls_dashboard'), name='dashboard'),

    # =========================
    # Account / Auth
    # =========================
    path(
        "account/password/change/",
        login_required(MyPasswordChangeView.as_view()),
        name="account_change_password",
    ),
    path(
        "account/password/set/",
        login_required(MyPasswordSetView.as_view()),
        name="account_set_password",
    ),
    path("account/", include("allauth.urls")),


]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)