"""Lógica compartida por los comandos `seed_01_*` / `seed_02_*` / `seed_03_*` /
`seed_plan_tecnico_trigo_cebada`. Al empezar con guión bajo, Django NO lo expone
como un comando ejecutable — es un módulo de soporte, no una etapa en sí misma.

Cada etapa es un comando de management independiente que puede correrse solo
(ver el `help` de cada uno). Como todo acá adentro es idempotente (get_or_create
o chequeos explícitos de "¿ya existe?"), una etapa posterior puede correrse sin
haber corrido las anteriores en la misma ejecución: `cargar_etapa_1`/`cargar_etapa_2`
verifican/crean lo que haga falta antes de agregar lo propio de esa etapa.
"""

from datetime import date

from django.core.management.base import BaseCommand

# Etiqueta usada para marcar los documentos generados por este set de datos y así
# poder detectar, en corridas posteriores, que ya fueron creados (idempotencia).
DEMO_TAG = 'DEMO-PLAN-TRIGO-CEBADA-2026-2027'
REPRICE_TAG = DEMO_TAG + '-REPRECIO'


def _cuit_digito_verificador(base10):
    """Calcula el dígito verificador de un CUIT a partir de sus primeros 10 dígitos."""
    base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    aux = sum(int(base10[i]) * base[i] for i in range(10))
    aux = 11 - (aux - (aux // 11) * 11)
    if aux == 11:
        aux = 0
    if aux == 10:
        aux = 9
    return str(aux)


def _cuit(base10):
    return base10 + _cuit_digito_verificador(base10)


class SeedCommandBase(BaseCommand):

    # Hectáreas de referencia del plan técnico: los "dose" de TechnicalPlanInput y los
    # "days_estimate" de TechnicalPlanDetail están definidos para esta superficie y el
    # sistema los escala proporcionalmente a las hectáreas productivas de cada cultivo.
    PLAN_REFERENCE_HECTARES = 100

    # ================================================================== #
    # Agregadores de etapa: cada uno se asegura (de forma idempotente) de #
    # que la etapa anterior ya esté cargada, y devuelve el `producer`.    #
    # ================================================================== #
    def cargar_estructura_base(self):
        """Parámetros, productor, infraestructura, plan técnico, cultivos y
        proveedores — la base común a las 3 etapas."""
        self._parametros_base()
        self._campania()
        producer = self._productor()
        self._infraestructura(producer)
        self._especies_actividades()
        self._estados_ot()
        self._contratista(producer)
        self._lotes(producer)
        self._insumos(producer)
        self._plan_tecnico(producer)
        self._cultivos(producer)
        self._proveedores(producer)
        return producer

    def cargar_etapa_1(self):
        """Etapa 1: estructura base + insumos con stock real (compras,
        recepciones, movimientos entre depósitos, recompra a precio distinto)."""
        producer = self.cargar_estructura_base()
        self._compras_y_recepciones(producer)
        self._movimiento_entre_depositos(producer)
        self._recompra_insumos_precio_diferente(producer)
        return producer

    def cargar_etapa_2(self):
        """Etapa 2: etapa 1 + ejecución del plan técnico (órdenes de trabajo,
        avances/consumos reales, costos de terceros)."""
        producer = self.cargar_etapa_1()
        self._registrar_avances_y_costos(producer)
        return producer

    def cargar_etapa_3(self):
        """Etapa 3: etapa 2 + circuito de acopio completo (silos propios,
        acopio en terceros, rindes reales, venta con asignación de stock)."""
        producer = self.cargar_etapa_2()
        self._tipos_silo_y_servicio()
        self._finalizar_cosecha(producer)
        self._rindes_reales(producer)
        self._silos_propios(producer)
        self._movimientos_silo(producer)
        self._proveedor_acopiador(producer)
        self._certificados_acopio_terceros(producer)
        self._venta_con_asignacion_de_stock(producer)
        return producer

    # ------------------------------------------------------------------ #
    # Parámetros base: country → province → city, moneda base, etc.       #
    # ------------------------------------------------------------------ #
    def _parametros_base(self):
        self.stdout.write('→ Parámetros base (geografía, moneda, género, etc.)...')

        from parameter.models.country import Country
        from parameter.models.province import Province
        from parameter.models.city import City
        from parameter.models.currency import Currency
        from parameter.models.gender import Gender
        from parameter.models.countryside_condition import CountrysideCondition
        from producer.models.typeStaff import TypeStaff
        from producer.models.cost_center import CostCenter

        # Reutiliza cualquier ciudad ya cargada (ej. importación de provincias/ciudades
        # de Argentina); si no hay ninguna, crea una cadena mínima de respaldo.
        self.city = City.objects.first()
        if not self.city:
            country, _ = Country.objects.get_or_create(name='Argentina')
            province, _ = Province.objects.get_or_create(name='Santa Fe', defaults={'country': country})
            self.city, _ = City.objects.get_or_create(name='Rosario', defaults={'province': province})

        self.gender, _ = Gender.objects.get_or_create(name='Masculino')
        self.condition, _ = CountrysideCondition.objects.get_or_create(name='Propio')
        self.type_staff, _ = TypeStaff.objects.get_or_create(name='Técnico Agrónomo')
        self.cost_center, _ = CostCenter.objects.get_or_create(name='Centro de Costo Plan Trigo-Cebada (Demo)', producer=None)

        Currency.objects.get_or_create(name='Pesos Argentinos')
        Currency.objects.get_or_create(name='Dólares')
        self.currency = Currency.objects.filter(name__icontains='peso').first() or Currency.objects.first()
        # El sistema necesita una moneda base para calcular costos/tasas de cambio;
        # si ninguna moneda fue marcada todavía, se usa esta como base.
        if not Currency.objects.filter(is_base=True).exists():
            self.currency.is_base = True
            self.currency.save()
            self.stdout.write(f'  (se marcó "{self.currency}" como moneda base del sistema)')

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Campaña 2026 - 2027                                                 #
    # ------------------------------------------------------------------ #
    def _campania(self):
        self.stdout.write('→ Campaña 2026 - 2027...')

        from parameter.models.campaign import Campaing

        self.campaing, created = Campaing.objects.get_or_create(
            name='2026 - 2027',
            defaults={
                'date_init': date(2026, 6, 1),
                'date_final': date(2027, 3, 31),
                'active': True,
            },
        )
        action = 'creada' if created else 'ya existía, se reutiliza'
        self.stdout.write(self.style.SUCCESS(f'  ✓ Campaña {action}: {self.campaing}'))

    # ------------------------------------------------------------------ #
    # Productor: reutiliza el primero que exista o crea uno de prueba     #
    # ------------------------------------------------------------------ #
    def _productor(self):
        self.stdout.write('→ Productor...')

        from user.models.user_producer import UserProducer

        producer = UserProducer.objects.first()
        if producer:
            self.stdout.write(f'  Usando productor existente: {producer}')
            return producer

        producer = UserProducer(
            email='productor.demo@test.com',
            name='Establecimiento Demo Plan Trigo-Cebada',
            cuit=_cuit('3050001091'),
            address='Ruta 226 Km 15',
            city=self.city,
            phone='2494123456',
        )
        producer.set_password('Test1234!')
        producer.save()
        self.stdout.write(self.style.SUCCESS('  ✓ Creado productor.demo@test.com / Test1234!'))
        return producer

    # ------------------------------------------------------------------ #
    # Staff, Countryside y depósitos (principal y secundario)              #
    # ------------------------------------------------------------------ #
    def _infraestructura(self, producer):
        self.stdout.write('→ Personal, campo y depósitos...')

        from producer.models.staff import Staff
        from producer.models.country_side import Countryside
        from producer.models.store import Store

        self.responsible = Staff.objects.filter(producer=producer).first()
        if not self.responsible:
            self.responsible = Staff.objects.create(
                name='Juan', surname='Pérez (Demo)',
                cuit=_cuit('3061111111'),
                address='Calle Falsa 123',
                city=self.city,
                phone='2494111111',
                type=self.type_staff,
                gender=self.gender,
                producer=producer,
            )

        # Depósito principal: reutiliza uno existente del productor, si lo hay.
        self.store_principal = Store.objects.filter(producer=producer).first()
        if not self.store_principal:
            self.store_principal, _ = Store.objects.get_or_create(
                name='Depósito Principal (Demo)', producer=producer,
                defaults={'address': 'Acceso Norte s/n', 'city': self.city, 'default': True},
            )

        # Depósito secundario: siempre se garantiza para poder ejemplificar
        # movimientos de inventario entre depósitos distintos.
        self.store_secundario, _ = Store.objects.get_or_create(
            name='Depósito Insumos - Sucursal (Demo)', producer=producer,
            defaults={'address': 'Ruta 226 Km 20', 'city': self.city, 'default': False},
        )

        self.countryside = Countryside.objects.filter(producer=producer).first()
        if not self.countryside:
            self.countryside = Countryside.objects.create(
                name='Campo Demo Plan Trigo-Cebada',
                condition=self.condition,
                hectares=300,
                responsible=self.responsible,
                address='Ruta 226 Km 18',
                city=self.city,
                phone='2494111111',
                cost_center=self.cost_center,
                store=self.store_principal,
                producer=producer,
            )

        self.stdout.write(
            f'  Usando: staff={self.responsible}, campo={self.countryside}, '
            f'depósito principal={self.store_principal}, depósito secundario={self.store_secundario}'
        )
        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Especie, actividad, área, estado de cultivo, calificación de lote    #
    # ------------------------------------------------------------------ #
    def _especies_actividades(self):
        self.stdout.write('→ Especies, actividades y parámetros de cultivo...')

        from parameter.models.specie import Specie
        from parameter.models.area import Area
        from parameter.models.cultivation_state import CiltivationState
        from parameter.models.lot_rating import LotRating
        from operation.models.variety import Variety

        specie_trigo, _ = Specie.objects.get_or_create(name='Trigo')
        specie_cebada, _ = Specie.objects.get_or_create(name='Cebada')

        self.variety_trigo, _ = Variety.objects.get_or_create(
            name='Trigo', defaults={'specie': specie_trigo, 'is_agricultural': True})
        self.variety_cebada, _ = Variety.objects.get_or_create(
            name='Cebada', defaults={'specie': specie_cebada, 'is_agricultural': True})

        self.area, _ = Area.objects.get_or_create(name='Zona Núcleo Demo')

        for estado in ['Planificado', 'Sembrado', 'En desarrollo', 'Cosechado', 'Cancelado']:
            CiltivationState.objects.get_or_create(name=estado)
        self.estado_trigo = CiltivationState.objects.get(name='En desarrollo')
        self.estado_cebada = CiltivationState.objects.get(name='Sembrado')

        for name in ['Alta', 'Media', 'Baja']:
            LotRating.objects.get_or_create(name=name)
        self.lot_rating = LotRating.objects.get(name='Alta')

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Estados de orden de trabajo                                         #
    # ------------------------------------------------------------------ #
    def _estados_ot(self):
        self.stdout.write('→ Estados de orden de trabajo...')

        from parameter.models.ot_state import OTState

        pendiente, _ = OTState.objects.get_or_create(name='Pendiente')
        OTState.objects.get_or_create(name='En Proceso')
        OTState.objects.get_or_create(name='Finalizada')
        if not OTState.objects.filter(is_default=True).exists():
            pendiente.is_default = True
            pendiente.save()

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Contratista (para la labor de cosecha subcontratada)                #
    # ------------------------------------------------------------------ #
    def _contratista(self, producer):
        self.stdout.write('→ Contratista...')

        from producer.models.contractor import Contractor

        self.contractor, _ = Contractor.objects.get_or_create(
            name='Contratista Cosecha del Sur (Demo)',
            defaults={
                'cuit': _cuit('3064444444'),
                'phone': '2494444444',
                'address': 'Ruta 226 Km 25',
                'producer': producer,
            },
        )

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Lotes de trigo y cebada                                             #
    # ------------------------------------------------------------------ #
    def _lotes(self, producer):
        self.stdout.write('→ Lotes...')

        from producer.models.lot import Lot

        self.lot_trigo, _ = Lot.objects.get_or_create(
            name='Lote Trigo - Plan Demo 2026/2027',
            defaults={
                'countryside': self.countryside,
                'area': self.area,
                'responsible': self.responsible,
                'hectares': 100,
                'hectares_productive': 100,
                'cost_center': self.cost_center,
                'LotRating': self.lot_rating,
            },
        )
        self.lot_trigo.variety.add(self.variety_trigo)

        self.lot_cebada, _ = Lot.objects.get_or_create(
            name='Lote Cebada - Plan Demo 2026/2027',
            defaults={
                'countryside': self.countryside,
                'area': self.area,
                'responsible': self.responsible,
                'hectares': 80,
                'hectares_productive': 80,
                'cost_center': self.cost_center,
                'LotRating': self.lot_rating,
            },
        )
        self.lot_cebada.variety.add(self.variety_cebada)

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Insumos (artículos) de ejemplo                                      #
    # ------------------------------------------------------------------ #
    def _insumos(self, producer):
        self.stdout.write('→ Insumos (artículos)...')

        from input.models.type_input import TypeInput
        from input.models.input import Input
        from parameter.models.measure_unit import MaensureUnit

        tipo_semilla, _ = TypeInput.objects.get_or_create(name='Semilla')
        tipo_fertilizante, _ = TypeInput.objects.get_or_create(name='Fertilizante')
        tipo_herbicida, _ = TypeInput.objects.get_or_create(name='Herbicida')
        tipo_fungicida, _ = TypeInput.objects.get_or_create(name='Fungicida')

        kg, _ = MaensureUnit.objects.get_or_create(name='Kg')
        litros, _ = MaensureUnit.objects.get_or_create(name='Litros')

        def _input(name, tipo, unidad, cost, presentation):
            obj, _ = Input.objects.get_or_create(
                name=name,
                producer=producer,
                defaults={
                    'type': tipo,
                    'unit_measure': unidad,
                    'presentation': presentation,
                    'cost': cost,
                    'currency': self.currency,
                },
            )
            return obj

        self.input_semilla_trigo = _input(
            'Semilla de Trigo (Demo)', tipo_semilla, kg, 350, 'Big bag 1000 kg')
        self.input_semilla_cebada = _input(
            'Semilla de Cebada (Demo)', tipo_semilla, kg, 300, 'Big bag 1000 kg')
        self.input_dap = _input(
            'Fertilizante Fosfato Diamónico - DAP (Demo)', tipo_fertilizante, kg, 850, 'Granel')
        self.input_urea = _input(
            'Urea Granulada (Demo)', tipo_fertilizante, kg, 780, 'Granel')
        self.input_herbicida = _input(
            'Herbicida Glifosato 66.2% (Demo)', tipo_herbicida, litros, 4200, 'Bidón 20 L')
        self.input_fungicida = _input(
            'Fungicida Triazol + Estrobirulina (Demo)', tipo_fungicida, litros, 15800, 'Bidón 5 L')

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Plan técnico (etapas, servicios e insumos por etapa)                #
    # ------------------------------------------------------------------ #
    def _plan_tecnico(self, producer):
        self.stdout.write('→ Plan técnico (etapas + insumos por etapa)...')

        from operation.models.service_type import ServiceType
        from operation.models.service import Service
        from operation.models.stage import Stage
        from operation.models.technical_plan import TechnicalPlan
        from operation.models.technical_plan_detail import TechnicalPlanDetail
        from operation.models.technical_plan_input import TechnicalPlanInput

        tipo_pulverizacion, _ = ServiceType.objects.get_or_create(name='Pulverización')
        tipo_siembra, _ = ServiceType.objects.get_or_create(name='Siembra')
        tipo_labores, _ = ServiceType.objects.get_or_create(name='Labores Generales')
        tipo_cosecha, _ = ServiceType.objects.get_or_create(name='Cosecha')

        servicio_barbecho, _ = Service.objects.get_or_create(
            name='Barbecho Químico', defaults={'type': tipo_pulverizacion})
        servicio_siembra, _ = Service.objects.get_or_create(
            name='Siembra Directa', defaults={'type': tipo_siembra})
        servicio_fertilizacion, _ = Service.objects.get_or_create(
            name='Fertilización Nitrogenada (Macollaje)', defaults={'type': tipo_labores})
        servicio_enfermedades, _ = Service.objects.get_or_create(
            name='Control de Enfermedades', defaults={'type': tipo_pulverizacion})
        servicio_cosecha, _ = Service.objects.get_or_create(
            name='Cosecha de Cereal', defaults={'type': tipo_cosecha})

        # (nombre etapa, servicio, dias, personas) — días/personas definidos para las
        # PLAN_REFERENCE_HECTARES hectáreas de referencia del plan.
        etapas_base = [
            ('Barbecho Químico', servicio_barbecho, 1, 1),
            ('Siembra', servicio_siembra, 2, 2),
            ('Macollaje - Fertilización', servicio_fertilizacion, 1, 1),
            ('Control de Enfermedades', servicio_enfermedades, 1, 1),
            ('Cosecha', servicio_cosecha, 3, 2),
        ]

        def _crear_plan(codigo, variety, insumos_por_etapa):
            plan, _ = TechnicalPlan.objects.get_or_create(
                code=codigo,
                defaults={
                    'detail': f'Plan técnico de ejemplo para {variety.name} - Campaña 2026/2027',
                    'hectares': self.PLAN_REFERENCE_HECTARES,
                    'variety': variety,
                    'area': self.area,
                    'active': True,
                    'producer': producer,
                },
            )
            if plan.hectares != self.PLAN_REFERENCE_HECTARES:
                plan.hectares = self.PLAN_REFERENCE_HECTARES
                plan.save()

            for secuencia, (nombre_etapa, servicio, dias, personas) in enumerate(etapas_base, start=1):
                stage, _ = Stage.objects.get_or_create(
                    name=nombre_etapa, variety=variety, defaults={'order': secuencia})
                detail, _ = TechnicalPlanDetail.objects.get_or_create(
                    technical_plan=plan,
                    secuence=secuencia,
                    defaults={
                        'stage': stage,
                        'service': servicio,
                        'days_estimate': dias,
                        'cant_persons': personas,
                    },
                )
                # La cosecha se subcontrata a un contratista externo (labor de terceros).
                if nombre_etapa == 'Cosecha' and (
                        not detail.subcontracted or detail.contractor_id != self.contractor.id):
                    detail.subcontracted = True
                    detail.contractor = self.contractor
                    detail.save()

                for input_obj, dosis_por_ha, store in insumos_por_etapa.get(nombre_etapa, []):
                    dosis_referencia = dosis_por_ha * self.PLAN_REFERENCE_HECTARES
                    tpi, _ = TechnicalPlanInput.objects.get_or_create(
                        technical_plan=plan,
                        technical_plan_detail=detail,
                        input=input_obj,
                        defaults={'dose': dosis_referencia, 'store': store},
                    )
                    if tpi.dose != dosis_referencia or tpi.store_id != store.id:
                        tpi.dose = dosis_referencia
                        tpi.store = store
                        tpi.save()
            return plan

        # La urea y el fungicida de cebada se aplican desde el depósito secundario
        # (hacia donde se transfirió stock), el resto se retira del depósito principal.
        self.plan_trigo = _crear_plan('PT-TRIGO-2026-2027', self.variety_trigo, {
            'Barbecho Químico': [(self.input_herbicida, 2, self.store_principal)],
            'Siembra': [
                (self.input_semilla_trigo, 120, self.store_principal),
                (self.input_dap, 80, self.store_principal),
            ],
            'Macollaje - Fertilización': [(self.input_urea, 150, self.store_principal)],
            'Control de Enfermedades': [(self.input_fungicida, 0.5, self.store_principal)],
        })

        self.plan_cebada = _crear_plan('PT-CEBADA-2026-2027', self.variety_cebada, {
            'Barbecho Químico': [(self.input_herbicida, 2, self.store_principal)],
            'Siembra': [
                (self.input_semilla_cebada, 100, self.store_principal),
                (self.input_dap, 70, self.store_principal),
            ],
            'Macollaje - Fertilización': [(self.input_urea, 120, self.store_secundario)],
            'Control de Enfermedades': [(self.input_fungicida, 0.4, self.store_secundario)],
        })

        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.plan_trigo} / {self.plan_cebada}'))

    # ------------------------------------------------------------------ #
    # Cultivos de trigo y cebada en la campaña 2026 - 2027                #
    # ------------------------------------------------------------------ #
    def _cultivos(self, producer):
        self.stdout.write('→ Cultivos (Trigo / Cebada)...')

        from operation.models.crop import Crop

        self.crop_trigo, _ = Crop.objects.get_or_create(
            name='Trigo 2026/2027 - Campo Demo L1',
            defaults={
                'campaing': self.campaing,
                'countryside': self.countryside,
                'area': self.area,
                'lot': self.lot_trigo,
                'variety': self.variety_trigo,
                'responsible': self.responsible,
                'state': self.estado_trigo,
                'hectares_productive': 100,
                'hectares_planted': 100,
                'hectares_harvested': 0,
                'hectares_not_harvested': 0,
                'date_init': date(2026, 6, 15),
                'producer': producer,
            },
        )

        self.crop_cebada, _ = Crop.objects.get_or_create(
            name='Cebada 2026/2027 - Campo Demo L2',
            defaults={
                'campaing': self.campaing,
                'countryside': self.countryside,
                'area': self.area,
                'lot': self.lot_cebada,
                'variety': self.variety_cebada,
                'responsible': self.responsible,
                'state': self.estado_cebada,
                'hectares_productive': 80,
                'hectares_planted': 80,
                'hectares_harvested': 0,
                'hectares_not_harvested': 0,
                'date_init': date(2026, 6, 20),
                'producer': producer,
            },
        )

        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.crop_trigo} / {self.crop_cebada}'))

    # ------------------------------------------------------------------ #
    # Proveedores de insumos                                              #
    # ------------------------------------------------------------------ #
    def _proveedores(self, producer):
        self.stdout.write('→ Proveedores...')

        from input.models.type_provider import TypeProvider
        from input.models.provider import Provider

        tipo, _ = TypeProvider.objects.get_or_create(name='Insumos Productivos')

        self.provider_semillas = Provider.objects.filter(producer=producer).first()
        if not self.provider_semillas:
            self.provider_semillas, _ = Provider.objects.get_or_create(
                cuit=_cuit('3062222222'),
                defaults={
                    'name': 'Cooperativa Agropecuaria Demo',
                    'type': tipo,
                    'address': 'Av. Siempreviva 742',
                    'city': self.city,
                    'phone': '2494222222',
                    'producer': producer,
                },
            )

        self.provider_fitosanitarios, _ = Provider.objects.get_or_create(
            cuit=_cuit('3063333333'),
            defaults={
                'name': 'Agroinsumos del Sur (Demo)',
                'type': tipo,
                'address': 'Ruta 226 Km 10',
                'city': self.city,
                'phone': '2494333333',
                'producer': producer,
            },
        )

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Compras y recepciones de stock (ingresa stock al depósito principal)#
    # ------------------------------------------------------------------ #
    def _agregar_stock_deposito(self, input_obj, store, cantidad):
        from input.models.input_stock import InputStock

        stock_record, _ = InputStock.objects.get_or_create(
            input=input_obj, store=store, defaults={'quantity': 0})
        stock_before = stock_record.quantity
        stock_record.quantity += cantidad
        stock_record.save()
        return stock_before, stock_record.quantity

    def _confirmar_orden_compra(self, order):
        """Replica la acción de admin `procesar_purchase_order`: confirma la orden,
        actualiza pendientes del insumo y genera la recepción pendiente asociada."""
        from input.models.purchase_order_detail import PurchaseOrderDetail
        from input.models.purchase_reception import PurchaseReception
        from input.models.purchase_reception_detail import PurchaseReceptionDetail
        from input.utils import update_input_cost

        order.state = 'confirm'
        order.save()

        details = PurchaseOrderDetail.objects.filter(purchase_order=order)
        for item in details:
            item.pending_amount = item.amount
            item.input.pending += item.amount
            item.input.save()
            item.save()
            # Si el insumo tiene un modo de costeo automático (última compra / promedio
            # de campaña), recalcula su costo en base al historial de compras confirmadas.
            update_input_cost(item.input)

        reception, created = PurchaseReception.objects.get_or_create(
            purchase_order=order,
            defaults={'store': order.store, 'producer': order.producer, 'state': 'pending'},
        )
        if created:
            for item in details:
                PurchaseReceptionDetail.objects.create(
                    purchase_reception=reception, input=item.input, amount=item.amount)
        return reception

    def _confirmar_recepcion(self, reception):
        """Replica la acción de admin `process_reception`: marca la recepción como
        confirmada, descuenta pendientes e ingresa el stock al depósito."""
        from input.models.purchase_order_detail import PurchaseOrderDetail
        from input.models.purchase_reception_detail import PurchaseReceptionDetail
        from input.models.stock_movement import StockMovement

        if reception.state == 'confirm':
            return

        reception.state = 'confirm'
        if not reception.delivery_date:
            reception.delivery_date = (
                reception.purchase_order.delivery_date if reception.purchase_order else None
            ) or date.today()
        reception.save()

        for item in PurchaseReceptionDetail.objects.filter(purchase_reception=reception):
            input_obj = item.input
            if reception.purchase_order:
                detail_po = PurchaseOrderDetail.objects.filter(
                    purchase_order=reception.purchase_order, input=input_obj).first()
                if detail_po:
                    detail_po.pending_amount -= item.amount
                    detail_po.save()
                    input_obj.pending -= item.amount
            input_obj.stock += item.amount
            input_obj.save()
            stock_before, stock_after = self._agregar_stock_deposito(
                input_obj, reception.store, item.amount)
            StockMovement.objects.create(
                date=reception.delivery_date,
                producer=reception.producer,
                input=input_obj,
                store=reception.store,
                quantity=item.amount,
                stock_before=stock_before,
                stock_after=stock_after,
                operation='purchase',
                purchase_reception=reception,
                notes=DEMO_TAG,
            )

    def _compras_y_recepciones(self, producer):
        self.stdout.write('→ Órdenes de compra y recepciones de stock...')

        from input.models.purchase_order import PurchaseOrder
        from input.models.purchase_order_detail import PurchaseOrderDetail

        if PurchaseOrder.objects.filter(reference=DEMO_TAG).exists():
            self.stdout.write('  Ya existían órdenes de compra de este set de ejemplo, se omite.')
            self.stdout.write(self.style.SUCCESS('  ✓'))
            return

        orden_semillas = PurchaseOrder.objects.create(
            date=date(2026, 5, 20),
            delivery_date=date(2026, 6, 5),
            reference=DEMO_TAG,
            applicant=self.responsible,
            provider=self.provider_semillas,
            store=self.store_principal,
            currency=self.currency,
            producer=producer,
        )
        for input_obj, cantidad in [
            (self.input_semilla_trigo, 13000),
            (self.input_semilla_cebada, 9000),
            (self.input_dap, 15000),
            (self.input_urea, 27000),
        ]:
            PurchaseOrderDetail.objects.create(
                purchase_order=orden_semillas, input=input_obj, amount=cantidad)

        orden_fitosanitarios = PurchaseOrder.objects.create(
            date=date(2026, 5, 22),
            delivery_date=date(2026, 6, 5),
            reference=DEMO_TAG,
            applicant=self.responsible,
            provider=self.provider_fitosanitarios,
            store=self.store_principal,
            currency=self.currency,
            producer=producer,
        )
        for input_obj, cantidad in [
            (self.input_herbicida, 400),
            (self.input_fungicida, 90),
        ]:
            PurchaseOrderDetail.objects.create(
                purchase_order=orden_fitosanitarios, input=input_obj, amount=cantidad)

        for orden in (orden_semillas, orden_fitosanitarios):
            reception = self._confirmar_orden_compra(orden)
            self._confirmar_recepcion(reception)

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {orden_semillas.code} y {orden_fitosanitarios.code} recibidas en {self.store_principal}'
        ))

    # ------------------------------------------------------------------ #
    # Movimiento de inventario entre depósitos                            #
    # ------------------------------------------------------------------ #
    def _mover_stock_entre_depositos(self, input_obj, origen, destino, cantidad, fecha, producer):
        """No existe un modelo de "transferencia" dedicado: se registra como un par
        de movimientos de ajuste (salida en origen / entrada en destino), igual a
        como lo haría un usuario manualmente desde el admin de StockMovement."""
        from input.models.input_stock import InputStock
        from input.models.stock_movement import StockMovement

        stock_origen, _ = InputStock.objects.get_or_create(
            input=input_obj, store=origen, defaults={'quantity': 0})
        stock_before_origen = stock_origen.quantity
        stock_origen.quantity -= cantidad
        stock_origen.save()

        StockMovement.objects.create(
            date=fecha, producer=producer, input=input_obj, store=origen,
            quantity=-cantidad, stock_before=stock_before_origen,
            stock_after=stock_origen.quantity, operation='adjustment',
            notes=f'{DEMO_TAG} - Transferencia a {destino.name}',
        )

        stock_destino, _ = InputStock.objects.get_or_create(
            input=input_obj, store=destino, defaults={'quantity': 0})
        stock_before_destino = stock_destino.quantity
        stock_destino.quantity += cantidad
        stock_destino.save()

        StockMovement.objects.create(
            date=fecha, producer=producer, input=input_obj, store=destino,
            quantity=cantidad, stock_before=stock_before_destino,
            stock_after=stock_destino.quantity, operation='adjustment',
            notes=f'{DEMO_TAG} - Transferencia desde {origen.name}',
        )

        # El stock global del insumo es la suma del stock en todos los depósitos.
        total = sum(InputStock.objects.filter(input=input_obj).values_list('quantity', flat=True))
        input_obj.stock = total
        input_obj.save()

    def _movimiento_entre_depositos(self, producer):
        self.stdout.write('→ Movimiento de inventario entre depósitos...')

        from input.models.stock_movement import StockMovement

        if StockMovement.objects.filter(operation='adjustment', notes__startswith=DEMO_TAG).exists():
            self.stdout.write('  Ya existía el movimiento entre depósitos de este set de ejemplo, se omite.')
            self.stdout.write(self.style.SUCCESS('  ✓'))
            return

        fecha = date(2026, 6, 10)
        self._mover_stock_entre_depositos(
            self.input_urea, self.store_principal, self.store_secundario, 8000, fecha, producer)
        self._mover_stock_entre_depositos(
            self.input_fungicida, self.store_principal, self.store_secundario, 30, fecha, producer)

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ Transferencia de Urea (8000 kg) y Fungicida (30 L) de '
            f'"{self.store_principal}" a "{self.store_secundario}"'
        ))

    # ------------------------------------------------------------------ #
    # Segunda compra de insumos ya existentes a precio distinto            #
    # (demuestra costeo por última compra y por promedio de campaña).      #
    # ------------------------------------------------------------------ #
    def _recompra_insumos_precio_diferente(self, producer):
        self.stdout.write('→ Segunda compra de insumos a precios distintos...')

        from input.models.purchase_order import PurchaseOrder
        from input.models.purchase_order_detail import PurchaseOrderDetail

        if PurchaseOrder.objects.filter(reference=REPRICE_TAG).exists():
            self.stdout.write('  Ya existía la recompra a precio distinto, se omite.')
            self.stdout.write(self.style.SUCCESS('  ✓'))
            return

        # Urea: costo pasa a tomarse de la última compra confirmada.
        self.input_urea.cost_update_mode = 'last_purchase'
        self.input_urea.save()
        # Semilla de Trigo: costo pasa a ser el promedio ponderado de la campaña activa.
        self.input_semilla_trigo.cost_update_mode = 'campaign_avg'
        self.input_semilla_trigo.save()

        orden = PurchaseOrder.objects.create(
            date=date(2026, 7, 10),
            delivery_date=date(2026, 7, 12),
            reference=REPRICE_TAG,
            applicant=self.responsible,
            provider=self.provider_semillas,
            store=self.store_principal,
            currency=self.currency,
            producer=producer,
        )
        # Precios distintos a los de la primera compra (350 y 780 respectivamente).
        PurchaseOrderDetail.objects.create(
            purchase_order=orden, input=self.input_semilla_trigo, amount=2000, price_unit=380)
        PurchaseOrderDetail.objects.create(
            purchase_order=orden, input=self.input_urea, amount=5000, price_unit=810)

        reception = self._confirmar_orden_compra(orden)
        self._confirmar_recepcion(reception)

        self.input_urea.refresh_from_db()
        self.input_semilla_trigo.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {orden.code}: Urea ahora cuesta ${self.input_urea.cost}/kg (última compra), '
            f'Semilla de Trigo ahora cuesta ${self.input_semilla_trigo.cost}/kg (promedio de campaña)'
        ))

    # ------------------------------------------------------------------ #
    # Procesar el plan técnico de un cultivo → genera sus órdenes de      #
    # trabajo e insumos planificados (replica la acción de admin          #
    # `process_plan` de Crop).                                            #
    # ------------------------------------------------------------------ #
    def _procesar_plan_tecnico(self, crop, plan):
        from datetime import timedelta
        from operation.models.technical_plan_detail import TechnicalPlanDetail
        from operation.models.technical_plan_input import TechnicalPlanInput
        from operation.models.work_order import WorkOrder
        from operation.models.input_work_order import InputWorkOrder
        from parameter.models.ot_state import OTState

        ordenes_por_etapa = {}
        date_init = crop.date_init

        for detail in TechnicalPlanDetail.objects.filter(technical_plan=plan).order_by('secuence'):
            days_estimate = crop.hectares_productive * detail.days_estimate / plan.hectares
            date_fin = date_init + timedelta(days=days_estimate)

            partner = None
            contractor = None
            if detail.subcontracted:
                type_wo = 'TPW'
                contractor = detail.contractor
            elif detail.with_partner:
                type_wo = 'PW'
                partner = detail.partner
            else:
                type_wo = 'OW'

            code = f'{crop.name} - {detail.service.name} - {date_init.strftime("%d-%m-%Y")}'
            order, _ = WorkOrder.objects.get_or_create(
                crop=crop,
                stage=detail.stage,
                defaults={
                    'code': code,
                    'date_emission': date_init - timedelta(days=3),
                    'date_init': date_init,
                    'date_fin': date_fin,
                    'producer': crop.producer,
                    'campaing': crop.campaing,
                    'area': crop.area,
                    'service': detail.service,
                    'stateOT': OTState.objects.get(is_default=True),
                    'type': type_wo,
                    'staff': crop.responsible,
                    'contractor': contractor,
                    'partner': partner,
                },
            )
            date_init = date_fin + timedelta(days=1)

            for item_input in TechnicalPlanInput.objects.filter(technical_plan_detail=detail):
                dose_total = item_input.dose * crop.hectares_productive / plan.hectares
                InputWorkOrder.objects.get_or_create(
                    work_order=order,
                    input=item_input.input,
                    defaults={
                        'dose': dose_total,
                        'value_estimated': item_input.input.cost or None,
                        'store': item_input.store,
                        'details': item_input.detail,
                    },
                )
            ordenes_por_etapa[detail.stage.name] = order

        return ordenes_por_etapa

    def _descontar_stock_deposito(self, input_obj, store, cantidad):
        from input.models.input_stock import InputStock

        if store is None:
            return 0, 0
        stock_record = InputStock.objects.filter(input=input_obj, store=store).first()
        if not stock_record:
            return 0, 0
        stock_before = stock_record.quantity
        stock_record.quantity -= cantidad
        stock_record.save()
        return stock_before, stock_record.quantity

    def _finalizar_orden_trabajo(self, work_order, dosis_aplicadas):
        """Replica la acción de admin `finish_order`: marca la orden como finalizada
        y descuenta del depósito los insumos realmente consumidos (dosis_aplicadas
        puede ser por debajo o por encima de lo planificado en `dose`)."""
        from operation.models.input_work_order import InputWorkOrder
        from input.models.stock_movement import StockMovement
        from parameter.models.ot_state import OTState

        if work_order.stateOT.name == 'Finalizada':
            return

        work_order.stateOT = OTState.objects.get(name='Finalizada')
        work_order.save()

        fallback_store = work_order.crop.countryside.store
        for iwo in InputWorkOrder.objects.filter(work_order=work_order):
            dose_applied = dosis_aplicadas.get(iwo.input.name)
            if dose_applied is None:
                continue
            iwo.dose_applied = dose_applied
            iwo.save()

            iwo.input.stock -= dose_applied
            iwo.input.save()
            store = iwo.store or fallback_store
            stock_before, stock_after = self._descontar_stock_deposito(iwo.input, store, dose_applied)
            StockMovement.objects.create(
                date=work_order.date_fin,
                producer=work_order.producer,
                input=iwo.input,
                store=store,
                quantity=-dose_applied,
                stock_before=stock_before,
                stock_after=stock_after,
                operation='output',
                work_order=work_order,
                notes=DEMO_TAG,
            )

    def _registrar_avances_y_costos(self, producer):
        self.stdout.write('→ Procesando planes técnicos, avances y costos de terceros...')

        from operation.models.work_order import WorkOrder

        if WorkOrder.objects.filter(crop=self.crop_trigo).exists():
            self.stdout.write('  Ya existían órdenes de trabajo de este set de ejemplo, se omite.')
            self.stdout.write(self.style.SUCCESS('  ✓'))
            return

        ordenes_trigo = self._procesar_plan_tecnico(self.crop_trigo, self.plan_trigo)
        ordenes_cebada = self._procesar_plan_tecnico(self.crop_cebada, self.plan_cebada)

        # --- Avances con consumos reales, algunos por debajo y otros por encima ---
        # de lo planificado (comparar con el `dose` de cada InputWorkOrder). La
        # cosecha de cada cultivo queda pendiente (todavía fuera de temporada).
        self._finalizar_orden_trabajo(ordenes_trigo['Barbecho Químico'], {
            'Herbicida Glifosato 66.2% (Demo)': 210,  # planificado 200 (+5%)
        })
        self._finalizar_orden_trabajo(ordenes_trigo['Siembra'], {
            'Semilla de Trigo (Demo)': 11700,  # planificado 12000 (-2.5%)
            'Fertilizante Fosfato Diamónico - DAP (Demo)': 8200,  # planificado 8000 (+2.5%)
        })
        self._finalizar_orden_trabajo(ordenes_trigo['Macollaje - Fertilización'], {
            'Urea Granulada (Demo)': 14500,  # planificado 15000 (-3.3%)
        })
        self._finalizar_orden_trabajo(ordenes_trigo['Control de Enfermedades'], {
            'Fungicida Triazol + Estrobirulina (Demo)': 55,  # planificado 50 (+10%)
        })

        self._finalizar_orden_trabajo(ordenes_cebada['Barbecho Químico'], {
            'Herbicida Glifosato 66.2% (Demo)': 150,  # planificado 160 (-6.25%)
        })
        self._finalizar_orden_trabajo(ordenes_cebada['Siembra'], {
            'Semilla de Cebada (Demo)': 8300,  # planificado 8000 (+3.75%)
            'Fertilizante Fosfato Diamónico - DAP (Demo)': 5500,  # planificado 5600 (-1.8%)
        })
        self._finalizar_orden_trabajo(ordenes_cebada['Macollaje - Fertilización'], {
            'Urea Granulada (Demo)': 7900,  # planificado 9600 (-17.7%)
        })
        self._finalizar_orden_trabajo(ordenes_cebada['Control de Enfermedades'], {
            'Fungicida Triazol + Estrobirulina (Demo)': 28,  # planificado 32 (-12.5%)
        })

        # --- Costo de labores de terceros: cosecha subcontratada ---
        orden_cosecha_trigo = ordenes_trigo['Cosecha']
        orden_cosecha_trigo.contractor_cost = 4500000
        orden_cosecha_trigo.save()

        orden_cosecha_cebada = ordenes_cebada['Cosecha']
        orden_cosecha_cebada.contractor_cost = 3200000
        orden_cosecha_cebada.save()

        self.stdout.write(self.style.SUCCESS(
            '  ✓ 8 órdenes finalizadas con consumo real (por debajo y por encima de lo '
            'planificado) + 2 órdenes de cosecha pendientes con costo de contratista'
        ))

    # ------------------------------------------------------------------ #
    # Tipos de silo y de servicio de acopio                                #
    # ------------------------------------------------------------------ #
    def _tipos_silo_y_servicio(self):
        self.stdout.write('→ Tipos de silo y de servicio de acopio...')

        from parameter.models.silo_type import SiloType
        from parameter.models.storage_service_type import StorageServiceType

        self.silo_type_metalico, _ = SiloType.objects.get_or_create(name='Metálico')
        self.silo_type_bolsa, _ = SiloType.objects.get_or_create(name='Bolsa plástica')
        self.silo_type_galpon, _ = SiloType.objects.get_or_create(name='Galpón')
        self.silo_type_torre, _ = SiloType.objects.get_or_create(name='Silo torre')

        for name in ['Almacenaje', 'Secada', 'Zaranda', 'Fumigación', 'Acondicionamiento']:
            StorageServiceType.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Finaliza la cosecha (pendiente desde el plan técnico) para que el   #
    # grano quede disponible para el módulo de acopio.                    #
    # ------------------------------------------------------------------ #
    def _finalizar_cosecha(self, producer):
        self.stdout.write('→ Finalizando cosecha de Trigo y Cebada...')

        from operation.models.work_order import WorkOrder
        from parameter.models.ot_state import OTState
        from parameter.models.cultivation_state import CiltivationState

        finalizada = OTState.objects.get(name='Finalizada')
        for crop in (self.crop_trigo, self.crop_cebada):
            orden_cosecha = WorkOrder.objects.filter(crop=crop, stage__name='Cosecha').first()
            if orden_cosecha and orden_cosecha.stateOT_id != finalizada.pk:
                orden_cosecha.stateOT = finalizada
                orden_cosecha.save()

        estado_cosechado, _ = CiltivationState.objects.get_or_create(name='Cosechado')
        for crop in (self.crop_trigo, self.crop_cebada):
            crop.state = estado_cosechado
            crop.hectares_harvested = crop.hectares_planted
            crop.hectares_not_harvested = 0
            crop.save()

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Rinde real de cada cultivo (requisito para poder acopiar: ver        #
    # storage.services.validate_crop_storage_entry).                      #
    # ------------------------------------------------------------------ #
    def _rindes_reales(self, producer):
        self.stdout.write('→ Rindes de cultivo (estimado y real)...')

        from operation.models.crop_yields import CropYields

        # Trigo: 100 ha x 3.2 tn/ha = 320 tn (coincide con lo cosechado a acopio).
        CropYields.objects.get_or_create(
            crop=self.crop_trigo,
            defaults={
                'date_estimate': self.crop_trigo.date_init,
                'yields_estimate': 3.0,
                'date_real': date(2026, 11, 25),
                'yields_real': 3.2,
                'detail': 'Rinde real de cosecha (Demo)',
            },
        )
        # Cebada: 80 ha x 3.0 tn/ha = 240 tn.
        CropYields.objects.get_or_create(
            crop=self.crop_cebada,
            defaults={
                'date_estimate': self.crop_cebada.date_init,
                'yields_estimate': 2.8,
                'date_real': date(2026, 11, 10),
                'yields_real': 3.0,
                'detail': 'Rinde real de cosecha (Demo)',
            },
        )

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Silos propios de distintos tipos                                    #
    # ------------------------------------------------------------------ #
    def _silos_propios(self, producer):
        self.stdout.write('→ Silos propios (metálico, bolsa, galpón, torre)...')

        from storage.models.silo import Silo

        self.silo_metalico, _ = Silo.objects.get_or_create(
            name='Silo Metálico 1 (Demo)',
            defaults={
                'type': self.silo_type_metalico,
                'capacity_tons': 300,
                'countryside': self.countryside,
                'producer': producer,
            },
        )
        self.silo_bolsa, _ = Silo.objects.get_or_create(
            name='Bolsón Lote Trigo (Demo)',
            defaults={
                'type': self.silo_type_bolsa,
                'capacity_tons': 200,
                'countryside': self.countryside,
                'lot': self.lot_trigo,
                'producer': producer,
            },
        )
        self.silo_galpon, _ = Silo.objects.get_or_create(
            name='Galpón Acopio Sur (Demo)',
            defaults={
                'type': self.silo_type_galpon,
                'capacity_tons': 500,
                'countryside': self.countryside,
                'producer': producer,
            },
        )
        self.silo_torre, _ = Silo.objects.get_or_create(
            name='Silo Torre Norte (Demo)',
            defaults={
                'type': self.silo_type_torre,
                'capacity_tons': 150,
                'countryside': self.countryside,
                'producer': producer,
            },
        )

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Movimientos de acopio propio: ingreso de cosecha a distintos silos, #
    # transferencia entre silos propios y salida por venta.               #
    # ------------------------------------------------------------------ #
    def _movimientos_silo(self, producer):
        self.stdout.write('→ Movimientos de acopio propio...')

        from storage.models.silo_movement import SiloMovement

        if SiloMovement.objects.filter(notes=DEMO_TAG).exists():
            self.stdout.write('  Ya existían movimientos de silo de este set de ejemplo, se omite.')
            self.stdout.write(self.style.SUCCESS('  ✓'))
            return

        fecha_cosecha_trigo = date(2026, 11, 25)
        fecha_cosecha_cebada = date(2026, 11, 10)

        # Ingreso de cosecha a distintos tipos de silo propio (320 tn trigo, 240 tn
        # cebada en total; parte queda en silos propios y parte va al acopiador).
        SiloMovement.objects.create(
            silo=self.silo_metalico, crop=self.crop_trigo, type=SiloMovement.ENTRY,
            date=fecha_cosecha_trigo, quantity_tons=140, producer=producer, notes=DEMO_TAG)
        SiloMovement.objects.create(
            silo=self.silo_bolsa, crop=self.crop_trigo, type=SiloMovement.ENTRY,
            date=fecha_cosecha_trigo, quantity_tons=60, producer=producer, notes=DEMO_TAG)
        SiloMovement.objects.create(
            silo=self.silo_galpon, crop=self.crop_cebada, type=SiloMovement.ENTRY,
            date=fecha_cosecha_cebada, quantity_tons=180, producer=producer, notes=DEMO_TAG)

        # Transferencia entre silos propios de distinto tipo (metálico → torre).
        SiloMovement.objects.create(
            silo=self.silo_metalico, crop=self.crop_trigo, type=SiloMovement.TRANSFER,
            destination_silo=self.silo_torre, date=date(2026, 12, 5), quantity_tons=40,
            producer=producer, notes=DEMO_TAG)

        # Salida por venta directa desde el silo metálico.
        SiloMovement.objects.create(
            silo=self.silo_metalico, crop=self.crop_trigo, type=SiloMovement.EXIT,
            date=date(2026, 12, 15), quantity_tons=20, remito_number='0001-00012345',
            producer=producer, notes=DEMO_TAG)

        self.stdout.write(self.style.SUCCESS(
            '  ✓ Ingreso a 3 silos propios, 1 transferencia entre silos y 1 salida por venta'
        ))

    # ------------------------------------------------------------------ #
    # Proveedor acopiador (acopio en terceros)                            #
    # ------------------------------------------------------------------ #
    def _proveedor_acopiador(self, producer):
        self.stdout.write('→ Proveedor acopiador...')

        from input.models.type_provider import TypeProvider
        from input.models.provider import Provider

        tipo_acopiador, _ = TypeProvider.objects.get_or_create(name='Acopiador')
        self.provider_acopiador, _ = Provider.objects.get_or_create(
            cuit=_cuit('3065555555'),
            defaults={
                'name': 'Acopiadora Cooperativa Sur (Demo)',
                'type': tipo_acopiador,
                'address': 'Ruta 226 Km 30',
                'city': self.city,
                'phone': '2494555555',
                'producer': producer,
            },
        )

        self.stdout.write(self.style.SUCCESS('  ✓'))

    # ------------------------------------------------------------------ #
    # Certificados de depósito en el acopiador (acopio en terceros)       #
    # ------------------------------------------------------------------ #
    def _certificados_acopio_terceros(self, producer):
        self.stdout.write('→ Certificados de depósito en el acopiador (acopio en terceros)...')

        from storage.models.storage_certificate import StorageCertificate
        from storage.models.storage_movement import StorageMovement
        from storage.models.storage_service import StorageService
        from parameter.models.storage_service_type import StorageServiceType

        if StorageCertificate.objects.filter(notes=DEMO_TAG).exists():
            self.stdout.write('  Ya existían certificados de depósito de este set de ejemplo, se omite.')
            self.stdout.write(self.style.SUCCESS('  ✓'))
            return

        tipo_secada = StorageServiceType.objects.get(name='Secada')
        tipo_zaranda = StorageServiceType.objects.get(name='Zaranda')

        # Certificado 1: Trigo, con un retiro parcial posterior → queda "Partial".
        cert_trigo = StorageCertificate.objects.create(
            number='CERT-TRIGO-2026-001',
            date_issue=date(2026, 11, 26),
            storage_provider=self.provider_acopiador,
            campaing=self.campaing,
            specie=self.variety_trigo.specie,
            crop=self.crop_trigo,
            quantity_entry=100,
            humidity_entry=13.5,
            impurities_entry=1.2,
            protein_entry=11.2,
            test_weight_entry=79,
            producer=producer,
            notes=DEMO_TAG,
        )
        StorageService.objects.create(
            certificate=cert_trigo, type=tipo_secada, date=date(2026, 11, 27),
            quantity_affected=100, shrinkage_tons=1.5, humidity_result=13.0,
            cost=45000, currency=self.currency, notes=DEMO_TAG)
        StorageMovement.objects.create(
            certificate=cert_trigo, type=StorageMovement.WITHDRAWAL, date=date(2026, 12, 20),
            quantity_tons=30, remito_number='0001-00099876', producer=producer, notes=DEMO_TAG)

        # Certificado 2: Trigo, convertido en warrant (el grano como garantía de un
        # financiamiento) → el estado queda fijo en "Warrant" sin importar los retiros.
        cert_trigo_warrant = StorageCertificate.objects.create(
            number='CERT-TRIGO-2026-002-W',
            date_issue=date(2026, 11, 28),
            storage_provider=self.provider_acopiador,
            campaing=self.campaing,
            specie=self.variety_trigo.specie,
            crop=self.crop_trigo,
            quantity_entry=20,
            humidity_entry=13.2,
            impurities_entry=1.0,
            protein_entry=11.5,
            test_weight_entry=80,
            is_warrant=True,
            warrant_entity='Banco Nación (Demo)',
            warrant_expiry=date(2027, 5, 31),
            producer=producer,
            notes=DEMO_TAG,
        )

        # Certificado 3: Cebada, vendida en su totalidad → queda "Cancelled".
        cert_cebada = StorageCertificate.objects.create(
            number='CERT-CEBADA-2026-001',
            date_issue=date(2026, 11, 11),
            storage_provider=self.provider_acopiador,
            campaing=self.campaing,
            specie=self.variety_cebada.specie,
            crop=self.crop_cebada,
            quantity_entry=60,
            humidity_entry=12.8,
            impurities_entry=1.5,
            test_weight_entry=65,
            producer=producer,
            notes=DEMO_TAG,
        )
        StorageService.objects.create(
            certificate=cert_cebada, type=tipo_zaranda, date=date(2026, 11, 12),
            quantity_affected=60, shrinkage_tons=0.8, cost=18000,
            currency=self.currency, notes=DEMO_TAG)
        StorageMovement.objects.create(
            certificate=cert_cebada, type=StorageMovement.SALE_EXIT, date=date(2027, 1, 15),
            quantity_tons=60, remito_number='0001-00099877', producer=producer, notes=DEMO_TAG)

        cert_trigo.refresh_from_db()
        cert_trigo_warrant.refresh_from_db()
        cert_cebada.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {cert_trigo.number} (estado: {cert_trigo.state}), '
            f'{cert_trigo_warrant.number} (estado: {cert_trigo_warrant.state}), '
            f'{cert_cebada.number} (estado: {cert_cebada.state})'
        ))

    # ------------------------------------------------------------------ #
    # Confirmar una venta: replica la acción de admin `confirmar_venta`    #
    # (sale.admin.sales_receipt) generando los movimientos de salida a     #
    # partir de las líneas de asignación de stock.                        #
    # ------------------------------------------------------------------ #
    def _confirmar_venta(self, sale):
        from django.db.models import Sum
        from sale.models.sale_stock_allocation import SaleStockAllocation
        from storage.models.silo_movement import SiloMovement
        from storage.models.storage_movement import StorageMovement

        allocations = SaleStockAllocation.objects.filter(sales_receipt=sale)
        total_asignado = allocations.aggregate(t=Sum('quantity_tons'))['t'] or 0
        if abs(total_asignado - sale.amount) > 0.01:
            raise ValueError(
                f'La venta {sale.number}: asignado {total_asignado} != vendido {sale.amount}')

        sale.state = 'confirm'
        sale.save()

        for alloc in allocations:
            if alloc.silo_stock_id:
                SiloMovement.objects.create(
                    silo=alloc.silo_stock.silo, crop=alloc.silo_stock.crop,
                    type=SiloMovement.EXIT, quantity_tons=alloc.quantity_tons,
                    related_sale=sale, producer=sale.producer, notes=DEMO_TAG)
            else:
                StorageMovement.objects.create(
                    certificate=alloc.certificate, type=StorageMovement.SALE_EXIT,
                    quantity_tons=alloc.quantity_tons, related_sale=sale,
                    producer=sale.producer, notes=DEMO_TAG)

    # ------------------------------------------------------------------ #
    # Venta de ejemplo que combina stock de un silo propio y de un         #
    # certificado de depósito en terceros en una misma operación,         #
    # demostrando la asignación venta → salidas de acopio.                #
    # ------------------------------------------------------------------ #
    def _venta_con_asignacion_de_stock(self, producer):
        self.stdout.write('→ Venta de granos (asignada a silo propio + certificado)...')

        from sale.models.sales_receipt import SalesReceipt
        from sale.models.type_sales_receipt import TypeSalesReceipt
        from sale.models.sale_stock_allocation import SaleStockAllocation
        from storage.models.silo_stock import SiloStock
        from storage.models.storage_certificate import StorageCertificate

        if SalesReceipt.objects.filter(number='V-0001-2026-DEMO').exists():
            self.stdout.write('  Ya existía la venta de ejemplo, se omite.')
            self.stdout.write(self.style.SUCCESS('  ✓'))
            return

        tipo_venta, _ = TypeSalesReceipt.objects.get_or_create(name='Venta de Granos')

        venta = SalesReceipt.objects.create(
            date=date(2027, 1, 20),
            type=tipo_venta,
            number='V-0001-2026-DEMO',
            currency=self.currency,
            name_custom='Molino Harinero del Sur (Demo)',
            cuit_custom=_cuit('3066666666'),
            campaing=self.campaing,
            cost_center=self.cost_center,
            especie=self.variety_trigo.specie,
            amount=100,  # toneladas
            subtotal=25000000,
            taxes=5250000,
            producer=producer,
        )

        silo_stock_metalico = SiloStock.objects.get(silo=self.silo_metalico, crop=self.crop_trigo)
        cert_trigo = StorageCertificate.objects.get(number='CERT-TRIGO-2026-001')

        SaleStockAllocation.objects.create(
            sales_receipt=venta, silo_stock=silo_stock_metalico, quantity_tons=60)
        SaleStockAllocation.objects.create(
            sales_receipt=venta, certificate=cert_trigo, quantity_tons=40)

        self._confirmar_venta(venta)

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {venta.number}: 100 tn de Trigo (60 tn desde {self.silo_metalico}, '
            f'40 tn desde {cert_trigo.number})'
        ))
