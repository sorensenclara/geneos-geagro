from django.contrib import admin, messages
from user.admin.adminSite import adminSite, ProducerAwareMixin, DefaultStoreAdminMixin, get_producer_for_request
from input.models.purchase_order import PurchaseOrder
from input.models.purchase_order_detail import PurchaseOrderDetail
from input.models.purchase_reception import PurchaseReception
from input.models.purchase_reception_detail import PurchaseReceptionDetail
from user.models.user_producer import UserProducer
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from input.utils import update_input_cost

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
            update_input_cost(item.input)

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


class PurchaseOrderDetailInline(ProducerAwareMixin, admin.StackedInline):
    model = PurchaseOrderDetail
    readonly_fields = ['pending_amount', 'total', 'total_base']
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'input':
            from operation.admin.technical_plan import _filter_inputs
            kwargs['queryset'] = _filter_inputs(request)
        elif db_field.name == 'costo_center':
            producers = self._producers_for_user(request)
            if producers is not None:
                from django.db.models import Q
                from producer.models.cost_center import CostCenter
                kwargs['queryset'] = CostCenter.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))
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
    
class PurchaseOrderAdmin(DefaultStoreAdminMixin, ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['code', 'date', 'provider', 'store', 'currency', 'state']
    list_filter = ['state', 'provider', 'currency']
    search_fields = ['number']
    ordering = ['-number']
    inlines = [PurchaseOrderDetailInline]
    actions = [procesar_purchase_order, cancelar_purchase_order, input_pending_pdf]

    def get_changeform_initial_data(self, request):
        from parameter.models.currency import Currency
        initial = super().get_changeform_initial_data(request)
        base = Currency.objects.filter(is_base=True).first()
        if base:
            initial['currency'] = base.pk
            initial['exchange_rate'] = 1.0
        return initial

    class Media:
        js = ('js/admin_purchase_order_currency.js',)

    def changelist_view(self, request, extra_context=None):
        if 'action' in request.POST and (request.POST['action'] == 'input_pending_pdf'):
            if not request.POST.getlist(ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                post.update({ACTION_CHECKBOX_NAME: str(PurchaseOrder.objects.first().number)})
                request._set_post(post)
        return super(PurchaseOrderAdmin, self).changelist_view(request, extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        from django.db.models import Q
        producers = self._producers_for_user(request)
        if producers is not None:
            if db_field.name == 'applicant':
                from producer.models.staff import Staff
                kwargs['queryset'] = Staff.objects.filter(producer__in=producers)
            elif db_field.name == 'provider':
                from input.models.provider import Provider
                kwargs['queryset'] = Provider.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))
            elif db_field.name == 'store':
                from producer.models.store import Store
                kwargs['queryset'] = Store.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Asigna por defecto el usuario productor logueado
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
            userProducer = UserProducer.objects.filter(organization=request.user)
            if userProducer.exists():
                return queryset.filter(producer__in=userProducer)
        if request.user.type in ('Producer', 'Staff'):
            userProducer = get_producer_for_request(request)
            if userProducer:
                return queryset.filter(producer=userProducer)
        return queryset.none()
        
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.state == 'confirm':
            return [field.name for field in obj._meta.fields]
        return super().get_readonly_fields(request, obj)


adminSite.register(PurchaseOrder, PurchaseOrderAdmin)