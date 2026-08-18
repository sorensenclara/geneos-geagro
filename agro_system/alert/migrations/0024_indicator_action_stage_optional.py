"""
Hace stage opcional en IndicatorAction.

Con stage=None y bbch_from/bbch_to=None, la acción aplica a cualquier
estadio fenológico (dispara siempre que el indicador se active).
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alert', '0023_indicator_action_and_alert_level'),
        ('operation', '0025_remove_stage_phen_fk'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indicatoraction',
            name='stage',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='operation.stage',
                verbose_name='stage',
                help_text=(
                    'Etapa operativa de la OT. Define también el rango BBCH si no se especifica '
                    'bbch_from/bbch_to. Dejar vacío para que la acción aplique a cualquier estadio.'
                ),
            ),
        ),
    ]
