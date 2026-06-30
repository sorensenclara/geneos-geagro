# myapp/admin.py
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from datetime import datetime

# from dateutil.relativedelta import relativedelta

from input.models.purchase_reception_detail import PurchaseReceptionDetail
from input.models.input import Input

# =========================
# CLARA - Imports dashboard agronómico
from parameter.models.campaign import Campaing
from operation.models.crop import Crop
from operation.models.work_order import WorkOrder
from operation.models.input_work_order import InputWorkOrder
from alert.models.alert import Alert


class MiAdmin(AdminSite):
    # site_header = "Mi Panel de Administración"
    # site_title = "Admin"
    # index_title = "Bienvenido al Dashboard"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}

        # =========================================================
        # DEV - lógica original de recepciones / insumos
        # =========================================================
        date = datetime.now().date()
        date_first_day = date.replace(day=1)

        filter_kwargs = {
            f"{'date'}__range": (date_first_day, date)
        }

        all_receipts = PurchaseReceptionDetail.objects.values('input').annotate(res=Sum('amount'))

        list_product_ammount = []
        list_product_receipt = []

        for prod in all_receipts:
            input_obj = Input.objects.filter(id=prod['input']).first()
            if input_obj:
                list_product_receipt.append(input_obj.name)
                list_product_ammount.append(prod['res'])

        extra_context['product_receipt'] = list_product_receipt
        extra_context['ammount_receipt'] = list_product_ammount


        campaing_id = request.GET.get("campaing")
        crop_id = request.GET.get("crop")

        if campaing_id:
            campaing = Campaing.objects.filter(id=campaing_id).first()
        else:
            campaing = Campaing.objects.filter(active=True).first() or Campaing.objects.order_by("-date_init").first()

        if crop_id:
            crop = Crop.objects.filter(id=crop_id).first()
        else:
            crop = (
                Crop.objects.filter(campaing=campaing, is_main=True).first()
                or Crop.objects.filter(campaing=campaing).order_by("-id").first()
                if campaing else None
            )

        campaings = Campaing.objects.all().order_by("-date_init")
        crops = Crop.objects.filter(campaing=campaing).order_by("-id") if campaing else Crop.objects.none()

        ordenes = WorkOrder.objects.filter(crop=crop).order_by("date_init") if crop else WorkOrder.objects.none()

        proxima_orden = ordenes.filter(date_fin__gte=date).order_by("date_init").first() if crop else None
        next_work_orders = ordenes.filter(date_fin__gte=date).order_by("date_init")[:5] if crop else []

        insumos_ot = InputWorkOrder.objects.filter(work_order__crop=crop) if crop else InputWorkOrder.objects.none()

        alerts = Alert.objects.filter(crop=crop).order_by("-date")[:5] if crop else []
        alerts_count = Alert.objects.filter(crop=crop).count() if crop else 0

        missing_inputs = []
        required_inputs_total = 0
        available_inputs_total = 0

        for item in insumos_ot:
            required_inputs_total += item.dose or 0
            available_inputs_total += item.input.stock or 0

            if item.input.stock <= 0 or item.input.stock < item.dose:
                missing_inputs.append(item)

        resumen = {
            "campaing": campaing.name if campaing else "-",
            "crop": str(crop) if crop else "-",
            "campo_lote": f"{crop.countryside} / {crop.lot}" if crop else "-",
            "actividad": crop.activity if crop else "-",
            "estado": crop.state if crop else "-",
            "hectareas_productivas": crop.hectares_productive if crop else 0,
            "hectareas_plantadas": crop.hectares_planted if crop else 0,
        }

        extra_context.update({
            # filtros
            "campaings": campaings,
            "campaings": campaings,  # compatibilidad legacy
            "crops": crops,

            # selección actual
            "selected_campaing": campaing,
            "selected_crop": crop,
            "campaing": campaing,
            "crop": crop,
            "campania": campaing,   # compatibilidad templates
            "cultivo": crop,

            # datos principales
            "resumen": resumen,
            "ordenes": ordenes,
            "proxima_orden": proxima_orden,
            "next_work_orders": next_work_orders,

            # alertas
            "alerts": alerts,
            "alerts_count": alerts_count,

            # insumos
            "insumos_ot": insumos_ot,
            "required_inputs": insumos_ot,
            "missing_inputs": missing_inputs,
            "missing_inputs_count": len(missing_inputs),
            "required_inputs_total": required_inputs_total,
            "available_inputs_total": available_inputs_total,

            "plan_progress": 0,
        })
                
        return super().index(request, extra_context=extra_context)


adminSite = MiAdmin(name='miadmin')


PRODUCER_TYPES = ('Producer', 'Staff', 'Organization')


class ProducerAwareMixin:
    """
    Permite que usuarios Producer/Staff/Organization vean y gestionen los modelos
    del admin sin necesitar permisos Django explícitos.
    - Producer/Staff/Organization: puede ver, agregar y modificar.
    El filtrado de datos por productor se delega a get_queryset() de cada ModelAdmin.
    La organización puede eliminar, pero el productor y su staff no.
    """

    def has_module_permission(self, request):
        if request.user.is_active and request.user.type in PRODUCER_TYPES:
            return True
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        if request.user.is_active and request.user.type in PRODUCER_TYPES:
            return True
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        if request.user.is_active and request.user.type in PRODUCER_TYPES:
            return True
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.is_active and request.user.type in PRODUCER_TYPES:
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_active and request.user.type == 'Organization':
            return True
        if request.user.is_active and request.user.type in ('Producer', 'Staff'):
            return False
        return super().has_delete_permission(request, obj)

    def get_exclude(self, request, obj=None):
        excluded = list(super().get_exclude(request, obj) or [])
        if not (request.user.is_superuser or request.user.type == 'Administration'):
            if 'producer' not in excluded:
                excluded.append('producer')
        return excluded