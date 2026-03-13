from django.db import models
from django.utils.translation import gettext_lazy as _
from .type_var_crop_technique import TypeVarCropTechnique


class VarCropTechnique(models.Model):

    """ Modelo para representar Variables técnicas de cultivo """

    name = models.CharField(max_length=200, unique=True, verbose_name = _('name'))
    type = models.ForeignKey(TypeVarCropTechnique,null=True, on_delete=models.CASCADE, verbose_name = _('type'))
    is_manual = models.BooleanField(default=False, verbose_name = _('is manual'), help_text=_('Indicates if the variable is entered manually or calculated automatically'))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('variable crop technique')
        verbose_name_plural = _('variables crop techniques')