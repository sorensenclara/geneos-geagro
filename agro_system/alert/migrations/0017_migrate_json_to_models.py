"""
Data migration: moves active_alerts JSONField → AlertProfileIndicator rows
and thresholds BBCH bands → IndicatorBand rows.

active_alerts format: {"helada": "on", "botrytis": "vigilancia", ...}
thresholds format (helada Mendoza):
    {"helada": {"bandas_bbch": [
        {"bbch_desde": 1, "bbch_hasta": 5, "aviso": -3.0, "alerta": -3.5, "critico": -5.0},
        ...
    ]}}
thresholds format (helada Tandil, simple):
    {"helada": {"bbch_65": -0.5, "bbch_07_57": -1.5}}
"""
from django.db import migrations

# Maps old JSON status values → new model status choices
STATUS_MAP = {
    "on":         "on",
    "vigilancia": "vigilance",
    "off":        "off",
}

# Maps old level keys → new model level choices
LEVEL_MAP = {
    "aviso":   "warning",
    "alerta":  "alert",
    "critico": "critical",
}


def migrate_active_alerts(apps, schema_editor):
    AlertProfile = apps.get_model("alert", "AlertProfile")
    Indicator = apps.get_model("alert", "Indicator")
    AlertProfileIndicator = apps.get_model("alert", "AlertProfileIndicator")
    IndicatorBand = apps.get_model("alert", "IndicatorBand")

    for profile in AlertProfile.objects.all():
        active = profile.active_alerts or {}
        thresholds = profile.thresholds or {}

        for alert_name, raw_status in active.items():
            status = STATUS_MAP.get(raw_status, "on")
            indicator = Indicator.objects.filter(name=alert_name).first()
            if not indicator:
                continue

            AlertProfileIndicator.objects.get_or_create(
                profile=profile,
                indicator=indicator,
                defaults={"status": status},
            )

        # Migrate threshold bands for indicators that have bbch band structure
        for alert_name, threshold_data in thresholds.items():
            if not isinstance(threshold_data, dict):
                continue

            indicator = Indicator.objects.filter(name=alert_name).first()
            if not indicator:
                continue

            bandas = threshold_data.get("bandas_bbch", [])
            for order, banda in enumerate(bandas, start=1):
                bbch_from = banda.get("bbch_desde")
                bbch_to   = banda.get("bbch_hasta")
                if bbch_from is None or bbch_to is None:
                    continue
                for level_key, new_level in LEVEL_MAP.items():
                    umbral = banda.get(level_key)
                    if umbral is None:
                        continue
                    IndicatorBand.objects.get_or_create(
                        indicator=indicator,
                        bbch_from=bbch_from,
                        bbch_to=bbch_to,
                        level=new_level,
                        defaults={"threshold": umbral, "order": order},
                    )


def reverse_migration(apps, schema_editor):
    apps.get_model("alert", "AlertProfileIndicator").objects.all().delete()
    apps.get_model("alert", "IndicatorBand").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("alert", "0016_add_indicator_band_alert_profile_indicator_role"),
    ]

    operations = [
        migrations.RunPython(migrate_active_alerts, reverse_migration),
    ]
