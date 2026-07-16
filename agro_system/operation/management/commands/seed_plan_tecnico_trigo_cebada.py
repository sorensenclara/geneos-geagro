from django.db import transaction

from ._seed_common import SeedCommandBase


class Command(SeedCommandBase):
    help = (
        'Corre de punta a punta las 3 etapas del set de datos de ejemplo Trigo/Cebada '
        '2026-2027: (1) plan técnico, cultivos e insumos; (2) ejecución del plan '
        'técnico y órdenes de trabajo; (3) circuito de acopio (propio y en terceros). '
        'Para probar y verificar cada etapa por separado, usá en su lugar '
        'seed_01_plan_insumos_cultivos / seed_02_ordenes_trabajo / seed_03_acopio. '
        'Es idempotente: puede correrse varias veces (o en otras bases de prueba) sin '
        'duplicar datos.'
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '=== Sembrando datos de ejemplo: Plan Técnico Trigo / Cebada 2026-2027 ===\n'
        ))
        with transaction.atomic():
            self.cargar_etapa_3()
        self.stdout.write(self.style.SUCCESS(
            '\n✓ Set de datos de ejemplo creado correctamente (etapas 1, 2 y 3).'
        ))
        self.stdout.write(
            '  Entrá al admin → Operaciones / Insumos para revisar el plan técnico, '
            'los cultivos, las órdenes de trabajo, las recepciones y los movimientos '
            'entre depósitos; y Acopio / Ventas para revisar los silos propios, los '
            'certificados de depósito en el acopiador y la venta de ejemplo.\n'
        )
