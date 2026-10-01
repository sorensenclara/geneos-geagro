from django.db import models
from django.utils.translation import gettext_lazy as _
from .crop import Crop


# Create your models here.

class CropYields(models.Model):

    """ Modelo para representar rindes de cultivos """


    crop = models.ForeignKey(Crop, models.CASCADE, verbose_name= _('crop'))
    date_estimate = models.DateField(verbose_name= _('date estimate'))
    yields_estimate = models.FloatField(verbose_name= _('yields estimate'))
    date_real =  models.DateField(blank=True, null=True, verbose_name= _('date real'))
    yields_real = models.FloatField(blank=True, null=True, verbose_name= _('yields real'))
    detail = models.CharField(max_length=200, null=True, blank=True,  verbose_name= _('detail'))


    @property
    def especie(self):
        return self.crop.variety.specie    

    def __str__(self):
        return f"{self.date_estimate} - {self.yields_estimate}"    

    class Meta:
        verbose_name = _('yields crop')
        verbose_name_plural = _('yields crops')