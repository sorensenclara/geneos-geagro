from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0022_work_order_alert_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='stage',
            name='bbch_from',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                verbose_name='BBCH from',
                help_text='Código BBCH mínimo (entero) en que aplica este estadio. '
                          'Nulo = sin límite inferior (ej. Poda, fuera de escala BBCH).',
            ),
        ),
        migrations.AddField(
            model_name='stage',
            name='bbch_to',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                verbose_name='BBCH to',
                help_text='Código BBCH máximo (entero) en que aplica este estadio. '
                          'Nulo = sin límite superior.',
            ),
        ),
    ]
