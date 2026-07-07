from django.db import models
from django.utils.translation import gettext_lazy as _
from operation.models.activity import Activity

class Stage(models.Model):

    """ Modelo para representar estadios de cultivo """

    name = models.CharField(max_length=200, verbose_name = _('name'))
    activity = models.ForeignKey(Activity, verbose_name = _('activity'), on_delete=models.CASCADE)
    order = models.PositiveIntegerField(verbose_name = _('order'))
    
    def __str__(self):
        return f"{self.activity} - {self.name}"

    class Meta:
        verbose_name = _('stage')
        verbose_name_plural = _('stages')
        unique_together = [('name', 'activity')]