from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Case, When, IntegerField, Value
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


def _current_stage_for_crop(crop):
    """Returns the operation Stage matching the crop's current phenological state, or None.
    Uses the same effective_state logic as the dashboard (calibration + field observations)."""
    try:
        from crop_monitoring.models.gdd_accumulator import GDDAccumulator
        from crop_monitoring.models.biofix import Biofix
        acc = GDDAccumulator.objects.filter(
            biofix__crop=crop, biofix__counter=Biofix.COUNTER_VINE
        ).select_related("biofix__crop__activity__specie", "biofix__crop__area").order_by("-calculation_date").first()
        if acc is None:
            return None
        pheno = acc.effective_state  # same logic the dashboard uses
        if pheno is None:
            return None
        if pheno.stage_id:
            return pheno.stage
    except Exception:
        pass
    return None


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

    ot_states       = _ordered_ot_states()
    contractors     = UserProducer.objects.all().order_by("name")
    available_inputs = Input.objects.select_related("unit_measure").order_by("name")

    if request.method == "POST":
        # --- Campos editables de la OT ---
        state_id      = request.POST.get("stateOT")
        contractor_id = request.POST.get("contractor") or None
        partner_id    = request.POST.get("partner")    or None
        date_fin      = request.POST.get("date_fin")   or None

        # Build change summary before applying new values
        changes = []
        if state_id and str(work_order.stateOT_id) != str(state_id):
            try:
                new_state = OTState.objects.get(pk=state_id)
                changes.append(f"Estado: {work_order.stateOT} → {new_state.name}")
            except OTState.DoesNotExist:
                pass
        old_date_fin = str(work_order.date_fin) if work_order.date_fin else None
        if date_fin and date_fin != old_date_fin:
            changes.append(f"Fecha fin: {old_date_fin or '—'} → {date_fin}")

        # Count new inputs being added
        raw_count = request.POST.get("new_inputs_count", "0").strip()
        new_count = int(raw_count) if raw_count.isdigit() else 0
        new_input_names = []
        for i in range(new_count):
            input_id = request.POST.get(f"new_input_{i}")
            if input_id and request.POST.get(f"new_dose_{i}", "").strip():
                try:
                    from input.models.input import Input as InputModel
                    new_input_names.append(str(InputModel.objects.get(pk=input_id).name))
                except Exception:
                    new_input_names.append("insumo")
        if new_input_names:
            changes.append(f"Insumos agregados: {', '.join(new_input_names)}")

        # Check dose updates on existing inputs
        dose_updated = False
        for iwo in input_work_orders:
            raw_dose = request.POST.get(f"iwo_{iwo.pk}_dose_applied", "").strip()
            new_dose = float(raw_dose) if raw_dose else None
            if new_dose != iwo.dose_applied:
                dose_updated = True
                break
        if dose_updated:
            changes.append("Dosis aplicadas actualizadas")

        if state_id:
            work_order.stateOT_id = state_id
        work_order.contractor_id = contractor_id
        work_order.partner_id    = partner_id
        if date_fin:
            work_order.date_fin  = date_fin
        work_order._edited_by = request.user
        work_order._change_summary = "; ".join(changes) if changes else None
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
    ot_states = _ordered_ot_states()
    staff_qs  = Staff.objects.filter(producer=selected_crop.producer).order_by("surname") if selected_crop else Staff.objects.all().order_by("surname")
    contractors = UserProducer.objects.all().order_by("name")
    available_inputs = Input.objects.select_related("unit_measure").order_by("name")

    if request.method == "POST":
        code       = request.POST.get("code", "").strip()
        date_init  = request.POST.get("date_init")
        date_fin   = request.POST.get("date_fin") or None
        wo_type    = request.POST.get("type", "OW")
        stage_id   = request.POST.get("stage") or None
        service_id = request.POST.get("service") or None
        staff_id   = request.POST.get("staff") or None
        state_id   = request.POST.get("stateOT") or None
        contractor_id = request.POST.get("contractor") or None
        partner_id    = request.POST.get("partner")    or None
        c_crop_id     = request.POST.get("crop_id")
        c_campaing_id = request.POST.get("campaing_id")
        c_area_id     = request.POST.get("area_id")
        c_producer_id = request.POST.get("producer_id")

        # Auto-fill stage from crop's current phenological stage
        if not stage_id and selected_crop:
            auto_stage = _current_stage_for_crop(selected_crop)
            if auto_stage:
                stage_id = auto_stage.pk

        # Validate required fields
        errors = {}
        if not code:
            errors["code"] = "El código es obligatorio."
        if not date_init:
            errors["date_init"] = "La fecha de inicio es obligatoria."
        if not service_id:
            errors["service"] = "El servicio es obligatorio."
        if not state_id:
            errors["stateOT"] = "El estado es obligatorio."
        if not stage_id:
            errors["stage"] = "La etapa es obligatoria y no se pudo determinar automáticamente."

        if errors:
            data = {
                "selected_crop":    selected_crop,
                "crop_id":          c_crop_id,
                "campaing_id":      c_campaing_id,
                "stages":           stages,
                "services":         services,
                "ot_states":        ot_states,
                "staff_list":       staff_qs,
                "contractors":      contractors,
                "available_inputs": available_inputs,
                "today":            date.today(),
                "wo_types":         WorkOrder.types,
                "errors":           errors,
                "post":             request.POST,
            }
            return render(request, "pages/work_order_create.html", data)

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


def _ordered_ot_states():
    return OTState.objects.exclude(name="Contingente").annotate(
        sort_order=Case(
            When(name="Pendiente",            then=Value(0)),
            When(name="En curso",             then=Value(1)),
            When(name="Finalizada",           then=Value(2)),
            When(name="Cancelada",            then=Value(3)),
            When(name="Cancelada por alerta", then=Value(4)),
            default=Value(99),
            output_field=IntegerField(),
        )
    ).order_by("sort_order")


@login_required
@require_POST
def WorkOrderQuickStateView(request, pk):
    wo = get_object_or_404(_ot_queryset_for_user(request.user), pk=pk)
    state_id = request.POST.get("stateOT")
    if not state_id:
        return JsonResponse({"ok": False, "error": "state required"}, status=400)
    try:
        state = OTState.objects.get(pk=state_id)
    except OTState.DoesNotExist:
        return JsonResponse({"ok": False, "error": "invalid state"}, status=400)
    old_state_name = str(wo.stateOT) if wo.stateOT_id else "—"
    wo.stateOT = state
    wo._edited_by = request.user
    wo._change_summary = f"Estado: {old_state_name} → {state.name}"
    wo.save()
    return JsonResponse({"ok": True, "state_name": str(state.name)})
