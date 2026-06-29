from django.contrib import admin, messages
from user.admin.adminSite import adminSite, ProducerAwareMixin
from operation.models.crop import Crop
from django.utils.translation import gettext_lazy as _
from operation.models.partner_crop import PartnerCrop
from operation.models.technical_crop_detail import TechnicalCropDetail
from operation.models.crop_yields import CropYields
from django.utils.translation import gettext_lazy as _
from user.models.user_producer import UserProducer
from operation.models.technical_plan import TechnicalPlan
from operation.models.technical_plan_detail import TechnicalPlanDetail
from datetime import datetime, timedelta
from operation.models.work_order import WorkOrder
from parameter.models.ot_state import OTState
from operation.models.technical_plan_input import TechnicalPlanInput
from operation.models.input_work_order import InputWorkOrder

class TechnicalCropDetailInline(admin.StackedInline):
    model = TechnicalCropDetail
    show_change_link = True
    extra = 0
    verbose_name_plural =  _("technical details")


class CropYieldsInline(admin.StackedInline):
    model = CropYields
    show_change_link = True
    extra = 0
    verbose_name_plural = _("yields")


class PartnerCropInline(admin.StackedInline):
    model = PartnerCrop
    #form = CultivoSociosAdminForm
    show_change_link = True
    extra = 0
    verbose_name_plural = _("partners")


@admin.action(description=_("Process Plan in Crop"))
def process_plan(modeladmin, request, queryset):

    for obj in queryset:
        if not obj.date_init:
            messages.error(request, _("The crop '%s' cannot be processed because it does not have an start date.") % obj.name)
            continue

        messages.success(request, _("The crop '%s' has been successfully processed.") % obj.name)

    
        plan  = TechnicalPlan.objects.filter(activity=obj.activity).filter(area=obj.area)
        detail_plan = TechnicalPlanDetail.objects.filter(technical_plan=plan.first())

        days = 0
        producer = obj.producer
        campaing = obj.campaing
        area = obj.area
        date_init = obj.date_init

        for detail in detail_plan:
            stage = detail.stage
            service = detail.service
            days_estimate = obj.hectares_productive * detail.days_estimate / plan.first().hectares
            date_fin = date_init + timedelta(days_estimate)
            days+=days_estimate
            partner = None
            contractor = None
            if detail.subcontracted:
                type_wo = 'TPW'
                contractor = detail.contractor
            elif detail.with_partner:
                type_wo = 'PW'
                partner = detail.partner
            else:
                type_wo = 'OW'
            
            
            code=obj.name + ' - ' + service.name + ' - ' + date_init.strftime('%d-%m-%Y')
            
            order = WorkOrder.objects.create(code=code,
                                                date_emission=datetime.today().strftime("%Y-%m-%d"),
                                                date_init=date_init,
                                                date_fin=date_fin,
                                                producer=producer,
                                                campaing=campaing,
                                                crop=obj,
                                                area=area,
                                                stage=stage,
                                                service=service,
                                                stateOT=OTState.default(),
                                                type=type_wo,
                                                staff=obj.responsible,
                                                contractor=contractor,
                                                partner=partner
                                                )
            order.save()
            # La proxima fecha de incio es un día más de la final de la tarea anterior
            date_init = date_fin + timedelta(1)

            input_plan = TechnicalPlanInput.objects.filter(technical_plan_detail=detail)
        
            for item_input in input_plan:
                input = item_input.input
                dose_reference = item_input.dose
                details = item_input.detail
                dose_total = dose_reference * obj.hectares_productive / plan.first().hectares

                InputWorkOrder.objects.create(
                    work_order=order,
                    input=input,
                    dose=dose_total,
                    store=item_input.store,
                    details=details,
                )



class CropAdmin(ProducerAwareMixin, admin.ModelAdmin):
    
    list_display = ['name','campaing', 'countryside', 'lot', 'activity']
    list_filter = ['campaing', 'activity', 'countryside']
    search_fields = ['name']
    ordering = ['campaing', 'activity', 'name']
    inlines = [TechnicalCropDetailInline, CropYieldsInline, PartnerCropInline]

    actions = [process_plan]


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


adminSite.register(Crop, CropAdmin)