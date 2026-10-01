from django.contrib import admin
from django.db.models import Q
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from sale.models.carrier_provider import Carrier
from sale.models.driver import Driver


class DriverInline(admin.TabularInline):
    model = Driver
    fields = ['name','cuit','address','city','phone','email']
    extra = 0


@admin.register(Carrier)
class CarrierAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ["name", "cuit", "address", "city", "phone", "email"]
    search_fields = ["name", "cuit", "address", "city__name", "phone", "email"]
    inlines = [DriverInline]

    def save_model(self, request, obj, form, change):
        # Asigna el productor logueado solo al crear (para no apropiarse de uno compartido)
        if not change:
            user_producer = get_producer_for_request(request)
            if user_producer:
                obj.producer = user_producer
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        # Transportistas del productor y los compartidos (sin productor)
        qs = super().get_queryset(request).filter(type__name="Transportista")
        producers = self._producers_for_user(request)
        if producers is None:
            return qs
        return qs.filter(Q(producer__in=producers) | Q(producer__isnull=True))

    def _is_shared_readonly(self, request, obj):
        # Los transportistas compartidos solo los modifica Administración
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
    
    
adminSite.register(Carrier, CarrierAdmin)