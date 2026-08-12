from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from user.models.user_producer import UserProducer
from input.models.stock_movement import StockMovement
from input.models.input_stock import InputStock

AUTO_OPERATIONS = ('purchase', 'output', 'sale')


class StockMovementAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['date', 'operation', 'input', 'store', 'quantity', 'stock_before', 'stock_after', 'producer']
    list_filter = ['operation', 'store', 'date']
    search_fields = ['input__name', 'notes']
    ordering = ['-date', '-id']

    def get_list_display(self, request):
        cols = list(super().get_list_display(request))
        if getattr(request.user, 'type', None) in ('Producer', 'Staff'):
            cols = [c for c in cols if c != 'producer']
        return cols

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.operation in AUTO_OPERATIONS:
            # Registros creados automáticamente: solo lectura
            return [f.name for f in obj._meta.fields]
        # Ajuste manual nuevo o existente: stock_before/after y refs calculadas
        return ['stock_before', 'stock_after', 'purchase_reception', 'work_order']

    def get_fields(self, request, obj=None):
        if obj and obj.operation in AUTO_OPERATIONS:
            fields = ['date', 'operation', 'input', 'store', 'quantity',
                      'stock_before', 'stock_after', 'purchase_reception', 'work_order', 'notes']
            if request.user.is_superuser or getattr(request.user, 'type', None) == 'Administration':
                fields.insert(fields.index('purchase_reception'), 'producer')
            return fields
        # Registro nuevo (ajuste manual): producer se asigna automáticamente
        return ['date', 'operation', 'input', 'store', 'quantity',
                'stock_before', 'stock_after', 'notes']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        from django.db.models import Q
        producers = self._producers_for_user(request)
        if producers is not None:
            if db_field.name == 'input':
                from operation.admin.technical_plan import _filter_inputs
                kwargs['queryset'] = _filter_inputs(request)
            elif db_field.name == 'store':
                from producer.models.store import Store
                kwargs['queryset'] = Store.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            producer = get_producer_for_request(request)
            if producer:
                obj.producer = producer

        if obj.operation == 'adjustment' and not change:
            stock_record = InputStock.objects.filter(input=obj.input, store=obj.store).first()
            obj.stock_before = stock_record.quantity if stock_record else 0
            obj.stock_after = obj.stock_before + obj.quantity

            if stock_record:
                stock_record.quantity = obj.stock_after
                stock_record.save()
            else:
                InputStock.objects.create(
                    input=obj.input,
                    store=obj.store,
                    quantity=obj.stock_after,
                )

            # Actualizar stock global del insumo
            total = sum(
                InputStock.objects.filter(input=obj.input).values_list('quantity', flat=True)
            )
            obj.input.stock = total
            obj.input.save()

        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.type == 'Administration':
            return qs
        if request.user.type == 'Organization':
            producers = UserProducer.objects.filter(organization=request.user)
            return qs.filter(producer__in=producers)
        if request.user.type in ('Producer', 'Staff'):
            producer = get_producer_for_request(request)
            if producer:
                return qs.filter(producer=producer)
        return qs.none()


adminSite.register(StockMovement, StockMovementAdmin)
