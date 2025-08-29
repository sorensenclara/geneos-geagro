from django.contrib import admin, messages
from user.admin.adminSite import adminSite
from input.models.purchaseReception import PurchaseReception
from input.models.purchaseReceptionDetail import PurchaseReceptionDetail
from user.models.userProducer import UserProducer
from django.utils.translation import gettext_lazy as _
from input.models.purchaseOrderDetail import PurchaseOrderDetail
from input.models.input import Input

@admin.action(description=_("Process Reception"))
def process_reception(modeladmin, request, queryset):
    if not queryset.filter(state="confirm").exists():
        queryset.update(state="confirm")
        for obj in queryset:
            details = PurchaseReceptionDetail.objects.filter(purchase_reception=obj)
            for item in details:
                detail_po = PurchaseOrderDetail.objects.filter(purchase_order=obj.purchase_order, input=item.input)[0]
                detail_po.pending_amount = detail_po.pending_amount - item.amount
                detail_po.save()
                input = Input.objects.filter(id=item.input.id)[0]
                input.stock += item.amount
                input.pending += detail_po.pending_amount
                input.save()
    else:
        return messages.error(request,"Only receptions in 'confirm' state can be processed.")


class DetalleRecepcionInline(admin.StackedInline):
    model = PurchaseReceptionDetail
    extra = 0

class PurchaseReceptionAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'delivery_date', 'state', 'store']
    list_filter = ['state', 'purchase_order', 'store']
    actions = [process_reception]
    inlines = [DetalleRecepcionInline]

    def save_model(self, request, obj, form, change):
        userProducer = UserProducer.objects.filter(email=request.user.email).first()
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
            userProducer = UserProducer.objects.filter(email=request.user.email).first()
            if userProducer:
                return queryset.filter(producer=userProducer)
        return queryset.none()
    
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if request.user.type == 'Producer':
            return ['producer']
        return readonly_fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "producer":
            if request.user.type == "Organization":
                kwargs["queryset"] = UserProducer.objects.filter(association=request.user)
            elif request.user.type == "Producer":
                kwargs["queryset"] = UserProducer.objects.filter(email=request.user.email)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

adminSite.register(PurchaseReception, PurchaseReceptionAdmin)