from django.contrib import admin
from user.admin.adminSite import adminSite
from operation.models.technical_plan_input import TechnicalPlanInput
from operation.models.technical_plan_detail import TechnicalPlanDetail
from operation.models.technical_plan import TechnicalPlan
from user.models.user_producer import UserProducer
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class TechnicalPlanDetailInline(admin.StackedInline):
    model = TechnicalPlanDetail
    extra = 0
    show_change_link = True


class TechnicalPlanInputInline(admin.StackedInline):
    model = TechnicalPlanInput
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "technical_plan_detail":
            technical_plan = request.resolver_match.kwargs.get('object_id')
            kwargs["queryset"] = TechnicalPlanDetail.objects.filter(
                technical_plan__id=technical_plan
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.action(description=_("Duplicate Technical Plan"))
def duplicate_plan(modeladmin, request, queryset):
    
    for obj in queryset:
        details = TechnicalPlanDetail.objects.filter(technical_plan=obj)
        inputs = TechnicalPlanInput.objects.filter(technical_plan=obj)
        obj.pk = None
        obj.code += " Versión 2"
        obj.save()
        for detail in details:
            detail.pk = None
            detail.technical_plan = obj
            detail.save()
        for input in inputs:
            input.pk = None
            input.technical_plan = obj
            input.save()

class TechnicalPlanAdmin(admin.ModelAdmin):
    list_display = ['code','activity','area','producer']
    list_filter = ['active', 'activity','area']
    search_fields = ['codce','activity','producer']
    ordering = ['code']
    actions = [duplicate_plan]

    inlines = [TechnicalPlanDetailInline, TechnicalPlanInputInline]

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
                return queryset.filter(Q(producer__in=userProducer) | Q(producer__isnull=True))
        if request.user.type == 'Producer':
            userProducer = UserProducer.objects.filter(email=request.user.email).first()
            if userProducer:
                return queryset.filter(Q(producer=userProducer) | Q(producer__isnull=True))
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



adminSite.register(TechnicalPlan, TechnicalPlanAdmin)