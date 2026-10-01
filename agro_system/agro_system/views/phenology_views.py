import logging

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from producer.models.lot import Lot
from producer.models.country_side import Countryside
from producer.models.staff import Staff
from parameter.models.campaign import Campaing
from operation.models.crop import Crop

from crop_monitoring.models.biofix import Biofix
from crop_monitoring.models.gdd_accumulator import GDDAccumulator
from crop_monitoring.models.phenological_state import PhenologicalState
from crop_monitoring.models.phenological_observation import PhenologicalObservation

logger = logging.getLogger(__name__)


@login_required
def PhenologyView(request):

    # ── 1. Parámetros GET ─────────────────────────────────────────
    countryside_id = request.GET.get('countryside')
    lot_id         = request.GET.get('lot')
    campaing_id    = request.GET.get('campaing')
    crop_id        = request.GET.get('crop')

    user  = request.user
    staff = None

    if user.type == 'Staff':
        staff         = Staff.objects.filter(user=user).first()
        country_sides = Countryside.objects.filter(producer=staff.producer)
        crops         = Crop.objects.filter(responsible=staff)
    elif user.type == 'Producer':
        country_sides = Countryside.objects.filter(producer=user)
        crops         = Crop.objects.filter(producer=user)
    elif user.type == 'Administration' or user.is_superuser:
        country_sides = Countryside.objects.all()
        crops         = Crop.objects.all()
    else:
        country_sides = Countryside.objects.none()
        crops         = Crop.objects.none()

    lots      = Lot.objects.filter(countryside__in=country_sides)
    campaings = Campaing.objects.all().order_by('-date_init')
    campaign_active = campaings.filter(active=True).first() or campaings.first()

    selected_campaing = (
        campaings.filter(id=campaing_id).first() if campaing_id else campaign_active
    )
    if selected_campaing:
        crops = crops.filter(campaing=selected_campaing)
    if countryside_id:
        crops = crops.filter(countryside_id=countryside_id)
        lots  = lots.filter(countryside_id=countryside_id)
    if lot_id:
        crops = crops.filter(lot_id=lot_id)
        lots  = lots.filter(id=lot_id)

    selected_crop = (
        crops.filter(id=crop_id).first()
        if crop_id
        else crops.filter(is_main=True).first() or crops.order_by('-id').first()
    )

    # ── 2. Biofix + acumulador ────────────────────────────────────
    biofix      = None
    accumulator = None
    vine_gdd    = None   # accumulated_gdd ya con offset aplicado
    vine_gdd_climatico = None   # solo la parte climática (sin offset)
    gdd_offset  = 0

    if selected_crop:
        biofix = Biofix.objects.filter(
            crop=selected_crop, counter=Biofix.COUNTER_VINE
        ).first()
        if biofix:
            try:
                accumulator        = biofix.accumulator
                vine_gdd           = float(accumulator.accumulated_gdd)
                gdd_offset         = float(accumulator.gdd_offset)
                vine_gdd_climatico = round(vine_gdd - gdd_offset, 1)
            except GDDAccumulator.DoesNotExist:
                pass

    # ── 3. Handle POST ────────────────────────────────────────────
    if request.method == 'POST':
        action   = request.POST.get('action')
        back_url = request.get_full_path()

        if action == 'set_offset' and accumulator:
            raw = request.POST.get('gdd_offset', '').strip()
            try:
                new_offset = float(raw)
                accumulator.gdd_offset = new_offset
                accumulator.recalculate()
                sign = f"+{new_offset:.1f}" if new_offset >= 0 else f"{new_offset:.1f}"
                messages.success(
                    request,
                    f"Offset actualizado a {sign} GDD. Acumulador recalculado."
                )
            except (ValueError, TypeError):
                messages.error(request, "Valor de offset inválido.")
            return redirect(back_url)

        if action == 'register_observation' and selected_crop:
            state_id = request.POST.get('observed_state', '').strip()
            gdd_raw  = request.POST.get('observed_gdd', '').strip()
            notes    = request.POST.get('notes', '').strip()
            if not state_id:
                messages.error(request, "Seleccioná un estadio BBCH.")
                return redirect(back_url)
            try:
                obs = PhenologicalObservation(
                    crop           = selected_crop,
                    date           = timezone.localdate(),
                    observed_state_id = int(state_id),
                    observed_gdd   = float(gdd_raw) if gdd_raw else None,
                    notes          = notes,
                    registered_by  = staff,
                )
                obs.save()
                messages.success(
                    request,
                    "Observación registrada. La calibración fenológica se actualizó automáticamente."
                )
            except Exception as e:
                logger.exception("Error al guardar observación fenológica: %s", e)
                messages.error(request, "Error al guardar la observación.")
            return redirect(back_url)

    # ── 4. Datos fenológicos ──────────────────────────────────────
    calculated_state  = None
    effective_state   = None
    gdd_stage_percent = 0

    if vine_gdd is not None and selected_crop:
        activity = getattr(selected_crop, 'activity', None)
        specie   = getattr(activity, 'specie', None) if activity else None
        lot      = getattr(selected_crop, 'lot', None)
        area     = getattr(lot, 'area', None) if lot else None

        try:
            calculated_state = PhenologicalState.current_stage(
                vine_gdd, specie=specie, area=area
            )
            effective_state = accumulator.effective_state if accumulator else calculated_state

            if calculated_state:
                stage_range = calculated_state.gdd_to - calculated_state.gdd_from
                if stage_range > 0:
                    gdd_stage_percent = min(100, int(
                        (vine_gdd - calculated_state.gdd_from) / stage_range * 100
                    ))
        except Exception as e:
            logger.exception("Error calculando estado fenológico: %s", e)

    last_observation    = None
    recent_observations = []
    if selected_crop:
        qs = (
            PhenologicalObservation.objects
            .filter(crop=selected_crop)
            .select_related('observed_state', 'calculated_state', 'registered_by')
            .order_by('-date')
        )
        last_observation    = qs.first()
        recent_observations = list(qs[:8])

    phenological_states = PhenologicalState.objects.all().order_by('order')

    data = {
        # Topbar
        'country_sides':     country_sides,
        'lots':              lots,
        'crops':             crops,
        'selected_crop':     selected_crop,
        'campaings':         campaings,
        'campaign_active':   campaign_active,
        'campaing_active':   campaign_active,
        'selected_campaing': selected_campaing,
        'today':             timezone.localdate(),

        # Acumulador
        'biofix':            biofix,
        'accumulator':       accumulator,
        'vine_gdd':          vine_gdd,
        'vine_gdd_climatico': vine_gdd_climatico,
        'gdd_offset':        gdd_offset,

        # Fenología
        'calculated_state':  calculated_state,
        'effective_state':   effective_state,
        'last_observation':  last_observation,
        'gdd_stage_percent': gdd_stage_percent,

        # Para el formulario de observación
        'phenological_states':  phenological_states,
        'recent_observations':  recent_observations,
    }

    return render(request, 'pages/fenologia.html', data)
