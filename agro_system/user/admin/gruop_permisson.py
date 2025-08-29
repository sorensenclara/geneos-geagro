# Para que aparezcan los grupos y permisos en el admin
from django.contrib.auth.models import Group, Permission
from user.admin.adminSite import adminSite 


adminSite.register(Group)
adminSite.register(Permission)