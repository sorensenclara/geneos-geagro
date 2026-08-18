from django.db import models
from django.utils.translation import gettext_lazy as _
from .type_var_crop_technique import TypeVarCropTechnique


class VarCropTechnique(models.Model):

    """ Modelo para representar Variables técnicas de cultivo """

    name = models.CharField(max_length=200, unique=True, verbose_name=_('name'))
    field_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('field name'),
        help_text=_(
            'ORM field name used to read this variable from DailySummary or OpenMeteoHourly '
            '(e.g. "wind_gusts", "tmin"). Leave blank when name already matches the field.'
        ),
    )
    type = models.ForeignKey(TypeVarCropTechnique, null=True, on_delete=models.CASCADE, verbose_name=_('type'))
    is_manual = models.BooleanField(default=False, verbose_name=_('is manual'), help_text=_('Indicates if the variable is entered manually or calculated automatically'))
    is_climatic = models.BooleanField(default=False, verbose_name=_('is climatic'), help_text=_('Marks this variable as a meteorological/climatic variable, available for mapping to external weather stations.'))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('variable crop technique')
        verbose_name_plural = _('variables crop techniques')