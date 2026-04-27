
from django.db import models
from django.utils.translation import gettext_lazy as _
from .technical_plan import TechnicalPlan
from operation.models.service import Service
from operation.models.stage import Stage
from user.models import UserProducer
# Create your models here.

class TechnicalPlanDetail(models.Model):

    """ Modelo para representarun el detalle de un  plan tecnico """

    technical_plan = models.ForeignKey(TechnicalPlan, on_delete=models.CASCADE,  verbose_name= _('technical plan'))
    secuence = models.IntegerField(verbose_name= _('secuence'))
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, verbose_name= _('stage'))
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name= _('service'))
    days_estimate = models.IntegerField( verbose_name= _('days estimate'))
    cant_persons = models.IntegerField(verbose_name= _('cant persons'), blank=True, null=True)
    active = models.BooleanField(default=True, verbose_name= _('active'))
    subcontracted = models.BooleanField(default=False, verbose_name= _('subcontracted'))
    contractor = models.ForeignKey(UserProducer, on_delete=models.CASCADE, null=True, blank=True, verbose_name= _('contractor'), related_name='contractor')
    with_partner = models.BooleanField(default=False, verbose_name= _('with partner'))
    partner = models.ForeignKey(UserProducer, on_delete=models.CASCADE, verbose_name= _('partner'), null=True, blank=True,  related_name='partner')


    def __str__(self):
        return f"{self.secuence} - {self.stage} / {self.service}"    

    class Meta:
        verbose_name = _('technical plan detail')
        verbose_name_plural = _('technical plan detail')
        ordering = ["secuence"]