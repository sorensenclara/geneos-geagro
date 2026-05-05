from django.contrib import admin
from user.admin.adminSite import adminSite  
from operation.models.work_order import WorkOrder
from operation.models.input_work_order import InputWorkOrder
from django.utils.translation import gettext_lazy as _
from parameter.models.ot_state import OTState
from django.urls import reverse
from django.http import HttpResponseRedirect
from user.models.user_producer import UserProducer

class InputWorkOrderInline(admin.StackedInline):
    model = InputWorkOrder
    extra = 0
    show_change_link = True
    verbose_name_plural = _("Inputs")

@admin.action(description="Finalizar orden")
def finish_order(modeladmin, request, queryset):
    for obj in queryset:
        obj.state = OTState.objects.filter(nombre="Finalizada")[0]
        obj.save()
        inputs = InputWorkOrder.objects.filter(work_order=obj)
        if inputs:
            for input in inputs:
                if input.dose_applied:
                    input.input.stock -= input.dose_applied
                    input.input.save()


@admin.action(description=_("Print work orders"))
def download_pdf(modeladmin, request, queryset):
    # Obtén la URL de la vista personalizada
    url = reverse('operation:work_orders_pdf')
    ids = ','.join(str(obj.id) for obj in queryset)
    url = f'{url}?ids={ids}'

    # Redirige a la vista personalizada
    return HttpResponseRedirect(url)

class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'code']
    list_filter = []
    search_fields = ['code']
    ordering = ['id']

    inlines = [InputWorkOrderInline]  # Clara: reactivado para cargar insumos en OT
    actions = []

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

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if request.user.type == 'Producer':
            return ['producer']
        return readonly_fields

    #  Limitar choices del campo en el formulario
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "producer":
            if request.user.type == "Organization":
                kwargs["queryset"] = UserProducer.objects.filter(association=request.user)
            elif request.user.type == "Producer":
                kwargs["queryset"] = UserProducer.objects.filter(email=request.user.email)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


adminSite.register(WorkOrder, WorkOrderAdmin)
