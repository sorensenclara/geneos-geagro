from django.contrib import admin, messages
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from user.models.user_producer import UserProducer
from sale.models.sales_receipt import SalesReceipt
from sale.models.sale_stock_allocation import SaleStockAllocation
from storage.models.silo_movement import SiloMovement
from storage.models.storage_movement import StorageMovement


class SaleStockAllocationInline(ProducerAwareMixin, admin.TabularInline):
    model = SaleStockAllocation
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        from storage.models.silo_stock import SiloStock
        from storage.models.storage_certificate import StorageCertificate
        producers = self._producers_for_user(request)
        if producers is not None:
            if db_field.name == 'silo_stock':
                kwargs['queryset'] = SiloStock.objects.filter(silo__producer__in=producers)
            elif db_field.name == 'certificate':
                kwargs['queryset'] = StorageCertificate.objects.filter(producer__in=producers)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request, obj=None):
        if obj and obj.state == 'confirm':
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.state == 'confirm':
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.state == 'confirm':
            return False
        return super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.state == 'confirm':
            return [field.name for field in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)


@admin.action(description=_("Confirmar venta"))
def confirmar_venta(modeladmin, request, queryset):
    if queryset.filter(state='confirm').exists():
        messages.error(request, _("Solo se pueden confirmar ventas que no estén ya confirmadas."))
        return

    for obj in queryset:
        allocations = SaleStockAllocation.objects.filter(sales_receipt=obj)
        total_asignado = allocations.aggregate(t=Sum('quantity_tons'))['t'] or 0

        if abs(total_asignado - obj.amount) > 0.01:
            messages.error(
                request,
                _("La venta %(number)s no se confirmó: lo asignado (%(asignado).2f tn) "
                  "no coincide con la cantidad vendida (%(cantidad).2f tn).")
                % {'number': obj.number, 'asignado': total_asignado, 'cantidad': obj.amount},
            )
            continue

        obj.state = 'confirm'
        obj.save()

        for alloc in allocations:
            if alloc.silo_stock_id:
                SiloMovement.objects.create(
                    silo=alloc.silo_stock.silo,
                    crop=alloc.silo_stock.crop,
                    type=SiloMovement.EXIT,
                    quantity_tons=alloc.quantity_tons,
                    related_sale=obj,
                    producer=obj.producer,
                )
            else:
                StorageMovement.objects.create(
                    certificate=alloc.certificate,
                    type=StorageMovement.SALE_EXIT,
                    quantity_tons=alloc.quantity_tons,
                    related_sale=obj,
                    producer=obj.producer,
                )
        messages.success(request, _("Venta %s confirmada.") % obj.number)


class SalesReceiptAdmin(ProducerAwareMixin, admin.ModelAdmin):

    list_display = ['date','type','number','name_custom','cuit_custom','especie','amount','subtotal','taxes','state']
    list_filter = ['type','especie','state']
    search_fields = ['type','number','name_custom','cuit_custom','especie']
    inlines = [SaleStockAllocationInline]
    actions = [confirmar_venta]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        producers = self._producers_for_user(request)
        if producers is not None:
            from django.db.models import Q
            if db_field.name == 'cost_center':
                from producer.models.cost_center import CostCenter
                kwargs['queryset'] = CostCenter.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))
            elif db_field.name == 'provider':
                from input.models.provider import Provider
                kwargs['queryset'] = Provider.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))
            elif db_field.name == 'driver':
                # El chofer pertenece a un transportista: se ven los de transportistas propios o compartidos
                from sale.models.driver import Driver
                kwargs['queryset'] = Driver.objects.filter(
                    Q(provider__producer__in=producers) | Q(provider__producer__isnull=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Asigna por defecto el usuario productor logueado
        userProducer = get_producer_for_request(request)
        if userProducer:
            obj.producer = userProducer
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.state == 'confirm':
            return [field.name for field in obj._meta.fields]
        return super().get_readonly_fields(request, obj)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)     
        if request.user.is_superuser:
            return queryset
        if request.user.type == 'Administration':
            return queryset
        if request.user.type == 'Organization':
            userProducer = UserProducer.objects.filter(organization=request.user)
            if userProducer.exists():
                return queryset.filter(producer__in=userProducer)
        if request.user.type in ('Producer', 'Staff'):
            userProducer = get_producer_for_request(request)
            if userProducer:
                return queryset.filter(producer=userProducer)
        return queryset.none()


adminSite.register(SalesReceipt, SalesReceiptAdmin)