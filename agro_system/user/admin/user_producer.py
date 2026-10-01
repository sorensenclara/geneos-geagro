from .user_extend import UserExtendAdmin
from user.models.user_producer import UserProducer
from user.models.user_organization import UserOrganization
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from user.admin.adminSite import adminSite
from producer.models.staff import Staff
from django.contrib import admin

class StaffInline(admin.TabularInline):
    model = Staff
    fields = ['name','surname','cuit','address','city','phone','email','type','gender','date_birth','date_entry','state','discharged']
    extra = 0


class UserProducerAdmin(UserExtendAdmin):
    """
    Administrador del modelo Usuario productor
    """

    #inlines = [StaffInline]
    list_display = ('name', 'email', 'cuit', 'address')
    fieldsets = (
        (None, {'fields': ('name', 'cuit', 'address','city', 'phone', 'organization', 'email', 'password', 'prefix', 'sequence')}),
        (_('Permissions'), {'fields': ('is_active',)}),
        ('Grupos', {'fields': ('groups',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'cuit', 'address', 'city', 'phone', 'email', 'password1', 'password2', 'is_active', 'organization', 'prefix', 'sequence')}
        ),
    )

    search_fields = ('email','name')
    ordering = ('name',)


    def save_model(self, request, obj, form, change):
        """ Verifica si el usuario logueado es del tipo 'Asociación' y se lo asigna """
        
        if hasattr(request.user, 'type') and request.user.type == 'Organization':
            userAsocciation = UserOrganization.objects.filter(email=request.user.email).first()
            obj.organization = userAsocciation
            obj.save()
        super().save_model(request, obj, form, change)
        
        producer_group, _ = Group.objects.get_or_create(name="Productor")
        if not obj.groups.filter(id=producer_group.id).exists():
            obj.groups.add(producer_group)


    def get_fieldsets(self, request, obj=None):
        """
        Modifica dinámicamente los fieldsets dependiendo del tipo de usuario logueado.
        Si el usuario logueado es del tipo 'Asociación', se oculta el campo 'organization'.
        """

        # Copia de los fieldsets por defecto
        fieldsets = super().get_fieldsets(request, obj)
        if hasattr(request.user, 'type') and request.user.type == 'Organization':
            # Quitar el campo 'organization' de los fieldsets
            fieldsets = tuple(
                (name, {'fields': [field for field in options['fields'] if field != 'organization']})
                for name, options in fieldsets
            )
        
        return fieldsets
    
    def get_queryset(self, request):
        """
        Filtrar los productores según la asociación del usuario logueado.
        """
        queryset = super().get_queryset(request)
        if hasattr(request.user, 'type') and request.user.type == 'Organization':
            return queryset.filter(organization=request.user)
        return queryset

adminSite.register(UserProducer, UserProducerAdmin)