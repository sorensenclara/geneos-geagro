from django.contrib import admin
from .userExtend import UserExtendAdmin
from user.models.userProducer import UserProducer
from user.models.userOrganization import UserOrganization
from django.contrib.auth.models import Group


class UserProducerAdmin(UserExtendAdmin):
    """
    Administrador del modelo Usuario productor
    """

    list_display = ('name', 'email', 'identification_number', 'address')
    fieldsets = (
        (None, {'fields': ('name', 'identification_number', 'address', 'association', 'email', 'password', 'prefix', 'sequence')}),
        ('Permissions', {'fields': ('is_active',)}),
        ('Grupos', {'fields': ('groups',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'identification_number', 'address', 'email', 'password1', 'password2', 'is_active', 'association', 'prefix', 'sequence')}
        ),
    )

    search_fields = ('email','name')
    ordering = ('name',)


    def save_model(self, request, obj, form, change):
        """ Verifica si el usuario logueado es del tipo 'Asociación' y se lo asigna """
        
        if hasattr(request.user, 'type') and request.user.type == 'Organization':
            userAsocciation = UserOrganization.objects.filter(email=request.user.email).first()
            obj.association = userAsocciation
            obj.save()
        super().save_model(request, obj, form, change)
        
        producer_group, _ = Group.objects.get_or_create(name="Productor")
        if not obj.groups.filter(id=producer_group.id).exists():
            obj.groups.add(producer_group)


    def get_fieldsets(self, request, obj=None):
        """
        Modifica dinámicamente los fieldsets dependiendo del tipo de usuario logueado.
        Si el usuario logueado es del tipo 'Asociación', se oculta el campo 'association'.
        """

        # Copia de los fieldsets por defecto
        fieldsets = super().get_fieldsets(request, obj)
        if hasattr(request.user, 'type') and request.user.type == 'Organization':
            # Quitar el campo 'association' de los fieldsets
            fieldsets = tuple(
                (name, {'fields': [field for field in options['fields'] if field != 'association']})
                for name, options in fieldsets
            )
        
        return fieldsets
    
    def get_queryset(self, request):
        """
        Filtrar los productores según la asociación del usuario logueado.
        """
        queryset = super().get_queryset(request)
        if hasattr(request.user, 'type') and request.user.type == 'Organization':
            return queryset.filter(association=request.user)
        return queryset

admin.site.register(UserProducer, UserProducerAdmin)