from django.db import models
from django.db.models import Sum, Q
from django.utils.translation import gettext_lazy as _
from datetime import date
from parameter.models.specie import Specie
from parameter.models.campaign import Campaing
from input.models.provider import Provider


class StorageCertificate(models.Model):

    """ Modelo para representar un certificado de depósito emitido por un acopiador. Representa el contrato de almacenamiento de granos en instalaciones de un tercero. Puede convertirse en warrant. """

    ACTIVE = 'active'
    PARTIAL = 'partial'
    CANCELLED = 'cancelled'
    WARRANT = 'warrant'
    STATE_CHOICES = [
        (ACTIVE, _('Active')),
        (PARTIAL, _('Partially withdrawn')),
        (CANCELLED, _('Cancelled')),
        (WARRANT, _('Warrant')),
    ]

    number = models.CharField(max_length=50, unique=True, verbose_name=_('certificate number'))
    date_issue = models.DateField(default=date.today, verbose_name=_('issue date'))
    date_expiry = models.DateField(null=True, blank=True, verbose_name=_('expiry date'))
    storage_provider = models.ForeignKey(
        Provider, on_delete=models.PROTECT,
        limit_choices_to={'type__name': 'Acopiador'},
        verbose_name=_('storage provider'),
    )
    campaing = models.ForeignKey(Campaing, on_delete=models.PROTECT, verbose_name=_('campaing'))
    specie = models.ForeignKey(Specie, on_delete=models.PROTECT, verbose_name=_('specie'))
    crop = models.ForeignKey('operation.Crop', on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name=_('crop'))
    quantity_entry = models.FloatField(verbose_name=_('quantity at entry (tons)'))
    humidity_entry = models.FloatField(null=True, blank=True, verbose_name=_('humidity at entry (%)'))
    impurities_entry = models.FloatField(null=True, blank=True, verbose_name=_('impurities at entry (%)'))
    protein_entry = models.FloatField(null=True, blank=True, verbose_name=_('protein at entry (%)'))
    test_weight_entry = models.FloatField(null=True, blank=True, verbose_name=_('test weight at entry (kg/hl)'))
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=ACTIVE, verbose_name=_('state'))
    is_warrant = models.BooleanField(default=False, verbose_name=_('is warrant'))
    warrant_entity = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('warrant entity'))
    warrant_expiry = models.DateField(null=True, blank=True, verbose_name=_('warrant expiry date'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.CASCADE, verbose_name=_('producer'))
    notes = models.TextField(blank=True, verbose_name=_('notes'))

    def clean(self):
        # El ingreso a un acopiador tercero solo se permite si el cultivo de
        # origen ya tiene un rinde real cargado, respetando ese techo (junto con
        # lo ya acopiado en silos propios y en otros certificados del mismo cultivo).
        if self.crop_id:
            from storage.services import validate_crop_storage_entry
            validate_crop_storage_entry(
                self.crop, self.quantity_entry, certificate_exclude_pk=self.pk)
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        is_new = self.pk is None
        if self.is_warrant:
            self.state = self.WARRANT
        super().save(*args, **kwargs)
        if is_new:
            # El ingreso al acopiador ES un movimiento de entrada — se crea automáticamente
            from .storage_movement import StorageMovement
            StorageMovement.objects.create(
                certificate=self,
                type=StorageMovement.ENTRY,
                date=self.date_issue,
                quantity_tons=self.quantity_entry,
                producer=self.producer,
            )

    @property
    def quantity_available(self):
        totals = self.movements.aggregate(
            entries=Sum('quantity_tons', filter=Q(type='entry')),
            exits=Sum('quantity_tons', filter=Q(type__in=['sale_exit', 'withdrawal', 'transfer'])),
        )
        return max((totals['entries'] or 0) - (totals['exits'] or 0), 0)

    quantity_available.fget.short_description = _('quantity available (tons)')

    def __str__(self):
        return f"{self.number} - {self.storage_provider} ({self.specie})"

    class Meta:
        verbose_name = _('storage certificate')
        verbose_name_plural = _('storage certificates')
        ordering = ['-date_issue']
