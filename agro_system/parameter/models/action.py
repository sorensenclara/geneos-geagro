from django.db import models
from django.utils.translation import gettext_lazy as _

class Action(models.Model):

    """ Modelo para representar acciones """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    send_email = models.BooleanField(default=False, verbose_name = _('send email'))
    send_notification = models.BooleanField(default=False, verbose_name = _('send notification'))
    
    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('action')
        verbose_name_plural = _('actions')







