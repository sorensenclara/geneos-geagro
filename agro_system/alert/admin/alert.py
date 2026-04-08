from django.contrib import admin
from user.admin.adminSite import adminSite

from alert.models.alert import Alert


class AlertAdmin(admin.ModelAdmin):

    list_display = ('name', 'indicator', 'date')
    search_fields = ('name', 'indicator__name')
    list_filter = ('indicator', 'date')
    ordering = ('-date',)

adminSite.register(Alert, AlertAdmin)