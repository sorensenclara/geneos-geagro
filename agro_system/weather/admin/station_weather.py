from django.contrib import admin
from weather.models.station_weather import WeatherStation
from user.admin.adminSite import adminSite


adminSite.register(WeatherStation)