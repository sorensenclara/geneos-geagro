from django.db import models
from django.utils.translation import gettext_lazy as _


class Campaing(models.Model):

    """ Modelo para representar Campañas """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    date_init = models.DateField(verbose_name = _('date init'))
    date_final = models.DateField(verbose_name = _('date final'))
    active = models.BooleanField(default=False, verbose_name = _('active'))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('campaign')
        verbose_name_plural = _('campaigns')
        ordering = ['-date_init']