from django.contrib import admin
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from operation.models.work_order import WorkOrder
from operation.models.input_work_order import InputWorkOrder
from operation.admin.technical_plan import _filter_inputs
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import localdate
from parameter.models.ot_state import OTState
from django.urls import reverse
from django.http import HttpResponseRedirect
from user.models.user_producer import UserProducer
from input.models.input_stock import InputStock
from input.models.stock_movement import StockMovement
from parameter.models.exchange_rate import exchangeRate


def _get_work_order_store(work_order):
    """Returns the store of the work order's countryside, or the producer's default store."""
    from producer.models.store import Store
    try:
        store = work_order.crop.countryside.store
    except AttributeError:
        store = None
    return store or Store.get_default(work_order.producer)


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


def _refresh_value_real(work_order):
    producer = work_order.producer
    for iwo in InputWorkOrder.objects.filter(work_order=work_order, dose_applied__isnull=True).select_related('input__currency'):
        inp = iwo.input
        if inp.cost is None:
            continue

        currency = inp.currency
        rate = exchangeRate.get_rate(currency, producer=producer) or 1.0 if (currency and not currency.is_base) else 1.0

        InputWorkOrder.objects.filter(pk=iwo.pk).update(
            value_real=inp.cost,
            currency_id=inp.currency_id,
            exchange_rate=rate,
            value_real_base=round(inp.cost * rate, 2),
        )


class InputWorkOrderInline(ProducerAwareMixin, admin.StackedInline):
    model = InputWorkOrder
    extra = 0
    show_change_link = True
    verbose_name_plural = _("Inputs")
    fields = ['input', 'unit_measure', 'dose', 'dose_applied', 'total_quantity',
              'value_estimated', 'value_real', 'currency', 'exchange_rate', 'value_real_base', 'total_real_display', 'store', 'details']
    readonly_fields = ['value_real_base', 'total_real_display']

    def total_real_display(self, obj):
        if obj.value_real is None:
            return '—'
        dose = obj.dose_applied if obj.dose_applied is not None else obj.dose
        if not dose:
            return '—'
        total = obj.value_real_base * dose
        currency_name = str(obj.currency) if obj.currency else ''
        return f'{total:,.2f} {currency_name}'.strip()
    total_real_display.short_description = _('Total')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "input":
            kwargs["queryset"] = _filter_inputs(request)
        elif db_field.name == "store":
            # Almacenes del productor y los compartidos (sin productor)
            producers = self._producers_for_user(request)
            if producers is not None:
                from django.db.models import Q
                from producer.models.store import Store
                kwargs["queryset"] = Store.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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
    url = reverse('operation:work_orders_pdf')
    ids = ','.join(str(obj.id) for obj in queryset)
    url = f'{url}?ids={ids}'
    return HttpResponseRedirect(url)


class WorkOrderAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['code', 'crop', 'surface', 'stage', 'date_init', 'stateOT', 'type']
    list_filter = ['campaing', 'stage', 'stateOT', 'crop', 'staff']
    search_fields = ['code', 'crop__name']
    ordering = ['code']
    inlines = [InputWorkOrderInline]
    actions = [finish_order, download_pdf]
    fieldsets = [
        (_('General'), {
            'fields': ['code', 'date_init', 'crop', 'surface', 'service', 'contractor', 'contractor_cost', 'contractor_cost_real'],
            #'description': _('Contractor costs are in base currency.'),
        }),
        # Si se dejan vacíos se completan solos: emisión = hoy, fin = inicio,
        # campaña activa, zona del cultivo y estado por defecto (Pendiente)
        (_('Additional fields'), {
            'fields': [
                'date_emission', 'date_fin', 'campaing', 'area', 'stage',
                'stateOT', 'type', 'staff', 'partner',
            ],
            'description': _('If left empty, they are filled in automatically.'),
        }),
    ]
    # Jazzmin: General arriba, luego los insumos y los campos adicionales al final
    jazzmin_section_order = [_('General'), _('Inputs')]

    class Media:
        js = ('js/admin_input_autocost.js', 'js/admin_work_order.js')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        producers = self._producers_for_user(request)
        if producers is not None:
            if db_field.name == 'crop':
                from operation.models.crop import Crop
                kwargs['queryset'] = Crop.objects.filter(producer__in=producers)
            elif db_field.name == 'staff':
                from producer.models.staff import Staff
                kwargs['queryset'] = Staff.objects.filter(producer__in=producers)
            elif db_field.name == 'contractor':
                from producer.models.contractor import Contractor
                kwargs['queryset'] = Contractor.objects.filter(producer__in=producers)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        userProducer = get_producer_for_request(request)
        if userProducer:
            obj.producer = userProducer

        # Detect state change using form.changed_data (the form tracks what the user actually changed).
        # Use request (not self) to avoid sharing state across concurrent requests on the singleton admin.
        request._wo_state_changed = change and 'stateOT' in form.changed_data

        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # Refresh runs BEFORE inline saves so the user's edits in the same submission override it.
        if getattr(request, '_wo_state_changed', False):
            _refresh_value_real(form.instance)
            request._wo_state_changed = False
        super().save_related(request, form, formsets, change)

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


adminSite.register(WorkOrder, WorkOrderAdmin)
