from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from .sales_receipt import SalesReceipt


class SaleStockAllocation(models.Model):

    """ Asigna una venta a una o varias fuentes de stock acopiado (un silo propio
    -a través de su SiloStock por cultivo- o un certificado de depósito en un
    acopiador tercero), para poder generar los movimientos de salida
    correspondientes al confirmar la venta. """

    sales_receipt = models.ForeignKey(
        SalesReceipt, on_delete=models.CASCADE, related_name='stock_allocations',
        verbose_name=_('sales receipt'))
    silo_stock = models.ForeignKey(
        'storage.SiloStock', on_delete=models.PROTECT, null=True, blank=True,
        verbose_name=_('silo stock'))
    certificate = models.ForeignKey(
        'storage.StorageCertificate', on_delete=models.PROTECT, null=True, blank=True,
        verbose_name=_('storage certificate'))
    quantity_tons = models.FloatField(verbose_name=_('quantity (tons)'))

    def clean(self):
        if bool(self.silo_stock_id) == bool(self.certificate_id):
            raise ValidationError(_(
                'Debe indicar exactamente un silo propio o un certificado de '
                'depósito, no ambos ni ninguno.'
            ))

        if self.silo_stock_id:
            origen = self.silo_stock
            disponible = origen.quantity_tons
            especie_origen_id = origen.specie_id
        else:
            origen = self.certificate
            disponible = origen.quantity_available
            especie_origen_id = origen.specie_id

        if self.sales_receipt_id and self.sales_receipt.especie_id and \
                especie_origen_id and especie_origen_id != self.sales_receipt.especie_id:
            raise ValidationError(_(
                'La especie de "%(origen)s" no coincide con la especie de la venta.'
            ) % {'origen': origen})

        # Lo ya reservado por otras asignaciones de ventas todavía no confirmadas
        # (una venta confirmada ya generó su movimiento y quedó reflejada en
        # `disponible`; una cancelada no compromete stock).
        filtro_origen = {'silo_stock_id': self.silo_stock_id} if self.silo_stock_id \
            else {'certificate_id': self.certificate_id}
        ya_reservado = SaleStockAllocation.objects.filter(**filtro_origen).exclude(
            pk=self.pk
        ).exclude(sales_receipt__state__in=['confirm', 'cancel']).aggregate(
            t=Sum('quantity_tons'))['t'] or 0

        if ya_reservado + self.quantity_tons > disponible + 1e-6:
            raise ValidationError(_(
                'La cantidad asignada supera el disponible en %(origen)s '
                '(%(disponible).2f tn, %(reservado).2f tn ya reservadas por otras ventas).'
            ) % {'origen': origen, 'disponible': disponible, 'reservado': ya_reservado})

        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        origen = self.silo_stock or self.certificate
        return f"{self.sales_receipt} ← {origen} ({self.quantity_tons} tn)"

    class Meta:
        verbose_name = _('sale stock allocation')
        verbose_name_plural = _('sale stock allocations')
