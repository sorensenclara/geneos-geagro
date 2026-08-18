"""
Reemplaza bbch_from / bbch_to (enteros) en Stage por FKs a PhenologicalState.

Pasos:
  1. Agrega phen_from / phen_to como FK nullables.
  2. Migración de datos: mapea los valores enteros existentes a los registros
     PhenologicalState correspondientes usando el BBCH como clave.
  3. Elimina bbch_from / bbch_to enteros.
"""
from django.db import migrations, models
import django.db.models.deletion


# Mapeo canónico nombre_estadio → (bbch_inicio, bbch_fin)
# Claves: valor exacto del campo PhenologicalState.bbch
_STAGE_PHEN_MAP = {
    "Poda":               (None,    None),
    "Brotación":          ("07-09", "07-09"),
    "Desarrollo foliar":  ("11-15", "11-15"),
    "Floración y Cuaje":  ("53-55", "71-73"),
    "Envero":             ("75",    "83"),
    "Maduración":         ("85",    "85"),
    "Cosecha":            ("89",    "89"),
}


def populate_phen_fks(apps, schema_editor):
    Stage = apps.get_model('operation', 'Stage')
    PhenologicalState = apps.get_model('crop_monitoring', 'PhenologicalState')

    phen_cache = {ps.bbch: ps for ps in PhenologicalState.objects.all()}

    for stage in Stage.objects.all():
        mapping = _STAGE_PHEN_MAP.get(stage.name)
        if mapping is None:
            # Estadio no reconocido: intentar resolver desde los enteros aún presentes
            # (bbch_from / bbch_to todavía existen en este punto de la migración)
            from_int = getattr(stage, 'bbch_from', None)
            to_int   = getattr(stage, 'bbch_to',   None)
            if from_int is not None:
                stage.phen_from = next(
                    (ps for ps in phen_cache.values()
                     if int(ps.bbch.split("-")[0]) == from_int),
                    None,
                )
            if to_int is not None:
                stage.phen_to = next(
                    (ps for ps in phen_cache.values()
                     if int(ps.bbch.split("-")[-1]) == to_int),
                    None,
                )
            stage.save()
            continue

        from_bbch, to_bbch = mapping
        stage.phen_from = phen_cache.get(from_bbch)
        stage.phen_to   = phen_cache.get(to_bbch)
        stage.save()


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0023_stage_bbch_range'),
        ('crop_monitoring', '0001_initial'),
    ]

    operations = [
        # 1. Agregar FKs nullables
        migrations.AddField(
            model_name='stage',
            name='phen_from',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='crop_monitoring.phenologicalstate',
                verbose_name='BBCH from',
            ),
        ),
        migrations.AddField(
            model_name='stage',
            name='phen_to',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='crop_monitoring.phenologicalstate',
                verbose_name='BBCH to',
            ),
        ),

        # 2. Poblar desde los enteros existentes
        migrations.RunPython(populate_phen_fks, migrations.RunPython.noop),

        # 3. Eliminar los enteros ya redundantes
        migrations.RemoveField(model_name='stage', name='bbch_from'),
        migrations.RemoveField(model_name='stage', name='bbch_to'),
    ]
