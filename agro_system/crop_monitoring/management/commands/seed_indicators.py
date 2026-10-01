"""
Management command: seed_indicators
====================================
Crea o actualiza todos los indicadores de alerta y los vincula a los perfiles
de zona (Mendoza y Tandil).

Idempotente: se puede correr cuantas veces sea necesario sin duplicar datos.
Usa update_or_create para que los cambios en evaluator / review_mode /
max_forecast_days se apliquen aunque el registro ya exista.

Uso:
    python manage.py seed_indicators

Agregar un indicador nuevo:
  1. Crear la clase evaluadora en alert/evaluators/<nombre>.py
  2. Agregar la entrada a INDICADORES con el path del evaluador
  3. Agregar su estado a MENDOZA_STATUS y/o TANDIL_STATUS
  4. Correr el comando
"""

from django.core.management.base import BaseCommand
from alert.models.indicator import Indicator


# ---------------------------------------------------------------------------
# Definición de todos los indicadores
# Campos: (slug, nombre_legible, criticidad, evaluador, review_mode, max_forecast_days)
#
#   evaluador         → path Python a la clase, o "" para motor genérico
#   review_mode       → "daily" (default) | "per_reading"
#   max_forecast_days → días a futuro para alertas de pronóstico (None = global)
# ---------------------------------------------------------------------------

INDICADORES = [
    # slug                 | nombre                    | criticidad | evaluador                                                  | review_mode | max_fc
    ("helada",             "Helada",                   "high",     "alert.evaluators.frost.FrostEvaluator",                    "daily",     5),
    ("granizo",            "Granizo",                  "high",     "alert.evaluators.storm_hail.StormHailEvaluator",           "daily",     2),
    ("estres_hidrico",     "Estrés hídrico",           "high",     "",                                                         "daily",     None),
    ("golpe_calor",        "Golpe de calor",           "medium",   "",                                                         "daily",     3),
    ("zonda",              "Zonda",                    "medium",   "",                                                         "daily",     2),
    ("lobesia",            "Lobesia botrana",          "medium",   "",                                                         "daily",     None),
    ("oidio",              "Oídio",                    "medium",   "",                                                         "daily",     None),
    ("botrytis",           "Botrytis",                 "medium",   "",                                                         "daily",     None),
    ("mildiu_primario",    "Mildiu primario",          "medium",   "alert.evaluators.mildiu_primario.MildiuPrimarioEvaluator", "daily",     3),
    ("mildiu_secundario",  "Mildiu secundario",        "low",      "",                                                         "daily",     None),
    ("ventana_aplicacion", "Ventana de aplicación",    "low",      "alert.evaluators.ventana_aplicacion.VentanaAplicacionEvaluator", "daily", 1),
    ("gdd_cosecha",        "Ventana de cosecha",       "low",      "",                                                         "daily",     None),
]

# ---------------------------------------------------------------------------
# Estado por zona (status: "on" | "vigilance" | "off")
# Los indicadores ausentes del mapa quedan sin perfil asociado para esa zona.
# ---------------------------------------------------------------------------

MENDOZA_STATUS = {
    "helada":             "on",
    "granizo":            "on",
    "estres_hidrico":     "on",
    "golpe_calor":        "on",
    "zonda":              "on",
    "lobesia":            "on",
    "oidio":              "on",
    "ventana_aplicacion": "on",
    "gdd_cosecha":        "on",
    "mildiu_primario":    "vigilance",  # solo años lluviosos
    "botrytis":           "vigilance",  # solo lluvia pre-cosecha
    "mildiu_secundario":  "off",
}

TANDIL_STATUS = {
    "helada":             "on",
    "ventana_aplicacion": "on",
    "mildiu_primario":    "on",
    "mildiu_secundario":  "on",
    "botrytis":           "on",
    "estres_hidrico":     "vigilance",
    "lobesia":            "vigilance",
    "granizo":            "vigilance",
    "golpe_calor":        "vigilance",
    "zonda":              "off",
}

# ---------------------------------------------------------------------------
# Recomendaciones (IndicatorRecommendation — texto informativo en la alerta)
# Formato: (alert_level, bbch_from, bbch_to, texto, order)
#   alert_level vacío → aplica a todos los niveles
#   bbch_from/to None → aplica a cualquier estadio
# ---------------------------------------------------------------------------

RECOMENDACIONES_HELADA = [
    ("", None, None, "Riego de aspersión 25 mm/ha.", 0),
    ("", None, None, "Activar helicóptero para mezcla del aire.", 0),
]

RECOMENDACIONES_ZONDA = [
    ("",         None, None,    "No realizar aplicaciones", 0),
    ("critical", 89,   100,     "Posponer cosecha",         0),
]

RECOMENDACIONES_VENTANA = [
    ("warning", None, None, "Precaución: condiciones subóptimas. Revisar viento y Delta T antes de comenzar la aplicación. Suspender si el viento supera 15 km/h o llueve.", 0),
    ("alert",   None, None, "No aplicar: condiciones fuera de rango (viento, Delta T o lluvia en las próximas horas). Reprogramar la aplicación.", 0),
]

RECOMENDACIONES_MILDIU = [
    ("warning",  None, None, "Fungicida preventivo (cobre o fosfonatos) ANTES de la lluvia.", 1),
    ("alert",    None, None, "Si ya llovió: aplicar curativo en 48–72 h (cimoxanilo, dimethomorph).", 1),
    ("critical", None, None, "Programa preventivo intensivo: repetir cada 7–10 días durante el período lluvioso.", 1),
]

# ---------------------------------------------------------------------------
# Acciones (IndicatorAction — genera orden de trabajo cuando dispara la alerta)
# Formato: (alert_level, bbch_from, bbch_to, service_name, stage_name, create_on_forecast, days_to_complete)
#   stage_name None → sin etapa asignada
# ---------------------------------------------------------------------------

ACCIONES_HELADA = [
    ("", None, None, "Activación de calefactores (helada)", None, True,  3),
    ("", None, None, "Protección contra Heladas",           None, True,  3),
    ("", None, None, "Riego de cobertura anti-helada",      None, False, 3),
]

ACCIONES_MILDIU = [
    ("", None, None, "Aplicación fungicida — Mildiu", None, False, 3),
]

ACCIONES_ZONDA = [
    ("",         None, None, "Monitoreo y resguardo por Zonda", None,      True, 2),
    ("",         None, None, "Riego canopy",                    None,      True, 0),
    ("critical", 89,   100,  "Posponer cosecha",                "Cosecha", True, 3),
]


class Command(BaseCommand):
    help = "Crea o actualiza todos los indicadores de alerta y sus vínculos con los perfiles de zona."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== seed_indicators ==="))
        self._seed_var_crop_techniques()
        self._seed_indicators()
        self._seed_mildiu_primario_config()
        self._seed_ventana_aplicacion_config()
        self._seed_recommendations("mildiu_primario",   RECOMENDACIONES_MILDIU)
        self._seed_recommendations("helada",            RECOMENDACIONES_HELADA)
        self._seed_recommendations("zonda",             RECOMENDACIONES_ZONDA)
        self._seed_recommendations("ventana_aplicacion", RECOMENDACIONES_VENTANA)
        self._seed_actions("helada",          ACCIONES_HELADA)
        self._seed_actions("zonda",           ACCIONES_ZONDA)
        self._seed_actions("mildiu_primario", ACCIONES_MILDIU)
        self._seed_profile_links()
        self.stdout.write(self.style.SUCCESS("Listo.\n"))

    # ------------------------------------------------------------------

    def _seed_var_crop_techniques(self):
        """Asegura que existan las VarCropTechnique necesarias para todos los evaluadores."""
        from parameter.models.var_crop_technique import VarCropTechnique
        from parameter.models.type_var_crop_technique import TypeVarCropTechnique

        tipo_clima, _ = TypeVarCropTechnique.objects.get_or_create(name="Climático")

        VARS = [
            "Temperatura media",   # mildiu
            "Lluvia (mm)",         # mildiu
            "Humedad relativa",    # mildiu
            "Viento máximo",       # ventana_aplicacion
            "Ráfaga máxima",       # ventana_aplicacion
            "Delta T mínimo",      # ventana_aplicacion
            "Delta T máximo",      # ventana_aplicacion
            "Viento mínimo noche", # ventana_aplicacion
        ]
        self.stdout.write("\n  VarCropTechnique:")
        for name in VARS:
            _, created = VarCropTechnique.objects.get_or_create(
                name=name,
                defaults={"type": tipo_clima, "field_name": ""},
            )
            tag = "+" if created else "✓"
            self.stdout.write(f"    {tag} {name}")

    def _seed_indicators(self):
        self.stdout.write("\n  Indicadores:")
        created_total = updated_total = 0

        for slug, nombre, criticidad, evaluador, review_mode, max_fc in INDICADORES:
            defaults = {
                "criticality_level": criticidad,
                "evaluator":         evaluador,
                "review_mode":       review_mode,
                "max_forecast_days": max_fc,
            }
            obj, created = Indicator.objects.update_or_create(
                name=slug,
                defaults=defaults,
            )
            if created:
                created_total += 1
                self.stdout.write(f"    + Creado:       {nombre} ({slug})")
            else:
                updated_total += 1
                self.stdout.write(f"    ✓ Actualizado:  {nombre} ({slug})")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n  → {created_total} creados, {updated_total} actualizados."
            )
        )

    def _seed_mildiu_primario_config(self):
        """
        Crea IndicatorVariable e IndicatorBand para mildiu_primario.

        IndicatorVariable (umbrales configurables):
          - Temperatura media  min_value=10  → T_media mínima de infección
          - Lluvia (mm)        min_value=10  → lluvia mínima en 24-48 h
          - Humedad relativa   min_value=80  → HR proxy de mojado foliar

        IndicatorBand (BBCH + nivel, sin threshold — solo por etapa):
          - BBCH 14-59  → alert    (pre-floración)
          - BBCH 60-69  → critical (floración — siempre crítico)
          - BBCH 70-79  → alert    (cuaje → envero)
          HR ≥ 80% escala alert → critical (via _escalar_nivel en el evaluador).
        """
        from alert.models.indicator_variable import IndicatorVariable
        from alert.models.indicator_band import IndicatorBand
        from parameter.models.var_crop_technique import VarCropTechnique

        try:
            ind = Indicator.objects.get(name="mildiu_primario")
        except Indicator.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ mildiu_primario no encontrado — omitido."))
            return

        self.stdout.write("\n  Configuración mildiu_primario:")

        # --- IndicatorVariable ---
        VARIABLES = [
            ("Temperatura media", "filter", 10.0,  None),
            ("Lluvia (mm)",       "filter", 10.0,  None),
            ("Humedad relativa",  "filter", 95.0,  None),
        ]
        for var_name, role, min_val, max_val in VARIABLES:
            try:
                var = VarCropTechnique.objects.get(name=var_name)
            except VarCropTechnique.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"    ⚠ VarCropTechnique '{var_name}' no encontrada."))
                continue
            obj, created = IndicatorVariable.objects.update_or_create(
                indicator=ind,
                variable=var,
                role=role,
                defaults={"min_value": min_val, "max_value": max_val},
            )
            tag = "+" if created else "✓"
            self.stdout.write(f"    {tag} Variable: {var_name}  min={min_val}")

        # --- IndicatorBand ---
        # Limpiamos primero las bandas existentes de este indicador para
        # evitar duplicados en caso de cambios de configuración.
        deleted, _ = IndicatorBand.objects.filter(indicator=ind).delete()
        if deleted:
            self.stdout.write(f"    ↻ {deleted} bandas previas eliminadas (reemplazadas).")

        BANDS = [
            # bbch_from, bbch_to, threshold, direction, level, order
            (14, 59, None, None, "alert",    1),   # pre-floración
            (60, 69, None, None, "critical", 1),   # floración — siempre crítico
            (70, 79, None, None, "alert",    1),   # cuaje → envero
        ]
        for bbch_from, bbch_to, threshold, direction, level, order in BANDS:
            IndicatorBand.objects.create(
                indicator=ind,
                bbch_from=bbch_from,
                bbch_to=bbch_to,
                threshold=threshold,
                direction=direction,
                level=level,
                order=order,
            )
            thr_str = f"lluvia ≥ {threshold} mm" if threshold is not None else "siempre"
            self.stdout.write(f"    + Banda BBCH {bbch_from}–{bbch_to} | {thr_str} → {level}")

    def _seed_ventana_aplicacion_config(self):
        """
        Crea IndicatorVariable para ventana_aplicacion.

        Cada variable tiene alert_level explícito ('warning' o 'alert') y
        min_value como umbral de disparo. Una misma variable climática puede
        tener dos registros: uno para warning y otro para alert.

          Viento máximo   | warning | 15 km/h  → viento > 15 → precaución
          Viento máximo   | alert   | 20 km/h  → viento > 20 → no aplicar
          Ráfaga máxima   | warning | 20 km/h
          Ráfaga máxima   | alert   | 25 km/h
          Delta T mínimo  | warning |  2 °C    → delta_t < 2 → precaución
          Delta T máximo  | warning |  8 °C    → delta_t > 8 → precaución
          Delta T máximo  | alert   | 10 °C    → delta_t > 10 → no aplicar
          Viento mínimo noche | alert | 3 km/h → viento < 3 de noche → no aplicar
        """
        from alert.models.indicator_variable import IndicatorVariable
        from parameter.models.var_crop_technique import VarCropTechnique

        try:
            ind = Indicator.objects.get(name="ventana_aplicacion")
        except Indicator.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ ventana_aplicacion no encontrada — omitido."))
            return

        IndicatorVariable.objects.filter(indicator=ind).delete()
        self.stdout.write("\n  Configuración ventana_aplicacion:")

        # (var_name, alert_level, min_value)
        VARIABLES = [
            ("Viento máximo",       "warning",  15.0),
            ("Viento máximo",       "alert",    20.0),
            ("Ráfaga máxima",       "warning",  20.0),
            ("Ráfaga máxima",       "alert",    25.0),
            ("Delta T mínimo",      "warning",   2.0),
            ("Delta T máximo",      "warning",   8.0),
            ("Delta T máximo",      "alert",    10.0),
            ("Viento mínimo noche", "alert",     3.0),
        ]
        for var_name, alert_level, min_val in VARIABLES:
            try:
                var = VarCropTechnique.objects.get(name=var_name)
            except VarCropTechnique.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"    ⚠ VarCropTechnique '{var_name}' no encontrada."))
                continue
            IndicatorVariable.objects.create(
                indicator=ind,
                variable=var,
                alert_level=alert_level,
                role="filter",
                min_value=min_val,
            )
            self.stdout.write(f"    + [{alert_level:7}] {var_name} = {min_val}")

    def _seed_recommendations(self, slug, recs_list):
        """Recrea las IndicatorRecommendation para un indicador dado (idempotente)."""
        from alert.models.indicator_recommendation import IndicatorRecommendation
        try:
            ind = Indicator.objects.get(name=slug)
        except Indicator.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"  ⚠ Indicador '{slug}' no encontrado — omitido."))
            return

        IndicatorRecommendation.objects.filter(indicator=ind).delete()
        self.stdout.write(f"\n  Recomendaciones {slug}:")
        for alert_level, bbch_from, bbch_to, text, order in recs_list:
            IndicatorRecommendation.objects.create(
                indicator=ind,
                alert_level=alert_level,
                bbch_from=bbch_from,
                bbch_to=bbch_to,
                text=text,
                order=order,
            )
            level_tag = alert_level or "todos"
            self.stdout.write(f"    + [{level_tag}] {text[:70]}")

    def _seed_actions(self, slug, actions_list):
        """Recrea las IndicatorAction para un indicador dado (idempotente)."""
        from alert.models.indicator_action import IndicatorAction
        from operation.models.service import Service
        from operation.models.stage import Stage
        try:
            ind = Indicator.objects.get(name=slug)
        except Indicator.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"  ⚠ Indicador '{slug}' no encontrado — omitido."))
            return

        IndicatorAction.objects.filter(indicator=ind).delete()
        self.stdout.write(f"\n  Acciones {slug}:")
        for alert_level, bbch_from, bbch_to, service_name, stage_name, forecast, days in actions_list:
            try:
                service = Service.objects.get(name=service_name)
            except Service.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"    ⚠ Servicio '{service_name}' no encontrado — omitido."))
                continue

            stage = None
            if stage_name:
                stage = Stage.objects.filter(name=stage_name).first()
                if not stage:
                    self.stdout.write(self.style.WARNING(f"    ⚠ Etapa '{stage_name}' no encontrada — acción sin etapa."))

            IndicatorAction.objects.create(
                indicator=ind,
                alert_level=alert_level,
                bbch_from=bbch_from,
                bbch_to=bbch_to,
                service=service,
                stage=stage,
                create_on_forecast=forecast,
                days_to_complete=days,
            )
            level_tag = alert_level or "todos"
            self.stdout.write(f"    + [{level_tag}] {service_name}")

    def _seed_profile_links(self):
        from alert.models.alert_profile import AlertProfile
        from alert.models.alert_profile_indicator import AlertProfileIndicator

        self.stdout.write("\n  Vínculos con perfiles de zona:")

        for area_name, status_map in [("Mendoza", MENDOZA_STATUS), ("Tandil", TANDIL_STATUS)]:
            try:
                profile = AlertProfile.objects.get(area__name=area_name)
            except AlertProfile.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"    ⚠ Sin perfil para zona '{area_name}' — omitido.")
                )
                continue

            ok = skipped = 0
            for slug, status in status_map.items():
                try:
                    indicator = Indicator.objects.get(name=slug)
                except Indicator.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"    ⚠ Indicador '{slug}' no encontrado — omitido.")
                    )
                    skipped += 1
                    continue

                AlertProfileIndicator.objects.update_or_create(
                    profile=profile,
                    indicator=indicator,
                    defaults={"status": status},
                )
                ok += 1

            self.stdout.write(
                f"    {area_name}: {ok} vínculos configurados"
                + (f", {skipped} omitidos" if skipped else "")
            )
