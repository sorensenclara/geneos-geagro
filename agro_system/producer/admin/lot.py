from django.contrib import admin
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from producer.models.country_side import Countryside
from user.models.user_producer import UserProducer
# from producer.models.staff import Staff
from producer.models.lot import Lot
from leaflet.admin import LeafletGeoAdmin

# Register your models here.
#class LotAdmin(admin.ModelAdmin):
class LotAdmin(ProducerAwareMixin, LeafletGeoAdmin):
    list_display = ['name', 'countryside', 'responsible', 'hectares_productive', 'cost_center']
    list_filter = ['responsible']
    search_fields = ['name']


        
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        from producer.models.country_side import Countryside
        from producer.models.staff import Staff
        producers = self._producers_for_user(request)
        if producers is not None:
            if db_field.name == 'countryside':
                kwargs['queryset'] = Countryside.objects.filter(producer__in=producers)
            elif db_field.name == 'responsible':
                kwargs['queryset'] = Staff.objects.filter(producer__in=producers)
            elif db_field.name == 'cost_center':
                from django.db.models import Q
                from producer.models.cost_center import CostCenter
                kwargs['queryset'] = CostCenter.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        
        if request.user.is_superuser:
            return queryset
        if request.user.type == 'Administration':
            return queryset
        if request.user.type == 'Organization':
            userProducer = UserProducer.objects.filter(organization=request.user)
            if userProducer.exists():
                return queryset.filter(countryside__producer__in=userProducer)
        if request.user.type in ('Producer', 'Staff'):
            userProducer = get_producer_for_request(request)
            if userProducer:
                countrysides = Countryside.objects.filter(producer=userProducer)
                return queryset.filter(countryside__in=countrysides)
        return queryset.none()


adminSite.register(Lot, LotAdmin)