from django.contrib import admin
from django.db.models import Q
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from producer.models.country_side import Countryside
from user.models.user_producer import UserProducer
from producer.models.staff import Staff
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from django.core.serializers import serialize
from producer.models.lot import Lot
from producer.models.store import Store
from producer.models.cost_center import CostCenter

# Register your models here.
class CountrysideAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['name', 'condition', 'hectares', 'responsible', 'city', 'cost_center', 'ver_mapa']
    list_filter = ['condition','responsible','city']
    search_fields = ['name']

    def save_model(self, request, obj, form, change):
        # Asigna por defecto el usuario productor logueado
        userProducer = get_producer_for_request(request)
        if userProducer:
            obj.producer = userProducer
        super().save_model(request, obj, form, change)
        
    def get_changeform_initial_data(self, request):
        # Al crear un campo se preseleccionan el almacén y el centro de costo por defecto
        # (el usuario puede dejarlos vacíos)
        initial = super().get_changeform_initial_data(request)
        producer = get_producer_for_request(request)
        default_store = Store.get_default(producer)
        default_cost_center = CostCenter.get_default(producer)
        if default_store and 'store' not in initial:
            initial['store'] = default_store.pk
        if default_cost_center and 'cost_center' not in initial:
            initial['cost_center'] = default_cost_center.pk
        return initial

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == "responsible":
            staff_qs = Staff.objects.none()
            # superuser ve todos
            if request.user.is_superuser or request.user.type in ['Administration']:
                staff_qs = Staff.objects.all()
            # si es una organización → ve todos los staff de sus productores
            elif request.user.type == 'Organization':
                user_producers = UserProducer.objects.filter(organization=request.user)
                staff_qs = Staff.objects.filter(producer__in=user_producers)
            # si es un productor → ve solo sus staff
            elif request.user.type in ('Producer', 'Staff'):
                user_producer = get_producer_for_request(request)
                if user_producer:
                    staff_qs = Staff.objects.filter(producer=user_producer)
            kwargs["queryset"] = staff_qs

        # Almacenes y centros de costo: los del productor y los compartidos (sin productor)
        elif db_field.name in ("store", "cost_center"):
            producers = self._producers_for_user(request)
            if producers is not None:
                model = Store if db_field.name == "store" else CostCenter
                kwargs["queryset"] = model.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))

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
                return queryset.filter(producer__in=userProducer)
        if request.user.type in ('Producer', 'Staff'):
            userProducer = get_producer_for_request(request)
            if userProducer:
                return queryset.filter(producer=userProducer)
        return queryset.none()

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:campo_id>/mapa_admin/', self.admin_site.admin_view(self.mapa_admin_view), name='campo-mapa-admin'),
        ]
        return custom_urls + urls

    def ver_mapa(self, obj):
        return format_html(
            '<a href="{}/mapa_admin/" target="_blank">Ver mapa</a>', obj.id
        )
    ver_mapa.short_description = "Mapa"

    def mapa_admin_view(self, request, campo_id):
        # get_queryset filtra por productor: solo se ve el mapa de campos propios
        campo = get_object_or_404(self.get_queryset(request), pk=campo_id)
        lotes = Lot.objects.filter(countryside=campo).exclude(delimitation__isnull=True)
        lotes_geojson = serialize('geojson', lotes, geometry_field='delimitation', fields=('name',))
        context = dict(
            self.admin_site.each_context(request),
            campo=campo,
            lotes_geojson=lotes_geojson,
        )
        return TemplateResponse(request, "admin/campo/mapa_lotes_admin.html", context)


adminSite.register(Countryside, CountrysideAdmin)