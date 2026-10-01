from django.contrib import admin
from producer.models.store import Store
from user.admin.adminSite import adminSite
from user.admin.producer_scope import producers_for, visible_stores


class StoreAdmin(admin.ModelAdmin):
    """
    - Cada productor (y su personal) ve sus almacenes y los que no tienen productor (compartidos).
    - Al crear un almacén, se le asigna automáticamente el productor del usuario.
    - El campo productor solo lo ve y lo edita el superusuario.
    - Los compartidos solo los modifica superusuario / Administración (nadie se los apropia).
    """
    list_display = ['name', 'address', 'city', 'default']

    def get_list_display(self, request):
        cols = list(super().get_list_display(request))
        if request.user.is_superuser:
            cols.append('producer')
        return cols

    def get_exclude(self, request, obj=None):
        excluded = list(super().get_exclude(request, obj) or [])
        if not request.user.is_superuser and 'producer' not in excluded:
            excluded.append('producer')
        return excluded

    def get_queryset(self, request):
        return super().get_queryset(request) & visible_stores(request.user)

    def save_model(self, request, obj, form, change):
        # Al crear lo crea un productor (o su personal): queda asignado a ese productor
        if not change and not request.user.is_superuser:
            producers = producers_for(request.user)
            if producers is not None and producers.count() == 1:
                obj.producer = producers.first()
        super().save_model(request, obj, form, change)

    def _is_shared_readonly(self, request, obj):
        return (obj is not None and obj.producer_id is None
                and producers_for(request.user) is not None)

    def has_change_permission(self, request, obj=None):
        if self._is_shared_readonly(request, obj):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if self._is_shared_readonly(request, obj):
            return False
        return super().has_delete_permission(request, obj)


adminSite.register(Store, StoreAdmin)
