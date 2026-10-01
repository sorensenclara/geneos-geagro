from django.contrib import admin
from user.admin.adminSite import adminSite

from alert.models.variable_register import VariableRegister


class VariableRegisterAdmin(admin.ModelAdmin):

    list_display = ('name', 'variable', 'date', 'value')
    search_fields = ('name', 'variable__name')
    list_filter = ('variable', 'date')
    ordering = ('-date',)

#adminSite.register(VariableRegister, VariableRegisterAdmin)
