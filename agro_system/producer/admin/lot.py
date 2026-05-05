from django.contrib import admin
from user.admin.adminSite import adminSite
from producer.models.country_side import Countryside
from user.models.user_producer import UserProducer
# from producer.models.staff import Staff
from producer.models.lot import Lot
# from leaflet.admin import LeafletGeoAdmin

# Register your models here.
class LotAdmin(admin.ModelAdmin):
    list_display = ['name', 'countryside', 'responsible', 'hectares_productive', 'cost_center']
    list_filter = ['responsible']
    search_fields = ['name']


        
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):

    #     if db_field.name == "responsible":
    #         staff_qs = Staff.objects.none()
    #         # superuser ve todos
    #         if request.user.is_superuser or request.user.type in ['Administration']:
    #             staff_qs = Staff.objects.all()
    #         # si es una organización → ve todos los staff de sus productores
    #         elif request.user.type == 'Organization':
    #             user_producers = UserProducer.objects.filter(association=request.user)
    #             staff_qs = Staff.objects.filter(producer__in=user_producers)
    #         # si es un productor → ve solo sus staff
    #         elif request.user.type == 'Producer':
    #             user_producer = UserProducer.objects.filter(email=request.user.email).first()
    #             if user_producer:
    #                 staff_qs = Staff.objects.filter(producer=user_producer)
    #         kwargs["queryset"] = staff_qs
        
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        
        if request.user.is_superuser:
            return queryset
        if request.user.type == 'Administration':
            return queryset
        if request.user.type == 'Organization':
            userProducer = UserProducer.objects.filter(association=request.user)
            if userProducer.exists():
                return queryset.filter(countryside_producer__in=userProducer)
        if request.user.type == 'Producer':
            userProducer = UserProducer.objects.filter(email=request.user.email).first()
            if userProducer:
                countrysides = Countryside.objects.filter(producer=userProducer)
                return queryset.filter(countryside__in=countrysides)
        return queryset.none()


adminSite.register(Lot, LotAdmin)