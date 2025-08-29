from django.db import models
from django.utils.translation import gettext_lazy as _
from agro_system.validacions import validation_cuit 
from parameter.models.city import City
from input.models.provider import Provider

class Driver(models.Model):

    """ Modelo para representar los choferes de un transportista"""

    name = models.CharField(max_length=200, verbose_name = _('name'))
    cuit = models.CharField(max_length=11, unique=True, validators=[validation_cuit])
    address = models.CharField(max_length=50, verbose_name = _('address'))
    city = models.ForeignKey(City, models.CASCADE, verbose_name = _('city'))
    phone = models.CharField(max_length=20, verbose_name = _('phone'))
    email = models.EmailField(null=True, blank=True, verbose_name = _('email'))
    provider = models.ForeignKey(Provider, models.CASCADE, verbose_name = _('carrier'), limit_choices_to={"type": "Transportista"})


    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('driver')
        verbose_name_plural = _('drivers')