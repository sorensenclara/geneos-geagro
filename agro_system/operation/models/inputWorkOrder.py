from django.db import models
from django.utils.translation import gettext_lazy as _
from .workOrder import WorkOrder
from input.models.input import Input

class InputWorkOrder(models.Model):
    """ Modelo que representa los insumos de la orden de trabajo"""

    work_order = models.ForeignKey(WorkOrder, models.CASCADE, verbose_name= _('work order'))
    input = models.ForeignKey(Input, models.CASCADE, verbose_name= _('input'))
    dose = models.FloatField(verbose_name= _('planned dose'))
    dose_applied = models.FloatField(null=True, blank=True, verbose_name= _('dose applied'))
    details = models.TextField(null=True, blank=True, verbose_name= _('details'))

    def __str__(self):
        return f"{self.work_order} - {self.input} - {self.dose}"    

    class Meta:
        verbose_name =  _('input work order')
        verbose_name_plural =  _('inputs work orders')