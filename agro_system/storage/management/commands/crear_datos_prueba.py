from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Crea datos de prueba completos para el módulo de acopio.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== Creando datos de prueba para Acopio ===\n'))
        with transaction.atomic():
            self._parametros_base()
            self._parametros_acopio()
            self._parametros_cultivo()
            producer = self._producer()
            self._datos_campo(producer)
            self._cultivo_cosechado(producer)
            self._proveedor_acopiador(producer)
        self.stdout.write(self.style.SUCCESS('\n✓ Datos de prueba creados correctamente.'))
        self.stdout.write('  Entrá al admin → Acopio para empezar a probar.\n')

    # ------------------------------------------------------------------ #
    # Parámetros base: country → province → city                          #
    # ------------------------------------------------------------------ #
    def _parametros_base(self):
        self.stdout.write('→ Parámetros base...')

        from parameter.models.country import Country
        from parameter.models.province import Province
        from parameter.models.city import City
        from parameter.models.area import Area
        from parameter.models.countryside_condition import CountrysideCondition
        from parameter.models.lot_rating import LotRating
        from parameter.models.gender import Gender
        from parameter.models.currency import Currency
        from parameter.models.port import Port
        from producer.models.typeStaff import TypeStaff
        from producer.models.cost_center import CostCenter

        country, _ = Country.objects.get_or_create(name='Argentina')
        province, _ = Province.objects.get_or_create(name='Santa Fe', defaults={'country': country})
        self.city, _ = City.objects.get_or_create(name='Rosario', defaults={'province': province})

        self.area, _ = Area.objects.get_or_create(name='Zona Núcleo')
        self.condition, _ = CountrysideCondition.objects.get_or_create(name='Propia')
        self.lot_rating, _ = LotRating.objects.get_or_create(name='Alta')
        self.gender, _ = Gender.objects.get_or_create(name='Masculino')
        self.type_staff, _ = TypeStaff.objects.get_or_create(name='Administración')
        self.cost_center, _ = CostCenter.objects.get_or_create(name='Centro Prueba Acopio', producer=None)
        Currency.objects.get_or_create(name='Peso Argentino')
        Port.objects.get_or_create(name='Rosario', defaults={'city': self.city})

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Parámetros de acopio                                                #
    # ------------------------------------------------------------------ #
    def _parametros_acopio(self):
        self.stdout.write('→ Parámetros de acopio (SiloType / StorageServiceType)...')

        from parameter.models.silo_type import SiloType
        from parameter.models.storage_service_type import StorageServiceType

        for name in ['Metálico', 'Bolsa plástica', 'Galpón', 'Silo torre']:
            SiloType.objects.get_or_create(name=name)

        for name in ['Almacenaje', 'Secada', 'Zaranda', 'Fumigación', 'Acondicionamiento']:
            StorageServiceType.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Parámetros de cultivo: specie, variety, state, campaign            #
    # ------------------------------------------------------------------ #
    def _parametros_cultivo(self):
        self.stdout.write('→ Especies, actividades, estados, campaña...')

        from parameter.models.specie import Specie
        from parameter.models.campaign import Campaing
        from parameter.models.cultivation_state import CiltivationState
        from operation.models.variety import Variety

        soja, _ = Specie.objects.get_or_create(name='Soja')
        trigo, _ = Specie.objects.get_or_create(name='Trigo')
        maiz, _ = Specie.objects.get_or_create(name='Maíz')
        Specie.objects.get_or_create(name='Girasol')

        self.variety_soja, _ = Variety.objects.get_or_create(
            name='Cosecha Soja', defaults={'specie': soja, 'is_agricultural': True})
        Variety.objects.get_or_create(
            name='Cosecha Trigo', defaults={'specie': trigo, 'is_agricultural': True})
        Variety.objects.get_or_create(
            name='Cosecha Maíz', defaults={'specie': maiz, 'is_agricultural': True})

        for estado in ['Planificado', 'Sembrado', 'En desarrollo', 'Cancelado']:
            CiltivationState.objects.get_or_create(name=estado)
        self.estado_cosechado, _ = CiltivationState.objects.get_or_create(name='Cosechado')

        self.campaing, _ = Campaing.objects.get_or_create(
            name='2024/2025',
            defaults={
                'date_init': date(2024, 7, 1),
                'date_final': date(2025, 6, 30),
                'active': True,
            },
        )

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # UserProducer de prueba                                              #
    # ------------------------------------------------------------------ #
    def _producer(self):
        self.stdout.write('→ Productor...')

        from user.models.user_producer import UserProducer

        # Usar el primero que exista, o crear uno de prueba
        producer = UserProducer.objects.first()
        if producer:
            self.stdout.write(f'  Usando productor existente: {producer}')
            return producer

        producer = UserProducer(
            email='productor.prueba@test.com',
            name='Establecimiento San Juan (PRUEBA)',
            cuit='30500010912',
            address='Ruta 9 Km 300',
            city=self.city,
            phone='3411234567',
        )
        producer.set_password('Test1234!')
        producer.save()
        self.stdout.write(self.style.SUCCESS('  ✓ Creado productor@test.com / Test1234!'))
        return producer

    # ------------------------------------------------------------------ #
    # Staff, Countryside, Lot (usa existentes si los hay)                 #
    # ------------------------------------------------------------------ #
    def _datos_campo(self, producer):
        self.stdout.write('→ Campo, lote, personal...')

        from producer.models.staff import Staff
        from producer.models.country_side import Countryside
        from producer.models.lot import Lot

        # Reutilizar staff existente del productor, o cualquiera disponible
        self.responsible = (
            Staff.objects.filter(producer=producer).first()
            or Staff.objects.first()
        )
        if not self.responsible:
            self.stdout.write(self.style.ERROR(
                '  ✗ No hay personal (Staff) en la BD. '
                'Creá al menos uno desde el admin antes de correr este comando.'
            ))
            raise SystemExit(1)

        # Campo
        self.countryside = (
            Countryside.objects.filter(producer=producer).first()
            or Countryside.objects.first()
        )
        if not self.countryside:
            self.stdout.write(self.style.ERROR(
                '  ✗ No hay campos (Countryside) en la BD. '
                'Creá al menos uno desde el admin antes de correr este comando.'
            ))
            raise SystemExit(1)

        # Lote
        self.lot = (
            Lot.objects.filter(countryside=self.countryside).first()
            or Lot.objects.first()
        )
        if not self.lot:
            self.stdout.write(self.style.ERROR(
                '  ✗ No hay lotes en la BD. '
                'Creá al menos uno desde el admin antes de correr este comando.'
            ))
            raise SystemExit(1)

        self.lot.variety.add(self.variety_soja)

        self.stdout.write(f'  Usando: staff={self.responsible}, campo={self.countryside}, lote={self.lot}')
        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Cultivo cosechado (para vincular con movimientos de acopio)         #
    # ------------------------------------------------------------------ #
    def _cultivo_cosechado(self, producer):
        self.stdout.write('→ Cultivo cosechado...')

        from operation.models.crop import Crop
        from parameter.models.specie import Specie

        soja = Specie.objects.get(name='Soja')
        variety = self.variety_soja

        crop, created = Crop.objects.get_or_create(
            name='Soja 2024/2025 - La Esperanza L1 (PRUEBA)',
            defaults={
                'campaing': self.campaing,
                'countryside': self.countryside,
                'area': self.area,
                'lot': self.lot,
                'variety': variety,
                'responsible': self.responsible,
                'state': self.estado_cosechado,
                'hectares_productive': 148,
                'hectares_planted': 145,
                'hectares_harvested': 145,
                'hectares_not_harvested': 0,
                'producer': producer,
            },
        )

        if not created:
            # Si ya existe, asegurar estado cosechado
            crop.state = self.estado_cosechado
            crop.hectares_harvested = crop.hectares_planted
            crop.save()

        action = 'Creado' if created else 'Ya existía (estado → Cosechado)'
        self.stdout.write(self.style.SUCCESS(f'  ✓ {action}: {crop}'))

    # ------------------------------------------------------------------ #
    # Proveedor Acopiador                                                 #
    # ------------------------------------------------------------------ #
    def _proveedor_acopiador(self, producer):
        self.stdout.write('→ Proveedor Acopiador...')

        from input.models.type_provider import TypeProvider
        from input.models.provider import Provider

        type_acopiador, _ = TypeProvider.objects.get_or_create(name='Acopiador')
        TypeProvider.objects.get_or_create(name='Transportista')
        TypeProvider.objects.get_or_create(name='Insumos')

        Provider.objects.get_or_create(
            cuit='30712345671',
            defaults={
                'name': 'Acopiadora El Granero SA (PRUEBA)',
                'type': type_acopiador,
                'address': 'San Martín 500',
                'city': self.city,
                'phone': '3413333333',
                'producer': producer,
            },
        )

        self.stdout.write(self.style.SUCCESS('  ✓'))
