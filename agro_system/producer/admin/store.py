from django.contrib import admin
from producer.models.store import Store
from user.models.user_producer import UserProducer
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from django.utils.translation import gettext_lazy as _
from input.models.input_stock import InputStock



class StoreInputStockInline(admin.TabularInline):
    model = InputStock
    extra = 0
    fields = ['input', 'quantity']
    readonly_fields = ['input', 'quantity']
    verbose_name = _('Input stock')
    verbose_name_plural = _('Input stock')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class StoreAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['name', 'address', 'city', 'default']
    inlines = [StoreInputStockInline,]
    
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
            userProducer = UserProducer.objects.filter(association=request.user)
            if userProducer.exists():
                return queryset.filter(producer__in=userProducer)
        if request.user.type == 'Producer':
            userProducer = get_producer_for_request(request)
            if userProducer:
                return queryset.filter(producer=userProducer)
        return queryset.none()

adminSite.register(Store, StoreAdmin)