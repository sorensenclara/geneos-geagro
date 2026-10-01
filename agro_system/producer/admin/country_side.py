from django.contrib import admin
from user.admin.adminSite import adminSite
from producer.models.country_side import Countryside
from user.models.user_producer import UserProducer
from producer.models.staff import Staff
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.core.serializers import serialize
from producer.models.lot import Lot

# Register your models here.
class CountrysideAdmin(admin.ModelAdmin):
    list_display = ['name', 'condition', 'hectares', 'responsible', 'city', 'cost_center']
    list_filter = ['condition','responsible','city']
    search_fields = ['name']

    def save_model(self, request, obj, form, change):
        # Asigna por defecto el usuario productor logueado
        userProducer = UserProducer.objects.filter(email=request.user.email).first()
        if userProducer:
            obj.producer = userProducer
        super().save_model(request, obj, form, change)
        
    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == "responsible":
            staff_qs = Staff.objects.none()
            # superuser ve todos
            if request.user.is_superuser or request.user.type in ['Administration']:
                staff_qs = Staff.objects.all()
            # si es una organización → ve todos los staff de sus productores
            elif request.user.type == 'Organization':
                user_producers = UserProducer.objects.filter(association=request.user)
                staff_qs = Staff.objects.filter(producer__in=user_producers)
            # si es un productor → ve solo sus staff
            elif request.user.type == 'Producer':
                user_producer = UserProducer.objects.filter(email=request.user.email).first()
                if user_producer:
                    staff_qs = Staff.objects.filter(producer=user_producer)
            kwargs["queryset"] = staff_qs
            
        if db_field.name == "producer":
            if request.user.type == "Organization":
                kwargs["queryset"] = UserProducer.objects.filter(association=request.user)
            elif request.user.type == "Producer":
                kwargs["queryset"] = UserProducer.objects.filter(email=request.user.email)
        if db_field.name == "store":
            # Almacenes del productor y los compartidos (sin productor)
            from user.admin.producer_scope import visible_stores
            kwargs["queryset"] = visible_stores(request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
        campo = Countryside.objects.get(pk=campo_id)
        lotes = Lot.objects.filter(campo=campo).exclude(delimitacion__isnull=True)
        lotes_geojson = serialize('geojson', lotes, geometry_field='delimitacion', fields=('name',))
        context = dict(
            self.admin_site.each_context(request),
            campo=campo,
            lotes_geojson=lotes_geojson,
        )
        return TemplateResponse(request, "admin/campo/mapa_lotes_admin.html", context)


adminSite.register(Countryside, CountrysideAdmin)