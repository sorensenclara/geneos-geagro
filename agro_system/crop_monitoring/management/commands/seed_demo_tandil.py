"""
Management command: seed_demo_tandil

Crea un productor de demostración en Tandil, aislado del resto de los datos:

  - Productor "Productor Demo Tandil" + personal con usuario (recibe notificaciones)
  - Campo, depósito, centro de costo y lote propios ("Lote Sierra", zona BS AS - MAR Y SIERRAS)
  - Cultivo Malbec 2026/27 en la campaña 2026-2027 (no se activa ninguna campaña)
  - Etapas operativas para Malbec y algunas órdenes de trabajo
  - Monitoreo de cultivo: estados fenológicos BBCH, calibración Malbec/zona, GDD de cosecha,
    biofix de brotación, acumulador GDD y una observación fenológica
  - Indicadores con evaluador (helada, granizo, mildiu primario, ventana de aplicación),
    vinculados a los perfiles de zona Tandil (MAR Y SIERRAS) y Mendoza (CUYO - MENDOZA)
    y asignados al cultivo nuevo
  - Estación externa Open-Meteo Tandil (solo para el lote nuevo) con sus variables
  - Descarga del clima real de esa estación, evaluación del motor SOLO para el lote nuevo
  - Alertas de pronóstico de prueba (mañana, +2 y +3 días) con sus notificaciones

No modifica el productor existente, sus cultivos, sus indicadores ni sus alertas.
Los indicadores existentes no se tocan (se crean otros con nombres distintos).

Idempotente: se puede correr varias veces.

Uso:
    python manage.py seed_demo_tandil
    python manage.py seed_demo_tandil --sin-clima   # no descarga clima ni evalúa el motor
"""
import contextlib
import io
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

PRODUCER_EMAIL = "demo.tandil@geneos.com.ar"
STAFF_EMAIL = "agronomo.tandil@geneos.com.ar"
DEMO_PASSWORD = "Demo1234!"

AREA_TANDIL = "BS AS - MAR Y SIERRAS"
AREA_MENDOZA = "CUYO - MENDOZA"
CAMPAIGN_NAME = "2026-2027"
VARIETY_NAME = "Malbec"
SPECIE_NAME = "MALBEC"
CROP_NAME = "Malbec 2026/27 — Lote Sierra"

STATION = {
    "name": "Open-Meteo Tandil",
    "latitude": -37.3217,
    "longitude": -59.1332,
    "url": "https://api.open-meteo.com/v1/forecast",
    "forecast_days": 7,
    "variable": "hourly",
}

# source_field de Open-Meteo -> nombre de la variable climática del sistema
STATION_VARIABLES = [
    ("precipitation", "Precipitación (mm)"),
    ("temperature_2m", "Temperatura"),
    ("et0_fao_evapotranspiration", "ETo"),
    ("cape", "CAPE"),
    ("relative_humidity_2m", "Humedad relativa"),
    ("wind_speed_10m", "Velocidad del viento"),
    ("wind_direction_10m", "Dirección del viento"),
    ("wind_gusts_10m", "Ráfagas de viento"),
]

# Indicadores con evaluador propio (mismos slugs que seed_indicators)
INDICATORS = [
    # slug, criticidad, evaluador, max_forecast_days
    ("helada", "high", "alert.evaluators.frost.FrostEvaluator", 5),
    ("granizo", "high", "alert.evaluators.storm_hail.StormHailEvaluator", 2),
    ("mildiu_primario", "medium", "alert.evaluators.mildiu_primario.MildiuPrimarioEvaluator", 3),
    ("ventana_aplicacion", "low", "alert.evaluators.ventana_aplicacion.VentanaAplicacionEvaluator", 1),
]
PROFILE_STATUS = {
    AREA_TANDIL: {"helada": "on", "granizo": "vigilance", "mildiu_primario": "on", "ventana_aplicacion": "on"},
    AREA_MENDOZA: {"helada": "on", "granizo": "on", "mildiu_primario": "vigilance", "ventana_aplicacion": "on"},
}

MALBEC_STAGES = [("Poda", 0), ("Brotación", 1), ("Floración y Cuaje", 2), ("Envero", 3),
                 ("Maduración", 4), ("Cosecha", 6)]

# (código, servicio, etapa, días desde hoy inicio, duración, estado)
WORK_ORDERS = [
    ("DT-0001", "Podar", "Poda", -30, 5, "Finalizada"),
    ("DT-0002", "Tratamiento Fitosanitario", "Brotación", -1, 2, "EN CURSO"),
    ("DT-0003", "Mantenimiento de Estructura", "Brotación", 3, 2, "PENDIENTE"),
]

# Alertas de prueba: (slug, días desde hoy, nivel)
TEST_ALERTS = [
    ("helada", 1, "alert"),
    ("granizo", 2, "warning"),
    ("mildiu_primario", 3, "alert"),
]


class Command(BaseCommand):
    help = "Crea un productor demo en Tandil con cultivo, OTs, monitoreo, indicadores, estación y alertas."

    def add_arguments(self, parser):
        parser.add_argument("--sin-clima", action="store_true",
                            help="No descarga clima de Open-Meteo ni evalúa el motor de alertas.")

    def handle(self, *args, **options):
        self.today = timezone.localdate()
        with transaction.atomic():
            self._lookups()
            self._step("Productor, personal y estructura")
            self._producer()
            self._step("Variables climáticas y estación externa")
            self._station()
            self._step("Lote y cultivo")
            self._lot_and_crop()
            self._step("Monitoreo de cultivo (BBCH, calibración, GDD, biofix)")
            self._crop_monitoring()
            self._step("Etapas")
            self._stages()
            self._step("Indicadores y perfiles de zona")
            self._indicators()
            self._step("Órdenes de trabajo")
            self._work_orders()

        if options["sin_clima"]:
            self._ok("Clima omitido (--sin-clima).")
        else:
            self._step("Clima real de Open-Meteo (solo estación Tandil)")
            self._fetch_weather()
            self._step("Motor de alertas (solo lote nuevo)")
            self._run_engine()

        self._step("Alertas de prueba")
        self._test_alerts()
        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Listo. Ingreso productor: {PRODUCER_EMAIL} / {DEMO_PASSWORD} — "
            f"personal: {STAFF_EMAIL} / {DEMO_PASSWORD}"))

    # ── helpers ────────────────────────────────────────────────────────────
    def _step(self, msg):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n→ {msg}"))

    def _ok(self, msg):
        self.stdout.write(f"   {msg}")

    def _tag(self, created):
        return "+ creado" if created else "✓ existía"

    def _get(self, model, label, **lookup):
        obj = model.objects.filter(**lookup).first()
        if obj is None:
            raise CommandError(f"No existe {label} ({lookup}). Cargalo antes de correr el comando.")
        return obj

    def _lookups(self):
        """Datos que ya existen y se reutilizan (no se crean ni se modifican)."""
        from parameter.models.area import Area
        from parameter.models.campaign import Campaing
        from parameter.models.city import City
        from parameter.models.gender import Gender
        from parameter.models.countryside_condition import CountrysideCondition
        from parameter.models.lot_rating import LotRating
        from parameter.models.cultivation_state import CiltivationState
        from parameter.models.specie import Specie
        from producer.models.typeStaff import TypeStaff
        from operation.models.variety import Variety

        self.area_tandil = self._get(Area, "la zona de Tandil", name=AREA_TANDIL)
        self.area_mendoza = self._get(Area, "la zona de Mendoza", name=AREA_MENDOZA)
        self.campaign = self._get(Campaing, "la campaña", name=CAMPAIGN_NAME)
        self.city = self._get(City, "la ciudad de Tandil", name="TANDIL")
        self.gender = self._get(Gender, "un género")
        self.condition = (CountrysideCondition.objects.filter(name__iexact="PROPIO").first()
                          or self._get(CountrysideCondition, "una condición de campo"))
        self.rating = self._get(LotRating, "una calificación de lote")
        self.crop_state = self._get(CiltivationState, "un estado de cultivo")
        self.type_staff = (TypeStaff.objects.filter(name__icontains="Agrónomo").first()
                           or self._get(TypeStaff, "un tipo de personal"))
        self.specie = self._get(Specie, "la especie Malbec", name=SPECIE_NAME)
        self.variety = self._get(Variety, "la variedad Malbec", name=VARIETY_NAME)

    # ── 1. Productor ───────────────────────────────────────────────────────
    def _producer(self):
        from user.models.user_producer import UserProducer
        from user.models.user_extend import UserExtend
        from producer.models.staff import Staff
        from producer.models.store import Store
        from producer.models.cost_center import CostCenter
        from producer.models.country_side import Countryside

        self.producer = UserProducer.objects.filter(email=PRODUCER_EMAIL).first()
        created = self.producer is None
        if created:
            self.producer = UserProducer(email=PRODUCER_EMAIL, name="Productor Demo Tandil", cuit="30712345678",
                                         address="Ruta 226 km 160", city=self.city, phone="2494000000")
            self.producer.set_password(DEMO_PASSWORD)
            self.producer.save()
        self._ok(f"{self._tag(created)}: productor {self.producer} (id={self.producer.pk})")

        staff_user = UserExtend.objects.filter(email=STAFF_EMAIL).first()
        if staff_user is None:
            staff_user = UserExtend.objects.create_user(STAFF_EMAIL, password=DEMO_PASSWORD)
            staff_user.username = "agronomo.tandil"
            staff_user.type = "Staff"
            staff_user.save()
        self.staff, created = Staff.objects.get_or_create(
            cuit="20345678901",
            defaults={"name": "Lucía", "surname": "Gómez", "address": "Av. Santamarina 500", "city": self.city,
                      "phone": "2494111111", "type": self.type_staff, "gender": self.gender,
                      "state": "active", "producer": self.producer, "user": staff_user},
        )
        self._ok(f"{self._tag(created)}: personal {self.staff} con usuario {STAFF_EMAIL}")

        self.cost_center, _ = CostCenter.objects.get_or_create(name="Viñedo Demo Tandil")
        self.store, _ = Store.objects.get_or_create(
            name="Depósito Demo Tandil",
            defaults={"address": "Ruta 226 km 160", "city": self.city, "producer": self.producer},
        )
        self.countryside, created = Countryside.objects.get_or_create(
            name="Finca Demo Tandil",
            defaults={"condition": self.condition, "responsible": self.staff, "address": "Ruta 226 km 160",
                      "city": self.city, "phone": "2494000000", "cost_center": self.cost_center,
                      "store": self.store, "producer": self.producer, "hectares": 20.0},
        )
        self._ok(f"{self._tag(created)}: campo {self.countryside}, depósito {self.store}, "
                 f"centro de costo {self.cost_center}")

    # ── 2. Estación externa ────────────────────────────────────────────────
    def _station(self):
        from parameter.models.var_crop_technique import VarCropTechnique
        from weather.models.station_external import ExternalStation
        from weather.models.station_external_variable import ExternalStationVariable

        self.station, created = ExternalStation.objects.get_or_create(
            name=STATION["name"], defaults={k: v for k, v in STATION.items() if k != "name"})
        self._ok(f"{self._tag(created)}: estación {self.station} ({self.station.latitude}, {self.station.longitude})")

        for source_field, var_name in STATION_VARIABLES:
            variable, var_created = VarCropTechnique.objects.get_or_create(
                name=var_name, defaults={"type": self._climate_type(), "is_climatic": True})
            _, map_created = ExternalStationVariable.objects.get_or_create(
                station=self.station, variable=variable, defaults={"source_field": source_field})
            extra = " (variable nueva)" if var_created else ""
            self._ok(f"   {self._tag(map_created)}: {var_name} → {source_field}{extra}")

    def _climate_type(self):
        from parameter.models.type_var_crop_technique import TypeVarCropTechnique
        return (TypeVarCropTechnique.objects.filter(name__icontains="CLIMA").first()
                or TypeVarCropTechnique.objects.create(name="CLIMATOLÓGICA"))

    # ── 3. Lote y cultivo ──────────────────────────────────────────────────
    def _lot_and_crop(self):
        from producer.models.lot import Lot
        from operation.models.crop import Crop

        self.lot, created = Lot.objects.get_or_create(
            name="Lote Sierra",
            defaults={"countryside": self.countryside, "area": self.area_tandil, "responsible": self.staff,
                      "hectares": 5.5, "hectares_productive": 5.0, "cost_center": self.cost_center,
                      "LotRating": self.rating, "external_station": self.station},
        )
        if self.lot.external_station_id != self.station.pk:
            self.lot.external_station = self.station
            self.lot.save(update_fields=["external_station"])
        self.lot.activity.add(self.variety)  # variedades del lote (en esta rama el campo se llama activity)
        self._ok(f"{self._tag(created)}: lote {self.lot} (zona {self.area_tandil}, estación {self.station})")

        self.crop, created = Crop.objects.get_or_create(
            name=CROP_NAME,
            defaults={"campaing": self.campaign, "countryside": self.countryside, "area": self.area_tandil,
                      "lot": self.lot, "activity": self.variety, "responsible": self.staff,
                      "state": self.crop_state, "producer": self.producer, "is_main": True,
                      "hectares_productive": 5.0, "hectares_planted": 5.0},
        )
        self._ok(f"{self._tag(created)}: cultivo {self.crop} (campaña {self.campaign}, sin activarla)")

    # ── 4. Monitoreo de cultivo ────────────────────────────────────────────
    def _crop_monitoring(self):
        from crop_monitoring.models.phenological_state import PhenologicalState, seed_phenological_stages
        from crop_monitoring.models.phenological_calibration import seed_phenological_calibrations
        from crop_monitoring.models.biofix import Biofix
        from crop_monitoring.models.gdd_accumulator import GDDAccumulator
        from crop_monitoring.models.phenological_observation import PhenologicalObservation

        before = PhenologicalState.objects.count()
        if before == 0:
            seed_phenological_stages()
        self._ok(f"Estados fenológicos BBCH: {PhenologicalState.objects.count()} "
                 f"({'cargados' if before == 0 else 'ya existían, no se modifican'})")

        n = seed_phenological_calibrations(self.specie, self.area_tandil)
        self._ok(f"Calibración Malbec / {self.area_tandil}: {n} nuevas")

        if self.specie.gdd_harvest_min is None and self.specie.gdd_harvest_max is None:
            self.specie.gdd_harvest_min, self.specie.gdd_harvest_max = 1450, 1700
            self.specie.save(update_fields=["gdd_harvest_min", "gdd_harvest_max"])
            self._ok("GDD de cosecha Malbec: 1450–1700 (cargado)")
        else:
            self._ok(f"GDD de cosecha Malbec: {self.specie.gdd_harvest_min}–{self.specie.gdd_harvest_max} (ya estaba)")

        biofix_date = self.today - timedelta(days=9)  # brotación reciente → riesgo de helada relevante
        self.biofix, created = Biofix.objects.get_or_create(
            crop=self.crop, counter=Biofix.COUNTER_VINE,
            defaults={"base_temp": 10.0, "date": biofix_date, "origin": Biofix.ORIGIN_MANUAL, "is_confirmed": True},
        )
        self.accumulator, _ = GDDAccumulator.objects.get_or_create(biofix=self.biofix)
        self._ok(f"{self._tag(created)}: biofix brotación {self.biofix.date} (base 10 °C) + acumulador GDD")

        sprouting = PhenologicalState.objects.order_by("order").first()
        _, created = PhenologicalObservation.objects.get_or_create(
            crop=self.crop, date=self.biofix.date,
            defaults={"observed_state": sprouting, "registered_by": self.staff,
                      "notes": "Brotación observada a campo (dato demo)."},
        )
        self._ok(f"{self._tag(created)}: observación fenológica {sprouting.bbch} — {sprouting.stage_name}")

    # ── 5. Indicadores ─────────────────────────────────────────────────────
    def _indicators(self):
        from alert.models.indicator import Indicator
        from alert.models.alert_profile import AlertProfile
        from alert.models.alert_profile_indicator import AlertProfileIndicator

        self.indicators = {}
        for slug, criticality, evaluator, max_fc in INDICATORS:
            ind, created = Indicator.objects.get_or_create(
                name=slug, defaults={"criticality_level": criticality, "evaluator": evaluator,
                                     "review_mode": "daily", "max_forecast_days": max_fc})
            self.indicators[slug] = ind
            self._ok(f"{self._tag(created)}: indicador {slug} ({evaluator.rsplit('.', 1)[-1]})")
            if created:
                getattr(self, f"_config_{slug}")(ind)

        for area, statuses in ((self.area_tandil, PROFILE_STATUS[AREA_TANDIL]),
                               (self.area_mendoza, PROFILE_STATUS[AREA_MENDOZA])):
            profile, created = AlertProfile.objects.get_or_create(area=area)
            for slug, status in statuses.items():
                AlertProfileIndicator.objects.get_or_create(
                    profile=profile, indicator=self.indicators[slug], defaults={"status": status})
            self._ok(f"{self._tag(created)}: perfil de zona {area} — " +
                     ", ".join(f"{s}={st}" for s, st in statuses.items()))

        self.crop.indicators.add(*self.indicators.values())
        self._ok(f"Indicadores asignados al cultivo {self.crop}")

        # La OT que crea una acción necesita etapa (stage es obligatorio en WorkOrder)
        from alert.models.indicator_action import IndicatorAction
        fixed = IndicatorAction.objects.filter(
            indicator__in=self.indicators.values(), stage__isnull=True).update(stage=self.stages["Brotación"])
        if fixed:
            self._ok(f"{fixed} acción(es) sin etapa → etapa Brotación")

    def _var(self, name):
        from parameter.models.var_crop_technique import VarCropTechnique
        var, _ = VarCropTechnique.objects.get_or_create(name=name, defaults={"type": self._climate_type()})
        return var

    def _recommendations(self, ind, recs):
        from alert.models.indicator_recommendation import IndicatorRecommendation
        for level, text in recs:
            IndicatorRecommendation.objects.create(indicator=ind, alert_level=level, text=text, order=0)

    def _action(self, ind, service_name, stage_name, forecast, days):
        from alert.models.indicator_action import IndicatorAction
        from operation.models.service import Service
        service = Service.objects.filter(name=service_name).first()
        if service:
            IndicatorAction.objects.create(indicator=ind, alert_level="", service=service,
                                           stage=self.stages[stage_name],
                                           create_on_forecast=forecast, days_to_complete=days)

    def _bands(self, ind, bands):
        from alert.models.indicator_band import IndicatorBand
        for bbch_from, bbch_to, level in bands:
            IndicatorBand.objects.create(indicator=ind, bbch_from=bbch_from, bbch_to=bbch_to,
                                         threshold=None, direction=None, level=level, order=1)

    def _config_helada(self, ind):
        # FrostEvaluator: umbrales por BBCH internos, no necesita variables ni bandas
        self._recommendations(ind, [("", "Riego de aspersión 25 mm/ha."),
                                    ("", "Activar helicóptero para mezcla del aire.")])
        self._action(ind, "Protección contra Heladas", "Brotación", forecast=True, days=3)

    def _config_granizo(self, ind):
        # StormHailEvaluator: caída de T y lluvia horaria internas; severidad por BBCH
        self._bands(ind, [(1, 53, "alert"), (54, 89, "critical")])

    def _config_mildiu_primario(self, ind):
        from alert.models.indicator_variable import IndicatorVariable
        for name, min_value in (("Temperatura media", 10.0), ("Lluvia (mm)", 10.0), ("Humedad relativa", 95.0)):
            IndicatorVariable.objects.create(indicator=ind, variable=self._var(name), role="filter",
                                             min_value=min_value)
        self._bands(ind, [(14, 59, "alert"), (60, 69, "critical"), (70, 79, "alert")])
        self._recommendations(ind, [
            ("warning", "Fungicida preventivo (cobre o fosfonatos) ANTES de la lluvia."),
            ("alert", "Si ya llovió: aplicar curativo en 48–72 h (cimoxanilo, dimethomorph)."),
            ("critical", "Programa preventivo intensivo: repetir cada 7–10 días durante el período lluvioso."),
        ])
        self._action(ind, "Tratamiento Fitosanitario", "Floración y Cuaje", forecast=False, days=3)

    def _config_ventana_aplicacion(self, ind):
        from alert.models.indicator_variable import IndicatorVariable
        for name, level, min_value in (
            ("Viento máximo", "warning", 15.0), ("Viento máximo", "alert", 20.0),
            ("Ráfaga máxima", "warning", 20.0), ("Ráfaga máxima", "alert", 25.0),
            ("Delta T mínimo", "warning", 2.0), ("Delta T máximo", "warning", 8.0),
            ("Delta T máximo", "alert", 10.0), ("Viento mínimo noche", "alert", 3.0),
        ):
            IndicatorVariable.objects.create(indicator=ind, variable=self._var(name), alert_level=level,
                                             role="filter", min_value=min_value)
        self._recommendations(ind, [
            ("warning", "Precaución: condiciones subóptimas. Revisar viento y Delta T antes de aplicar."),
            ("alert", "No aplicar: condiciones fuera de rango. Reprogramar la aplicación."),
        ])

    # ── 6. Órdenes de trabajo ──────────────────────────────────────────────
    def _stages(self):
        from operation.models.stage import Stage

        # El nombre de la etapa es único en todo el sistema: se reusan las existentes
        # y solo se crean (para Malbec) las que no existan.
        self.stages = {}
        for name, order in MALBEC_STAGES:
            self.stages[name], created = Stage.objects.get_or_create(
                name=name, defaults={"activity": self.variety, "order": order})
            self._ok(f"{self._tag(created)}: etapa {name}")

    def _work_orders(self):
        from operation.models.service import Service
        from operation.models.work_order import WorkOrder
        from parameter.models.ot_state import OTState

        stages = self.stages
        for code, service_name, stage_name, start, duration, state_name in WORK_ORDERS:
            service = self._get(Service, f"el servicio {service_name}", name=service_name)
            state = self._get(OTState, f"el estado {state_name}", name__iexact=state_name)
            date_init = self.today + timedelta(days=start)
            wo, created = WorkOrder.objects.get_or_create(
                code=code, producer=self.producer,
                defaults={"date_emission": date_init, "date_init": date_init,
                          "date_fin": date_init + timedelta(days=duration), "campaing": self.campaign,
                          "crop": self.crop, "area": self.area_tandil, "stage": stages[stage_name],
                          "service": service, "stateOT": state, "staff": self.staff, "type": "OW"},
            )
            self._ok(f"{self._tag(created)}: OT {code} {service_name} — {state.name} (inicio {date_init})")

    # ── 7. Clima ───────────────────────────────────────────────────────────
    def _fetch_weather(self):
        import openmeteo_requests
        import requests_cache
        from retry_requests import retry
        from weather.views.open_mateo import _fetch_station

        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        client = openmeteo_requests.Client(session=retry(cache_session, retries=5, backoff_factor=0.2))
        with contextlib.redirect_stdout(io.StringIO()):  # _fetch_station imprime la tabla completa
            created, updated = _fetch_station(client, self.station)
        self._ok(f"Datos horarios: {created} nuevos, {updated} actualizados")

    def _run_engine(self):
        """Mismos pasos que run_daily_cycle, pero solo para el lote nuevo."""
        from weather.models.daily_summary import DailySummary
        from alert.signals import evaluate_indicators_forecast

        DailySummary.consolidate_from_open_meteo(self.lot, self.today, self.station)
        gdd = self.accumulator.recalculate()
        days = sum(1 for d in range(1, 8)
                   if DailySummary.consolidate_from_open_meteo(self.lot, self.today + timedelta(days=d), self.station))
        evaluate_indicators_forecast(lot=self.lot, today=self.today)
        self._ok(f"GDD acumulado: {gdd} | días de pronóstico evaluados: {days}")

    # ── 8. Alertas de prueba ───────────────────────────────────────────────
    def _test_alerts(self):
        """
        Alertas de pronóstico artificiales. El motor las aborta cuando el pronóstico real no las
        confirma (_abort_stale_forecast); en ese caso se reactivan en vez de crear otra con el mismo
        nombre (Alert.name es único) y sin repetir notificaciones.
        """
        from alert.models.alert import Alert
        from alert.signals import _emit_alert, _get_bbch_stage_label, _get_bbch_for_crop
        from parameter.models.ot_state import OTState

        bbch_label = _get_bbch_stage_label(self.crop)
        bbch_code = _get_bbch_for_crop(self.crop)
        contingent = OTState.objects.filter(name="Contingente").first()
        for slug, days, level in TEST_ALERTS:
            date = self.today + timedelta(days=days)
            indicator = self.indicators[slug]
            alerts = Alert.objects.filter(crop=self.crop, indicator=indicator, date=date)
            if alerts.filter(is_aborted=False).exists():
                tag = "✓ existía"
            elif alerts.filter(is_aborted=True).exists():
                alert = alerts.filter(is_aborted=True).first()
                alert.is_aborted = False
                alert.save(update_fields=["is_aborted"])
                if contingent:
                    alert.work_orders.filter(stateOT__name="Cancelada por alerta").update(stateOT=contingent)
                tag = "↻ reactivada"
            else:
                _emit_alert(self.crop, indicator, date, level, bbch_label, status="on",
                            is_forecast=True, bbch_code=bbch_code)
                tag = "+ creada"
            self._ok(f"{tag}: alerta {slug} [{level}] para el {date} (pronóstico)")
