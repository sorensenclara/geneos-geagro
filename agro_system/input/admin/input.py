from django.contrib import admin
from user.admin.adminSite import adminSite
from input.models.purchase_order import PurchaseOrder
from input.models.purchase_order_detail import PurchaseOrderDetail
from input.models.input import Input
from django.utils.translation import gettext_lazy as _


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
    list_display = ['name', 'type', 'cost', 'stock', 'pending']
    list_filter = ['type', 'unit_measure', 'currency']
    readonly_fields = ['pending']


adminSite.register(Input, InputAdmin)