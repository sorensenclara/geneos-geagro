from django.contrib import admin, messages
from user.admin.adminSite import adminSite
from input.models.purchase_reception import PurchaseReception
from input.models.purchase_reception_detail import PurchaseReceptionDetail
from user.models.user_producer import UserProducer
from django.utils.translation import gettext_lazy as _
from input.models.purchase_order_detail import PurchaseOrderDetail
from input.models.input import Input

@admin.action(description=_("Process Reception"))
def process_reception(modeladmin, request, queryset):
    if not queryset.filter(state="confirm").exists():
        queryset.update(state="confirm")
        for obj in queryset:
            details = PurchaseReceptionDetail.objects.filter(purchase_reception=obj)
            for item in details:
                input_obj = item.input
                if obj.purchase_order:
                    detail_po = PurchaseOrderDetail.objects.filter(purchase_order=obj.purchase_order, input=input_obj).first()
                    if detail_po:
                        detail_po.pending_amount -= item.amount
                        detail_po.save()
                        input_obj.stock += item.amount
                        input_obj.pending -= item.amount
                        input_obj.save()
                else:
                    input_obj.stock += item.amount
                    input_obj.save()
    else:
        messages.error(request, _("Only receptions that are not already confirmed can be processed."))


class DetalleRecepcionInline(admin.StackedInline):
    model = PurchaseReceptionDetail
    extra = 0

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
        if obj and obj.state == 'confirm':
            return [field.name for field in obj._meta.fields]

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