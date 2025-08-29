from .userExtend import UserExtendAdmin
from user.models.userOrganization import UserOrganization
from django.contrib.auth.models import Group
from user.admin.adminSite import adminSite

class UserOrganizationAdmin(UserExtendAdmin):
    """
    Administrador del modelo Usuario Organizacion
    """


    list_display = ('company_name', 'email', 'identification_number', 'address')
    fieldsets = (
        (None, {'fields': ('company_name', 'identification_number', 'address','email', 'password')}),
        ('Permissions', {'fields': ('is_active',)}),
        ('Permisos', {'fields': ('groups',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('company_name', 'identification_number', 'address','email', 'password1', 'password2', 'is_active')}
        ),
    )

    search_fields = ('email','company_name', 'identification_number', 'address')
    ordering = ('company_name',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        organization_group, _ = Group.objects.get_or_create(name="Organizacion")
        if not obj.groups.filter(id=organization_group.id).exists():
            obj.groups.add(organization_group)
    


adminSite.register(UserOrganization, UserOrganizationAdmin)