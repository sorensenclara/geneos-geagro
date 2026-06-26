
from django.db import models
from django.utils.translation import gettext_lazy as _
from .technical_plan import TechnicalPlan
from .technical_plan_detail import TechnicalPlanDetail
from input.models.input import Input
from producer.models.store import Store


# Create your models here.

class TechnicalPlanInput(models.Model):

    """ Modelo para representarun los insumos de un plan tecnico """

    technical_plan = models.ForeignKey(TechnicalPlan, models.CASCADE, verbose_name= _('technical plan'))
    technical_plan_detail = models.ForeignKey(TechnicalPlanDetail, models.CASCADE, verbose_name= _('technical plan detail'))
    input = models.ForeignKey(Input, models.CASCADE, verbose_name= _('input'))
    dose = models.FloatField(verbose_name= _('dose'))
    store = models.ForeignKey(Store, models.SET_NULL, null=True, blank=True, verbose_name=_('store'))
    detail = models.TextField(null=True, blank=True, verbose_name= _('detail'))

    def __str__(self):
        return f"{self.input} - {self.dose}"    
    

    class Meta:
        verbose_name = _('technical plan input')
        verbose_name_plural = _('technical plan inputs')