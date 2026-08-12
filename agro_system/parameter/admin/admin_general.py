from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from user.admin.adminSite import adminSite, ProducerAwareMixin
from parameter.models.country import Country
from parameter.models.province import Province
from parameter.models.city import City
from parameter.models.gender import Gender
from parameter.models.countryside_condition import CountrysideCondition
from parameter.models.lot_rating import LotRating
from parameter.models.campaign import Campaing
from parameter.models.action import Action
from parameter.models.cultivation_state import CiltivationState  
from parameter.models.ot_state import OTState
from parameter.models.port import Port
from parameter.models.var_crop_technique import VarCropTechnique
from parameter.models.specie import Specie
from parameter.models.area import Area
from parameter.models.measure_unit import MaensureUnit
from parameter.models.currency import Currency
from parameter.models.exchange_rate import exchangeRate
from parameter.models.type_var_crop_technique  import TypeVarCropTechnique
from parameter.models.silo_type import SiloType
from parameter.models.storage_service_type import StorageServiceType


adminSite.register(Country)
adminSite.register(Province)
adminSite.register(City)
adminSite.register(Gender)
adminSite.register(CountrysideCondition)
adminSite.register(LotRating)
adminSite.register(Campaing)
adminSite.register(Action)
adminSite.register(CiltivationState)
adminSite.register(OTState)
adminSite.register(Port)
adminSite.register(VarCropTechnique)
adminSite.register(Specie)
adminSite.register(Area)


class MeasureUnitAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['name', 'is_reference', 'multiplier']
    list_filter = ['is_reference']
    search_fields = ['name']

adminSite.register(MaensureUnit, MeasureUnitAdmin)
class CurrencyAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['name', 'symbol', 'is_base']
    list_filter = ['is_base']
    fields = ['name', 'symbol', 'is_base']

adminSite.register(Currency, CurrencyAdmin)
class ExchangeRateAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['currency_origin', 'rate', 'date', 'currency_destination', 'producer']
    list_filter = ['currency_origin', 'date']
    ordering = ['-date']

    def get_fields(self, request, obj=None):  # noqa: ARG002
        fields = ['currency_origin', 'rate', 'date', 'currency_destination']
        if request.user.is_superuser or getattr(request.user, 'type', None) == 'Administration':
            fields.append('producer')
        return fields

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        base = Currency.objects.filter(is_base=True).first()
        if base:
            initial['currency_destination'] = base.pk
        return initial

    def save_model(self, request, obj, form, change):
        if not (request.user.is_superuser or getattr(request.user, 'type', None) == 'Administration'):
            from user.admin.adminSite import get_producer_for_request
            producer = get_producer_for_request(request)
            if producer:
                obj.producer = producer
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('currency_origin', 'currency_destination', 'producer')
        if request.user.is_superuser or getattr(request.user, 'type', None) == 'Administration':
            return qs
        from user.admin.adminSite import get_producer_for_request
        from user.models.user_producer import UserProducer
        if getattr(request.user, 'type', None) == 'Organization':
            producers = UserProducer.objects.filter(association=request.user)
            return qs.filter(producer__in=producers)
        producer = get_producer_for_request(request)
        if producer:
            return qs.filter(producer=producer)
        return qs.none()


adminSite.register(exchangeRate, ExchangeRateAdmin)
adminSite.register(TypeVarCropTechnique)
adminSite.register(SiloType)
adminSite.register(StorageServiceType)
