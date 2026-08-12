from django.contrib import admin
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from user.models.user_producer import UserProducer
from alert.models.alert import Alert
from operation.models.crop import Crop

class AlertAdmin(ProducerAwareMixin, admin.ModelAdmin):

    list_display = ('name', 'crop', 'date')
    search_fields = ('name', 'crop__name')
    list_filter = ('crop', 'date')
    ordering = ('-date',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        producers = self._producers_for_user(request)
        if producers is not None:
            if db_field.name == 'crop':
               
                kwargs['queryset'] = Crop.objects.filter(producer__in=producers)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.type == 'Administration':
            return qs
        if request.user.type == 'Organization':
            producers = UserProducer.objects.filter(association=request.user)
            return qs.filter(crop__producer__in=producers)
        if request.user.type == 'Producer':
            producer = get_producer_for_request(request)
            if producer:
                return qs.filter(crop__producer=producer)
        return qs.none()


adminSite.register(Alert, AlertAdmin)