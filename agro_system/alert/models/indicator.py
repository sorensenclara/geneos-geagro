from django.db import models
from django.utils.translation import gettext_lazy as _
from parameter.models.var_crop_technique import VarCropTechnique
from user.models.user_extend import UserExtend

class Indicator(models.Model):

    """ Modelo para representar el indicador que se va a evaluar para generar una alerta"""

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    variable_one = models.ForeignKey(VarCropTechnique, on_delete=models.CASCADE, verbose_name = _('variable one'), related_name='variable_one')
    max_var_one = models.FloatField(verbose_name = _('max variable one'))
    min_var_one = models.FloatField(verbose_name = _('min variable one'))
    variable_two = models.ForeignKey(VarCropTechnique, on_delete=models.CASCADE, null=True, blank=True, verbose_name = _('variable two'), related_name='variable_two')
    max_var_two = models.FloatField(verbose_name = _('max variable two'), null=True, blank=True,)
    min_var_two = models.FloatField(verbose_name = _('min variable two'), null=True, blank=True,)
    variable_three = models.ForeignKey(VarCropTechnique, on_delete=models.CASCADE, null=True, blank=True, verbose_name = _('variable three'), related_name='variable_three')
    max_var_three = models.FloatField(verbose_name = _('max variable three'),null=True, blank=True,)
    min_var_three = models.FloatField(verbose_name = _('min variable three'), null=True, blank=True,)
    report_user = models.ManyToManyField(UserExtend, verbose_name = _('user alert'), blank=True)
    report_mails = models.TextField(verbose_name = _('report mails'), blank=True, null=True)
    
    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('indicator')
        verbose_name_plural = _('indicators')