# Para que aparezcan los grupos y permisos en el admin
from django.contrib.auth.models import Group, Permission
from django.contrib import admin

admin.site.register(Group)
admin.site.register(Permission)