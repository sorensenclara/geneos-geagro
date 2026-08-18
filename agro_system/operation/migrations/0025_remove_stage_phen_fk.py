"""
Elimina phen_from y phen_to de Stage.

La relación Stage ↔ PhenologicalState ahora vive al revés:
PhenologicalState.stage apunta a Stage (FK directa en el modelo de detalle).
El rango BBCH de un Stage se deriva de los estadios que lo referencian.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0024_stage_phen_fk'),
        ('crop_monitoring', '0003_phenological_state_stage_data'),
    ]

    operations = [
        migrations.RemoveField(model_name='stage', name='phen_from'),
        migrations.RemoveField(model_name='stage', name='phen_to'),
    ]
