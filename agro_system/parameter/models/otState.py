from django.db import models
from django.utils.translation import gettext_lazy as _
from .action import Action

class OTState(models.Model):

    """ Modelo para representar los estados de ordenes de trabajo """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    actions = models.ManyToManyField(Action, null=True, blank=True,  verbose_name = _('actions')) 
    is_default  = models.BooleanField(default=False, verbose_name = _('is default')) 

    def __str__(self):
        return f"{self.name}"

    def default():
        return OTState.objects.filter(is_default=True)[0]


    class Meta:
        verbose_name = _('state of work order')
        verbose_name_plural = _('states of work orders')