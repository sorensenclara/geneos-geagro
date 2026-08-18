"""
Seed completo de datos maestros para el sistema vitivinícola.

Carga (en orden, con dependencias resueltas):
  1. Estadios fenológicos BBCH  (PhenologicalState)
  2. Variedades               (Specie)       con GDD de cosecha
  3. Actividades              (Activity)     una por variedad
  4. Etapas operativas        (Stage)        sin campos BBCH directos
  5. Relación estadio→etapa   (PhenologicalState.stage)
  6. Tipos de servicio        (ServiceType)
  7. Servicios concretos      (Service)

Idempotente: usa update_or_create en todo — sirve tanto para bases vacías
como para actualizar valores ya existentes.

Uso:
    python manage.py seed_viticulture_operations [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.db import transaction


# ──────────────────────────────────────────────────────────────────────────────
# 1. Estadios fenológicos BBCH
#    Fuente: escala BBCH vid (Lorenz et al. 1994) + calibración Mendoza (Poni 2022)
#    GDD: base 10 °C desde brotación
# ──────────────────────────────────────────────────────────────────────────────
PHENOLOGICAL_STAGES = [
    # bbch       stage_name                                           gdd_from  gdd_to  order
    ("01-09",  "Brotación — yema hinchada a puntas verdes",                0,    30,   1),
    ("11-15",  "Desarrollo foliar (1 a 5 hojas)",                         30,   120,   2),
    ("53-55",  "Inflorescencias visibles",                               120,   230,   3),
    ("57",     "Flores separándose",                                     230,   290,   4),
    ("60",     "Inicio de floración",                                    250,   330,   5),
    ("65",     "Plena floración",                                        300,   400,   6),
    ("69",     "Fin de floración / cuajado inicial",                     350,   450,   7),
    ("71-73",  "Cuajado (grano perdigón)",                               400,   550,   8),
    ("75",     "Grano tamaño arveja",                                    500,   620,   9),
    ("77-79",  "Cierre de racimo",                                       620,   760,  10),
    ("81",     "Inicio de envero",                                       800,   950,  11),
    ("83",     "Envero avanzado",                                        900,  1050,  12),
    ("85",     "Ablandamiento / maduración",                            1000,  1200,  13),
    ("89",     "Madurez de cosecha (según variedad)",                   1200,  1800,  14),
]

# ──────────────────────────────────────────────────────────────────────────────
# 2 + 3. Variedades y actividades
#    GDD de cosecha: base 10 °C desde brotación (calibración Mendoza)
# ──────────────────────────────────────────────────────────────────────────────
VARIETIES = [
    {"name": "Malbec",             "gdd_min": 1450, "gdd_max": 1700},
    {"name": "Cabernet Sauvignon", "gdd_min": 1550, "gdd_max": 1800},
    {"name": "Merlot",             "gdd_min": 1400, "gdd_max": 1650},
    {"name": "Bonarda",            "gdd_min": 1600, "gdd_max": 1900},
    {"name": "Syrah",              "gdd_min": 1500, "gdd_max": 1750},
    {"name": "Chardonnay",         "gdd_min": 1100, "gdd_max": 1350},
    {"name": "Chenin",             "gdd_min": 1200, "gdd_max": 1450},
    {"name": "Semillón",           "gdd_min": 1250, "gdd_max": 1500},
    {"name": "Tannat",             "gdd_min": 1500, "gdd_max": 1800},
    {"name": "Tempranillo",        "gdd_min": 1350, "gdd_max": 1600},
    {"name": "Pinot Noir",         "gdd_min": 1100, "gdd_max": 1350},
    {"name": "Viognier",           "gdd_min": 1200, "gdd_max": 1450},
]

# ──────────────────────────────────────────────────────────────────────────────
# 4 + 5. Etapas operativas y sus estadios fenológicos BBCH
#
#    Cada etapa agrupa varios estadios BBCH contiguos bajo un período de manejo.
#    La relación se persiste como PhenologicalState.stage (FK inversa).
#
#    Mapeo:
#      Poda            — sin estadios BBCH (dormancia, antes de brotación)
#      Brotación       — "01-09"
#      Desarrollo foliar — "11-15"
#      Floración y Cuaje — "53-55", "57", "60", "65", "69", "71-73"
#      Envero          — "75", "77-79", "81", "83"
#      Maduración      — "85"
#      Cosecha         — "89"
# ──────────────────────────────────────────────────────────────────────────────
STAGES = [
    # order  name                   bbch_codes (lista de PhenologicalState.bbch que pertenecen a esta etapa)
    (0,  "Poda",              []),
    (1,  "Brotación",         ["01-09"]),
    (2,  "Desarrollo foliar", ["11-15"]),
    (3,  "Floración y Cuaje", ["53-55", "57", "60", "65", "69", "71-73"]),
    (4,  "Envero",            ["75", "77-79", "81", "83"]),
    (5,  "Maduración",        ["85"]),
    (6,  "Cosecha",           ["89"]),
]

# ──────────────────────────────────────────────────────────────────────────────
# 6 + 7. Tipos de servicio y servicios
# ──────────────────────────────────────────────────────────────────────────────
SERVICE_TYPES = [
    {
        "name": "Fitosanitario",
        "services": [
            "Tratamiento Fitosanitario",
            "Aplicación fungicida preventiva",
            "Aplicación fungicida — Oídio",
            "Aplicación fungicida — Mildiu",
            "Aplicación fungicida — Botrytis",
            "Aplicación insecticida — Lobesia botrana",
        ],
    },
    {
        "name": "Emergencia climática",
        "services": [
            "Protección contra Heladas",
            "Activación de calefactores (helada)",
            "Riego de cobertura anti-helada",
            "Instalación / verificación red antigranizo",
            "Monitoreo y resguardo por Zonda",
            "Riego foliar de emergencia (golpe de calor)",
        ],
    },
    {
        "name": "Gestión hídrica",
        "services": [
            "Riego correctivo por estrés hídrico",
            "Verificación y ajuste de caudal de riego",
        ],
    },
    {
        "name": "Monitoreo y vigilancia",
        "services": [
            "Monitoreo de trampas Lobesia botrana",
            "Monitoreo fenológico (BBCH)",
            "Control de madurez — Brix y acidez",
            "Vigilancia meteorológica",
        ],
    },
    {
        "name": "Labores culturales",
        "services": [
            "Podar",
            "Tironear",
            "Enterrar",
            "Deshoje manual",
            "Aclareo de racimos",
            "Despunte de brotes",
            "Atado de sarmientos",
        ],
    },
    {
        "name": "Mantenimiento",
        "services": [
            "Mantenimiento de Estructura",
            "Reparación de sistema de riego",
            "Reparación de espalderos",
        ],
    },
    {
        "name": "Cosecha",
        "services": [
            "Cosecha manual",
            "Cosecha mecánica",
            "Estimación de cosecha (GDD)",
            "Control de calidad de cosecha",
        ],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Comando
# ──────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Carga/actualiza todos los datos maestros vitícolas (idempotente, update_or_create)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra lo que se crearía/actualizaría sin tocar la base de datos.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options["dry_run"]
        if dry:
            self.stdout.write(self.style.WARNING("— DRY RUN — nada se escribe\n"))

        created = updated = 0

        created, updated = self._seed_phenological_stages(dry, created, updated)
        created, updated = self._seed_varieties_and_activities(dry, created, updated)
        created, updated = self._seed_stages(dry, created, updated)
        created, updated = self._seed_services(dry, created, updated)

        self.stdout.write("")
        if dry:
            self.stdout.write(self.style.WARNING("DRY RUN — nada fue escrito."))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Listo — {created} creados, {updated} actualizados.")
            )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _log(self, action, label, dry):
        if dry:
            self.stdout.write(f"  ? {label}")
            return
        colors = {"[+]": self.style.SUCCESS, "[~]": self.style.WARNING, "[=]": str}
        fn = colors.get(action, str)
        self.stdout.write(fn(f"  {action} {label}"))

    # ── 1. PhenologicalState ──────────────────────────────────────────────────

    def _seed_phenological_stages(self, dry, created, updated):
        from crop_monitoring.models.phenological_state import PhenologicalState

        self.stdout.write("1. Estadios fenológicos BBCH:")

        # Eliminar duplicado "07-09" si existe (creado por seed anterior)
        if not dry:
            deleted, _ = PhenologicalState.objects.filter(bbch="07-09").delete()
            if deleted:
                self.stdout.write(self.style.WARNING(
                    f"  [!] Eliminado registro duplicado bbch='07-09' ({deleted} fila/s)"
                ))

        for bbch, stage_name, gdd_from, gdd_to, order in PHENOLOGICAL_STAGES:
            label = f"BBCH {bbch:6s}  {stage_name}  GDD {gdd_from}–{gdd_to}"
            if dry:
                self._log(None, label, dry)
                continue
            _, was_created = PhenologicalState.objects.update_or_create(
                bbch=bbch,
                defaults={"stage_name": stage_name, "gdd_from": gdd_from,
                          "gdd_to": gdd_to, "order": order},
            )
            action = "[+]" if was_created else "[=]"
            self._log(action, label, dry)
            if was_created:
                created += 1
            else:
                updated += 1
        return created, updated

    # ── 2 + 3. Varieties + Activities ────────────────────────────────────────

    def _seed_varieties_and_activities(self, dry, created, updated):
        from parameter.models.specie import Specie
        from operation.models.variety import Variety as Activity

        self.stdout.write("\n2. Variedades y actividades:")
        for v in VARIETIES:
            label = f"{v['name']:22s}  GDD cosecha {v['gdd_min']}–{v['gdd_max']}"
            if dry:
                self._log(None, label, dry)
                continue

            specie, s_created = Specie.objects.update_or_create(
                name=v["name"],
                defaults={"gdd_harvest_min": v["gdd_min"], "gdd_harvest_max": v["gdd_max"]},
            )
            _, a_created = Activity.objects.update_or_create(
                name=v["name"],
                defaults={
                    "description":     f"Cultivo de {v['name']}",
                    "specie":          specie,
                    "is_agricultural": True,
                    "is_livestock":    False,
                },
            )
            action = "[+]" if s_created else "[=]"
            self._log(action, label, dry)
            created += s_created + a_created
            updated += (not s_created) + (not a_created)

        return created, updated

    # ── 4 + 5. Stages + PhenologicalState.stage FK ───────────────────────────

    def _seed_stages(self, dry, created, updated):
        from crop_monitoring.models.phenological_state import PhenologicalState
        from operation.models.variety import Variety as Activity
        from operation.models.stage import Stage

        self.stdout.write("\n3. Etapas operativas y relación con estadios fenológicos:")

        if dry:
            for order, name, bbch_codes in STAGES:
                codes_str = ", ".join(bbch_codes) if bbch_codes else "sin BBCH (dormancia)"
                self._log(None, f"{order}. {name:25s}  [{codes_str}]", dry)
            return created, updated

        # Caché de PhenologicalState por bbch
        phen_cache = {ps.bbch: ps for ps in PhenologicalState.objects.all()}

        base_activity = Activity.objects.order_by("id").first()
        if base_activity is None:
            self.stdout.write(self.style.ERROR("  No hay actividades — omitiendo etapas."))
            return created, updated

        for order, name, bbch_codes in STAGES:
            _, was_created = Stage.objects.update_or_create(
                name=name,
                defaults={
                    "activity": base_activity,
                    "order":    order,
                },
            )
            action = "[+]" if was_created else "[~]"
            codes_str = ", ".join(bbch_codes) if bbch_codes else "sin BBCH"
            self._log(action, f"{order}. {name:25s}  [{codes_str}]", dry)
            if was_created:
                created += 1
            else:
                updated += 1

        # Asignar PhenologicalState.stage según los códigos BBCH
        stage_cache = {s.name: s for s in Stage.objects.all()}
        for order, name, bbch_codes in STAGES:
            stage = stage_cache.get(name)
            if stage is None:
                continue
            for bbch in bbch_codes:
                ps = phen_cache.get(bbch)
                if ps is None:
                    self.stdout.write(self.style.WARNING(
                        f"  [!] PhenologicalState bbch='{bbch}' no encontrado"
                    ))
                    continue
                if ps.stage_id != stage.pk:
                    ps.stage = stage
                    ps.save(update_fields=["stage"])
                    self.stdout.write(f"      → BBCH {bbch} asignado a etapa '{name}'")

        # Desasignar cualquier estadio que ya no pertenezca a ninguna etapa del seed
        all_seeded_bbch = {bbch for _, _, codes in STAGES for bbch in codes}
        orphaned = PhenologicalState.objects.exclude(bbch__in=all_seeded_bbch).filter(
            stage__isnull=False
        )
        if orphaned.exists():
            orphaned_codes = list(orphaned.values_list("bbch", flat=True))
            self.stdout.write(self.style.WARNING(
                f"  [!] Estadios con etapa asignada fuera del seed: {orphaned_codes} — no se modifican"
            ))

        return created, updated

    # ── 6 + 7. ServiceType + Service ─────────────────────────────────────────

    def _seed_services(self, dry, created, updated):
        from operation.models.service_type import ServiceType
        from operation.models.service import Service

        self.stdout.write("\n4. Tipos de servicio y servicios:")
        for st_data in SERVICE_TYPES:
            if dry:
                self.stdout.write(f"  Tipo: {st_data['name']}")
                for s in st_data["services"]:
                    self.stdout.write(f"    Servicio: {s}")
                continue

            svc_type, t_created = ServiceType.objects.get_or_create(name=st_data["name"])
            t_action = "[+]" if t_created else "[=]"
            self.stdout.write(self.style.SUCCESS(f"  {t_action} Tipo: {svc_type.name}") if t_created
                              else f"  {t_action} Tipo: {svc_type.name}")
            if t_created:
                created += 1

            for svc_name in st_data["services"]:
                _, s_created = Service.objects.update_or_create(
                    name=svc_name,
                    defaults={"type": svc_type},
                )
                s_action = "[+]" if s_created else "[=]"
                self._log(s_action, svc_name, dry)
                if s_created:
                    created += 1
                else:
                    updated += 1

        return created, updated
