from django.contrib import admin
from django.db.models import Q
from user.admin.adminSite import adminSite, ProducerAwareMixin, UniqueNamePerProducerAdminMixin, get_producer_for_request
from producer.models.cost_center import CostCenter
from producer.models.typeStaff import TypeStaff
# Register your models here.

class CostCenterAdmin(UniqueNamePerProducerAdminMixin, ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['name', 'default', 'producer']

    def save_model(self, request, obj, form, change):
        # Asigna por defecto el usuario productor logueado (solo al crear,
        # para no apropiarse de un centro de costo compartido)
        if not change:
            userProducer = get_producer_for_request(request)
            if userProducer:
                obj.producer = userProducer
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        # Cada productor ve sus centros de costo y los compartidos (sin productor)
        queryset = super().get_queryset(request)
        producers = self._producers_for_user(request)
        if producers is None:
            return queryset
        return queryset.filter(Q(producer__in=producers) | Q(producer__isnull=True))

    def _is_shared_readonly(self, request, obj):
        # Los centros de costo compartidos solo los modifica Administración
        return (obj is not None and obj.producer_id is None
                and self._producers_for_user(request) is not None)

    def has_change_permission(self, request, obj=None):
        if self._is_shared_readonly(request, obj):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if self._is_shared_readonly(request, obj):
            return False
        return super().has_delete_permission(request, obj)


adminSite.register(CostCenter, CostCenterAdmin)
adminSite.register(TypeStaff)