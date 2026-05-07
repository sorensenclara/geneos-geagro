from django.contrib import admin
from producer.models.store import Store
from user.models.user_producer import UserProducer
from user.admin.adminSite import adminSite
from django.utils.translation import gettext_lazy as _


class StoreAdmin(admin.ModelAdmin):
    exclude=['producer']
    list_display =  ['name', 'address', 'city', 'default']
    
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

adminSite.register(Store, StoreAdmin)