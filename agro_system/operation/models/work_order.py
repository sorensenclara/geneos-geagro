from django.db import models
from django.utils.translation import gettext_lazy as _
from .crop import Crop
from parameter.models.area import Area
from datetime import datetime, time
from parameter.models.campaign import Campaing
from operation.models.service import Service
from parameter.models.ot_state import OTState
from producer.models.staff import Staff



class ActiveWorkOrderManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(stateOT__name="Cancelada por alerta").exclude(stateOT__name="Omitida").exclude(stateOT__name="Cancelada")


class WorkOrder(models.Model):

    objects = models.Manager()
    active  = ActiveWorkOrderManager()

    types = [
        ('TPW', _('Third-Party Work')),
        ('OW', _('Own Work')),
        ('PW', _('Partner Work'))
    ]

    code = models.CharField(max_length=100, verbose_name= _('code'))
    date_emission = models.DateField(verbose_name= _('date emission'))
    date_init = models.DateField(verbose_name= _('date init'))
    date_fin = models.DateField(verbose_name= _('date fin'))
    
    campaing = models.ForeignKey(Campaing, on_delete=models.CASCADE, verbose_name= _('campaign'))
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, verbose_name= _('crop'))
    area = models.ForeignKey(Area, on_delete=models.CASCADE, verbose_name= _('are'))
    # Info de la tarea
    stage = models.ForeignKey('operation.Stage', on_delete=models.CASCADE, verbose_name= _('stage'))
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name= _('service'))
    stateOT = models.ForeignKey(OTState, on_delete=models.CASCADE,verbose_name= _('state ot'))
    type = models.CharField(max_length=3, choices=types, default='OW', verbose_name= _('type'))
    # Responsable interno de ejecutar o controlar según corresponda
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True, verbose_name= _('staff'))
    # Si es una labor de terceros detallar el contratista
    contractor = models.ForeignKey('user.UserProducer', on_delete=models.CASCADE, related_name="contractor_wo", null=True, blank=True,verbose_name= _('contractor'))
    # Si es una labor de socios detallar el contratista
    partner =  models.ForeignKey('user.UserProducer', on_delete=models.CASCADE, related_name="partner_wo", null=True, blank=True, verbose_name= _('partner'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.CASCADE, verbose_name= _('producer'))
    alert = models.ForeignKey(
        'alert.Alert',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='work_orders',
        verbose_name=_('alert'),
    )

    @property
    def init_order(self):
        return datetime.combine(self.date_init,  time(9, 0))

    def __str__(self):
        return f"{self.code} - {self.crop} - {self.stage}"    

    class Meta:
        verbose_name =  _('work order')
        verbose_name_plural =  _('work orders')
