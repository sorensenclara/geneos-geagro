from django.db import models
from django.utils.translation import gettext_lazy as _


class PhenologicalState(models.Model):
    """
    Tabla compartida GDD → BBCH → estadio fenológico. Un único registro por estadio para
    todas las variedades. Lo que varía por variedad (cosecha) vive en Specie.
    Eje: GDD acumulado desde brotación, base 10°C.

    Cada estado fenológico pertenece a una Etapa operativa (Stage), que agrupa
    varios estadios contiguos en un período de manejo (poda, brotación, floración…).
    """

    bbch       = models.CharField(max_length=8,  verbose_name=_("BBCH code"))   # "65"
    stage_name = models.CharField(max_length=80, verbose_name=_("stage name"))  # "Plena floración"
    gdd_from   = models.PositiveIntegerField(verbose_name=_("GDD from"))
    gdd_to     = models.PositiveIntegerField(verbose_name=_("GDD to"))
    order      = models.PositiveIntegerField(verbose_name=_("order"))

    stage = models.ForeignKey(
        'operation.Stage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='phenological_states',
        verbose_name=_('operational stage'),
        help_text=_('Operational period (etapa) this phenological state belongs to.'),
    )

    class Meta:
        ordering = ["order"]
        verbose_name = _("phenological stage")
        verbose_name_plural = _("phenological stages")

    def __str__(self):
        return f"BBCH {self.bbch} — {self.stage_name}"

    @classmethod
    def current_stage(cls, vine_gdd):
        """Estadio donde cae el GDD actual (base 10, contador 'vine')."""
        return (
            cls.objects.filter(gdd_from__lte=vine_gdd, gdd_to__gte=vine_gdd)
            .order_by("order")
            .first()
        )

    @classmethod
    def next_stage(cls, vine_gdd):
        """Próximo estadio por delante del GDD actual."""
        return cls.objects.filter(gdd_from__gt=vine_gdd).order_by("order").first()


def seed_phenological_stages():
    """
    Carga la tabla fenológica base. Llamar desde data migration o management command.
    Eje: GDD acumulado desde brotación, base 10°C. Fuente: Poni 2022 + calibración Mendoza.
    """
    stages = [
        #  bbch      stage_name                              gdd_from  gdd_to  order
        ("01-09",  "Brotación — yema hinchada a puntas verdes",   0,    30,   1),
        ("11-15",  "Desarrollo foliar (1 a 5 hojas)",            30,   120,   2),
        ("53-55",  "Inflorescencias visibles",                  120,   230,   3),
        ("57",     "Flores separándose",                        230,   290,   4),
        ("60",     "Inicio de floración",                       250,   330,   5),
        ("65",     "Plena floración",                           300,   400,   6),
        ("69",     "Fin de floración / cuajado inicial",        350,   450,   7),
        ("71-73",  "Cuajado (grano perdigón)",                  400,   550,   8),
        ("75",     "Grano tamaño arveja",                       500,   620,   9),
        ("77-79",  "Cierre de racimo",                          620,   760,  10),
        ("81",     "Inicio de envero",                          800,   950,  11),
        ("83",     "Envero avanzado",                           900,  1050,  12),
        ("85",     "Ablandamiento / maduración",               1000,  1200,  13),
        ("89",     "Madurez de cosecha (según variedad)",       1200,  1800,  14),
    ]
    for bbch, stage_name, gdd_from, gdd_to, order in stages:
        PhenologicalState.objects.update_or_create(
            bbch=bbch,
            defaults={
                "stage_name": stage_name,
                "gdd_from":   gdd_from,
                "gdd_to":     gdd_to,
                "order":      order,
            },
        )
