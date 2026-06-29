from django.contrib import admin, messages
from user.admin.adminSite import adminSite, ProducerAwareMixin
from input.models.purchase_order import PurchaseOrder
from input.models.purchase_order_detail import PurchaseOrderDetail
from input.models.purchase_reception import PurchaseReception
from input.models.purchase_reception_detail import PurchaseReceptionDetail
from user.models.user_producer import UserProducer
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME


@admin.action(description=_("Process Purchase Order"))
def procesar_purchase_order(modeladmin, request, queryset):
    for obj in queryset:
        if obj.state == 'confirm':
            messages.error(request, _("The order %s is already confirmed.") % obj.number)
            continue

        obj.state = "confirm"
        obj.save()

        details = PurchaseOrderDetail.objects.filter(purchase_order=obj)
        for item in details:
            item.pending_amount = item.amount
            item.input.pending += item.amount
            item.input.save()
            item.save()

        # Crear recepción pendiente automáticamente si todavía no existe una
        if not PurchaseReception.objects.filter(purchase_order=obj).exists():
            reception = PurchaseReception.objects.create(
                purchase_order=obj,
                store=obj.store,
                producer=obj.producer,
                state='pending',
            )
            for item in details:
                PurchaseReceptionDetail.objects.create(
                    purchase_reception=reception,
                    input=item.input,
                    amount=item.amount,
                )
            messages.success(
                request,
                _("Order %(number)s confirmed. A pending reception was created automatically — "
                  "adjust quantities if needed and then confirm it.")
                % {'number': obj.number}
            )

@admin.action(description=_("Cancel Purchase Order"))
def cancelar_purchase_order(modeladmin, request, queryset):
    for obj in queryset:
        # Valida si existen recepciones asociadas a esta orden
        if PurchaseReception.objects.filter(purchase_order=obj).exists():
            messages.error(request, _("Order %s cannot be cancelled because it already has associated receptions.") % obj.number)
            continue

        # Si la orden estaba confirmada, restamos lo pendiente de los insumos antes de cancelar
        if obj.state == 'confirm':
            details = PurchaseOrderDetail.objects.filter(purchase_order=obj)
            for item in details:
                if item.pending_amount:
                    item.input.pending -= item.pending_amount
                    item.input.save()

        obj.state = "cancel"
        obj.save()
        messages.success(request, _("Order %s has been successfully cancelled.") % obj.number)


@admin.action(description=_("Pending purchases"))
def input_pending_pdf(modeladmin, request, queryset):
    # Obtén la URL de la vista personalizada
    url = reverse('input:input_pending_pdf')
    url = f'{url}'
    
    # Redirige a la vista personalizada
    return HttpResponseRedirect(url)


class PurchaseOrderDetailInline(admin.StackedInline):
    model = PurchaseOrderDetail
    readonly_fields = ['pending_amount', 'total']
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
    
class PurchaseOrderAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['code', 'date', 'provider', 'store', 'state']
    list_filter = ['state', 'provider']
    search_fields = ['number']
    ordering = ['-number']
    inlines = [PurchaseOrderDetailInline]
    actions = [procesar_purchase_order, cancelar_purchase_order, input_pending_pdf]

    def changelist_view(self, request, extra_context=None):
        if 'action' in request.POST and (request.POST['action'] == 'input_pending_pdf'):
            if not request.POST.getlist(ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                post.update({ACTION_CHECKBOX_NAME: str(PurchaseOrder.objects.first().number)})
                request._set_post(post)
        return super(PurchaseOrderAdmin, self).changelist_view(request, extra_context)

    def save_model(self, request, obj, form, change):
        # Asigna por defecto el usuario productor logueado
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
        if obj and obj.state == 'confirm':
            return [field.name for field in obj._meta.fields]
        return super().get_readonly_fields(request, obj)


adminSite.register(PurchaseOrder, PurchaseOrderAdmin)