from django.db import models
from .userExtend import UserExtend
from django.contrib.auth.models import Group
from .userOrganization import UserOrganization
from django.utils.translation import gettext_lazy as _
from agro_system.validacions import validation_cuit 
from parameter.models.city import City

class UserProducer(UserExtend):
    """
    Modelo que representa al usuario productor heredado del usuario extendido
    """
   
    name = models.CharField(max_length=100, verbose_name = _('name_company'))
    cuit = models.CharField(max_length=11, unique=True,validators=[validation_cuit])
    address = models.CharField(max_length=50, verbose_name = _('address'))
    city = models.ForeignKey(City, models.CASCADE,verbose_name = _('city'))
    phone = models.CharField(max_length=20,verbose_name = _('phone'))
    organization = models.ForeignKey(UserOrganization, on_delete=models.RESTRICT, null=True, blank=True, verbose_name = _('organization'))
    prefix = models.CharField(blank=True, null=True, verbose_name = _('prefix'))
    sequence = models.IntegerField(blank=True, null=True, verbose_name = _('sequence'))

    class Meta:
        verbose_name = _('userProducer'),
        verbose_name_plural = _('usersProducers')

    def save(self, *args, **kwargs):
        self.type = 'Producer'
        self.is_staff = True
        super().save(*args, **kwargs)
        
    
    def __str__(self):
        return self.name