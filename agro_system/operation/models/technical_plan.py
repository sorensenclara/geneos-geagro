
from django.db import models
from django.utils.translation import gettext_lazy as _
from .activity import Activity
from parameter.models.area import Area


# Create your models here.

class TechnicalPlan(models.Model):

    """ Modelo para representarun plan tecnico """

    code = models.CharField(max_length=100, verbose_name= _('code'))
    detail = models.TextField(null=True, blank=True,  verbose_name= _('detail'))
    # Referencia para los cálculos proporcionales
    hectares = models.FloatField(verbose_name= _('proportion of hectares'), default=10)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE,verbose_name= _('activity '))
    area = models.ForeignKey(Area, on_delete=models.CASCADE, verbose_name= _('area'))
    # Permite filtrar planes específicos de las empresas que no se comparten.
    active = models.BooleanField(default=True, verbose_name= _('active') )
    producer = models.ForeignKey('user.UserProducer', on_delete=models.CASCADE, blank=True, null=True, verbose_name= _('producer'))

    def __str__(self):
        return f"{self.code}"    

    class Meta:
        verbose_name = _('technical plan')
        verbose_name_plural = _('technical plans')