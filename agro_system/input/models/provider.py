from django.db import models
from django.utils.translation import gettext_lazy as _
from .type_provider import TypeProvider 
from agro_system.validacions import validation_cuit 
from parameter.models.city import City


class Provider(models.Model):

    """ Modelo para representar los proveedores"""

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name_company'))
    type = models.ForeignKey(TypeProvider, models.CASCADE, verbose_name = _('type of provider'))
    cuit = models.CharField(max_length=11, unique=True, validators=[validation_cuit])
    address = models.CharField(max_length=50, verbose_name = _('address'))
    city = models.ForeignKey(City, models.CASCADE, verbose_name = _('city'))
    phone = models.CharField(max_length=20, verbose_name = _('phone'))
    email = models.EmailField(null=True, blank=True, verbose_name = _('email'))
    default = models.BooleanField(default=False, verbose_name = _('default'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.RESTRICT, verbose_name= _('producer'), null=True, blank=True)


    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('provider')
        verbose_name_plural = _('providers')