from django.contrib import admin
from weather.models.weather_data import WeatherData
from user.admin.adminSite import adminSite


adminSite.register(WeatherData)