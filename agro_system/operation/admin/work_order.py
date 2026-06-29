from django.contrib import admin
from user.admin.adminSite import adminSite, ProducerAwareMixin
from operation.models.work_order import WorkOrder
from operation.models.input_work_order import InputWorkOrder
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import localdate
from parameter.models.ot_state import OTState
from django.urls import reverse
from django.http import HttpResponseRedirect
from user.models.user_producer import UserProducer
from input.models.input_stock import InputStock
from input.models.stock_movement import StockMovement


def _get_work_order_store(work_order):
    """Returns the store associated with the work order's countryside, or None."""
    try:
        return work_order.crop.countryside.store
    except AttributeError:
        return None


def _subtract_from_store_stock(input_obj, store, amount):
    """Deducts amount from InputStock. Returns (stock_before, stock_after) or (0, 0) if no store."""
    if store is None:
        return 0, 0
    stock_record = InputStock.objects.filter(input=input_obj, store=store).first()
    if stock_record:
        stock_before = stock_record.quantity
        stock_record.quantity -= amount
        stock_record.save()
        return stock_before, stock_record.quantity
    return 0, 0


class InputWorkOrderInline(admin.StackedInline):
    model = InputWorkOrder
    extra = 0
    show_change_link = True
    verbose_name_plural = _("Inputs")


@admin.action(description="Finalizar orden")
def finish_order(modeladmin, request, queryset):
    for obj in queryset:
        obj.stateOT = OTState.objects.filter(name="Finalizada")[0]
        obj.save()
        fallback_store = _get_work_order_store(obj)
        inputs = InputWorkOrder.objects.filter(work_order=obj)
        for iwo in inputs:
            if not iwo.dose_applied:
                continue
            iwo.input.stock -= iwo.dose_applied
            iwo.input.save()
            store = iwo.store or fallback_store
            stock_before, stock_after = _subtract_from_store_stock(iwo.input, store, iwo.dose_applied)
            StockMovement.objects.create(
                date=localdate(),
                producer=obj.producer,
                input=iwo.input,
                store=store,
                quantity=-iwo.dose_applied,
                stock_before=stock_before,
                stock_after=stock_after,
                operation='output',
                work_order=obj,
            )


@admin.action(description=_("Print work orders"))
def download_pdf(modeladmin, request, queryset):
    # Obtén la URL de la vista personalizada
    url = reverse('operation:work_orders_pdf')
    ids = ','.join(str(obj.id) for obj in queryset)
    url = f'{url}?ids={ids}'

    # Redirige a la vista personalizada
    return HttpResponseRedirect(url)

class WorkOrderAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['code', 'crop', 'stage', 'date_init', 'stateOT', 'type']
    list_filter = ['campaing','stage','stateOT', 'crop']
    search_fields = ['code', 'crop__name']
    ordering = ['code']
    inlines = [InputWorkOrderInline]
    actions = [finish_order, download_pdf]

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


adminSite.register(WorkOrder, WorkOrderAdmin)
