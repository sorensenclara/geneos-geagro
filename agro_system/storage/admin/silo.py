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
    readonly_fields = ['crop', 'specie', 'campaing', 'quantity_tons']
    fields = ['crop', 'specie', 'campaing', 'quantity_tons', 'active',
              'humidity_pct', 'impurities_pct', 'protein_pct', 'test_weight', 'date_entry']
    can_delete = False

    def has_add_permission(self, *args, **kwargs):
        return False


class SiloMovementInline(admin.TabularInline):
    model = SiloMovement
    fk_name = 'silo'
    extra = 0
    fields = ['date', 'type', 'crop', 'quantity_tons', 'destination_silo', 'remito_number', 'driver', 'related_sale']
    readonly_fields = ['date', 'type', 'crop', 'quantity_tons', 'destination_silo', 'remito_number', 'driver', 'related_sale']
    can_delete = False

    def has_add_permission(self, *args, **kwargs):
        return False


class SiloAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['name', 'type', 'capacity_tons', 'countryside', 'active', 'producer']
    list_filter = ['type', 'countryside', 'active']
    search_fields = ['name', 'countryside__name']
    inlines = [SiloStockInline, SiloMovementInline]

    def get_list_display(self, request):
        cols = list(super().get_list_display(request))
        if getattr(request.user, 'type', None) in ('Producer', 'Staff'):
            cols = [c for c in cols if c != 'producer']
        return cols

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


class SiloStockAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['silo', 'crop', 'specie', 'campaing', 'quantity_tons', 'active']
    list_filter = ['active', 'silo', 'campaing']
    search_fields = ['silo__name', 'crop__name']
    readonly_fields = ['silo', 'crop', 'specie', 'campaing', 'quantity_tons', 'active']
    fields = ['silo', 'crop', 'specie', 'campaing', 'quantity_tons', 'active',
              'humidity_pct', 'impurities_pct', 'protein_pct', 'test_weight', 'date_entry']

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.type == 'Administration':
            return qs
        if request.user.type == 'Organization':
            producers = UserProducer.objects.filter(association=request.user)
            return qs.filter(silo__producer__in=producers)
        if request.user.type == 'Producer':
            producer = UserProducer.objects.filter(email=request.user.email).first()
            if producer:
                return qs.filter(silo__producer=producer)
        return qs.none()


adminSite.register(Silo, SiloAdmin)
adminSite.register(SiloStock, SiloStockAdmin)
