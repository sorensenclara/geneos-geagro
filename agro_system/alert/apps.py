from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class AlertConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alert'
    verbose_name = _('alerts')

    def ready(self):
        import alert.signals
    