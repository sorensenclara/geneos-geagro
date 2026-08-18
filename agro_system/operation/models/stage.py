from django.db import models
from django.utils.translation import gettext_lazy as _
from operation.models.variety import Variety


class Stage(models.Model):
    """
    Estadio operativo del año vitícola (Poda, Brotación, Floración y Cuaje, …).

    Los estados fenológicos (PhenologicalState) que componen este estadio apuntan
    acá vía FK inversa `phenological_states`. bbch_from_int / bbch_to_int derivan
    el rango BBCH entero a partir del primer y último estadio fenológico asignado.
    """

    name     = models.CharField(max_length=200, unique=True, verbose_name=_('name'))
    activity = models.ForeignKey(Variety, verbose_name=_('variety'), on_delete=models.CASCADE)
    order    = models.PositiveIntegerField(verbose_name=_('order'))

    @property
    def bbch_from_int(self) -> int | None:
        """Código BBCH entero de inicio (ej. '01-09' → 1). None si sin rango."""
        first = self.phenological_states.order_by('order').first()
        if first is None:
            return None
        return int(first.bbch.split("-")[0])

    @property
    def bbch_to_int(self) -> int | None:
        """Código BBCH entero de fin (ej. '71-73' → 73). None si sin rango."""
        last = self.phenological_states.order_by('order').last()
        if last is None:
            return None
        return int(last.bbch.split("-")[-1])

    @property
    def bbch_range_display(self) -> str:
        f, t = self.bbch_from_int, self.bbch_to_int
        if f is None:
            return "—"
        return f"BBCH {f}–{t}" if t != f else f"BBCH {f}"

    def __str__(self):
        return f"{self.activity} - {self.name}"

    class Meta:
        verbose_name = _('stage')
        verbose_name_plural = _('stages')
