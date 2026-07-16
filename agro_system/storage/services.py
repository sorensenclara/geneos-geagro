from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _


def get_real_yield_tons(crop):
    """Devuelve (tiene_rinde_real, toneladas_totales) para `crop`, a partir del
    rinde real (tn/ha) más reciente cargado en CropYields y sus hectáreas
    cosechadas. Si no hay ningún rinde real cargado, devuelve (False, None)."""
    from operation.models.crop_yields import CropYields

    ultimo_real = (
        CropYields.objects
        .filter(crop=crop, yields_real__isnull=False)
        .order_by('-date_real', '-pk')
        .first()
    )
    if not ultimo_real:
        return False, None
    return True, ultimo_real.yields_real * (crop.hectares_harvested or 0)


def validate_crop_storage_entry(crop, quantity_tons, *, silo_movement_exclude_pk=None,
                                 certificate_exclude_pk=None):
    """Valida que se pueda ingresar `quantity_tons` de grano acopiado (a un silo
    propio o a un certificado de depósito en terceros) desde `crop`: exige que el
    cultivo tenga un rinde real cargado y que el total histórico ya acopiado desde
    ese cultivo (silos propios + certificados) más esta nueva cantidad no supere el
    rinde real (rinde real tn/ha x hectáreas cosechadas)."""
    from storage.models.silo_movement import SiloMovement
    from storage.models.storage_certificate import StorageCertificate

    tiene_rinde_real, techo = get_real_yield_tons(crop)
    if not tiene_rinde_real:
        raise ValidationError(_(
            'No se puede acopiar grano de "%(crop)s": todavía no se cargó su rinde real '
            '(CropYields.yields_real).'
        ) % {'crop': crop})

    ya_acopiado_silo = SiloMovement.objects.filter(
        crop=crop, type=SiloMovement.ENTRY
    ).exclude(pk=silo_movement_exclude_pk).aggregate(t=Sum('quantity_tons'))['t'] or 0
    ya_acopiado_certificado = StorageCertificate.objects.filter(
        crop=crop
    ).exclude(pk=certificate_exclude_pk).aggregate(t=Sum('quantity_entry'))['t'] or 0

    total_luego = ya_acopiado_silo + ya_acopiado_certificado + quantity_tons
    if total_luego > techo + 1e-6:
        raise ValidationError(_(
            'El acopio de "%(crop)s" superaría su rinde real disponible: ya acopiado '
            '%(acopiado).2f tn + %(nuevo).2f tn nuevas > %(techo).2f tn de rinde real.'
        ) % {
            'crop': crop,
            'acopiado': ya_acopiado_silo + ya_acopiado_certificado,
            'nuevo': quantity_tons,
            'techo': techo,
        })
