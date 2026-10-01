"""
Importa insumos desde un Excel (columnas: Categoría | Insumo) y los asigna a un productor.

Uso:
    python manage.py importar_insumos <producer_id>
    python manage.py importar_insumos                 # sin id: compartidos (sin productor), para todos
    python manage.py importar_insumos <producer_id> --dry-run
    python manage.py importar_insumos <producer_id> --unidad 1 --moneda 3 --archivo otro.xlsx

- Las categorías que no existen se crean como Categoría de insumos y como Tipo de insumo
  (el insumo se relaciona con el Tipo).
- Si el productor ya tiene un insumo con el mismo nombre no se modifica: se informa y se saltea
  (el nombre de insumo es único por productor).
"""
from pathlib import Path

import openpyxl
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from input.models.category_input import CategoryInput
from input.models.input import Input
from input.models.type_input import TypeInput
from parameter.models.currency import Currency
from parameter.models.measure_unit import MaensureUnit
from user.models.user_producer import UserProducer

DEFAULT_FILE = Path(__file__).resolve().parent.parent / 'data' / 'Insumos.xlsx'


class Command(BaseCommand):
    help = 'Importa insumos desde un Excel (Categoría | Insumo) y los asigna al productor indicado (o compartidos si se omite).'

    def add_arguments(self, parser):
        parser.add_argument('producer_id', type=int, nargs='?',
                            help='ID del productor (UserProducer). Si se omite, los insumos quedan compartidos (sin productor)')
        parser.add_argument('--archivo', default=str(DEFAULT_FILE), help=f'Ruta del Excel (por defecto: {DEFAULT_FILE.name})')
        parser.add_argument('--unidad', type=int, help='ID de la unidad de medida (por defecto: la de referencia)')
        parser.add_argument('--moneda', type=int, help='ID de la moneda (por defecto: la moneda base)')
        parser.add_argument('--dry-run', action='store_true', help='Muestra lo que haría sin guardar nada')

    def handle(self, *args, **options):
        producer = None
        if options['producer_id'] is not None:
            producer = UserProducer.objects.filter(pk=options['producer_id']).first()
            if not producer:
                raise CommandError(
                    f"No existe el productor con id {options['producer_id']}. Productores: "
                    + ', '.join(f'{p.pk} ({p})' for p in UserProducer.objects.all())
                )

        unit = self._get_unit(options['unidad'])
        currency = self._get_currency(options['moneda'])
        rows = self._read_rows(options['archivo'])

        owner = f'{producer} (id {producer.pk})' if producer else 'compartidos (sin productor)'
        self.stdout.write(
            f'Productor: {owner} | Unidad: {unit} | Moneda: {currency} | '
            f'{len(rows)} insumos en el archivo'
        )

        created, skipped, new_categories = [], [], []
        with transaction.atomic():
            for category_name, input_name in rows:
                input_type, type_created = TypeInput.objects.get_or_create(name=category_name)
                _, category_created = CategoryInput.objects.get_or_create(name=category_name)
                if type_created or category_created:
                    new_categories.append(category_name)

                if Input.objects.filter(name=input_name, producer=producer).exists():
                    skipped.append(f'{input_name} (ya existe para {"el productor" if producer else "todos"})')
                    continue

                Input.objects.create(
                    name=input_name,
                    type=input_type,
                    unit_measure=unit,
                    currency=currency,
                    producer=producer,
                )
                created.append(input_name)

            if options['dry_run']:
                transaction.set_rollback(True)

        self._report(created, skipped, new_categories, options['dry_run'])

    def _get_unit(self, unit_id):
        if unit_id:
            unit = MaensureUnit.objects.filter(pk=unit_id).first()
            if not unit:
                raise CommandError(f'No existe la unidad de medida con id {unit_id}.')
            return unit
        unit = MaensureUnit.objects.filter(is_reference=True).first()
        if not unit:
            raise CommandError('No hay unidad de medida de referencia. Indicá una con --unidad <id>.')
        return unit

    def _get_currency(self, currency_id):
        if currency_id:
            currency = Currency.objects.filter(pk=currency_id).first()
            if not currency:
                raise CommandError(f'No existe la moneda con id {currency_id}.')
            return currency
        currency = Currency.objects.filter(is_base=True).first()
        if not currency:
            raise CommandError('No hay moneda base. Indicá una con --moneda <id>.')
        return currency

    def _read_rows(self, path):
        """Devuelve [(categoría, insumo)] a partir de la fila de encabezado (Categoría | Insumo)."""
        if not Path(path).exists():
            raise CommandError(f'No se encontró el archivo: {path}')
        sheet = openpyxl.load_workbook(path, data_only=True, read_only=True).worksheets[0]

        rows, header_found, seen = [], False, set()
        for category, name, *_ in sheet.iter_rows(values_only=True):
            if not header_found:
                # El encabezado puede no estar en la primera fila (el archivo trae filas vacías arriba)
                header_found = str(category or '').strip().lower().startswith('cat')
                continue
            category = str(category or '').strip()
            name = str(name or '').strip()
            if not name or not category or name in seen:
                continue
            seen.add(name)
            rows.append((category, name))

        if not header_found:
            raise CommandError('No se encontró la fila de encabezado (Categoría | Insumo) en la primera hoja.')
        return rows

    def _report(self, created, skipped, new_categories, dry_run):
        prefix = '[DRY-RUN] ' if dry_run else ''
        if new_categories:
            self.stdout.write(f'{prefix}Categorías nuevas: ' + ', '.join(sorted(set(new_categories))))
        for line in skipped:
            self.stdout.write(self.style.WARNING(f'  - Salteado: {line}'))
        self.stdout.write(self.style.SUCCESS(
            f'{prefix}Insumos creados: {len(created)} | Salteados: {len(skipped)}'
        ))
        if dry_run:
            self.stdout.write('No se guardó nada (dry-run).')
