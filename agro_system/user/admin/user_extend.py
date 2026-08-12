from ..models.user_extend import UserExtend
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from user.models import UserExtend
from user.admin.adminSite import adminSite

_GROUP_MAP = {
    'Administration': 'Administrador',
    'Producer': 'Productor',
    'Organization': 'Organizacion',
    'Staff': 'Personal',
}


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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        group_name = _GROUP_MAP.get(getattr(obj, 'type', None))
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            obj.groups.add(group)


adminSite.register(UserExtend, UserExtendAdmin)