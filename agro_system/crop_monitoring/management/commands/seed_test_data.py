"""
Management command: seed_test_data
Crea datos mínimos de prueba para el motor vitivinícola.
Productor base: UserProducer id=2 (Florencia Productor).
Idem potente: update_or_create en todo, safe de correr varias veces.
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Crea datos de prueba para el motor vitivinícola (idem potente)"

    def handle(self, *args, **options):
        self._step("Parámetros base")
        self._seed_params()

        self._step("Productor y estructura del campo")
        self._seed_producer()

        self._step("Operación: actividades y cultivo")
        self._seed_operation()

        self._step("Etapas fenológicas BBCH")
        self._seed_bbch()

        self._step("Biofix + GDD acumulado de prueba")
        self._seed_crop_monitoring()

        self._step("Indicadores de alerta")
        self._seed_indicators()

        self.stdout.write(self.style.SUCCESS("\n✓ Seed completado. Datos listos para pruebas."))

    # ──────────────────────────────────────────────
    def _step(self, msg):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n→ {msg}"))

    def _ok(self, msg):
        self.stdout.write(f"   {msg}")

    # ── 1. Parámetros base ────────────────────────
    def _seed_params(self):
        from parameter.models.gender import Gender
        from parameter.models.currency import Currency
        from parameter.models.measure_unit import MaensureUnit
        from parameter.models.lot_rating import LotRating
        from parameter.models.countryside_condition import CountrysideCondition
        from parameter.models.cultivation_state import CiltivationState
        from parameter.models.ot_state import OTState
        from parameter.models.action import Action
        from parameter.models.area import Area
        from parameter.models.specie import Specie
        from parameter.models.type_var_crop_technique import TypeVarCropTechnique
        from parameter.models.var_crop_technique import VarCropTechnique

        # Géneros
        g_m, _ = Gender.objects.get_or_create(name="Masculino")
        g_f, _ = Gender.objects.get_or_create(name="Femenino")
        self._ok("Géneros: Masculino, Femenino")

        # Moneda
        ars, _ = Currency.objects.get_or_create(name="ARS", defaults={"name": "ARS"})
        self._ok("Moneda: ARS")

        # Unidad de medida
        MaensureUnit.objects.get_or_create(name="kg")
        MaensureUnit.objects.get_or_create(name="l")
        MaensureUnit.objects.get_or_create(name="ha")
        self._ok("Unidades: kg, l, ha")

        # Clasificación de lote
        LotRating.objects.get_or_create(name="A")
        LotRating.objects.get_or_create(name="B")
        self._ok("Clasificación de lote: A, B")

        # Condición de establecimiento
        CountrysideCondition.objects.get_or_create(name="Propio")
        CountrysideCondition.objects.get_or_create(name="Arrendado")
        self._ok("Condición: Propio, Arrendado")

        # Estados de cultivo
        CiltivationState.objects.get_or_create(name="Activo")
        CiltivationState.objects.get_or_create(name="Cosechado")
        CiltivationState.objects.get_or_create(name="Cancelado")
        self._ok("Estados de cultivo: Activo, Cosechado, Cancelado")

        # Estados de OT
        OTState.objects.get_or_create(name="Pendiente")
        OTState.objects.get_or_create(name="En curso")
        OTState.objects.get_or_create(name="Finalizada")
        OTState.objects.get_or_create(name="Contingente")
        OTState.objects.get_or_create(name="Cancelada")
        OTState.objects.get_or_create(name="Omitida")
        OTState.objects.get_or_create(name="Cancelada por alerta")
        self._ok("Estados de OT: Pendiente, En curso, Finalizada, Contingente, Cancelada")

        # Acciones
        Action.objects.get_or_create(name="Notificar")
        self._ok("Acción: Notificar")

        # Áreas vitivinícolas
        mendoza_alerts = {
            "estres_hidrico":    "on",
            "helada":            "on",
            "granizo":           "on",
            "golpe_calor":       "on",
            "zonda":             "on",
            "lobesia":           "on",
            "oidio":             "on",
            "ventana_aplicacion":"on",
            "gdd_cosecha":       "on",
            "bbch_dinamico":     "on",
            "mildiu_primario":   "vigilancia",
            "mildiu_secundario": "off",
            "botrytis":          "vigilancia",
            "exceso_hidrico":    "off",
        }
        mendoza_thresholds = {
           "helada": {
                "categoria": "climatica",
                "variable_disparo": "t_min",
                # La alerta solo vive en esta ventana del año (Mendoza). Fuera de acá, ni se evalúa.
                "ventana_calendario": {"desde": "08-20", "hasta": "11-30"},  # MM-DD
                # El umbral cambia por estado: tejido más avanzado = más sensible = umbral más tibio.
                "bandas_bbch": [
                    {"bbch_desde": 1,  "bbch_hasta": 5,  "aviso": -3.0, "alerta": -3.5, "critico": -5.0},
                    {"bbch_desde": 7,  "bbch_hasta": 9,  "aviso": -1.5, "alerta": -2.0, "critico": -3.0},
                    {"bbch_desde": 11, "bbch_hasta": 27, "aviso": -0.5, "alerta": -1.0, "critico": -2.0},
                    {"bbch_desde": 28, "bbch_hasta": 65, "aviso": -0.5, "alerta": -1.0, "critico": -2.0},
                ],
                # El viento/HR no es otra alerta: modula el riesgo. Helada radiativa = noche calma y seca.
                "modificadores": {
                    "radiativa": {"viento_max": 3, "hr_max": 60, "efecto": "subir_nivel"},
                },
            }
        }
        area_mza, _ = Area.objects.update_or_create(
            name="Mendoza",
            defaults={
                "climate":          "BWk_arid",
                "gdd_upper_cutoff": 30.0,
            },
        )
        from alert.models.alert_profile import AlertProfile
        AlertProfile.objects.update_or_create(
            area=area_mza,
            defaults={
                "priority_sources": ["open_meteo_eto", "estacion_humedad_suelo", "estacion"],
            },
        )
        self._ok(f"Area: Mendoza (id={area_mza.id}, gdd_upper_cutoff=30.0)")

        area_tnd, _ = Area.objects.update_or_create(
            name="Tandil",
            defaults={
                "climate":          "Cfb_humid",
                "gdd_upper_cutoff": None,
            },
        )
        AlertProfile.objects.update_or_create(
            area=area_tnd,
            defaults={
                "priority_sources": ["estacion", "open_meteo_eto"],
            },
        )
        self._ok(f"Area: Tandil (id={area_tnd.id}, gdd_upper_cutoff=null)")

        # Especies / variedades
        species_data = [
            ("Malbec",             1450, 1700),
            ("Cabernet Sauvignon", 1550, 1800),
            ("Bonarda",            1600, 1900),
            ("Chardonnay",         1100, 1350),
            ("Merlot",             1300, 1550),
            ("Syrah",              1400, 1650),
        ]
        for name, gdd_min, gdd_max in species_data:
            Specie.objects.update_or_create(
                name=name,
                defaults={"gdd_harvest_min": gdd_min, "gdd_harvest_max": gdd_max},
            )
        self._ok(f"Especies: {', '.join(s[0] for s in species_data)}")

        # Tipos y variables para indicadores
        tipo_clima, _ = TypeVarCropTechnique.objects.get_or_create(name="Climático")
        tipo_suelo, _ = TypeVarCropTechnique.objects.get_or_create(name="Suelo")
        VarCropTechnique.objects.get_or_create(name="Temperatura mínima", defaults={"type": tipo_clima})
        VarCropTechnique.objects.get_or_create(name="Temperatura máxima", defaults={"type": tipo_clima})
        VarCropTechnique.objects.get_or_create(name="Humedad relativa",   defaults={"type": tipo_clima})
        VarCropTechnique.objects.get_or_create(name="Lluvia (mm)",        defaults={"type": tipo_clima})
        VarCropTechnique.objects.get_or_create(name="Humedad de suelo",   defaults={"type": tipo_suelo})
        self._ok("Variables técnicas: Temp mín/máx, HR, Lluvia, Humedad suelo")

    # ── 2. Productor ──────────────────────────────
    def _seed_producer(self):
        from user.models.user_producer import UserProducer
        from producer.models.typeStaff import TypeStaff
        from parameter.models.gender import Gender
        from parameter.models.city import City
        from parameter.models.cultivation_state import CiltivationState
        from parameter.models.countryside_condition import CountrysideCondition
        from parameter.models.lot_rating import LotRating
        from parameter.models.area import Area
        from producer.models.cost_center import CostCenter
        from producer.models.store import Store
        from producer.models.country_side import Countryside
        from producer.models.staff import Staff
        from producer.models.lot import Lot

        producer = UserProducer.objects.get(id=2)

        # TypeStaff
        tipo_agronomo, _ = TypeStaff.objects.get_or_create(name="Agrónomo")
        tipo_admin, _    = TypeStaff.objects.get_or_create(name="Administración")
        self._ok("TypeStaff: Agrónomo, Administración")

        # Ciudades
        mendoza_city = City.objects.filter(name__icontains="MENDOZA").first() \
                       or City.objects.filter(name__icontains="EL MANZANO").first()
        lujan_city   = City.objects.filter(name__icontains="LUJAN DE CUYO").first() \
                       or mendoza_city

        # CostCenter
        cc_vid, _ = CostCenter.objects.get_or_create(name="Viñedo Mendoza")
        self._ok(f"CostCenter: Viñedo Mendoza (id={cc_vid.id})")

        # Staff / agrónomo
        gender_m = Gender.objects.filter(name="Masculino").first()
        gender_f = Gender.objects.filter(name="Femenino").first()
        staff, created = Staff.objects.get_or_create(
            cuit="20301234567",
            defaults={
                "name":        "Juan",
                "surname":     "Pérez",
                "address":     "Av. San Martín 100",
                "city":        lujan_city,
                "phone":       "2614000000",
                "email":       "juan.perez@finca.com",
                "type":        tipo_agronomo,
                "gender":      gender_m or gender_f,
                "date_entry":  date(2024, 1, 1),
                "state":       "active",
                "producer":    producer,
            },
        )
        self._ok(f"Staff: Juan Pérez, Agrónomo (id={staff.id})")

        # Store
        store, _ = Store.objects.get_or_create(
            name="Depósito Luján de Cuyo",
            defaults={
                "address":  "Ruta 15 km 5",
                "city":     lujan_city,
                "default":  True,
                "producer": producer,
            },
        )
        self._ok(f"Store: Depósito Luján de Cuyo (id={store.id})")

        # Countryside (establecimiento)
        condition = CountrysideCondition.objects.filter(name="Propio").first()
        countryside, _ = Countryside.objects.get_or_create(
            name="Finca San Carlos",
            defaults={
                "number_id":   "1001",
                "condition":   condition,
                "hectares":    50.0,
                "responsible": staff,
                "address":     "Ruta 40 km 1040",
                "city":        lujan_city,
                "phone":       "2614111111",
                "cost_center": cc_vid,
                "store":       store,
                "producer":    producer,
            },
        )
        self._ok(f"Countryside: Finca San Carlos (id={countryside.id})")

        # Lots
        area_mza  = Area.objects.get(name="Mendoza")
        rating_a  = LotRating.objects.filter(name="A").first()

        from operation.models.variety import Variety as Activity
        # La actividad puede no existir aún, se la asignamos después
        # Lot requiere activity (M2M), se agrega después

        lot, created = Lot.objects.get_or_create(
            name="Lote Norte — Malbec",
            defaults={
                "countryside":         countryside,
                "area":                area_mza,
                "responsible":         staff,
                "hectares":            12.0,
                "hectares_productive": 10.0,
                "cost_center":         cc_vid,
                "LotRating":           rating_a,
            },
        )
        self._ok(f"Lot: Lote Norte — Malbec (id={lot.id})")

        lot2, created2 = Lot.objects.get_or_create(
            name="Lote Sur — Cabernet",
            defaults={
                "countryside":         countryside,
                "area":                area_mza,
                "responsible":         staff,
                "hectares":            8.0,
                "hectares_productive": 7.5,
                "cost_center":         cc_vid,
                "LotRating":           rating_a,
            },
        )
        self._ok(f"Lot: Lote Sur — Cabernet (id={lot2.id})")

    # ── 3. Operación ──────────────────────────────
    def _seed_operation(self):
        from parameter.models.specie import Specie
        from parameter.models.cultivation_state import CiltivationState
        from parameter.models.campaign import Campaing
        from parameter.models.area import Area
        from producer.models.country_side import Countryside
        from producer.models.lot import Lot
        from producer.models.staff import Staff
        from producer.models.cost_center import CostCenter
        from user.models.user_producer import UserProducer
        from operation.models.variety import Variety as Activity
        from operation.models.crop import Crop

        producer    = UserProducer.objects.get(id=2)
        malbec      = Specie.objects.get(name="Malbec")
        cab_sauv    = Specie.objects.get(name="Cabernet Sauvignon")
        campaing    = Campaing.objects.get(id=1)
        area_mza    = Area.objects.get(name="Mendoza")
        countryside = Countryside.objects.get(name="Finca San Carlos")
        lot_norte   = Lot.objects.get(name="Lote Norte — Malbec")
        lot_sur     = Lot.objects.get(name="Lote Sur — Cabernet")
        staff       = Staff.objects.filter(cuit="20301234567").first()
        state_activo= CiltivationState.objects.get(name="Activo")

        # Actividades (Activity → Specie)
        act_malbec, _ = Activity.objects.get_or_create(
            name="Malbec",
            defaults={
                "specie":          malbec,
                "is_agricultural": True,
                "is_livestock":    False,
            },
        )
        act_cab, _ = Activity.objects.get_or_create(
            name="Cabernet Sauvignon",
            defaults={
                "specie":          cab_sauv,
                "is_agricultural": True,
                "is_livestock":    False,
            },
        )
        self._ok(f"Activities: Malbec (id={act_malbec.id}), Cabernet Sauv. (id={act_cab.id})")

        # Asignar actividad al lote (M2M)
        lot_norte.activity.add(act_malbec)
        lot_sur.activity.add(act_cab)

        # Crops
        crop_malbec, _ = Crop.objects.get_or_create(
            name="Malbec 2026/27 — Lote Norte",
            defaults={
                "campaing":              campaing,
                "countryside":           countryside,
                "area":                  area_mza,
                "lot":                   lot_norte,
                "activity":              act_malbec,
                "responsible":           staff,
                "state":                 state_activo,
                "hectares_productive":   10.0,
                "hectares_planted":      10.0,
                "hectares_unplanted":    0.0,
                "hectares_harvested":    0.0,
                "hectares_not_harvested":10.0,
                "impute_bills":          True,
                "producer":              producer,
                "is_main":               True,
            },
        )
        self._ok(f"Crop: Malbec 2026/27 Lote Norte (id={crop_malbec.id}, is_main=True)")

        crop_cab, _ = Crop.objects.get_or_create(
            name="Cabernet Sauv. 2026/27 — Lote Sur",
            defaults={
                "campaing":              campaing,
                "countryside":           countryside,
                "area":                  area_mza,
                "lot":                   lot_sur,
                "activity":              act_cab,
                "responsible":           staff,
                "state":                 state_activo,
                "hectares_productive":   7.5,
                "hectares_planted":      7.5,
                "hectares_unplanted":    0.0,
                "hectares_harvested":    0.0,
                "hectares_not_harvested":7.5,
                "impute_bills":          True,
                "producer":              producer,
                "is_main":               False,
            },
        )
        self._ok(f"Crop: Cabernet Sauv. 2026/27 Lote Sur (id={crop_cab.id})")

    # ── 4. BBCH ───────────────────────────────────
    def _seed_bbch(self):
        from crop_monitoring.models.phenological_state import seed_phenological_stages
        seed_phenological_stages()
        self._ok("14 etapas fenológicas cargadas/actualizadas")

    # ── 5. Biofix + GDD ───────────────────────────
    def _seed_crop_monitoring(self):
        from operation.models.crop import Crop
        from crop_monitoring.models.biofix import Biofix
        from crop_monitoring.models.gdd_accumulator import GDDAccumulator

        crop_malbec = Crop.objects.filter(name="Malbec 2026/27 — Lote Norte").first()
        if not crop_malbec:
            self._ok("Crop Malbec no encontrado, saltando biofix")
            return

        # Biofix vine: brotación simulada hace ~100 días
        biofix_date = date.today() - timedelta(days=100)
        biofix_vine, created = Biofix.objects.get_or_create(
            crop=crop_malbec,
            counter=Biofix.COUNTER_VINE,
            defaults={
                "base_temp":    10.0,
                "date":         biofix_date,
                "origin":       Biofix.ORIGIN_MANUAL,
                "is_confirmed": True,
            },
        )
        if not created:
            self._ok(f"Biofix vine ya existía (id={biofix_vine.id})")
        else:
            self._ok(f"Biofix vine creado: {biofix_date} (id={biofix_vine.id})")

        # GDDAccumulator con valor simulado para que caiga en floración (BBCH 65 ~ 350 GDD)
        acc, _ = GDDAccumulator.objects.get_or_create(biofix=biofix_vine)
        acc.accumulated_gdd  = 350.0   # BBCH 65 — Plena floración
        acc.calculation_date = date.today()
        acc.save()
        self._ok(f"GDDAccumulator: 350.0 GDD → BBCH 65 Plena floración (id={acc.id})")

        # Biofix Lobesia para el mismo crop
        biofix_lob, created = Biofix.objects.get_or_create(
            crop=crop_malbec,
            counter=Biofix.COUNTER_LOBESIA,
            defaults={
                "base_temp":    7.0,
                "date":         date.today() - timedelta(days=60),
                "origin":       Biofix.ORIGIN_MANUAL,
                "is_confirmed": True,
            },
        )
        acc_lob, _ = GDDAccumulator.objects.get_or_create(biofix=biofix_lob)
        acc_lob.accumulated_gdd  = 180.0   # Cerca de 1ª generación (~200-250 GDD)
        acc_lob.calculation_date = date.today()
        acc_lob.save()
        self._ok(f"Biofix Lobesia + acumulador: 180.0 GDD base 7 (pre-1ª gen)")

    # ── 6. Indicadores ────────────────────────────
    def _seed_indicators(self):
        from alert.models.indicator import Indicator

        indicadores = [
            ("helada",             "Helada",                    "high"),
            ("estres_hidrico",     "Estrés hídrico",            "high"),
            ("granizo",            "Granizo",                   "high"),
            ("golpe_calor",        "Golpe de calor",            "medium"),
            ("zonda",              "Zonda",                     "medium"),
            ("lobesia",            "Lobesia botrana",           "medium"),
            ("oidio",              "Oídio",                     "medium"),
            ("botrytis",           "Botrytis",                  "medium"),
            ("mildiu_primario",    "Mildiu primario",           "low"),
            ("mildiu_secundario",  "Mildiu secundario",         "low"),
            ("ventana_aplicacion", "Ventana de aplicación",     "low"),
            ("gdd_cosecha",        "Ventana de cosecha",        "low"),
        ]

        for slug, nombre, criticidad in indicadores:
            obj, created = Indicator.objects.get_or_create(
                name=slug,
                defaults={"criticality_level": criticidad},
            )
            if created:
                self._ok(f"Indicator: {nombre} (slug={slug}, criticality={criticidad})")

        self._ok(f"Total: {len(indicadores)} indicadores creados/verificados")

        # AlertProfileIndicator: status de cada indicador por zona
        from alert.models.alert_profile import AlertProfile
        from alert.models.alert_profile_indicator import AlertProfileIndicator
        from parameter.models.area import Area

        MENDOZA_STATUS = {
            "estres_hidrico":    "on",
            "helada":            "on",
            "granizo":           "on",
            "golpe_calor":       "on",
            "zonda":             "on",
            "lobesia":           "on",
            "oidio":             "on",
            "ventana_aplicacion":"on",
            "gdd_cosecha":       "on",
            "mildiu_primario":   "vigilance",
            "botrytis":          "vigilance",
        }
        TANDIL_STATUS = {
            "helada":            "on",
            "ventana_aplicacion":"on",
            "mildiu_primario":   "on",
            "mildiu_secundario": "on",
            "botrytis":          "on",
            "estres_hidrico":    "vigilance",
            "lobesia":           "vigilance",
            "granizo":           "vigilance",
        }
        for area_name, status_map in [("Mendoza", MENDOZA_STATUS), ("Tandil", TANDIL_STATUS)]:
            try:
                profile = AlertProfile.objects.get(area__name=area_name)
            except AlertProfile.DoesNotExist:
                continue
            for slug, status in status_map.items():
                try:
                    indicator = Indicator.objects.get(name=slug)
                    AlertProfileIndicator.objects.update_or_create(
                        profile=profile, indicator=indicator,
                        defaults={"status": status},
                    )
                except Indicator.DoesNotExist:
                    pass
        self._ok("AlertProfileIndicators creados para Mendoza y Tandil")
