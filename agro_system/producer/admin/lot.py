from django.contrib import admin
from user.admin.adminSite import adminSite
from producer.models.country_side import Countryside
from user.models.user_producer import UserProducer
from producer.models.lot import Lot
from leaflet.admin import LeafletGeoAdmin


class LotAdmin(LeafletGeoAdmin):
    list_display  = ['name', 'countryside', 'responsible', 'hectares_productive', 'area']
    list_filter   = ['responsible', 'area']
    search_fields = ['name']

    fieldsets = [
        (None, {
            "fields": [
                "name", "countryside", "area", "responsible",
                "hectares", "hectares_productive", "cost_center",
                "activity", "LotRating", "last_activity",
                "station", "external_station", "observations",
            ],
        }),
        ("Ubicación geográfica", {
            "fields": ["ubication", "delimitation"],
        }),
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser or request.user.type == 'Administration':
            return queryset
        if request.user.type == 'Organization':
            userProducer = UserProducer.objects.filter(association=request.user)
            if userProducer.exists():
                return queryset.filter(countryside__producer__in=userProducer)
        if request.user.type == 'Producer':
            userProducer = UserProducer.objects.filter(email=request.user.email).first()
            if userProducer:
                countrysides = Countryside.objects.filter(producer=userProducer)
                return queryset.filter(countryside__in=countrysides)
        return queryset.none()


adminSite.register(Lot, LotAdmin)
