from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from user.models.user_producer import UserProducer
from storage.models.silo_movement import SiloMovement
from storage.models.silo_stock import SiloStock


class SiloMovementAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['date', 'type', 'crop', 'silo', 'quantity_tons', 'remito_number', 'driver', 'producer']
    list_filter = ['type', 'silo', 'date']
    search_fields = ['silo__name', 'remito_number', 'crop__name']
    ordering = ['-date', '-id']
    readonly_fields = ['silo_stock']

    def get_list_display(self, request):
        cols = list(super().get_list_display(request))
        if getattr(request.user, 'type', None) in ('Producer', 'Staff'):
            cols = [c for c in cols if c != 'producer']
        return cols

    # Funcion para que aparezca el silo destino en caso de que sea un movimiento de transferencia
    class Media:
        js = ('js/admin_silo_movement.js',)

    def save_model(self, request, obj, form, change):
        if not change:
            user_producer = get_producer_for_request(request)
            if user_producer:
                obj.producer = user_producer
        # Snapshot stocks de origen y destino antes de guardar para detectar nuevos
        silo_id = obj.silo_id
        dest_silo = form.cleaned_data.get('destination_silo')
        dest_silo_id = dest_silo.pk if dest_silo else None
        silo_ids = [s for s in [silo_id, dest_silo_id] if s]
        existing_pks = set(
            SiloStock.objects.filter(silo_id__in=silo_ids).values_list('pk', flat=True)
        ) if silo_ids else set()
        super().save_model(request, obj, form, change)
        if silo_ids:
            after_pks = set(SiloStock.objects.filter(silo_id__in=silo_ids).values_list('pk', flat=True))
            new_pks = after_pks - existing_pks
            request._new_stock_pk = next(iter(new_pks), None)
        else:
            request._new_stock_pk = None

    def _redirect_to_new_stock(self, request):
        stock_pk = getattr(request, '_new_stock_pk', None)
        if not stock_pk:
            return None
        stock = SiloStock.objects.filter(pk=stock_pk).first()
        if not stock:
            return None
        self.message_user(
            request,
            format_html(
                'Movimiento guardado. Completá los datos de calidad del stock <strong>{}</strong>.',
                stock.crop,
            ),
            messages.SUCCESS,
        )
        return HttpResponseRedirect(
            reverse('miadmin:storage_silostock_change', args=[stock_pk])
        )

    def response_add(self, request, obj, post_url_continue=None):
        redirect = self._redirect_to_new_stock(request)
        if redirect:
            return redirect
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        redirect = self._redirect_to_new_stock(request)
        if redirect:
            return redirect
        return super().response_change(request, obj)

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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        producers = self._producers_for_user(request)
        if producers is not None:
            if db_field.name in ('silo', 'destination_silo'):
                from storage.models.silo import Silo
                kwargs['queryset'] = Silo.objects.filter(producer__in=producers)
            elif db_field.name == 'crop':
                from operation.models.crop import Crop
                kwargs['queryset'] = Crop.objects.filter(producer__in=producers)
            elif db_field.name == 'driver':
                # El chofer pertenece a un transportista: se ven los de transportistas propios o compartidos
                from django.db.models import Q
                from sale.models.driver import Driver
                kwargs['queryset'] = Driver.objects.filter(
                    Q(provider__producer__in=producers) | Q(provider__producer__isnull=True))
            elif db_field.name == 'related_sale':
                from sale.models.sales_receipt import SalesReceipt
                kwargs['queryset'] = SalesReceipt.objects.filter(producer__in=producers)
        elif db_field.name == 'producer':
            if request.user.type == 'Organization':
                kwargs['queryset'] = UserProducer.objects.filter(organization=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


adminSite.register(SiloMovement, SiloMovementAdmin)
