from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alert', '0026_indicator_review_mode'),
    ]

    operations = [
        migrations.CreateModel(
            name='IndicatorRecommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_level', models.CharField(
                    blank=True, max_length=10,
                    choices=[('', 'All levels'), ('warning', 'Warning'), ('alert', 'Alert'), ('critical', 'Critical')],
                    verbose_name='alert level',
                    help_text='Dejar vacío para aplicar a todos los niveles.',
                )),
                ('bbch_from', models.PositiveSmallIntegerField(
                    null=True, blank=True,
                    verbose_name='BBCH from',
                    help_text='Código BBCH mínimo (inclusivo). Vacío = sin límite inferior.',
                )),
                ('bbch_to', models.PositiveSmallIntegerField(
                    null=True, blank=True,
                    verbose_name='BBCH to',
                    help_text='Código BBCH máximo (inclusivo). Vacío = sin límite superior.',
                )),
                ('text', models.TextField(
                    verbose_name='recommendation',
                    help_text='Texto que se mostrará al usuario cuando la alerta se active.',
                )),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='order')),
                ('indicator', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recommendations',
                    to='alert.indicator',
                    verbose_name='indicator',
                )),
            ],
            options={
                'verbose_name': 'recommendation',
                'verbose_name_plural': 'recommendations',
                'ordering': ('order', 'id'),
            },
        ),
    ]
