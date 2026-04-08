from django.contrib import admin
from user.admin.adminSite import adminSite

from alert.models.indicator import  Indicator


class IndicatorAdmin(admin.ModelAdmin):

    list_display = ('name', 'variable_one', 'variable_two', 'variable_three')
    search_fields = ('name', 'variable_one__name', 'variable_two__name', 'variable_three__name')
    list_filter = ('variable_one', 'variable_two', 'variable_three')


adminSite.register(Indicator, IndicatorAdmin)