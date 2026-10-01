from django.contrib import admin
from user.admin.adminSite import adminSite, ProducerAwareMixin, get_producer_for_request
from operation.models.technical_plan_input import TechnicalPlanInput
from operation.models.technical_plan_detail import TechnicalPlanDetail
from operation.models.technical_plan import TechnicalPlan
from user.models.user_producer import UserProducer
from input.models.input import Input
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


def _filter_inputs(request):
    user = request.user
    if user.is_superuser or getattr(user, 'type', None) == 'Administration':
        return Input.objects.all()
    if getattr(user, 'type', None) == 'Organization':
        producers = UserProducer.objects.filter(organization=user)
        return Input.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))
    if getattr(user, 'type', None) == 'Producer':
        producer = UserProducer.objects.filter(email=user.email).first()
        if producer:
            return Input.objects.filter(Q(producer=producer) | Q(producer__isnull=True))
    return Input.objects.filter(producer__isnull=True)


class TechnicalPlanDetailInline(ProducerAwareMixin, admin.StackedInline):
    model = TechnicalPlanDetail
    extra = 0
    show_change_link = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'contractor':
            producers = self._producers_for_user(request)
            if producers is not None:
                from producer.models.contractor import Contractor
                kwargs['queryset'] = Contractor.objects.filter(producer__in=producers)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TechnicalPlanInputInline(admin.StackedInline):
    model = TechnicalPlanInput
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "technical_plan_detail":
            technical_plan = request.resolver_match.kwargs.get('object_id')
            kwargs["queryset"] = TechnicalPlanDetail.objects.filter(
                technical_plan__id=technical_plan
            )
        elif db_field.name == "input":
            kwargs["queryset"] = _filter_inputs(request)
        elif db_field.name == "store":
            from django.db.models import Q
            from producer.models.store import Store
            from user.models.user_producer import UserProducer
            user = request.user
            if user.is_superuser or getattr(user, 'type', None) == 'Administration':
                pass
            elif getattr(user, 'type', None) == 'Organization':
                producers = UserProducer.objects.filter(organization=user)
                kwargs['queryset'] = Store.objects.filter(Q(producer__in=producers) | Q(producer__isnull=True))
            else:
                # Producer y Staff: almacenes de su productor y los compartidos
                producer = get_producer_for_request(request)
                if producer:
                    kwargs['queryset'] = Store.objects.filter(Q(producer=producer) | Q(producer__isnull=True))
                else:
                    kwargs['queryset'] = Store.objects.filter(producer__isnull=True)
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

class TechnicalPlanAdmin(ProducerAwareMixin, admin.ModelAdmin):
    list_display = ['code','variety','area','producer']
    list_filter = ['active', 'variety','area']
    search_fields = ['codce','variety','producer']
    ordering = ['code']
    actions = [duplicate_plan]

    inlines = [TechnicalPlanDetailInline, TechnicalPlanInputInline]

    def get_list_display(self, request):
        cols = list(super().get_list_display(request))
        if getattr(request.user, 'type', None) in ('Producer', 'Staff'):
            cols = [c for c in cols if c != 'producer']
        return cols

    def save_model(self, request, obj, form, change):
        # Asigna por defecto el usuario productor logueado
        userProducer = get_producer_for_request(request)
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
            userProducer = UserProducer.objects.filter(organization=request.user)
            if userProducer.exists():
                return queryset.filter(Q(producer__in=userProducer) | Q(producer__isnull=True))
        if request.user.type in ('Producer', 'Staff'):
            userProducer = get_producer_for_request(request)
            if userProducer:
                return queryset.filter(Q(producer=userProducer) | Q(producer__isnull=True))
        return queryset.none()



adminSite.register(TechnicalPlan, TechnicalPlanAdmin)