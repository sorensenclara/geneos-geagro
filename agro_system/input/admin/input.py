from django.contrib import admin, messages
from producer.models.store import Store
from input.models.provider import Provider
from user.models.user_producer import UserProducer
from user.admin.adminSite import adminSite
from input.models.purchase_order import PurchaseOrder
from input.models.purchase_order_detail import PurchaseOrderDetail
from input.models.input import Input
from django.utils.translation import gettext_lazy as _, gettext


class PurchaseInline(admin.StackedInline):
    model = PurchaseOrderDetail
    can_delete = False
    extra = 0
    fields = ['date_order', 'amount', 'price_unit']
    readonly_fields = ['date_order', 'amount', 'price_unit']

    def date_order(self, obj):
        return obj.purchase_order.date if obj.purchase_order else None

    date_order.short_description = _('Order Date')
    
    verbose_name_plural = _("Purchases")
    verbose_name = _("Purchase")

    def has_add_permission(self, request, obj=None):
        return False


class InputAdmin(admin.ModelAdmin):
    search_fields = ['name'] 
    inlines = [PurchaseInline]
    list_display = ['name', 'type', 'cost', 'stock', 'min_stock', 'pending', 'producer']
    list_filter = ['type', 'unit_measure', 'currency']
    readonly_fields = ['pending']
    
    def save_model(self, request, obj, form, change):
        # Asigna por defecto el usuario productor logueado
        userProducer = UserProducer.objects.filter(email=request.user.email).first()
        if userProducer:
            obj.producer = userProducer
        super().save_model(request, obj, form, change)

        # Lógica de reorden automático (trasladada desde señales para usar mensajes)
        min_stock = getattr(obj, 'min_stock', 0)
        if obj.control_stock and min_stock > 0 and obj.stock <= min_stock:
            # Evitamos duplicados: no crear si ya hay una orden pendiente para este insumo
            already_ordered = PurchaseOrderDetail.objects.filter(
                input=obj, 
                purchase_order__state='pending'
            ).exists()
            
            if not already_ordered:
                # Buscamos el último proveedor al que se le compró este insumo
                last_detail = PurchaseOrderDetail.objects.filter(input=obj).order_by('-purchase_order__date').first()
                if last_detail and last_detail.purchase_order.provider and last_detail.purchase_order.store:
                    po = PurchaseOrder.objects.create(
                        provider=last_detail.purchase_order.provider,
                        store=last_detail.purchase_order.store,
                        state='pending',
                        producer=obj.producer
                    )
                    PurchaseOrderDetail.objects.create(
                        purchase_order=po,
                        input=obj,
                        amount=min_stock * 2, # Cantidad sugerida: el doble del mínimo
                        price_unit=obj.cost
                    )
                    messages.info(request, gettext("Automatic Reorder: A new pending order has been created for %s based on history.") % obj.name)
                else:
                    default_provider = Provider.objects.filter(default=True, producer=obj.producer).first()
                    default_store = Store.objects.filter(default=True, producer=obj.producer).first()
                    if default_provider and default_store:
                        po = PurchaseOrder.objects.create(
                            provider=default_provider,
                            producer=obj.producer,
                            store=default_store,
                            state='pending'
                        )
                        PurchaseOrderDetail.objects.create(
                            purchase_order=po,
                            input=obj,
                            amount=min_stock,
                            price_unit=obj.cost
                        )
                        messages.info(request, gettext("Automatic Reorder: A new pending order has been created for %s using defaults.") % obj.name)
                    else:
                        messages.error(request, gettext("Automatic Reorder Failed for %s: No default provider or store found.") % obj.name)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        
        if request.user.is_superuser:
            return queryset
        if request.user.type == 'Administration':
            return queryset
        if request.user.type == 'Organization':
            userProducer = UserProducer.objects.filter(association=request.user)
            if userProducer.exists():
                return queryset.filter(producer__in=userProducer)
        if request.user.type == 'Producer':
            userProducer = UserProducer.objects.filter(email=request.user.email).first()
            if userProducer:
                return queryset.filter(producer=userProducer)
        return queryset.none()

adminSite.register(Input, InputAdmin)