from django.contrib import admin, messages
from django.db.models import Q
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from input.models.purchase_reception import PurchaseReception
from input.models.purchase_reception_detail import PurchaseReceptionDetail
from user.models.user_producer import UserProducer
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import localdate
from input.models.purchase_order_detail import PurchaseOrderDetail
from input.models.input import Input
from input.models.input_stock import InputStock
from input.models.stock_movement import StockMovement


def _add_to_store_stock(input_obj, store, amount):
    stock_record, _ = InputStock.objects.get_or_create(
        input=input_obj,
        store=store,
        defaults={'quantity': 0},
    )
    stock_before = stock_record.quantity
    stock_record.quantity += amount
    stock_record.save()
    return stock_before, stock_record.quantity


@admin.action(description=_("Process Reception"))
def process_reception(modeladmin, request, queryset):
    if queryset.filter(state="confirm").exists():
        messages.error(request, _("Only receptions that are not already confirmed can be processed."))
        return

    queryset.update(state="confirm")
    for obj in queryset:
        if not obj.delivery_date:
            obj.delivery_date = localdate()
            obj.save(update_fields=['delivery_date'])
        details = PurchaseReceptionDetail.objects.filter(purchase_reception=obj)
        for item in details:
            input_obj = item.input
            if obj.purchase_order:
                detail_po = PurchaseOrderDetail.objects.filter(
                    purchase_order=obj.purchase_order, input=input_obj
                ).first()
                if detail_po:
                    detail_po.pending_amount -= item.amount
                    detail_po.save()
                    input_obj.pending -= item.amount
            input_obj.stock += item.amount
            input_obj.save()
            stock_before, stock_after = _add_to_store_stock(input_obj, obj.store, item.amount)
            StockMovement.objects.create(
                date=obj.delivery_date or localdate(),
                producer=obj.producer,
                input=input_obj,
                store=obj.store,
                quantity=item.amount,
                stock_before=stock_before,
                stock_after=stock_after,
                operation='purchase',
                purchase_reception=obj,
            )


class DetalleRecepcionInline(ProducerAwareMixin, admin.StackedInline):
    model = PurchaseReceptionDetail
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'input':
            from operation.admin.technical_plan import _filter_inputs
            kwargs['queryset'] = _filter_inputs(request)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request, obj=None):
        if obj and obj.state == 'confirm':
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        # obj here is the parent PurchaseReception
        if obj and obj.state == 'confirm':
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # obj here is the parent PurchaseReception
        if obj and obj.state == 'confirm':
            return False
        return super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.state == 'confirm':
            return [field.name for field in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

class PurchaseReceptionAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['code', 'purchase_order', 'delivery_date', 'state', 'store']
    list_filter = ['state', 'store']
    search_fields = ['code', 'purchase_order__number']
    ordering = ['-code']
    actions = [process_reception]
    inlines = [DetalleRecepcionInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        producers = self._producers_for_user(request)
        if producers is not None:
            if db_field.name == 'purchase_order':
                from input.models.purchase_order import PurchaseOrder
                kwargs['queryset'] = PurchaseOrder.objects.filter(producer__in=producers)
            elif db_field.name == 'store':
                from producer.models.store import Store
                kwargs['queryset'] = Store.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        userProducer = get_producer_for_request(request)
        if userProducer:
            obj.producer = userProducer
        super().save_model(request, obj, form, change)


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
            userProducer = get_producer_for_request(request)
            if userProducer:
                return queryset.filter(producer=userProducer)
        return queryset.none()
    
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.state == 'confirm':
            return [field.name for field in obj._meta.fields]
        return super().get_readonly_fields(request, obj)

adminSite.register(PurchaseReception, PurchaseReceptionAdmin)