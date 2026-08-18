from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parameter', '0009_area_alert_fields'),
        # Necesita que la data migration haya corrido primero
        ('alert', '0015_copy_area_alerts_to_profile'),
    ]

    operations = [
        migrations.RemoveField(model_name='area', name='active_alerts'),
        migrations.RemoveField(model_name='area', name='thresholds'),
        migrations.RemoveField(model_name='area', name='priority_sources'),
    ]
