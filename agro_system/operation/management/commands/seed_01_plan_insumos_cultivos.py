from django.db import transaction

from ._seed_common import SeedCommandBase


class Command(SeedCommandBase):
    help = (
        'ETAPA 1/3 — Carga de datos base: campaña 2026/2027, cultivos de trigo y '
        'cebada, plan técnico con sus etapas e insumos, depósitos, proveedores, '
        'compras/recepciones de stock, movimiento entre depósitos y una recompra '
        'a precio distinto. No genera órdenes de trabajo ni acopio (ver etapas 2 y 3). '
        'Es idempotente: puede correrse varias veces sin duplicar datos.'
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '=== ETAPA 1/3 — Plan técnico, cultivos e insumos (Trigo/Cebada 2026-2027) ===\n'
        ))
        with transaction.atomic():
            self.cargar_etapa_1()
        self.stdout.write(self.style.SUCCESS('\n✓ Etapa 1 completa.'))
        self.stdout.write(
            '  Revisá en el admin: Operaciones → Cultivos / Planes técnicos, '
            'Insumos → Insumos / Recepciones de compra / Movimientos de stock.\n'
            '  Siguiente paso: python manage.py seed_02_ordenes_trabajo\n'
        )
