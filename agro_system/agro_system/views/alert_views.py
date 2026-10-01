from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import date

from alert.models.alert import Alert
from alert.models.alert_outcome import AlertOutcome
from operation.models.crop import Crop
from producer.models.country_side import Countryside
from producer.models.lot import Lot
from parameter.models.campaign import Campaing
from producer.models.staff import Staff
from user.models.notification import Notification
from user.admin.producer_scope import accessible_crops, producers_for
from django.utils import timezone


def _alert_recipients(alert, exclude_user=None):
    """All users to notify for an alert change: producer + responsible + all staff with users."""
    crop = alert.crop
    if crop is None:
        return set()
    users = set()
    if crop.producer:
        users.add(crop.producer)
    if crop.responsible and crop.responsible.user_id:
        users.add(crop.responsible.user)
    for staff in Staff.objects.filter(producer=crop.producer, user__isnull=False).select_related("user"):
        users.add(staff.user)
    if exclude_user is not None:
        users.discard(exclude_user)
    return users

@login_required
def AlertView(request):

    # =========================================================
    # CLARA - filtros desde topbar/dashboard
    # =========================================================
    countryside_id = request.GET.get('countryside')
    lot_id = request.GET.get('lot')
    campaing_id = request.GET.get('campaing')
    crop_id = request.GET.get('crop')
    selected_status = request.GET.get('status')
    search_query = request.GET.get('q')

    user = request.user

    # Visibilidad: solo cultivos/campos del productor del usuario (todo para Administración).
    # Sin fallbacks a "todos": un productor sin cultivos no ve los de otros.
    crops_base = accessible_crops(user)
    producers = producers_for(user)
    country_sides = Countryside.objects.all() if producers is None else Countryside.objects.filter(producer__in=producers)

    campaings = Campaing.objects.all()
    campaign_active = campaings.filter(active=True).first()

    if campaing_id:
        selected_campaing = campaings.filter(id=campaing_id).first()
    else:
        selected_campaing = campaign_active or campaings.first()

    lots = Lot.objects.filter(countryside__in=country_sides)

    crops = crops_base

    if selected_campaing:
        crops = crops.filter(campaing_id=selected_campaing.id)

    if countryside_id:
        crops = crops.filter(countryside_id=countryside_id)
        lots = lots.filter(countryside_id=countryside_id)

    if lot_id:
        crops = crops.filter(lot_id=lot_id)
        lots = lots.filter(id=lot_id)

    if crop_id:
        selected_crop = crops.filter(id=crop_id).first()
    else:
        selected_crop = crops.filter(is_main=True).first() or crops.order_by('-id').first()

    alerts = Alert.active.none()

    if selected_crop:
        alerts = Alert.active.filter(
            crop=selected_crop
        ).order_by('-date')

    if selected_status == 'active':
        alerts = alerts.filter(date__gte=date.today())

    elif selected_status == 'history':
        alerts = alerts.filter(date__lt=date.today()).order_by('-date')

    if search_query:
        alerts = alerts.filter(
            Q(name__icontains=search_query) |
            Q(detail__icontains=search_query)
        ).order_by('-date')

    alerts_count = alerts.count()
    featured_alert = alerts.first()

    data = {
        'country_sides': country_sides,
        'lots': lots,
        'crops': crops,
        'campaings': campaings,

        'selected_crop': selected_crop,
        'crop_main': selected_crop,
        'selected_campaing': selected_campaing,
        'campaign_active': campaign_active,

        'alerts': alerts,
        'alerts_count': alerts_count,
        'featured_alert': featured_alert,

        'selected_status': selected_status,
        'search_query': search_query,
        'today': date.today(),
    }

    return render(request, 'pages/alert.html', data)


@login_required
def AlertOutcomeView(request, alert_id):
    # Solo alertas de cultivos del usuario: una alerta ajena da 404 (ni se ve ni se edita)
    alert = get_object_or_404(Alert, pk=alert_id, crop__in=accessible_crops(request.user))
    outcome, _ = AlertOutcome.objects.get_or_create(alert=alert)

    staff = Staff.objects.filter(user=request.user).first()

    if request.method == "POST":
        outcome.damage_occurred        = request.POST.get("damage_occurred") == "on"
        outcome.damage_severity        = request.POST.get("damage_severity", AlertOutcome.SEVERITY_NONE)
        raw_area                       = request.POST.get("area_affected_pct", "").strip()
        outcome.area_affected_pct      = float(raw_area) if raw_area else None
        raw_kg                         = request.POST.get("estimated_loss_kg_ha", "").strip()
        outcome.estimated_loss_kg_ha   = float(raw_kg) if raw_kg else None
        raw_ars                        = request.POST.get("estimated_loss_ars", "").strip()
        outcome.estimated_loss_ars     = float(raw_ars) if raw_ars else None
        outcome.intervention_effective = request.POST.get("intervention_effective", AlertOutcome.EFFECTIVENESS_NA)
        outcome.notes                  = request.POST.get("notes", "").strip()
        if staff and not outcome.registered_by_id:
            outcome.registered_by = staff
        outcome.save()

        # Notify all relevant users about the outcome registration (exclude the editor)
        damage_label = "con daño" if outcome.damage_occurred else "sin daño"
        notif_detail = f"{alert.crop} — {alert.indicator} ({damage_label})."
        for user in _alert_recipients(alert, exclude_user=request.user):
            Notification.objects.create(
                name=f"Resultado registrado: {alert.indicator}",
                detail=notif_detail,
                date=timezone.localdate(),
                user=user,
                notification_type=Notification.TYPE_ALERT,
            )

        back = request.POST.get("back_url", "alert")
        return redirect(back)

    back_url = request.GET.get("back", "alert")
    return render(request, "pages/alert_outcome.html", {
        "alert":   alert,
        "outcome": outcome,
        "severity_choices":      AlertOutcome.SEVERITY_CHOICES,
        "effectiveness_choices": AlertOutcome.EFFECTIVENESS_CHOICES,
        "back_url": back_url,
    })