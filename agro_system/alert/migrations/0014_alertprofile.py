from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alert', '0013_indicatorvariable_fks_remove_alert_lot'),
        ('parameter', '0009_area_alert_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active_alerts', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Estado de cada alerta. Valores: "on", "vigilancia", "off".',
                    verbose_name='active alerts',
                )),
                ('thresholds', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Umbrales numéricos por alerta. Puede incluir sub-claves BBCH.',
                    verbose_name='thresholds',
                )),
                ('priority_sources', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='Orden de prioridad de fuentes de datos.',
                    verbose_name='priority sources',
                )),
                ('area', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='alert_profile',
                    to='parameter.area',
                    verbose_name='area',
                )),
            ],
            options={
                'verbose_name': 'alert profile',
                'verbose_name_plural': 'alert profiles',
            },
        ),
    ]
