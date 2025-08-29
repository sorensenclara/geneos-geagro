from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class InputsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'input'
    verbose_name = _('inputs')
