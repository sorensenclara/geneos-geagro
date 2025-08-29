from django.db import models
from input.models import Provider
from input.models.typeProvider import TypeProvider
from django.utils.translation import gettext_lazy as _


class Carrier(Provider):

    """Modelo que representa a los proveedores transportistas."""
    
    class Meta:
        proxy = True
        verbose_name = _("Carrier")
        verbose_name_plural = _("Carriers")


    def save(self, *args, **kwargs):
        type = TypeProvider.objects.get(name="Transportista")
        if type:
            self.type = type
        super().save(*args, **kwargs)