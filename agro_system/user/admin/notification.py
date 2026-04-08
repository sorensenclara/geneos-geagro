from django.contrib import admin
from user.admin.adminSite import adminSite

from user.models.notification import Notification


class NotificationAdmin(admin.ModelAdmin):

    list_display = ('name', 'user', 'date', 'detail')
    search_fields = ('name', 'user__username')
    list_filter = ('user', 'date')
    ordering = ('-date',)

adminSite.register(Notification, NotificationAdmin)
