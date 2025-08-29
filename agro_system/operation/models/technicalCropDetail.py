from django.db import models
from django.utils.translation import gettext_lazy as _
from .crop import Crop
from parameter.models.varCropTechnique import VarCropTechnique
from ckeditor.fields import RichTextField

# Create your models here.

class TechnicalCropDetail(models.Model):

    """ Modelo para representar detalles técnicos de cultivos """


    crop = models.ForeignKey(Crop, models.CASCADE, verbose_name= _('crop'))
    varTechnique = models.ForeignKey(VarCropTechnique, models.CASCADE,  verbose_name= _('variable'))
    value = models.FloatField(verbose_name= _('value'))
    date = models.DateField(verbose_name= _('date'))
    detail = RichTextField(max_length=200, null=True, blank=True,  verbose_name= _('detail'))

    

    def __str__(self):
        return f"{self.varTechnique} - {self.value}"    

    class Meta:
        verbose_name = _('Crop technical detail')
        verbose_name_plural = _('Crop technical details')