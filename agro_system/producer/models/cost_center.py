from django.db import models
from django.utils.translation import gettext_lazy as _

class CostCenter(models.Model):

    """ Modelo para representar el centro de costo"""

    name = models.CharField(max_length=200, verbose_name = _('name'))
    default = models.BooleanField(default=False, verbose_name = _('default'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.RESTRICT, verbose_name= _('producer'), null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Solo puede haber un centro de costo por defecto por productor
        if self.default:
            CostCenter.objects.filter(default=True, producer=self.producer).exclude(pk=self.pk).update(default=False)

    @classmethod
    def get_default(cls, producer=None):
        """Centro de costo por defecto del productor; si no tiene, el por defecto compartido (sin productor)."""
        cost_center = None
        if producer is not None:
            cost_center = cls.objects.filter(default=True, producer=producer).first()
        return cost_center or cls.objects.filter(default=True, producer__isnull=True).first()

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('center of cost')
        verbose_name_plural = _('centes of cost')
        # Nombre único por productor (y entre los compartidos, sin productor)
        constraints = [
            models.UniqueConstraint(fields=['name', 'producer'], name='unique_cost_center_name_per_producer'),
            models.UniqueConstraint(fields=['name'], condition=models.Q(producer__isnull=True),
                                    name='unique_cost_center_name_shared'),
        ]