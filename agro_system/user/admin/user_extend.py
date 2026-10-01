from ..models.user_extend import UserExtend
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from user.models import UserExtend
from user.admin.adminSite import adminSite

class UserExtendAdmin(UserAdmin):
    """
    Administrador del modelo Usuario Extendido
    """


    list_display = ('email','first_name', 'last_name','type')
    fieldsets = (
        (None, {'fields': ('email', 'password','first_name', 'last_name','type')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active')}),
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
    

adminSite.register(UserExtend, UserExtendAdmin)