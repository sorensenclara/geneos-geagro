"""
Management command: seed_demo_data

Genera datos completos de demostración para el sistema vitivinícola:
  - Campaña 2025/2026 (anterior, cosechada) y 2026/2027 (actual, activa)
  - Tres cultivos por campaña: Malbec, Cabernet Sauvignon, Bonarda
  - Plan técnico Malbec/Mendoza con etapas e insumos reales
  - Órdenes de trabajo propias y contratadas, con insumos aplicados
  - DailySummary sintéticos para eventos climáticos clave de cada campaña
  - Alertas históricas confirmadas (2025/2026) + activas y pronóstico (2026/2027)

Requiere haber corrido antes:
    python manage.py seed_viticulture_operations
    python manage.py seed_test_data

Idempotente: se puede correr múltiples veces sin duplicar datos.

Correlo con:
    python manage.py seed_demo_data

Para complementar con alertas del ciclo diario (basadas en clima real):
    python manage.py run_daily_cycle
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Crea datos de demo: 2 campañas, 3 cultivos c/u, plan técnico, "
        "órdenes de trabajo con insumos y contratistas, alertas históricas y pronóstico."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self._step("Campañas 2025/2026 y 2026/2027")
        camp_prev, camp_curr = self._seed_campaigns()

        self._step("Tercer lote — Bonarda (Lote Este, 5 ha)")
        lot_este = self._seed_third_lot()

        self._step("Insumos fitosanitarios")
        inputs = self._seed_inputs()

        self._step("Plan técnico Malbec — Mendoza (10 ha referencia)")
        self._seed_technical_plan(inputs)

        self._step("Cultivos campaña anterior 2025/2026 (Cosechado)")
        crops_prev = self._seed_crops(camp_prev, lot_este, season="prev")

        self._step("Cultivos campaña actual 2026/2027 (Activo)")
        crops_curr = self._seed_crops(camp_curr, lot_este, season="curr")

        self._step("Biofix + GDD — campaña anterior 2025/2026")
        self._seed_gdd_prev(crops_prev)

        self._step("Biofix + GDD — campaña actual 2026/2027 (dormancia/poda)")
        self._seed_gdd_curr(crops_curr)

        self._step("Órdenes de trabajo — campaña anterior 2025/2026")
        self._seed_work_orders_prev(camp_prev, crops_prev, inputs)

        self._step("Órdenes de trabajo — campaña actual 2026/2027")
        self._seed_work_orders_curr(camp_curr, crops_curr, inputs)

        self._step("DailySummary sintéticos — eventos climáticos clave")
        self._seed_daily_summaries()

        self._step("Alertas — campaña anterior (históricas, confirmadas)")
        self._seed_alerts_prev(crops_prev)

        self._step("Alertas — campaña actual (activas + pronóstico temporada)")
        self._seed_alerts_curr(crops_curr)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("✓ seed_demo_data completado."))
        self.stdout.write(
            "  Para agregar alertas del día de hoy basadas en clima real:\n"
            "    python manage.py run_daily_cycle\n"
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _step(self, msg):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n→ {msg}"))

    def _ok(self, msg):
        self.stdout.write(f"   {msg}")

    def _get_deps(self):
        """Objetos comunes reutilizados en múltiples métodos."""
        from user.models.user_producer import UserProducer
        from parameter.models.area import Area
        from producer.models.staff import Staff
        from producer.models.country_side import Countryside

        return {
            "producer":    UserProducer.objects.get(id=2),
            "area_mza":    Area.objects.get(name="Mendoza"),
            "staff":       Staff.objects.filter(cuit="20301234567").first(),
            "countryside": Countryside.objects.filter(name="Finca San Carlos").first(),
        }

    # ── 1. Campañas ──────────────────────────────────────────────────────────

    def _seed_campaigns(self):
        from parameter.models.campaign import Campaing

        camp_prev, _ = Campaing.objects.update_or_create(
            name="Campaña 2025/2026",
            defaults={
                "date_init":  date(2025, 8, 1),
                "date_final": date(2026, 7, 31),
                "active":     False,
            },
        )
        self._ok(f"Campaña anterior: {camp_prev.name}  (active=False, id={camp_prev.id})")

        camp_curr, _ = Campaing.objects.update_or_create(
            name="Campaña 2026/2027",
            defaults={
                "date_init":  date(2026, 8, 1),
                "date_final": date(2027, 7, 31),
                "active":     True,
            },
        )
        self._ok(f"Campaña actual:    {camp_curr.name}  (active=True,  id={camp_curr.id})")

        # Desactivar cualquier otra campaña activa (seguridad)
        deact = Campaing.objects.exclude(pk__in=[camp_prev.pk, camp_curr.pk]).filter(active=True)
        if deact.exists():
            names = list(deact.values_list("name", flat=True))
            deact.update(active=False)
            self._ok(f"Desactivadas: {names}")

        return camp_prev, camp_curr

    # ── 2. Tercer lote ───────────────────────────────────────────────────────

    def _seed_third_lot(self):
        from producer.models.lot import Lot
        from parameter.models.lot_rating import LotRating
        from producer.models.cost_center import CostCenter
        from operation.models.variety import Variety as Activity

        deps = self._get_deps()
        countryside = deps["countryside"]
        if not countryside:
            self._ok("[!] Countryside 'Finca San Carlos' no encontrado — corriendo seed_test_data primero")
            return None

        rating_a = LotRating.objects.filter(name="A").first()
        cc_vid   = CostCenter.objects.filter(name="Viñedo Mendoza").first()

        lot_este, created = Lot.objects.get_or_create(
            name="Lote Este — Bonarda",
            defaults={
                "countryside":         countryside,
                "area":                deps["area_mza"],
                "responsible":         deps["staff"],
                "hectares":            5.0,
                "hectares_productive": 4.5,
                "cost_center":         cc_vid,
                "LotRating":           rating_a,
            },
        )
        self._ok(f"{'Creado' if created else 'Existente'}: Lote Este — Bonarda  (5 ha, id={lot_este.id})")

        act_bonarda = Activity.objects.filter(name="Bonarda").first()
        if act_bonarda:
            lot_este.activity.add(act_bonarda)

        return lot_este

    # ── 3. Insumos ───────────────────────────────────────────────────────────

    def _seed_inputs(self):
        from input.models.type_input import TypeInput
        from input.models.input import Input
        from parameter.models.measure_unit import MaensureUnit
        from parameter.models.currency import Currency

        deps = self._get_deps()
        ars  = Currency.objects.get_or_create(name="ARS")[0]
        kg   = MaensureUnit.objects.get_or_create(name="kg")[0]
        lt   = MaensureUnit.objects.get_or_create(name="l")[0]

        t_fungi, _ = TypeInput.objects.get_or_create(name="Fungicida")
        t_insec, _ = TypeInput.objects.get_or_create(name="Insecticida")
        t_coad,  _ = TypeInput.objects.get_or_create(name="Coadyuvante")
        t_fert,  _ = TypeInput.objects.get_or_create(name="Fertilizante")

        # (nombre, tipo, unidad, presentación, costo_unit, stock_inicial)
        INPUTS_DATA = [
            ("Azufre mojable 80% WP",             t_fungi, kg, "Bolsa 25 kg",   850,  50),
            ("Mancozeb 80% WP",                   t_fungi, kg, "Bolsa 10 kg",  1200,  30),
            ("Fosetil-Al 80% WP",                 t_fungi, kg, "Bolsa 10 kg",  1850,  20),
            ("Ciproconazol 10% SC",               t_fungi, lt, "Bidón 1 L",   18000,  10),
            ("Boscalid + Piraclostrobin 38% WG",  t_fungi, kg, "Bolsa 5 kg",  12000,   5),
            ("Clorpirifós 48% CE",                t_insec, lt, "Bidón 5 L",    4500,  15),
            ("Acetamiprid 20% SP",                t_insec, kg, "Sobre 100 g",  9500,   5),
            ("Citowett (coadyuvante mojante)",     t_coad,  lt, "Bidón 1 L",    3200,  10),
            ("Fosfato monoamónico foliar",         t_fert,  kg, "Bolsa 25 kg",  2200,  20),
        ]

        result = {}
        for name, tipo, unit, pres, cost, stock in INPUTS_DATA:
            obj, created = Input.objects.update_or_create(
                name=name,
                defaults={
                    "type":          tipo,
                    "unit_measure":  unit,
                    "presentation":  pres,
                    "cost":          float(cost),
                    "currency":      ars,
                    "control_stock": True,
                    "stock":         float(stock),
                    "min_stock":     5.0,
                    "producer":      deps["producer"],
                },
            )
            result[name] = obj
            self._ok(f"  {'[+]' if created else '[=]'} {name}")

        return result

    # ── 4. Plan técnico ──────────────────────────────────────────────────────

    def _seed_technical_plan(self, inputs):
        from operation.models.technical_plan import TechnicalPlan
        from operation.models.technical_plan_detail import TechnicalPlanDetail
        from operation.models.technical_plan_input import TechnicalPlanInput
        from operation.models.stage import Stage
        from operation.models.service import Service
        from operation.models.variety import Variety as Activity

        deps       = self._get_deps()
        act_malbec = Activity.objects.filter(name="Malbec").first()
        if not act_malbec:
            self._ok("[!] Actividad Malbec no encontrada — correr seed_viticulture_operations")
            return None

        plan, _ = TechnicalPlan.objects.update_or_create(
            code="PT-MBL-MZA-10HA",
            defaults={
                "detail":   (
                    "Plan técnico Malbec Mendoza — referencia 10 ha. Incluye labores culturales, "
                    "tratamientos fitosanitarios (oídio, mildiu, botrytis, lobesia) y cosecha. "
                    "Adaptado al clima árido de Luján de Cuyo (BWk). Base: GDD 10 °C, biofix = brotación."
                ),
                "hectares": 10,
                "activity": act_malbec,
                "area":     deps["area_mza"],
                "active":   True,
                "producer": deps["producer"],
            },
        )
        self._ok(f"TechnicalPlan: {plan.code}")

        stage_cache = {s.name: s for s in Stage.objects.all()}
        svc_cache   = {s.name: s for s in Service.objects.all()}

        # (seq, etapa, servicio, días, personas, subcontratado, [(insumo, dosis_ha, nota)])
        DETAILS = [
            (1,  "Poda",              "Podar",                                  5, 8,  False, []),
            (2,  "Poda",              "Atado de sarmientos",                    3, 6,  False, []),
            (3,  "Brotación",         "Monitoreo fenológico (BBCH)",            1, 2,  False, []),
            (4,  "Desarrollo foliar", "Deshoje manual",                         4, 6,  False, []),
            (5,  "Desarrollo foliar", "Despunte de brotes",                     2, 4,  False, []),
            (6,  "Desarrollo foliar", "Aplicación fungicida — Oídio",           1, 2,  True,  [
                ("Azufre mojable 80% WP",           3.0,  "3 kg/ha — cubriente preventivo"),
                ("Ciproconazol 10% SC",             0.1,  "100 mL/ha — sistémico penetrante"),
                ("Citowett (coadyuvante mojante)",   0.1,  "100 mL/100 L"),
            ]),
            (7,  "Floración y Cuaje", "Monitoreo de trampas Lobesia botrana",   1, 1,  True,  []),
            (8,  "Floración y Cuaje", "Aclareo de racimos",                     3, 8,  False, []),
            (9,  "Floración y Cuaje", "Aplicación fungicida — Mildiu",          1, 2,  True,  [
                ("Mancozeb 80% WP",                 2.5,  "2.5 kg/ha — cubriente"),
                ("Fosetil-Al 80% WP",               2.0,  "2 kg/ha — sistémico"),
                ("Citowett (coadyuvante mojante)",   0.1,  "100 mL/100 L"),
            ]),
            (10, "Floración y Cuaje", "Aplicación insecticida — Lobesia botrana",1, 2, True,  [
                ("Clorpirifós 48% CE",              1.0,  "1 L/ha — 1ª generación"),
                ("Citowett (coadyuvante mojante)",   0.1,  "100 mL/100 L"),
            ]),
            (11, "Envero",            "Control de madurez — Brix y acidez",     2, 2,  False, []),
            (12, "Maduración",        "Aplicación fungicida — Botrytis",        1, 2,  True,  [
                ("Boscalid + Piraclostrobin 38% WG",0.3,  "300 g/ha — pre-cierre racimo"),
                ("Citowett (coadyuvante mojante)",   0.1,  "100 mL/100 L"),
            ]),
            (13, "Cosecha",           "Cosecha manual",                          3, 20, True,  []),
            (14, "Cosecha",           "Control de calidad de cosecha",           1, 2,  False, []),
        ]

        for seq, stage_name, svc_name, days, persons, subct, inp_list in DETAILS:
            stage = stage_cache.get(stage_name)
            svc   = svc_cache.get(svc_name)
            if not stage or not svc:
                self._ok(f"  [!] Stage='{stage_name}' o Service='{svc_name}' no encontrado — seq {seq} omitido")
                continue

            detail, _ = TechnicalPlanDetail.objects.update_or_create(
                technical_plan=plan,
                secuence=seq,
                defaults={
                    "stage":         stage,
                    "service":       svc,
                    "days_estimate": days,
                    "cant_persons":  persons,
                    "active":        True,
                    "subcontracted": subct,
                },
            )

            for inp_name, dose, nota in inp_list:
                inp = inputs.get(inp_name)
                if inp:
                    TechnicalPlanInput.objects.update_or_create(
                        technical_plan=plan,
                        technical_plan_detail=detail,
                        input=inp,
                        defaults={"dose": dose, "detail": nota},
                    )

            self._ok(f"  [{seq:2d}] {stage_name:20s} — {svc_name}")

        return plan

    # ── 5. Cultivos (campaña anterior y actual) ───────────────────────────────

    def _seed_crops(self, campaign, lot_este, season="curr"):
        from parameter.models.cultivation_state import CiltivationState
        from producer.models.lot import Lot
        from operation.models.variety import Variety as Activity
        from operation.models.crop import Crop

        deps = self._get_deps()
        lot_norte   = Lot.objects.filter(name="Lote Norte — Malbec").first()
        lot_sur     = Lot.objects.filter(name="Lote Sur — Cabernet").first()
        act_malbec  = Activity.objects.filter(name="Malbec").first()
        act_cab     = Activity.objects.filter(name="Cabernet Sauvignon").first()
        act_bonarda = Activity.objects.filter(name="Bonarda").first()

        yr = "2025/26" if season == "prev" else "2026/27"
        state_name  = "Cosechado" if season == "prev" else "Activo"
        state       = CiltivationState.objects.get(name=state_name)

        ha_harvest_m = 10.0 if season == "prev" else 0.0
        ha_harvest_c = 7.5  if season == "prev" else 0.0
        ha_harvest_b = 4.5  if season == "prev" else 0.0

        CROPS = [
            # (nombre,                               lot,       activity,    ha_prod, ha_plant, ha_harv,     is_main)
            (f"Malbec {yr} — Lote Norte",       lot_norte,  act_malbec,   10.0,    10.0,    ha_harvest_m, True),
            (f"Cabernet Sauv. {yr} — Lote Sur", lot_sur,    act_cab,       7.5,     7.5,    ha_harvest_c, False),
            (f"Bonarda {yr} — Lote Este",        lot_este,   act_bonarda,   4.5,     4.5,    ha_harvest_b, False),
        ]

        result = {}
        for name, lot, activity, ha_prod, ha_plant, ha_harv, is_main in CROPS:
            if lot is None or activity is None:
                self._ok(f"  [!] Lote o actividad faltante para '{name}' — omitido")
                continue

            crop, created = Crop.objects.get_or_create(
                name=name,
                defaults={
                    "campaing":              campaign,
                    "countryside":           deps["countryside"],
                    "area":                  deps["area_mza"],
                    "lot":                   lot,
                    "activity":              activity,
                    "responsible":           deps["staff"],
                    "state":                 state,
                    "hectares_productive":   ha_prod,
                    "hectares_planted":      ha_plant,
                    "hectares_unplanted":    0.0,
                    "hectares_harvested":    ha_harv,
                    "hectares_not_harvested":ha_prod - ha_harv,
                    "impute_bills":          True,
                    "producer":              deps["producer"],
                    "is_main":               is_main,
                },
            )
            if not created and crop.campaing_id != campaign.pk:
                crop.campaing = campaign
                crop.save(update_fields=["campaing"])

            key = name.split(" — ")[0].split(f" {yr}")[0].lower().replace(" ", "_").rstrip(".")
            result[key] = crop
            self._ok(f"  {'[+]' if created else '[=]'} {name}  (id={crop.id})")

        return result  # keys: 'malbec', 'cabernet_sauv', 'bonarda'

    # ── 6. GDD campaña anterior ──────────────────────────────────────────────

    def _seed_gdd_prev(self, crops_prev):
        from crop_monitoring.models.biofix import Biofix
        from crop_monitoring.models.gdd_accumulator import GDDAccumulator

        # Brotación ~1 sep 2025 → cosecha ~mar-abr 2026 → GDD final por variedad
        PREV = [
            # (crop_key, biofix_date, gdd_final, fecha_calculo)
            ("malbec",      date(2025, 9, 2), 1610.0, date(2026, 3, 22)),  # cosecha 22 mar
            ("cabernet_sauv", date(2025, 9, 5), 1575.0, date(2026, 3, 30)),  # cosecha 30 mar
            ("bonarda",     date(2025, 9, 1), 1680.0, date(2026, 4,  5)),  # cosecha 5 abr (ciclo largo)
        ]

        for key, biofix_date, gdd, fecha_calc in PREV:
            crop = crops_prev.get(key)
            if not crop:
                continue
            bf, created = Biofix.objects.get_or_create(
                crop=crop, counter=Biofix.COUNTER_VINE,
                defaults={
                    "base_temp": 10.0, "date": biofix_date,
                    "origin": Biofix.ORIGIN_MANUAL, "is_confirmed": True,
                },
            )
            if not created:
                bf.date = biofix_date
                bf.is_confirmed = True
                bf.save(update_fields=["date", "is_confirmed"])
            acc, _ = GDDAccumulator.objects.get_or_create(biofix=bf)
            acc.accumulated_gdd  = gdd
            acc.calculation_date = fecha_calc
            acc.save()
            self._ok(f"  {key:15s} biofix={biofix_date}  GDD={gdd}  (cosecha {fecha_calc})")

    # ── 7. GDD campaña actual ────────────────────────────────────────────────

    def _seed_gdd_curr(self, crops_curr):
        from crop_monitoring.models.biofix import Biofix
        from crop_monitoring.models.gdd_accumulator import GDDAccumulator

        # Agosto 2026 = dormancia / poda. Brotación esperada ~1 sep 2026 (fallback).
        CURR = [
            ("malbec",      date(2026, 9,  1)),
            ("cabernet_sauv", date(2026, 9,  3)),
            ("bonarda",     date(2026, 8, 30)),
        ]
        today = date.today()
        for key, biofix_date in CURR:
            crop = crops_curr.get(key)
            if not crop:
                continue
            bf, _ = Biofix.objects.get_or_create(
                crop=crop, counter=Biofix.COUNTER_VINE,
                defaults={
                    "base_temp": 10.0, "date": biofix_date,
                    "origin": Biofix.ORIGIN_FALLBACK, "is_confirmed": False,
                },
            )
            acc, _ = GDDAccumulator.objects.get_or_create(biofix=bf)
            if acc.accumulated_gdd == 0 or acc.calculation_date is None:
                acc.accumulated_gdd  = 0.0
                acc.calculation_date = today
                acc.save()
            self._ok(f"  {key:15s} biofix estimado={biofix_date}  GDD=0  (dormancia)")

    # ── 8. Work orders campaña anterior ──────────────────────────────────────

    def _seed_work_orders_prev(self, campaign, crops_prev, inputs):
        from operation.models.work_order import WorkOrder
        from operation.models.input_work_order import InputWorkOrder
        from operation.models.stage import Stage
        from operation.models.service import Service
        from parameter.models.ot_state import OTState

        deps      = self._get_deps()
        st_cache  = {s.name: s for s in Stage.objects.all()}
        svc_cache = {s.name: s for s in Service.objects.all()}
        ot_final  = OTState.objects.get(name="Finalizada")
        ot_cont   = OTState.objects.get(name="Contingente")

        def wo(code, crop, stage_n, svc_n, d_emis, d_init, d_fin, estado, tipo="OW",
               insumos=None):
            stage = st_cache.get(stage_n)
            svc   = svc_cache.get(svc_n)
            if not stage or not svc or not crop:
                return None
            obj, created = WorkOrder.objects.update_or_create(
                code=code, crop=crop,
                defaults={
                    "date_emission": d_emis, "date_init": d_init, "date_fin": d_fin,
                    "campaing": campaign, "area": deps["area_mza"],
                    "stage": stage, "service": svc, "stateOT": estado,
                    "type": tipo, "staff": deps["staff"],
                    "contractor": deps["producer"] if tipo == "TPW" else None,
                    "producer": deps["producer"],
                },
            )
            if insumos and created:
                for inp_name, dose, dose_ap, nota in insumos:
                    inp_obj = inputs.get(inp_name)
                    if inp_obj:
                        InputWorkOrder.objects.get_or_create(
                            work_order=obj, input=inp_obj,
                            defaults={"dose": dose, "dose_applied": dose_ap, "details": nota},
                        )
            return obj

        crop_m = crops_prev.get("malbec")
        crop_c = crops_prev.get("cabernet_sauv")
        crop_b = crops_prev.get("bonarda")

        # ────────────── MALBEC 2025/26 ──────────────────────────────────────
        wo("OT-25/26-M-01", crop_m, "Poda", "Podar",
           date(2025, 7,10), date(2025, 7,15), date(2025, 7,25), ot_final)
        wo("OT-25/26-M-02", crop_m, "Poda", "Atado de sarmientos",
           date(2025, 8, 5), date(2025, 8, 8), date(2025, 8,15), ot_final)
        wo("OT-25/26-M-03", crop_m, "Brotación", "Monitoreo fenológico (BBCH)",
           date(2025, 9, 1), date(2025, 9, 5), date(2025, 9, 7), ot_final)
        wo("OT-25/26-M-04", crop_m, "Brotación", "Activación de calefactores (helada)",
           date(2025,10, 9), date(2025,10,10), date(2025,10,10), ot_final)  # helada 10-oct
        wo("OT-25/26-M-05", crop_m, "Desarrollo foliar", "Deshoje manual",
           date(2025,10, 5), date(2025,10,10), date(2025,10,16), ot_final)
        wo("OT-25/26-M-06", crop_m, "Desarrollo foliar", "Aplicación fungicida — Oídio",
           date(2025,10,18), date(2025,10,22), date(2025,10,22), ot_final, tipo="TPW",
           insumos=[
               ("Azufre mojable 80% WP",           30.0, 30.0, "10 ha × 3 kg/ha — preventivo"),
               ("Ciproconazol 10% SC",              1.0,  1.0,  "10 ha × 100 mL/ha — sistémico"),
               ("Citowett (coadyuvante mojante)",    1.0,  1.0,  "mojante"),
           ])
        wo("OT-25/26-M-07", crop_m, "Floración y Cuaje", "Monitoreo de trampas Lobesia botrana",
           date(2025,11, 1), date(2025,11, 5), date(2025,11, 6), ot_final, tipo="TPW")
        wo("OT-25/26-M-08", crop_m, "Floración y Cuaje", "Aclareo de racimos",
           date(2025,12, 1), date(2025,12, 5), date(2025,12,12), ot_final)
        wo("OT-25/26-M-09", crop_m, "Floración y Cuaje", "Aplicación fungicida — Mildiu",
           date(2025,11,18), date(2025,11,20), date(2025,11,20), ot_final, tipo="TPW",
           insumos=[
               ("Mancozeb 80% WP",                 25.0, 25.0, "10 ha × 2.5 kg/ha"),
               ("Fosetil-Al 80% WP",               20.0, 20.0, "10 ha × 2 kg/ha"),
               ("Citowett (coadyuvante mojante)",    1.0,  1.0,  "mojante"),
           ])
        wo("OT-25/26-M-10", crop_m, "Floración y Cuaje", "Aplicación insecticida — Lobesia botrana",
           date(2025,12, 8), date(2025,12,10), date(2025,12,10), ot_final, tipo="TPW",
           insumos=[
               ("Clorpirifós 48% CE",              10.0, 10.0, "10 ha × 1 L/ha — 1ª generación"),
               ("Citowett (coadyuvante mojante)",    1.0,  1.0,  "mojante"),
           ])
        wo("OT-25/26-M-11", crop_m, "Floración y Cuaje", "Riego foliar de emergencia (golpe de calor)",
           date(2026, 1,19), date(2026, 1,20), date(2026, 1,20), ot_final)  # golpe calor
        wo("OT-25/26-M-12", crop_m, "Envero", "Control de madurez — Brix y acidez",
           date(2026, 2, 1), date(2026, 2, 5), date(2026, 2,10), ot_final)
        wo("OT-25/26-M-13", crop_m, "Cosecha", "Cosecha manual",
           date(2026, 3,15), date(2026, 3,20), date(2026, 3,23), ot_final, tipo="TPW")
        wo("OT-25/26-M-14", crop_m, "Cosecha", "Control de calidad de cosecha",
           date(2026, 3,18), date(2026, 3,20), date(2026, 3,23), ot_final)
        self._ok("  Malbec 2025/26:       14 OTs (3 TPW con contratista, 3 con insumos)")

        # ────────────── CABERNET SAUV. 2025/26 ─────────────────────────────
        wo("OT-25/26-C-01", crop_c, "Poda", "Podar",
           date(2025, 7,12), date(2025, 7,18), date(2025, 7,28), ot_final)
        wo("OT-25/26-C-02", crop_c, "Poda", "Atado de sarmientos",
           date(2025, 8, 8), date(2025, 8,12), date(2025, 8,18), ot_final)
        wo("OT-25/26-C-03", crop_c, "Brotación", "Riego de cobertura anti-helada",
           date(2025, 9,27), date(2025, 9,28), date(2025, 9,28), ot_final)  # helada 28-sep
        wo("OT-25/26-C-04", crop_c, "Desarrollo foliar", "Aplicación fungicida — Oídio",
           date(2025,10,22), date(2025,10,25), date(2025,10,25), ot_final, tipo="TPW",
           insumos=[
               ("Azufre mojable 80% WP",           22.5, 22.5, "7.5 ha × 3 kg/ha"),
               ("Ciproconazol 10% SC",              0.75, 0.75, "7.5 ha × 100 mL/ha"),
               ("Citowett (coadyuvante mojante)",    0.75, 0.75, "mojante"),
           ])
        wo("OT-25/26-C-05", crop_c, "Floración y Cuaje", "Monitoreo de trampas Lobesia botrana",
           date(2025,11, 5), date(2025,11, 8), date(2025,11, 9), ot_final, tipo="TPW")
        wo("OT-25/26-C-06", crop_c, "Floración y Cuaje", "Aplicación insecticida — Lobesia botrana",
           date(2025,12, 8), date(2025,12,10), date(2025,12,10), ot_final, tipo="TPW",
           insumos=[
               ("Clorpirifós 48% CE",               7.5,  7.5, "7.5 ha × 1 L/ha"),
               ("Citowett (coadyuvante mojante)",    0.75, 0.75, "mojante"),
           ])
        wo("OT-25/26-C-07", crop_c, "Envero", "Control de madurez — Brix y acidez",
           date(2026, 2, 5), date(2026, 2, 8), date(2026, 2,14), ot_final)
        wo("OT-25/26-C-08", crop_c, "Cosecha", "Cosecha manual",
           date(2026, 3,25), date(2026, 3,28), date(2026, 4, 1), ot_final, tipo="TPW")
        self._ok("  Cabernet 2025/26:      8 OTs (2 TPW con contratista, 2 con insumos)")

        # ────────────── BONARDA 2025/26 ─────────────────────────────────────
        wo("OT-25/26-B-01", crop_b, "Poda", "Podar",
           date(2025, 7,20), date(2025, 7,22), date(2025, 7,30), ot_final)
        wo("OT-25/26-B-02", crop_b, "Desarrollo foliar", "Aplicación fungicida — Oídio",
           date(2025,10,28), date(2025,10,30), date(2025,10,30), ot_final, tipo="TPW",
           insumos=[
               ("Azufre mojable 80% WP",           13.5, 13.5, "4.5 ha × 3 kg/ha"),
               ("Ciproconazol 10% SC",              0.45, 0.45, "4.5 ha × 100 mL/ha"),
           ])
        wo("OT-25/26-B-03", crop_b, "Floración y Cuaje", "Aplicación fungicida — Mildiu",
           date(2025,11,22), date(2025,11,24), date(2025,11,24), ot_final, tipo="TPW",
           insumos=[
               ("Mancozeb 80% WP",                11.25,11.25, "4.5 ha × 2.5 kg/ha"),
               ("Fosetil-Al 80% WP",               9.0,  9.0, "4.5 ha × 2 kg/ha"),
           ])
        wo("OT-25/26-B-04", crop_b, "Maduración", "Aplicación fungicida — Botrytis",
           date(2026, 2, 8), date(2026, 2,10), date(2026, 2,10), ot_final, tipo="TPW",
           insumos=[
               ("Boscalid + Piraclostrobin 38% WG", 1.35, 1.35, "4.5 ha × 300 g/ha — pre-cosecha"),
               ("Citowett (coadyuvante mojante)",    0.45, 0.45, "mojante"),
           ])
        wo("OT-25/26-B-05", crop_b, "Cosecha", "Cosecha manual",
           date(2026, 4, 2), date(2026, 4, 5), date(2026, 4, 8), ot_final, tipo="TPW")
        self._ok("  Bonarda 2025/26:       5 OTs (3 TPW con contratista, 3 con insumos)")

    # ── 9. Work orders campaña actual ────────────────────────────────────────

    def _seed_work_orders_curr(self, campaign, crops_curr, inputs):
        from operation.models.work_order import WorkOrder
        from operation.models.input_work_order import InputWorkOrder
        from operation.models.stage import Stage
        from operation.models.service import Service
        from parameter.models.ot_state import OTState

        deps      = self._get_deps()
        st_cache  = {s.name: s for s in Stage.objects.all()}
        svc_cache = {s.name: s for s in Service.objects.all()}
        ot_pend   = OTState.objects.get(name="Pendiente")
        ot_curso  = OTState.objects.get(name="En curso")
        ot_cont   = OTState.objects.get(name="Contingente")

        def wo(code, crop, stage_n, svc_n, d_emis, d_init, d_fin, estado, tipo="OW",
               insumos=None):
            stage = st_cache.get(stage_n)
            svc   = svc_cache.get(svc_n)
            if not stage or not svc or not crop:
                return None
            obj, created = WorkOrder.objects.update_or_create(
                code=code, crop=crop,
                defaults={
                    "date_emission": d_emis, "date_init": d_init, "date_fin": d_fin,
                    "campaing": campaign, "area": deps["area_mza"],
                    "stage": stage, "service": svc, "stateOT": estado,
                    "type": tipo, "staff": deps["staff"],
                    "contractor": deps["producer"] if tipo == "TPW" else None,
                    "producer": deps["producer"],
                },
            )
            if insumos and created:
                for inp_name, dose, nota in insumos:
                    inp_obj = inputs.get(inp_name)
                    if inp_obj:
                        InputWorkOrder.objects.get_or_create(
                            work_order=obj, input=inp_obj,
                            defaults={"dose": dose, "dose_applied": None, "details": nota},
                        )
            return obj

        crop_m = crops_curr.get("malbec")
        crop_c = crops_curr.get("cabernet_sauv")
        crop_b = crops_curr.get("bonarda")

        # ────────────── MALBEC 2026/27 ──────────────────────────────────────
        wo("OT-26/27-M-01", crop_m, "Poda", "Podar",
           date(2026, 7,15), date(2026, 7,20), date(2026, 8,5), ot_curso)   # poda en curso
        wo("OT-26/27-M-02", crop_m, "Poda", "Atado de sarmientos",
           date(2026, 8,10), date(2026, 8,20), date(2026, 8,30), ot_pend)
        wo("OT-26/27-M-03", crop_m, "Poda", "Reparación de espalderos",
           date(2026, 8,15), date(2026, 8,25), date(2026, 9, 5), ot_pend)
        wo("OT-26/27-M-04", crop_m, "Brotación", "Monitoreo fenológico (BBCH)",
           date(2026, 9, 1), date(2026, 9, 5), date(2026, 9, 8), ot_pend)
        wo("OT-26/27-M-05", crop_m, "Brotación", "Vigilancia meteorológica",
           date(2026, 9, 1), date(2026, 9, 5), date(2026,10,31), ot_pend)   # vigilancia heladas
        wo("OT-26/27-M-06", crop_m, "Brotación", "Activación de calefactores (helada)",
           date(2026, 9,20), date(2026, 9,25), date(2026, 9,25), ot_cont)   # contingente pronóstico
        wo("OT-26/27-M-07", crop_m, "Desarrollo foliar", "Deshoje manual",
           date(2026,10,10), date(2026,10,15), date(2026,10,22), ot_pend)
        wo("OT-26/27-M-08", crop_m, "Desarrollo foliar", "Aplicación fungicida — Oídio",
           date(2026,10,10), date(2026,10,15), date(2026,10,15), ot_pend, tipo="TPW",
           insumos=[
               ("Azufre mojable 80% WP",            30.0, "10 ha × 3 kg/ha — preventivo"),
               ("Ciproconazol 10% SC",               1.0,  "10 ha × 100 mL/ha"),
               ("Citowett (coadyuvante mojante)",     1.0,  "mojante"),
           ])
        wo("OT-26/27-M-09", crop_m, "Floración y Cuaje", "Aclareo de racimos",
           date(2026,12, 1), date(2026,12, 5), date(2026,12,12), ot_pend)
        wo("OT-26/27-M-10", crop_m, "Floración y Cuaje", "Aplicación fungicida — Mildiu",
           date(2026,11,18), date(2026,11,20), date(2026,11,20), ot_pend, tipo="TPW",
           insumos=[
               ("Mancozeb 80% WP",                  25.0, "10 ha × 2.5 kg/ha"),
               ("Fosetil-Al 80% WP",                20.0, "10 ha × 2 kg/ha"),
               ("Citowett (coadyuvante mojante)",     1.0,  "mojante"),
           ])
        wo("OT-26/27-M-11", crop_m, "Envero", "Control de madurez — Brix y acidez",
           date(2027, 1,15), date(2027, 1,20), date(2027, 1,25), ot_pend)
        wo("OT-26/27-M-12", crop_m, "Cosecha", "Estimación de cosecha (GDD)",
           date(2027, 2, 1), date(2027, 2,15), date(2027, 2,20), ot_pend)
        wo("OT-26/27-M-13", crop_m, "Cosecha", "Cosecha manual",
           date(2027, 3,15), date(2027, 3,20), date(2027, 3,25), ot_pend, tipo="TPW")
        self._ok("  Malbec 2026/27:      13 OTs (2 en curso/contingente, 3 TPW, 2 con insumos)")

        # ────────────── CABERNET SAUV. 2026/27 ─────────────────────────────
        wo("OT-26/27-C-01", crop_c, "Poda", "Podar",
           date(2026, 7,18), date(2026, 7,22), date(2026, 8, 8), ot_curso)
        wo("OT-26/27-C-02", crop_c, "Poda", "Reparación de sistema de riego",
           date(2026, 8,12), date(2026, 8,18), date(2026, 8,25), ot_pend)
        wo("OT-26/27-C-03", crop_c, "Brotación", "Monitoreo fenológico (BBCH)",
           date(2026, 9, 5), date(2026, 9, 8), date(2026, 9,10), ot_pend)
        wo("OT-26/27-C-04", crop_c, "Brotación", "Riego de cobertura anti-helada",
           date(2026, 9,22), date(2026, 9,28), date(2026, 9,28), ot_cont)   # contingente helada
        wo("OT-26/27-C-05", crop_c, "Desarrollo foliar", "Deshoje manual",
           date(2026,10,15), date(2026,10,20), date(2026,10,26), ot_pend)
        wo("OT-26/27-C-06", crop_c, "Desarrollo foliar", "Aplicación fungicida — Oídio",
           date(2026,10,22), date(2026,10,25), date(2026,10,25), ot_pend, tipo="TPW",
           insumos=[
               ("Azufre mojable 80% WP",            22.5, "7.5 ha × 3 kg/ha"),
               ("Ciproconazol 10% SC",               0.75, "7.5 ha × 100 mL/ha"),
           ])
        wo("OT-26/27-C-07", crop_c, "Floración y Cuaje", "Monitoreo de trampas Lobesia botrana",
           date(2026,11, 1), date(2026,11, 5), date(2026,11, 6), ot_pend, tipo="TPW")
        wo("OT-26/27-C-08", crop_c, "Cosecha", "Cosecha manual",
           date(2027, 4, 1), date(2027, 4, 5), date(2027, 4,10), ot_pend, tipo="TPW")
        self._ok("  Cabernet 2026/27:     8 OTs (1 en curso, 2 contingentes, 2 TPW)")

        # ────────────── BONARDA 2026/27 ─────────────────────────────────────
        wo("OT-26/27-B-01", crop_b, "Poda", "Podar",
           date(2026, 7,20), date(2026, 7,25), date(2026, 8, 5), ot_curso)
        wo("OT-26/27-B-02", crop_b, "Brotación", "Monitoreo fenológico (BBCH)",
           date(2026, 9, 5), date(2026, 9, 8), date(2026, 9,10), ot_pend)
        wo("OT-26/27-B-03", crop_b, "Desarrollo foliar", "Aplicación fungicida — Oídio",
           date(2026,10,18), date(2026,10,20), date(2026,10,20), ot_pend, tipo="TPW",
           insumos=[
               ("Azufre mojable 80% WP",            13.5, "4.5 ha × 3 kg/ha"),
               ("Ciproconazol 10% SC",               0.45, "4.5 ha × 100 mL/ha"),
           ])
        wo("OT-26/27-B-04", crop_b, "Floración y Cuaje", "Aclareo de racimos",
           date(2026,12, 5), date(2026,12, 8), date(2026,12,12), ot_pend)
        wo("OT-26/27-B-05", crop_b, "Cosecha", "Cosecha manual",
           date(2027, 3,25), date(2027, 3,28), date(2027, 4, 2), ot_pend, tipo="TPW")
        self._ok("  Bonarda 2026/27:      5 OTs (1 en curso, 1 TPW con insumos)")

    # ── 10. DailySummary ─────────────────────────────────────────────────────

    def _seed_daily_summaries(self):
        from weather.models.daily_summary import DailySummary
        from producer.models.lot import Lot

        lots = list(Lot.objects.filter(
            name__in=["Lote Norte — Malbec", "Lote Sur — Cabernet", "Lote Este — Bonarda"]
        ))
        if not lots:
            self._ok("[!] No se encontraron lotes — saltando DailySummary")
            return

        # Evento climático → (date, tmin, tmax, hr_media, lluvia_mm, eto, wind_max, wind_gusts, horas_hr_alta, horas_oidio)
        # Clima Mendoza Luján de Cuyo — datos sintéticos realistas (BWk árido continental)
        EVENTOS = [
            # ── CAMPAÑA 2025/2026 ──────────────────────────────────────────
            # Brotación (sep-2025) — días fríos nocturnos, sin lluvia
            (date(2025, 9, 5),   9.0, 24.0, 48.0,  0.0, 4.8, 15.0, 22.0,  0,  0),
            (date(2025, 9,15),  11.0, 25.0, 45.0,  0.0, 5.1, 12.0, 18.0,  0,  0),
            # Helada radiativa (28-sep-2025) — T=-1.5, viento calmo
            (date(2025, 9,28),  -1.5, 21.0, 68.0,  0.0, 3.9,  2.5,  4.0,  0,  0),
            # Helada severa (10-oct-2025) — T=-3°C, helada radiativa con daño
            (date(2025,10,10),  -3.0, 20.0, 65.0,  0.0, 4.2,  2.0,  3.0,  0,  0),
            # Viento Zonda (20-oct-2025) — T=38°C, HR=18%, viento 52 km/h
            (date(2025,10,20),  15.0, 38.0, 18.0,  0.0, 9.5, 52.0, 75.0,  0,  3),
            # Desarrollo foliar normal (nov-2025)
            (date(2025,11, 5),  16.0, 29.0, 42.0,  0.0, 5.8, 18.0, 25.0,  0,  5),
            # Floración / Oídio (25-nov-2025) — 8 horas banda Gubler-Thomas
            (date(2025,11,25),  17.0, 30.0, 38.0,  0.0, 6.2, 20.0, 28.0,  0,  8),
            # Cuajado / Lobesia (10-dic-2025)
            (date(2025,12,10),  20.0, 35.0, 32.0,  0.0, 8.0, 22.0, 32.0,  0,  6),
            # Golpe de calor (20-ene-2026) — T=41°C en envero
            (date(2026, 1,20),  22.0, 41.0, 22.0,  0.0,10.5, 25.0, 38.0,  0,  2),
            # Lluvia pre-cosecha / Botrytis (10-feb-2026) — 22 mm, HR=82%
            (date(2026, 2,10),  16.0, 26.0, 82.0, 22.0, 3.5, 10.0, 15.0, 12,  0),
            # Cosecha (20-mar-2026) — condiciones ideales
            (date(2026, 3,20),  13.0, 27.0, 52.0,  0.0, 5.0, 12.0, 18.0,  0,  0),

            # ── CAMPAÑA 2026/2027 — clima reciente (agosto 2026, dormancia) ──
            (date(2026, 8, 1),   0.0, 13.0, 55.0,  0.0, 1.8, 10.0, 15.0,  0,  0),
            (date(2026, 8, 8),  -1.0, 12.0, 60.0,  2.0, 1.5,  8.0, 12.0,  0,  0),
            (date(2026, 8,15),   2.0, 15.0, 50.0,  0.0, 2.0,  9.0, 14.0,  0,  0),
            (date(2026, 8,17),   3.0, 16.0, 48.0,  0.0, 2.2, 11.0, 16.0,  0,  0),  # hoy
        ]

        total = 0
        for lot in lots:
            for d, tmin, tmax, hr, lluvia, eto, wmax, wgust, hrs_hr, hrs_oid in EVENTOS:
                DailySummary.objects.update_or_create(
                    lot=lot, date=d,
                    defaults={
                        "tmin": tmin, "tmax": tmax, "hr_media": hr,
                        "lluvia_mm": lluvia, "eto_mm": eto,
                        "wind_max": wmax, "wind_gusts_max": wgust,
                        "horas_hr_alta": hrs_hr, "horas_banda_oidio": hrs_oid,
                        "fuente_predominante": "open_meteo",
                    },
                )
            total += len(EVENTOS)

        self._ok(f"{total} DailySummary  ({len(lots)} lotes × {len(EVENTOS)} eventos clave)")

    # ── 11. Alertas campaña anterior ─────────────────────────────────────────

    def _seed_alerts_prev(self, crops_prev):
        from alert.models.indicator import Indicator
        from alert.models.alert import Alert

        inds  = {i.name: i for i in Indicator.objects.all()}
        crop_m = crops_prev.get("malbec")
        crop_c = crops_prev.get("cabernet_sauv")
        crop_b = crops_prev.get("bonarda")

        # (slug, fecha, crop, nivel, bbch_stage, detalle_confirmado)
        ALERTAS = [
            # Heladas sep-oct 2025
            ("helada", date(2025, 9,28), crop_c, "warning",
             "01-09 — Brotación",
             "T mínima −1.5 °C con viento < 3 km/h (helada radiativa). Yemas en apertura. "
             "Riego de cobertura aplicado. Sin daño visible confirmado."),
            ("helada", date(2025,10,10), crop_m, "alert",
             "01-09 — Brotación",
             "T mínima −3.0 °C. Helada severa radiativa. Calefactores activados a las 04h. "
             "Daño confirmado en ~15% de brotes tiernos del bloque alto del lote."),
            ("helada", date(2025,10,12), crop_m, "warning",
             "11-15 — Desarrollo foliar (1 a 5 hojas)",
             "T mínima −1.8 °C. Segunda helada en dos días. Menor impacto — brotes más avanzados. "
             "Calefactores encendidos preventivamente."),
            # Zonda
            ("zonda", date(2025,10,20), crop_m, "alert",
             "11-15 — Desarrollo foliar (1 a 5 hojas)",
             "T máx 38 °C, HR 18%, viento 52 km/h (ráfagas 75 km/h). Evento Zonda típico de primavera. "
             "Quemazón foliar leve en hojas jóvenes. Riego activado."),
            ("zonda", date(2025,10,20), crop_c, "warning",
             "11-15 — Desarrollo foliar (1 a 5 hojas)",
             "Mismo sistema Zonda. T máx 38 °C, HR 18%. Menor exposición que Lote Norte. Vigilancia."),
            # Oídio
            ("oidio", date(2025,11,25), crop_m, "warning",
             "65 — Plena floración",
             "8 horas en banda Gubler-Thomas (21–30 °C). Riesgo oídio elevado en floración. "
             "Tratamiento con Azufre + Ciproconazol aplicado 22-oct — cobertura activa."),
            # Lobesia
            ("lobesia", date(2025,12,10), crop_m, "warning",
             "71-73 — Cuajado (grano perdigón)",
             "Primer vuelo confirmado en trampa delta Lote Norte. GDD Lobesia ≈ 220 (base 7). "
             "Superado umbral de 3 capturas/trampa/semana. Aplicación Clorpirifós ejecutada."),
            ("lobesia", date(2025,12,10), crop_c, "warning",
             "71-73 — Cuajado (grano perdigón)",
             "Correlación trampa Lote Norte. Aplicación preventiva ejecutada."),
            # Golpe de calor
            ("golpe_calor", date(2026, 1,20), crop_m, "alert",
             "77-79 — Cierre de racimo",
             "T máx 41 °C en período de cierre de racimo. Sunburn risk alto. "
             "Riego foliar de emergencia aplicado 7–10 h. Daño menor en exposición oeste."),
            ("golpe_calor", date(2026, 1,20), crop_b, "alert",
             "77-79 — Cierre de racimo",
             "T máx 41 °C. Bonarda tiene piel fina — alta sensibilidad al sunburn. Riego foliar ejecutado."),
            # Botrytis
            ("botrytis", date(2026, 2,10), crop_b, "warning",
             "83 — Envero avanzado",
             "22 mm lluvia en 24 h + 12 horas HR ≥ 90%. Racimo cerrado — condiciones favorables botrytis. "
             "Tratamiento Boscalid + Piraclostrobin aplicado 12-feb."),
            # Mildiu (vigilancia — año seco)
            ("mildiu_primario", date(2025,11,20), crop_m, "warning",
             "57 — Flores separándose",
             "Alerta vigilancia. Año seco — sin lluvia en 3 semanas. Riesgo bajo para Mendoza. "
             "Tratamiento preventivo con Mancozeb aplicado igualmente dado BBCH sensible."),
            # Ventana de aplicación
            ("ventana_aplicacion", date(2025,11, 5), crop_m, "warning",
             "53-55 — Inflorescencias visibles",
             "Delta T = 9 °C (T=29°C, TW=20°C). Ventana óptima estrecha. "
             "Aplicación realizada entre 6h–9h cuando Delta T estuvo en 4–7 °C."),
        ]

        count = 0
        for slug, d, crop, level, bbch, detail in ALERTAS:
            ind = inds.get(slug)
            if not ind or not crop:
                continue
            Alert.objects.get_or_create(
                crop=crop, indicator=ind, date=d, is_aborted=False,
                defaults={
                    "name":        f"Alerta {ind.name} — {d} — {crop.name}",
                    "detail":      detail,
                    "bbch_stage":  bbch,
                    "level":       level,
                    "is_forecast": False,
                },
            )
            count += 1

        self._ok(f"{count} alertas históricas — campaña 2025/2026")

    # ── 12. Alertas campaña actual ────────────────────────────────────────────

    def _seed_alerts_curr(self, crops_curr):
        from alert.models.indicator import Indicator
        from alert.models.alert import Alert

        inds  = {i.name: i for i in Indicator.objects.all()}
        crop_m = crops_curr.get("malbec")
        crop_c = crops_curr.get("cabernet_sauv")
        crop_b = crops_curr.get("bonarda")

        # Alertas de pronóstico para toda la temporada 2026/2027.
        # Persisten en la base de datos — no las borra el ciclo diario.
        # is_forecast=True indica que son proyecciones, no eventos confirmados.
        # Cuando run_daily_cycle confirme un evento real, creará/actualizará la alerta de ese día.
        ALERTAS_CURR = [
            # ── Brotación sep-oct 2026 — heladas esperadas ──────────────────
            ("helada", date(2026, 9,25), crop_m, "warning", True,
             "01-09 — Brotación",
             "PRONÓSTICO: T mínima −1.0 °C prevista en brotación. Helada radiativa probable. "
             "Activar calefactores si T < 0 °C a las 3h. OT contingente generada."),
            ("helada", date(2026, 9,25), crop_c, "warning", True,
             "01-09 — Brotación",
             "PRONÓSTICO: T mínima −1.0 °C. Yemas en apertura — alta sensibilidad. "
             "Riego de cobertura preparado como medida preventiva."),
            ("helada", date(2026, 9,25), crop_b, "warning", True,
             "01-09 — Brotación",
             "PRONÓSTICO: T mínima −1.0 °C. Bonarda brotación temprana — verificar exposición."),
            ("helada", date(2026,10, 5), crop_m, "alert", True,
             "11-15 — Desarrollo foliar (1 a 5 hojas)",
             "PRONÓSTICO: T mínima −2.5 °C. Helada tardía con brotes en 2–4 hojas. "
             "Umbral crítico para Malbec (−2.0 °C). Alta probabilidad de daño sin protección."),
            # ── Zonda oct 2026 ────────────────────────────────────────────
            ("zonda", date(2026,10,12), crop_m, "warning", True,
             "11-15 — Desarrollo foliar (1 a 5 hojas)",
             "PRONÓSTICO: viento N 45 km/h, T máx 36 °C, HR < 25%. "
             "Condiciones de Zonda previstas. Monitorear carga hídrica del suelo."),
            ("zonda", date(2026,10,12), crop_c, "warning", True,
             "11-15 — Desarrollo foliar (1 a 5 hojas)",
             "PRONÓSTICO: mismo sistema Zonda. Riego preventivo recomendado antes del evento."),
            # ── Oídio nov 2026 ────────────────────────────────────────────
            ("oidio", date(2026,11,15), crop_m, "warning", True,
             "53-55 — Inflorescencias visibles",
             "PRONÓSTICO: condiciones favorables — 7+ horas previstas en banda 21–30 °C. "
             "Primera aplicación preventiva programada para mediados de noviembre."),
            ("oidio", date(2026,11,15), crop_b, "warning", True,
             "53-55 — Inflorescencias visibles",
             "PRONÓSTICO: mismas condiciones. Bonarda — sensibilidad media al oídio."),
            # ── Lobesia dic 2026 ──────────────────────────────────────────
            ("lobesia", date(2026,12,10), crop_m, "warning", True,
             "71-73 — Cuajado (grano perdigón)",
             "PRONÓSTICO: primer vuelo esperado ~200 GDD base 7 (≈ 10-dic). "
             "Instalar trampas delta antes del 1/12. Monitoreo semanal."),
            # ── Ventana de aplicación nov 2026 ────────────────────────────
            ("ventana_aplicacion", date(2026,11,20), crop_m, "warning", True,
             "57 — Flores separándose",
             "PRONÓSTICO: Delta T estimado > 8 °C (T~30°C, HR~40%). "
             "Ventana de aplicación reducida. Planificar tratamientos para 6h–9h."),
            # ── Mildiu (vigilancia) nov 2026 ──────────────────────────────
            ("mildiu_primario", date(2026,11,22), crop_m, "warning", True,
             "65 — Plena floración",
             "VIGILANCIA: Mendoza zona árida — riesgo mildiu bajo en ausencia de lluvia. "
             "Activar alerta solo si lluvia > 10 mm en 48 h durante floración."),
            # ── Golpe de calor ene 2027 (proyección estacional) ───────────
            ("golpe_calor", date(2027, 1,15), crop_m, "warning", True,
             "77-79 — Cierre de racimo",
             "PROYECCIÓN ESTACIONAL: enero 2027 — T máx histórica zona 38–42 °C. "
             "Preparar riego foliar de emergencia y monitoreo diario T máx."),
            ("golpe_calor", date(2027, 1,15), crop_b, "warning", True,
             "77-79 — Cierre de racimo",
             "PROYECCIÓN ESTACIONAL: Bonarda piel fina — prioridad en Plan de contingencia verano."),
        ]

        count = 0
        for slug, d, crop, level, is_fc, bbch, detail in ALERTAS_CURR:
            ind = inds.get(slug)
            if not ind or not crop:
                continue
            Alert.objects.get_or_create(
                crop=crop, indicator=ind, date=d, is_aborted=False,
                defaults={
                    "name":        f"Alerta {ind.name} — {d} — {crop.name}",
                    "detail":      detail,
                    "bbch_stage":  bbch,
                    "level":       level,
                    "is_forecast": is_fc,
                },
            )
            count += 1

        self._ok(f"{count} alertas temporada 2026/2027  (todas is_forecast=True — pronóstico)")
        self._ok(
            "  Tip: corré 'run_daily_cycle' para agregar alertas confirmadas del día de hoy."
        )
