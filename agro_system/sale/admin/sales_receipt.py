from django.contrib import admin
from user.admin.adminSite import adminSite, ProducerAwareMixin
from user.models.user_producer import UserProducer
from sale.models.sales_receipt import SalesReceipt


class SalesReceiptAdmin(ProducerAwareMixin, admin.ModelAdmin):

    list_display = ['date','type','number','name_custom','cuit_custom','especie','amount','subtotal','taxes']
    list_filter = ['type','especie']
    search_fields = ['type','number','name_custom','cuit_custom','especie']

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


adminSite.register(SalesReceipt, SalesReceiptAdmin)