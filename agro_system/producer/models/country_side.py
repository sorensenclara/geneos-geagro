from django.db import models
from django.utils.translation import gettext_lazy as _
from parameter.models.countryside_condition import CountrysideCondition
from .staff import Staff
from .cost_center import CostCenter
from parameter.models.city import City
from .store import Store

class Countryside(models.Model):

    """ Modelo para representar el campo """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    condition = models.ForeignKey(CountrysideCondition, models.CASCADE, verbose_name = _('countryside condition'))
    hectares = models.FloatField(default=0, verbose_name = _('hectares'))
    responsible = models.ForeignKey(Staff, models.CASCADE,verbose_name = _('responsible'))
    address = models.CharField(max_length=50, verbose_name = _('address'))
    city = models.ForeignKey(City, models.CASCADE, verbose_name = _('city'))
    phone = models.CharField(max_length=20, verbose_name = _('phone'))
    email = models.EmailField(null=True, blank=True, verbose_name = _('email'))
    cost_center = models.ForeignKey(CostCenter, models.CASCADE, verbose_name = _('cost center'))
    store = models.ForeignKey(Store, models.CASCADE, verbose_name = _('store'))
    observation = models.TextField(blank=True, null=True,verbose_name = _('observation'))
    producer = models.ForeignKey('user.UserProducer', models.CASCADE, verbose_name = _('producer'))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('countryside')
        verbose_name_plural = _('countrysides')