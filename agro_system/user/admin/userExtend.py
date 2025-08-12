from django.contrib import admin
from ..models.userExtend import UserExtend
from django.contrib.auth.admin import UserAdmin
from user.models import UserExtend


class UserExtendAdmin(UserAdmin):
    """
    Administrador del modelo Usuario Extendido
    """


    list_display = ('email','first_name', 'last_name','type')
    fieldsets = (
        (None, {'fields': ('email', 'password','first_name', 'last_name','type')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
        ('Permisos', {'fields': ('groups','user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2',  'first_name', 'last_name', 'is_staff', 'is_active', 'groups','user_permissions', 'type')}
        ),
    )

    search_fields = ('email',)
    ordering = ('email',)
    list_filter = ('groups','type')
    

admin.site.register(UserExtend, UserExtendAdmin)