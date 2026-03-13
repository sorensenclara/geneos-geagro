from django.contrib import admin
from user.admin.adminSite import adminSite
from input.models.purchase_order import PurchaseOrder
from input.models.purchase_order_detail import PurchaseOrderDetail
from user.models.user_producer import UserProducer
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME


@admin.action(description=_("Process Purchase Order"))
def procesar_purchase_order(modeladmin, request, queryset):
    queryset.update(state="confirm")
    
    for obj in queryset:
        details = PurchaseOrderDetail.objects.filter(purchase_order=obj)
        for item in details:
            item.pending_amount = item.amount
            item.input.save()
            item.save()

@admin.action(description=_("Pending purchases"))
def input_pending_pdf(modeladmin, request, queryset):
    # Obtén la URL de la vista personalizada
    url = reverse('input:input_pending_pdf')
    url = f'{url}'
    
    # Redirige a la vista personalizada
    return HttpResponseRedirect(url)


class PurchaseOrderDetailInline(admin.StackedInline):
    model = PurchaseOrderDetail
    readonly_fields = ['pending_amount', 'total']
    extra = 0
    
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['number','date', 'provider', 'state']
    list_filter = ['state', 'provider']
    search_fields = ['number',]
    inlines = [PurchaseOrderDetailInline]
    actions = [procesar_purchase_order, input_pending_pdf]

    def changelist_view(self, request, extra_context=None):
        if 'action' in request.POST and (request.POST['action'] == 'input_pending_pdf'):
            if not request.POST.getlist(ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                post.update({ACTION_CHECKBOX_NAME: str(PurchaseOrder.objects.first().number)})
                request._set_post(post)
        return super(PurchaseOrderAdmin, self).changelist_view(request, extra_context)

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


adminSite.register(PurchaseOrder, PurchaseOrderAdmin)