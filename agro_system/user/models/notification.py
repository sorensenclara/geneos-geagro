from django.db import models
from django.utils.translation import gettext_lazy as _
from .user_extend import UserExtend


class Notification(models.Model):

    TYPE_ALERT      = "alert"
    TYPE_WORK_ORDER = "work_order"
    TYPE_PLAN       = "plan"
    TYPE_SYSTEM     = "system"

    TYPE_CHOICES = [
        (TYPE_ALERT,      _("Alert")),
        (TYPE_WORK_ORDER, _("Work order")),
        (TYPE_PLAN,       _("Plan")),
        (TYPE_SYSTEM,     _("System")),
    ]

    # Icon + border color per type — consumed by the topbar template
    TYPE_STYLE = {
        TYPE_ALERT:      {"icon": "mdi-alert-circle-outline",   "border": "border-warning"},
        TYPE_WORK_ORDER: {"icon": "mdi-clipboard-text-outline",  "border": "border-info"},
        TYPE_PLAN:       {"icon": "mdi-billboard",               "border": "border-success"},
        TYPE_SYSTEM:     {"icon": "mdi-information-outline",     "border": "border-secondary"},
    }

    name              = models.CharField(max_length=200, verbose_name=_("name"))
    user              = models.ForeignKey(UserExtend, on_delete=models.CASCADE, verbose_name=_("user"))
    date              = models.DateField(verbose_name=_("date"))
    detail            = models.TextField(verbose_name=_("detail"))
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_SYSTEM,
        verbose_name=_("type"),
    )
    is_read = models.BooleanField(default=False, verbose_name=_("read"))

    def __str__(self):
        return f"{self.user} - {self.date} [{self.notification_type}]"

    @property
    def style(self):
        return self.TYPE_STYLE.get(self.notification_type, self.TYPE_STYLE[self.TYPE_SYSTEM])

    class Meta:
        ordering = ["-id"]
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")
