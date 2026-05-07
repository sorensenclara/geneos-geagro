from django.db import models
from django.utils.translation import gettext_lazy as _
from parameter.models.var_crop_technique import VarCropTechnique
from .indicator import Indicator

class Alert(models.Model):

    """ Modelo para representar una alerta generada a partir de la evaluación de un indicador"""

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, verbose_name = _('indicator'), null=True)
    date = models.DateField(verbose_name = _('date'))
    detail = models.TextField(verbose_name = _('detail'))
    crop = models.ForeignKey('operation.Crop', on_delete=models.CASCADE, verbose_name = _('crop'), null=True, blank=True)
    
    def __str__(self):

        return f"{self.name} - {self.date}"

    class Meta:
        verbose_name = _('alert')
        verbose_name_plural = _('alerts')