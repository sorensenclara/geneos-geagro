from django.contrib import admin, messages
from producer.models.store import Store
from input.models.provider import Provider
from user.models.user_producer import UserProducer
from user.admin.adminSite import adminSite, ProducerAwareMixin
from input.models.purchase_order import PurchaseOrder
from input.models.purchase_order_detail import PurchaseOrderDetail
from input.models.input import Input
from input.models.input_stock import InputStock
from django.utils.translation import gettext_lazy as _, gettext
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from import_export import fields
from input.models.type_input import TypeInput
from parameter.models.measure_unit import  MaensureUnit
from parameter.models.currency import Currency


class InputStockInline(admin.TabularInline):
    model = InputStock
    extra = 0
    fields = ['store', 'quantity']
    readonly_fields = ['store', 'quantity']
    verbose_name = _('Stock per store')
    verbose_name_plural = _('Stock per store')

    def has_view_permission(self, request, obj=None):
        return request.user.is_active

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or getattr(request.user, 'type', None) in ('Administration', 'Organization'):
            return qs
        if getattr(request.user, 'type', None) in ('Producer', 'Staff'):
            producer = UserProducer.objects.filter(email=request.user.email).first()
            if producer:
                return qs.filter(store__producer=producer)
        return qs.none()


class PurchaseInline(admin.StackedInline):
    model = PurchaseOrderDetail
    can_delete = False
    extra = 0
    fields = ['date_order', 'amount', 'price_unit', 'currency', 'total_base']
    readonly_fields = ['date_order', 'amount', 'price_unit', 'currency', 'total_base']

    def date_order(self, obj):
        return obj.purchase_order.date if obj.purchase_order else None
    date_order.short_description = _('Order Date')

    def currency(self, obj):
        return obj.purchase_order.currency if obj.purchase_order else None
    currency.short_description = _('Currency')

    verbose_name_plural = _("Purchases")
    verbose_name = _("Purchase")

    def has_add_permission(self, request, obj=None):
        return False



class InputResource(resources.ModelResource):

    type = fields.Field(
        column_name='type',
        attribute='type',
        widget=ForeignKeyWidget(TypeInput, 'name')
    )

    unit_measure = fields.Field(
        column_name='unit_measure',
        attribute='unit_measure',
        widget=ForeignKeyWidget(MaensureUnit, 'name')
    )

    currency = fields.Field(
        column_name='currency',
        attribute='currency',
        widget=ForeignKeyWidget(Currency, 'name')
    )

    class Meta:
        model = Input
        fields = ('id','name','type','unit_measure','presentation','cost','currency','control_stock','stock','min_stock','pending','control_lot')
        skip_unchanged = True
        report_skipped = True
    
    def __init__(self, user=None):
        super().__init__()
        self.user = user

    def before_save_instance(self, instance, row, **kwargs):
        userProducer = UserProducer.objects.filter(email=self.user.email).first()
        if userProducer:
            instance.producer = userProducer
        elif self.user.is_superuser:
            instance.producer = None
        else:
            raise ValueError("No se pudo asignar el productor al insumo. Usuario no tiene un productor asociado.")

class InputAdmin(ProducerAwareMixin, ImportExportModelAdmin):
    search_fields = ['name']
    inlines = [InputStockInline, PurchaseInline]
    list_display = ['name', 'type', 'cost', 'currency', 'cost_update_mode', 'stock', 'min_stock', 'pending', 'producer']
    list_filter = ['type', 'unit_measure', 'currency', 'cost_update_mode']
    readonly_fields = ['pending', 'stock']
    resource_class = InputResource

    def get_readonly_fields(self, request, obj=None):
        rf = list(super().get_readonly_fields(request, obj))
        # En modos automáticos la moneda siempre es la base — no permitir edición manual
        if obj and getattr(obj, 'cost_update_mode', 'manual') != 'manual':
            if 'currency' not in rf:
                rf.append('currency')
        return rf

    def get_fieldsets(self, request, obj=None):
        show_producer = request.user.is_superuser or getattr(request.user, 'type', None) == 'Administration'
        general_fields = ['name', 'type', 'unit_measure', 'presentation']
        if show_producer:
            general_fields.append('producer')
        return [
            (None, {'fields': general_fields}),
            ('Costo', {
                'fields': ['cost', 'currency', 'cost_update_mode'],
                'description': 'Para modos automáticos, el precio se actualiza en moneda base al confirmar compras. El historial de conversión queda en cada orden de compra.',
            }),
            ('Stock', {'fields': ['control_stock', 'stock', 'min_stock', 'pending', 'control_lot']}),
        ]


    def get_import_resource_kwargs(self, request, *args, **kwargs):
        return {"user": request.user}

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

    def get_list_display(self, request):
        cols = list(super().get_list_display(request))
        if getattr(request.user, 'type', None) == 'Producer':
            cols = [c for c in cols if c != 'producer']
        return cols

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        from django.db.models import Q
        if request.user.is_superuser:
            return queryset
        if request.user.type == 'Administration':
            return queryset
        if request.user.type == 'Organization':
            userProducer = UserProducer.objects.filter(association=request.user)
            if userProducer.exists():
                return queryset.filter(Q(producer__in=userProducer) | Q(producer__isnull=True))
        if request.user.type == 'Producer':
            userProducer = UserProducer.objects.filter(email=request.user.email).first()
            if userProducer:
                return queryset.filter(Q(producer=userProducer) | Q(producer__isnull=True))
        return queryset.none()

adminSite.register(Input, InputAdmin)