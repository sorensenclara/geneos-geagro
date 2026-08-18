"""
Data migration: asigna PhenologicalState.stage y limpia el duplicado bbch='07-09'.

Corre después de 0002 (que agrega el FK) y del seed de etapas operativas.
"""
from django.db import migrations


_BBCH_TO_STAGE = {
    "01-09":  "Brotación",
    "11-15":  "Desarrollo foliar",
    "53-55":  "Floración y Cuaje",
    "57":     "Floración y Cuaje",
    "60":     "Floración y Cuaje",
    "65":     "Floración y Cuaje",
    "69":     "Floración y Cuaje",
    "71-73":  "Floración y Cuaje",
    "75":     "Envero",
    "77-79":  "Envero",
    "81":     "Envero",
    "83":     "Envero",
    "85":     "Maduración",
    "89":     "Cosecha",
}


def remove_duplicate_bbch(apps, schema_editor):
    """Elimina el registro bbch='07-09' (duplicado del '01-09' original)."""
    PhenologicalState = apps.get_model('crop_monitoring', 'PhenologicalState')
    PhenologicalState.objects.filter(bbch="07-09").delete()


def assign_stage_fks(apps, schema_editor):
    PhenologicalState = apps.get_model('crop_monitoring', 'PhenologicalState')
    Stage = apps.get_model('operation', 'Stage')

    stage_cache = {s.name: s for s in Stage.objects.all()}

    for ps in PhenologicalState.objects.all():
        stage_name = _BBCH_TO_STAGE.get(ps.bbch)
        if stage_name:
            stage = stage_cache.get(stage_name)
            if stage:
                ps.stage = stage
                ps.save(update_fields=["stage"])


class Migration(migrations.Migration):

    dependencies = [
        ('crop_monitoring', '0002_phenological_state_stage_fk'),
        ('operation', '0024_stage_phen_fk'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_bbch, migrations.RunPython.noop),
        migrations.RunPython(assign_stage_fks, migrations.RunPython.noop),
    ]
