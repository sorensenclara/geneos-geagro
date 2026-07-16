from django.db import transaction

from ._seed_common import SeedCommandBase


class Command(SeedCommandBase):
    help = (
        'ETAPA 3/3 — Circuito de acopio: finaliza la cosecha pendiente, carga el '
        'rinde real de cada cultivo (requisito para poder acopiar), crea silos '
        'propios de distintos tipos con sus movimientos (ingreso, transferencia, '
        'salida), un acopiador tercero con certificados de depósito (activo/parcial, '
        'warrant y cancelado), y una venta de granos asignada a stock propio y de '
        'terceros a la vez. Si las etapas 1 y 2 no corrieron todavía, las ejecuta '
        'primero automáticamente. Es idempotente: puede correrse varias veces sin '
        'duplicar datos.'
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '=== ETAPA 3/3 — Circuito de acopio (propio y en terceros) ===\n'
        ))
        with transaction.atomic():
            self.cargar_etapa_3()
        self.stdout.write(self.style.SUCCESS('\n✓ Etapa 3 completa. Set de datos de ejemplo terminado.'))
        self.stdout.write(
            '  Revisá en el admin: Acopio → Silos / Stock por silo / Movimientos de '
            'silo, Certificados de depósito (y sus servicios/movimientos); y Ventas → '
            'Comprobantes de venta (con sus asignaciones de stock).\n'
        )
