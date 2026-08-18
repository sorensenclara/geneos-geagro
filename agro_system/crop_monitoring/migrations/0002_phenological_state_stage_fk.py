"""
Agrega FK PhenologicalState.stage → Stage (etapa operativa).
Solo schema change — los datos se migran en 0003.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crop_monitoring', '0001_initial'),
        ('operation', '0024_stage_phen_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='phenologicalstate',
            name='stage',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='phenological_states',
                to='operation.stage',
                verbose_name='operational stage',
                help_text='Operational period (etapa) this phenological state belongs to.',
            ),
        ),
    ]
