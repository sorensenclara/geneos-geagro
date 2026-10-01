from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class OperationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'operation'
    verbose_name = _('operations')

    def ready(self):
        import operation.signals