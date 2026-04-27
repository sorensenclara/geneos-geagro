from django.contrib import admin
from user.admin.adminSite import adminSite

from alert.models.alert import Alert


class AlertAdmin(admin.ModelAdmin):

    list_display = ('name', 'crop', 'date')
    search_fields = ('name', 'crop__name')
    list_filter = ('crop', 'date')
    ordering = ('-date',)

adminSite.register(Alert, AlertAdmin)