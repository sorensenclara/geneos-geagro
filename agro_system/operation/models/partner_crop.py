from django.db import models
from django.db import models
from django.utils.translation import gettext_lazy as _
from .crop import Crop

# Create your models here.

class PartnerCrop(models.Model):

    """ Modelo para representar los socios de cultivos """


    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, verbose_name= _('crop'))
    partner = models.ForeignKey('user.UserProducer', on_delete=models.CASCADE,  verbose_name= _('partner'))
    percentage = models.FloatField(verbose_name= _('value'))
   

    

    def __str__(self):
        return f"{self.varTechnique} - {self.value}"    

    class Meta:
        verbose_name = _('partner in crop')
        verbose_name_plural = _('partners in crops')