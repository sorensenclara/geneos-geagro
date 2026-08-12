from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from user.models.user_producer import UserProducer
from storage.models.storage_certificate import StorageCertificate
from storage.models.storage_service import StorageService
from storage.models.storage_movement import StorageMovement


class StorageServiceInline(admin.TabularInline):
    model = StorageService
    extra = 0
    fields = ['date', 'type', 'quantity_affected', 'shrinkage_tons', 'humidity_result', 'cost', 'currency', 'notes']


class StorageMovementInline(admin.TabularInline):
    model = StorageMovement
    extra = 0
    fields = ['date', 'type', 'quantity_tons', 'remito_number', 'driver', 'destination', 'port', 'related_sale']
    readonly_fields = ['date', 'type', 'quantity_tons', 'remito_number', 'driver', 'destination', 'port', 'related_sale']
    can_delete = False
    def has_add_permission(self, request, obj=None): return False


class StorageCertificateAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['number', 'storage_provider', 'specie', 'campaing', 'state',
                    'quantity_entry', 'quantity_available', 'is_warrant', 'producer']
    list_filter = ['state', 'specie', 'campaing', 'storage_provider', 'is_warrant']
    search_fields = ['number', 'storage_provider__name']
    ordering = ['-date_issue']
    readonly_fields = ['quantity_available', 'state']
    inlines = [StorageServiceInline, StorageMovementInline]

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj:  # editando un existente
            if 'quantity_entry' not in ro:
                ro.append('quantity_entry')
        return ro

    def save_model(self, request, obj, form, change):
        if not change:
            user_producer = get_producer_for_request(request)
            if user_producer:
                obj.producer = user_producer
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        producers = self._producers_for_user(request)
        if producers is not None:
            if db_field.name == 'crop':
                from operation.models.crop import Crop
                kwargs['queryset'] = Crop.objects.filter(producer__in=producers)
        elif db_field.name == 'producer':
            if request.user.type == 'Organization':
                kwargs['queryset'] = UserProducer.objects.filter(organization=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class StorageMovementAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['date', 'type', 'certificate', 'quantity_tons', 'remito_number', 'port', 'producer']
    list_filter = ['type', 'date', 'port']
    search_fields = ['certificate__number', 'remito_number', 'destination']
    ordering = ['-date', '-id']

    def get_list_display(self, request):
        cols = list(super().get_list_display(request))
        if getattr(request.user, 'type', None) in ('Producer', 'Staff'):
            cols = [c for c in cols if c != 'producer']
        return cols

    def save_model(self, request, obj, form, change):
        if not change:
            user_producer = get_producer_for_request(request)
            if user_producer:
                obj.producer = user_producer
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        producers = self._producers_for_user(request)
        if producers is not None:
            if db_field.name == 'certificate':
                kwargs['queryset'] = StorageCertificate.objects.filter(producer__in=producers)
        elif db_field.name == 'producer':
            if request.user.type == 'Organization':
                kwargs['queryset'] = UserProducer.objects.filter(organization=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


adminSite.register(StorageCertificate, StorageCertificateAdmin)
adminSite.register(StorageMovement, StorageMovementAdmin)
