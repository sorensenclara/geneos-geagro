from django.db import models
from django.utils.translation import gettext_lazy as _
from parameter.models.city import City


class Store(models.Model):

    """ Modelo para representar los almacenes """

    name = models.CharField(max_length=200, verbose_name = _('name'))
    address = models.CharField(max_length=50, verbose_name = _('address'))
    city = models.ForeignKey(City, models.CASCADE, verbose_name = _('city'))
    default = models.BooleanField(default=False, verbose_name = _('default'))
    producer = models.ForeignKey('user.UserProducer', on_delete=models.RESTRICT, verbose_name= _('producer'), null=True, blank=True)


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Solo puede haber un almacén por defecto por productor
        if self.default:
            Store.objects.filter(default=True, producer=self.producer).exclude(pk=self.pk).update(default=False)

    @classmethod
    def get_default(cls, producer=None):
        """Almacén por defecto del productor; si no tiene, el por defecto compartido (sin productor)."""
        store = None
        if producer is not None:
            store = cls.objects.filter(default=True, producer=producer).first()
        return store or cls.objects.filter(default=True, producer__isnull=True).first()

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('Store')
        verbose_name_plural = _('Stores')
        # Nombre único por productor (y entre los compartidos, sin productor)
        constraints = [
            models.UniqueConstraint(fields=['name', 'producer'], name='unique_store_name_per_producer'),
            models.UniqueConstraint(fields=['name'], condition=models.Q(producer__isnull=True),
                                    name='unique_store_name_shared'),
        ]