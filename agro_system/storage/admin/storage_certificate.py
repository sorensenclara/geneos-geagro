from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from user.admin.adminSite import adminSite
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


class StorageCertificateAdmin(admin.ModelAdmin):
    list_display = ['number', 'storage_provider', 'specie', 'campaing', 'state',
                    'quantity_entry', 'quantity_available', 'is_warrant', 'producer']
    list_filter = ['state', 'specie', 'campaing', 'storage_provider', 'is_warrant']
    search_fields = ['number', 'storage_provider__name']
    ordering = ['-date_issue']
    readonly_fields = ['quantity_available']
    inlines = [StorageServiceInline, StorageMovementInline]

    def save_model(self, request, obj, form, change):
        if not change:
            user_producer = UserProducer.objects.filter(email=request.user.email).first()
            if user_producer:
                obj.producer = user_producer
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.type == 'Administration':
            return qs
        if request.user.type == 'Organization':
            producers = UserProducer.objects.filter(association=request.user)
            return qs.filter(producer__in=producers)
        if request.user.type == 'Producer':
            producer = UserProducer.objects.filter(email=request.user.email).first()
            if producer:
                return qs.filter(producer=producer)
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        readonly.append('quantity_available')
        if request.user.type == 'Producer':
            readonly.append('producer')
        return readonly

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'producer':
            if request.user.type == 'Organization':
                kwargs['queryset'] = UserProducer.objects.filter(association=request.user)
            elif request.user.type == 'Producer':
                kwargs['queryset'] = UserProducer.objects.filter(email=request.user.email)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class StorageMovementAdmin(admin.ModelAdmin):
    list_display = ['date', 'type', 'certificate', 'quantity_tons', 'remito_number', 'port', 'producer']
    list_filter = ['type', 'date', 'port']
    search_fields = ['certificate__number', 'remito_number', 'destination']
    ordering = ['-date', '-id']

    def save_model(self, request, obj, form, change):
        if not change:
            user_producer = UserProducer.objects.filter(email=request.user.email).first()
            if user_producer:
                obj.producer = user_producer
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.type == 'Administration':
            return qs
        if request.user.type == 'Organization':
            producers = UserProducer.objects.filter(association=request.user)
            return qs.filter(producer__in=producers)
        if request.user.type == 'Producer':
            producer = UserProducer.objects.filter(email=request.user.email).first()
            if producer:
                return qs.filter(producer=producer)
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        if request.user.type == 'Producer':
            return ['producer']
        return super().get_readonly_fields(request, obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'producer':
            if request.user.type == 'Organization':
                kwargs['queryset'] = UserProducer.objects.filter(association=request.user)
            elif request.user.type == 'Producer':
                kwargs['queryset'] = UserProducer.objects.filter(email=request.user.email)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


adminSite.register(StorageCertificate, StorageCertificateAdmin)
adminSite.register(StorageMovement, StorageMovementAdmin)
