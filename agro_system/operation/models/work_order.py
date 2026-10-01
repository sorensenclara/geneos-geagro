from django.db import models
from django.db.models import Max
from django.db.models.functions import Cast
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import localdate
from .crop import Crop
from parameter.models.area import Area
from datetime import datetime, time
from parameter.models.campaign import Campaing
from operation.models.service import Service
from parameter.models.ot_state import OTState
from producer.models.staff import Staff



class WorkOrder(models.Model):

    types = [
        ('TPW', _('Third-Party Work')),
        ('OW', _('Own Work')),
        ('PW', _('Partner Work'))
    ]

    # Si queda vacío se numera solo por productor: 0001, 0002... (ver _next_code)
    code = models.CharField(max_length=100, blank=True, verbose_name= _('code'),
                            help_text=_('If left empty, it is numbered automatically (0001, 0002...).'))
    # Los campos con blank=True sin null=True se completan automáticamente (ver _fill_defaults)
    date_emission = models.DateField(blank=True, verbose_name= _('date emission'))
    date_init = models.DateField(verbose_name= _('date init'))
    date_fin = models.DateField(blank=True, verbose_name= _('date fin'))

    campaing = models.ForeignKey(Campaing, on_delete=models.CASCADE, blank=True, verbose_name= _('campaign'))
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, verbose_name= _('crop'))
    surface = models.FloatField(null=True, blank=True, verbose_name= _('surface (ha)'))
    area = models.ForeignKey(Area, on_delete=models.CASCADE, blank=True, verbose_name= _('are'))
    # Info de la tarea
    stage = models.ForeignKey('operation.Stage', on_delete=models.CASCADE, null=True, blank=True, verbose_name= _('stage'))
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True, verbose_name= _('service'))
    stateOT = models.ForeignKey(OTState, on_delete=models.CASCADE, blank=True, verbose_name= _('state ot'))
    type = models.CharField(max_length=3, choices=types, default='OW', verbose_name= _('type'))
    # Responsable interno de ejecutar o controlar según corresponda
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True, verbose_name= _('staff'))
    # Si es una labor de terceros detallar el contratista
    contractor = models.ForeignKey('producer.Contractor', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('contractor'))
    contractor_cost = models.FloatField(null=True, blank=True, verbose_name=_('contractor cost (planned, base currency)'))
    contractor_cost_real = models.FloatField(null=True, blank=True, verbose_name=_('contractor cost (real, base currency)'))
    # Si es una labor de socios detallar el contratista
    partner =  models.ForeignKey('user.UserProducer', on_delete=models.CASCADE, related_name="partner_wo", null=True, blank=True, verbose_name= _('partner'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.CASCADE, verbose_name= _('producer'))
    
    def _fill_defaults(self):
        """Completa los campos que no se cargaron en el formulario."""
        if not self.date_emission:
            self.date_emission = localdate()
        if not self.date_fin and self.date_init:
            self.date_fin = self.date_init
        crop = self.crop if self.crop_id else None
        if not self.campaing_id:
            # La campaña activa; si no hay ninguna, la del cultivo
            self.campaing = Campaing.objects.filter(active=True).first() or (crop.campaing if crop else None)
        if not self.area_id and crop:
            self.area = crop.area
        if not self.stateOT_id:
            self.stateOT = (OTState.objects.filter(is_default=True).first()
                            or OTState.objects.filter(name='Pendiente').first())

    def clean(self):
        super().clean()
        self._fill_defaults()
        errors = {}
        if not self.campaing_id:
            errors['campaing'] = _('There is no active campaign. Select one.')
        if not self.stateOT_id:
            errors['stateOT'] = _('There is no default work order state. Select one.')
        if errors:
            raise ValidationError(errors)

    def _next_code(self):
        """Siguiente código numérico del productor: el mayor código solo numérico + 1, con 4 dígitos."""
        last = (WorkOrder.objects
                .filter(producer_id=self.producer_id, code__regex=r'^\d+$')
                .annotate(code_number=Cast('code', models.BigIntegerField()))
                .aggregate(last=Max('code_number'))['last']) or 0
        return f"{last + 1:04d}"

    def save(self, *args, **kwargs):
        self._fill_defaults()
        # El código se asigna acá (no en clean) porque el productor lo completa el admin en save_model
        if not self.code and self.producer_id:
            self.code = self._next_code()
        super().save(*args, **kwargs)

    @property
    def contractor_cost_diff(self):
        """Real - planeado del costo de contratista (moneda base); None si falta alguno."""
        if self.contractor_cost is None or self.contractor_cost_real is None:
            return None
        return round(self.contractor_cost_real - self.contractor_cost, 2)

    @property
    def init_order(self):
        return datetime.combine(self.date_init,  time(9, 0))

    def __str__(self):
        if self.stage_id:
            return f"{self.code} - {self.crop} - {self.stage}"
        return f"{self.code} - {self.crop}"

    class Meta:
        verbose_name =  _('work order')
        verbose_name_plural =  _('work orders')
