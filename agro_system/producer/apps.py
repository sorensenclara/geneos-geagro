from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class ProducerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'producer'
    verbose_name = _('producers')
