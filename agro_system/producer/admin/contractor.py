from django.contrib import admin
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from producer.models.contractor import Contractor
from user.models.user_producer import UserProducer


class ContractorAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['name', 'cuit', 'phone', 'email', 'producer']
    list_filter = ['producer']
    search_fields = ['name', 'cuit', 'email']
    ordering = ['name']

    def get_list_display(self, request):
        cols = list(super().get_list_display(request))
        if getattr(request.user, 'type', None) in ('Producer', 'Staff'):
            cols = [c for c in cols if c != 'producer']
        return cols

    def save_model(self, request, obj, form, change):
        if not change:
            producer = get_producer_for_request(request)
            if producer:
                obj.producer = producer
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.type == 'Administration':
            return qs
        if request.user.type == 'Organization':
            producers = UserProducer.objects.filter(association=request.user)
            return qs.filter(producer__in=producers)
        if request.user.type == 'Producer':
            producer = get_producer_for_request(request)
            if producer:
                return qs.filter(producer=producer)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'producer' and request.user.type == 'Organization':
            kwargs['queryset'] = UserProducer.objects.filter(association=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


adminSite.register(Contractor, ContractorAdmin)
