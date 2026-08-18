from django.db import migrations


def copy_area_alerts_to_profile(apps, schema_editor):
    Area = apps.get_model('parameter', 'Area')
    AlertProfile = apps.get_model('alert', 'AlertProfile')

    for area in Area.objects.all():
        active_alerts    = area.active_alerts or {}
        thresholds       = area.thresholds or {}
        priority_sources = area.priority_sources or []

        # Solo crea perfil si hay algo configurado
        if active_alerts or thresholds or priority_sources:
            AlertProfile.objects.get_or_create(
                area=area,
                defaults={
                    'active_alerts':    active_alerts,
                    'thresholds':       thresholds,
                    'priority_sources': priority_sources,
                },
            )


def revert_profile_to_area(apps, schema_editor):
    Area = apps.get_model('parameter', 'Area')
    AlertProfile = apps.get_model('alert', 'AlertProfile')

    for profile in AlertProfile.objects.select_related('area'):
        area = profile.area
        area.active_alerts    = profile.active_alerts
        area.thresholds       = profile.thresholds
        area.priority_sources = profile.priority_sources
        area.save()


class Migration(migrations.Migration):

    dependencies = [
        ('alert', '0014_alertprofile'),
        ('parameter', '0009_area_alert_fields'),
    ]

    operations = [
        migrations.RunPython(copy_area_alerts_to_profile, revert_profile_to_area),
    ]
