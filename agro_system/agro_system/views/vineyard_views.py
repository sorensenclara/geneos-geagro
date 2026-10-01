import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from producer.models.lot import Lot
from parameter.models.campaign import Campaing
from producer.models.country_side import Countryside
from operation.models.technical_plan import TechnicalPlan
from operation.models.work_order import WorkOrder
from producer.models.staff import Staff
from operation.models.crop import Crop
from agro_system.views.filter_helpers import read_filter, get_producer_ref, build_user_scope

from storage.models.silo import Silo
from storage.models.silo_movement import SiloMovement
from storage.models.storage_certificate import StorageCertificate
from storage.models.storage_movement import StorageMovement
from operation.models.crop_yields import CropYields


def _build_crops_yield_detail(crops_qs):
    """Devuelve lista de dicts con rinde estimado/real por cultivo para mostrar en detalle."""
    result = []
    for crop in crops_qs.select_related('variety', 'lot', 'variety__specie'):
        cy = CropYields.objects.filter(crop=crop).first()
        est  = cy.yields_estimate if cy else None
        real = cy.yields_real if cy else None
        pct  = round((real / est * 100)) if est and real else None
        result.append({
            'crop':     crop,
            'specie':   crop.variety.specie.name if crop.variety and crop.variety.specie else '—',
            'variety': str(crop.variety) if crop.variety else '—',
            'lot':      str(crop.lot) if crop.lot else '—',
            'ha':       crop.hectares_planted or 0,
            'est':      est,
            'real':     real,
            'pct':      pct,
        })
    return result


@login_required
def VineyardView(request):

    # =========================================================
    # filtros desde topbar/dashboard
    # =========================================================
    campaing_id, crop_id = read_filter(request)

    user = request.user
    crops_base, country_sides = build_user_scope(user)

    # TechnicalPlan y Staff filtrados por el mismo scope
    _p = get_producer_ref(user)
    if user.is_superuser or getattr(user, 'type', None) == 'Administration':
        technical_plans = TechnicalPlan.objects.all()
        staff = Staff.objects.all()
    elif getattr(user, 'type', None) == 'Organization':
        from user.models.user_producer import UserProducer
        _producers = UserProducer.objects.filter(organization=user)
        technical_plans = TechnicalPlan.objects.filter(producer__in=_producers)
        staff = Staff.objects.filter(producer__in=_producers)
    elif _p:
        technical_plans = TechnicalPlan.objects.filter(producer=_p)
        staff = Staff.objects.filter(producer=_p)
    else:
        technical_plans = TechnicalPlan.objects.none()
        staff = Staff.objects.none()

    # =========================================================
    # campaña seleccionada / activa
    # =========================================================
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

    # =========================================================
    #  cultivo principal / seleccionado
    # =========================================================
    if crop_id:
        main_crop = crops.filter(id=crop_id).first()
    else:
        main_crop = crops.filter(is_main=True).first() or crops.order_by('-id').first()

    # =========================================================
    # métricas reales
    # =========================================================
    total_productive_hectares = lots.aggregate(
        total=Sum('hectares_productive')
    )['total'] or 0

    # =========================================================
    # ACOPIO por campo
    # =========================================================
    producer_ref = get_producer_ref(user)

    sf = {'producer': producer_ref} if producer_ref else {}

    # Silos con stock calculado
    silos_qs = Silo.objects.filter(active=True, **sf).select_related('countryside', 'type')
    silos_con_stock = []
    for silo in silos_qs:
        s_in  = SiloMovement.objects.filter(silo=silo, type='entry').aggregate(t=Sum('quantity_tons'))['t'] or 0
        s_out = SiloMovement.objects.filter(silo=silo, type__in=['exit', 'transfer']).aggregate(t=Sum('quantity_tons'))['t'] or 0
        silos_con_stock.append({
            'silo': silo,
            'stock': round(max(0, s_in - s_out), 2),
            'capacity': silo.capacity_tons,
            'pct': min(100, round((max(0, s_in - s_out) / silo.capacity_tons * 100) if silo.capacity_tons else 0)),
        })

    acopio_silo_total = sum(s['stock'] for s in silos_con_stock)

    # Certificados de acopio externo activos
    certs_activos = StorageCertificate.objects.filter(
        state__in=['active', 'partial'], **sf
    ).select_related('storage_provider', 'specie', 'campaing')

    # Stock disponible por certificado
    certs_con_stock = []
    cert_total_entry = 0
    cert_total_disponible = 0
    for cert in certs_activos:
        exits = StorageMovement.objects.filter(
            certificate=cert,
            type__in=['sale_exit', 'withdrawal', 'transfer']
        ).aggregate(t=Sum('quantity_tons'))['t'] or 0
        disponible = max(0, cert.quantity_entry - exits)
        cert_total_entry += cert.quantity_entry
        cert_total_disponible += disponible
        certs_con_stock.append({
            'cert': cert,
            'disponible': round(disponible, 2),
            'entrada': cert.quantity_entry,
        })

    # Chart ventas últimas campañas (reutiliza datos del dashboard)
    recent_campaigns = list(reversed(list(Campaing.objects.order_by('-date_init')[:5])))
    chart_labels   = [c.name for c in recent_campaigns]
    chart_acopiado = []
    chart_vendido  = []
    for camp in recent_campaigns:
        date_fin = camp.date_final
        si_in = SiloMovement.objects.filter(type='entry', date__gte=camp.date_init, **sf)
        if date_fin:
            si_in = si_in.filter(date__lte=date_fin)
        si_in = si_in.aggregate(t=Sum('quantity_tons'))['t'] or 0

        ci_in = StorageCertificate.objects.filter(campaing=camp, **sf).aggregate(t=Sum('quantity_entry'))['t'] or 0

        si_out = SiloMovement.objects.filter(type='exit', date__gte=camp.date_init, **sf)
        if date_fin:
            si_out = si_out.filter(date__lte=date_fin)
        si_out = si_out.aggregate(t=Sum('quantity_tons'))['t'] or 0

        ci_out_f = {'certificate__campaing': camp}
        if producer_ref:
            ci_out_f['certificate__producer'] = producer_ref
        ci_out = StorageMovement.objects.filter(type='sale_exit', **ci_out_f).aggregate(t=Sum('quantity_tons'))['t'] or 0

        chart_acopiado.append(round(si_in + ci_in, 2))
        chart_vendido.append(round(si_out + ci_out, 2))

    data = {
        'technical_plans': technical_plans,
        'staff': staff,
        'country_sides': country_sides,
        'lots': lots,
        'crops': crops,
        'campaings': campaings,

        'selected_campaing': selected_campaing,
        'campaign_active': campaign_active,

        'selected_crop': main_crop,
        'crop_selected': main_crop,
        'crop_main': main_crop,
        'main_crop': main_crop,

        'total_productive_hectares': total_productive_hectares,

        # Acopio
        'silos_con_stock': silos_con_stock,
        'acopio_silo_total': round(acopio_silo_total, 2),
        'certs_con_stock': certs_con_stock,
        'acopio_externo_total': round(cert_total_disponible, 2),
        'acopio_total': round(acopio_silo_total + cert_total_disponible, 2),

        # Chart
        'chart_labels_json': json.dumps(chart_labels),
        'chart_acopiado_json': json.dumps(chart_acopiado),
        'chart_vendido_json': json.dumps(chart_vendido),

        # Detalle rendimiento por cultivo de la campaña seleccionada
        'crops_yield_detail': _build_crops_yield_detail(crops),
    }

    return render(request, 'pages/vineyard.html', data)