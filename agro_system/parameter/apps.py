from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class ParameterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'parameter'
    verbose_name = _('parameters')