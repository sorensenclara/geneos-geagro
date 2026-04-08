from django.db import models
from django.utils.translation import gettext_lazy as _
from parameter.models.var_crop_technique import VarCropTechnique
from .user_extend import UserExtend

class Notification(models.Model):

    """ Modelo para representar una notificación generada a partir de la evaluación de un indicador al usaurio"""

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    user = models.ForeignKey(UserExtend, on_delete=models.CASCADE, verbose_name = _('user'))
    date = models.DateField(verbose_name = _('date'))
    detail = models.TextField(verbose_name = _('detail'))

    def __str__(self):
        return f"{self.user} - {self.date}"

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')