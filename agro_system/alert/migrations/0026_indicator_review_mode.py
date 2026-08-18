from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alert', '0025_alert_is_aborted'),
    ]

    operations = [
        migrations.AddField(
            model_name='indicator',
            name='review_mode',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('daily',       'Revisión diaria'),
                    ('per_reading', 'Revisión por registro'),
                ],
                default='daily',
                verbose_name='review mode',
                help_text=(
                    'Revisión diaria: se evalúa una vez por día con el resumen diario. '
                    'Revisión por registro: todos los filtros deben cumplirse en el mismo registro.'
                ),
            ),
        ),
    ]
