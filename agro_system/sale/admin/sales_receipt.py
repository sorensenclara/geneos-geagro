from django.contrib import admin
from user.admin.adminSite import adminSite
from user.models.user_producer import UserProducer
from sale.models.sales_receipt import SalesReceipt


class SalesReceiptAdmin(admin.ModelAdmin):

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

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if request.user.type == 'Producer':
            return ['producer']
        return readonly_fields

    #  Limitar choices del campo en el formulario
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "producer":
            if request.user.type == "Organization":
                kwargs["queryset"] = UserProducer.objects.filter(association=request.user)
            elif request.user.type == "Producer":
                kwargs["queryset"] = UserProducer.objects.filter(email=request.user.email)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


adminSite.register(SalesReceipt, SalesReceiptAdmin)