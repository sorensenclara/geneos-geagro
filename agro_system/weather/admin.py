from django.contrib import admin
from .models import WeatherData
from user.admin.adminSite import adminSite


adminSite.register(WeatherData)