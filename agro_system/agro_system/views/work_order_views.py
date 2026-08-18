from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from datetime import date

from operation.models.work_order import WorkOrder
from operation.models.input_work_order import InputWorkOrder
from operation.models.crop import Crop
from operation.models.stage import Stage
from operation.models.service import Service
from input.models.input import Input
from parameter.models.ot_state import OTState
from user.models.user_producer import UserProducer
from producer.models.staff import Staff


def _ot_queryset_for_user(user):
    """Devuelve el queryset de WorkOrders accesible según el rol del usuario."""
    if user.type == 'Producer':
        return WorkOrder.objects.filter(producer=user)
    if user.type == 'Staff':
        staff = Staff.objects.filter(user=user).first()
        if staff:
            return WorkOrder.objects.filter(producer=staff.producer)
        return WorkOrder.objects.none()
    # Administration u otros: ve todo
    return WorkOrder.objects.all()


@login_required
def WorkOrderDetailView(request, pk):
    work_order = get_object_or_404(_ot_queryset_for_user(request.user), pk=pk)
    input_work_orders = InputWorkOrder.objects.filter(
        work_order=work_order
    ).select_related("input__unit_measure", "input__currency")

    ot_states       = OTState.objects.all().order_by("name")
    contractors     = UserProducer.objects.all().order_by("name")
    available_inputs = Input.objects.select_related("unit_measure").order_by("name")

    if request.method == "POST":
        # --- Campos editables de la OT ---
        state_id      = request.POST.get("stateOT")
        contractor_id = request.POST.get("contractor") or None
        partner_id    = request.POST.get("partner")    or None
        date_fin      = request.POST.get("date_fin")   or None

        if state_id:
            work_order.stateOT_id = state_id
        work_order.contractor_id = contractor_id
        work_order.partner_id    = partner_id
        if date_fin:
            work_order.date_fin  = date_fin
        work_order.save()

        # --- Actualizar dosis aplicadas e insumos existentes ---
        for iwo in input_work_orders:
            key_dose    = f"iwo_{iwo.pk}_dose_applied"
            key_details = f"iwo_{iwo.pk}_details"
            raw_dose = request.POST.get(key_dose, "").strip()
            iwo.dose_applied = float(raw_dose) if raw_dose else None
            iwo.details      = request.POST.get(key_details, "").strip() or None
            iwo.save()

        # --- Agregar insumos nuevos ---
        raw_count = request.POST.get("new_inputs_count", "0").strip()
        new_count = int(raw_count) if raw_count.isdigit() else 0
        for i in range(new_count):
            input_id  = request.POST.get(f"new_input_{i}")
            raw_dose  = (request.POST.get(f"new_dose_{i}") or "").strip()
            details   = (request.POST.get(f"new_details_{i}") or "").strip()
            if input_id and raw_dose:
                InputWorkOrder.objects.create(
                    work_order=work_order,
                    input_id=int(input_id),
                    dose=float(raw_dose),
                    dose_applied=None,
                    details=details or None,
                )

        return redirect("work-order-detail", pk=pk)

    data = {
        "work_order":      work_order,
        "input_work_orders": input_work_orders,
        "ot_states":       ot_states,
        "contractors":     contractors,
        "available_inputs": available_inputs,
    }
    return render(request, "pages/work_order_detail.html", data)


@login_required
def WorkOrderCreateView(request):
    user = request.user

    # Contexto del cultivo seleccionado (viene como query param desde el plan)
    crop_id     = request.GET.get("crop") or request.POST.get("crop_id")
    campaing_id = request.GET.get("campaing") or request.POST.get("campaing_id")

    selected_crop = None
    if crop_id:
        qs_crop = _ot_queryset_for_user(user).values_list("crop_id", flat=True)
        # Verificar que el crop pertenece al contexto del usuario
        selected_crop = Crop.objects.filter(
            pk=crop_id, producer__in=_allowed_producers(user)
        ).select_related("campaing", "area", "producer", "activity").first()

    stages    = Stage.objects.filter(activity=selected_crop.activity).order_by("order") if selected_crop else Stage.objects.all().order_by("name")
    services  = Service.objects.all().order_by("name")
    ot_states = OTState.objects.all().order_by("name")
    staff_qs  = Staff.objects.filter(producer=selected_crop.producer).order_by("surname") if selected_crop else Staff.objects.all().order_by("surname")
    contractors = UserProducer.objects.all().order_by("name")
    available_inputs = Input.objects.select_related("unit_measure").order_by("name")

    if request.method == "POST":
        code       = request.POST.get("code", "").strip()
        date_init  = request.POST.get("date_init")
        date_fin   = request.POST.get("date_fin") or None
        wo_type    = request.POST.get("type", "OW")
        stage_id   = request.POST.get("stage")
        service_id = request.POST.get("service")
        staff_id   = request.POST.get("staff")
        state_id   = request.POST.get("stateOT")
        contractor_id = request.POST.get("contractor") or None
        partner_id    = request.POST.get("partner")    or None
        c_crop_id     = request.POST.get("crop_id")
        c_campaing_id = request.POST.get("campaing_id")
        c_area_id     = request.POST.get("area_id")
        c_producer_id = request.POST.get("producer_id")

        wo = WorkOrder.objects.create(
            code=code,
            date_emission=date.today(),
            date_init=date_init,
            date_fin=date_fin or date_init,
            type=wo_type,
            crop_id=c_crop_id,
            campaing_id=c_campaing_id,
            area_id=c_area_id,
            producer_id=c_producer_id,
            stage_id=stage_id,
            service_id=service_id,
            staff_id=staff_id,
            stateOT_id=state_id,
            contractor_id=contractor_id,
            partner_id=partner_id,
        )

        # Insumos nuevos
        raw_count = request.POST.get("new_inputs_count", "0").strip()
        new_count = int(raw_count) if raw_count.isdigit() else 0
        for i in range(new_count):
            input_id = request.POST.get(f"new_input_{i}")
            raw_dose = (request.POST.get(f"new_dose_{i}") or "").strip()
            details  = (request.POST.get(f"new_details_{i}") or "").strip()
            if input_id and raw_dose:
                InputWorkOrder.objects.create(
                    work_order=wo,
                    input_id=int(input_id),
                    dose=float(raw_dose),
                    dose_applied=None,
                    details=details or None,
                )

        return redirect("work-order-detail", pk=wo.pk)

    data = {
        "selected_crop":     selected_crop,
        "crop_id":           crop_id,
        "campaing_id":       campaing_id,
        "stages":            stages,
        "services":          services,
        "ot_states":         ot_states,
        "staff_list":        staff_qs,
        "contractors":       contractors,
        "available_inputs":  available_inputs,
        "today":             date.today(),
        "wo_types":          WorkOrder.types,
    }
    return render(request, "pages/work_order_create.html", data)


def _allowed_producers(user):
    """Productores a los que el usuario tiene acceso."""
    if user.type == 'Producer':
        return UserProducer.objects.filter(pk=user.pk)
    if user.type == 'Staff':
        staff = Staff.objects.filter(user=user).first()
        if staff:
            return UserProducer.objects.filter(pk=staff.producer_id)
        return UserProducer.objects.none()
    return UserProducer.objects.all()
