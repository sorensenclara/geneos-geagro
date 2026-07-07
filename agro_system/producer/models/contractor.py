from django.db import models
from django.utils.translation import gettext_lazy as _


class Contractor(models.Model):

    """ Modelo para representar un contratista externo """

    name = models.CharField(max_length=200, verbose_name=_('name'))
    cuit = models.CharField(max_length=11, null=True, blank=True, verbose_name=_('CUIT'))
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name=_('phone'))
    email = models.EmailField(null=True, blank=True, verbose_name=_('email'))
    address = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('address'))
    notes = models.TextField(null=True, blank=True, verbose_name=_('notes'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.CASCADE,
                                 verbose_name=_('producer'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('contractor')
        verbose_name_plural = _('contractors')
        ordering = ['name']
