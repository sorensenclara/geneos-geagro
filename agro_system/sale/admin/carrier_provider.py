from django.contrib import admin
from user.admin.adminSite import adminSite
from sale.models.carrier_provider import Carrier
from sale.models.driver import Driver


class DriverInline(admin.TabularInline):
    model = Driver
    fields = ['name','cuit','address','city','phone','email']
    extra = 0


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ["name", "cuit", "address", "city", "phone", "email"]
    search_fields = ["name", "cuit", "address", "city__name", "phone", "email"]
    inlines = [DriverInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(type__name="Transportista")
    
    
adminSite.register(Carrier, CarrierAdmin)