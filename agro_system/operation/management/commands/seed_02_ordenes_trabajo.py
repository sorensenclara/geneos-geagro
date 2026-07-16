from django.db import transaction

from ._seed_common import SeedCommandBase


class Command(SeedCommandBase):
    help = (
        'ETAPA 2/3 — Ejecución del plan técnico: genera las órdenes de trabajo de '
        'cada cultivo (replica "Procesar Plan"), registra avances con consumos '
        'reales de insumos (algunos por debajo y otros por encima de lo '
        'planificado) y el costo de la labor de cosecha subcontratada. '
        'Si la Etapa 1 no corrió todavía, la ejecuta primero automáticamente. '
        'Es idempotente: puede correrse varias veces sin duplicar datos.'
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '=== ETAPA 2/3 — Ejecución del plan técnico y órdenes de trabajo ===\n'
        ))
        with transaction.atomic():
            self.cargar_etapa_2()
        self.stdout.write(self.style.SUCCESS('\n✓ Etapa 2 completa.'))
        self.stdout.write(
            '  Revisá en el admin: Operaciones → Órdenes de trabajo (avances, '
            'consumos reales vs. planificados, costo de contratista en Cosecha).\n'
            '  Siguiente paso: python manage.py seed_03_acopio\n'
        )
