from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from user.admin.adminSite import adminSite, ProducerAwareMixin
from user.models.user_producer import UserProducer
from storage.models.silo import Silo
from storage.models.silo_stock import SiloStock
from storage.models.silo_movement import SiloMovement


class SiloStockInline(admin.TabularInline):
    model = SiloStock
    extra = 0
    fields = ['specie', 'campaing', 'crop', 'quantity_tons', 'humidity_pct', 'impurities_pct',
              'protein_pct', 'test_weight', 'date_entry']


class SiloMovementInline(admin.TabularInline):
    model = SiloMovement
    fk_name = 'silo'
    extra = 0
    fields = ['date', 'type', 'quantity_tons', 'destination_silo', 'remito_number', 'driver', 'related_sale']


class SiloAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['name', 'type', 'capacity_tons', 'countryside', 'active', 'producer']
    list_filter = ['type', 'countryside', 'active']
    search_fields = ['name', 'countryside__name']
    inlines = [SiloStockInline, SiloMovementInline]

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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'producer' and request.user.type == 'Organization':
            kwargs['queryset'] = UserProducer.objects.filter(association=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SiloMovementAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['date', 'type', 'silo', 'quantity_tons', 'remito_number', 'driver', 'producer']
    list_filter = ['type', 'silo', 'date']
    search_fields = ['silo__name', 'remito_number']
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'producer' and request.user.type == 'Organization':
            kwargs['queryset'] = UserProducer.objects.filter(association=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


adminSite.register(Silo, SiloAdmin)
adminSite.register(SiloMovement, SiloMovementAdmin)
