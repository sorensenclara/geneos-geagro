from django.db import models
from django.utils.translation import gettext_lazy as _
from .action import Action

class CiltivationState(models.Model):

    """ Modelo para representar los estados de cultivo """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    actions = models.ManyToManyField(Action, null=True, blank=True,  verbose_name = _('actions')) 
    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('cultivation state')
        verbose_name_plural = _('cultivation states')