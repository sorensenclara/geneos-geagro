# Generated manually — reemplaza el 0013 original que dependía de vineyard.Season (eliminado).
# Agrega los FKs a IndicatorVariable, copia las variables/rangos de los indicadores existentes
# (variable_N, min_var_N, max_var_N -> IndicatorVariable con order=N), elimina esos campos viejos
# y elimina Alert.lot (redundante via crop.lot).

import django.db.models.deletion
from django.db import migrations, models

OLD_SLOTS = [(1, 'one'), (2, 'two'), (3, 'three')]


def copy_indicator_variables(apps, schema_editor):
    """Pasa cada variable configurada en el indicador a un IndicatorVariable (rol 'filter' por defecto,
    igual que la lógica vieja: todas las variables deben estar dentro de su rango)."""
    Indicator = apps.get_model('alert', 'Indicator')
    IndicatorVariable = apps.get_model('alert', 'IndicatorVariable')
    new_rows = []
    for indicator in Indicator.objects.all():
        for order, suffix in OLD_SLOTS:
            variable_id = getattr(indicator, f'variable_{suffix}_id')
            if not variable_id:
                continue
            new_rows.append(IndicatorVariable(
                indicator_id=indicator.pk,
                variable_id=variable_id,
                min_value=getattr(indicator, f'min_var_{suffix}'),
                max_value=getattr(indicator, f'max_var_{suffix}'),
                order=order,
            ))
    IndicatorVariable.objects.bulk_create(new_rows)


def restore_indicator_variables(apps, schema_editor):
    """Reversa: vuelve a cargar los campos viejos del indicador desde IndicatorVariable (order 1-3)."""
    Indicator = apps.get_model('alert', 'Indicator')
    IndicatorVariable = apps.get_model('alert', 'IndicatorVariable')
    slots = dict(OLD_SLOTS)
    for iv in IndicatorVariable.objects.filter(order__in=slots).order_by('order'):
        suffix = slots[iv.order]
        Indicator.objects.filter(pk=iv.indicator_id).update(**{
            f'variable_{suffix}_id': iv.variable_id,
            f'min_var_{suffix}': iv.min_value,
            f'max_var_{suffix}': iv.max_value,
        })
    IndicatorVariable.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('alert', '0012_indicatorvariable_remove_indicator_max_var_one_and_more'),
        ('parameter', '0007_typevarcroptechnique_varcroptechnique_is_manual_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='indicatorvariable',
            name='indicator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variables', to='alert.indicator', verbose_name='indicator'),
        ),
        migrations.AddField(
            model_name='indicatorvariable',
            name='variable',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parameter.varcroptechnique', verbose_name='variable'),
        ),
        # Los campos de la variable uno eran obligatorios: se vuelven opcionales antes de borrarlos
        # para que la reversa pueda recrearlos vacíos y recién después cargarles los valores.
        migrations.AlterField(
            model_name='indicator',
            name='variable_one',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='variable_one', to='parameter.varcroptechnique', verbose_name='variable one'),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='min_var_one',
            field=models.FloatField(blank=True, null=True, verbose_name='min variable one'),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='max_var_one',
            field=models.FloatField(blank=True, null=True, verbose_name='max variable one'),
        ),
        migrations.RunPython(copy_indicator_variables, restore_indicator_variables),
        migrations.RemoveField(model_name='indicator', name='max_var_one'),
        migrations.RemoveField(model_name='indicator', name='max_var_three'),
        migrations.RemoveField(model_name='indicator', name='max_var_two'),
        migrations.RemoveField(model_name='indicator', name='min_var_one'),
        migrations.RemoveField(model_name='indicator', name='min_var_three'),
        migrations.RemoveField(model_name='indicator', name='min_var_two'),
        migrations.RemoveField(model_name='indicator', name='variable_one'),
        migrations.RemoveField(model_name='indicator', name='variable_three'),
        migrations.RemoveField(model_name='indicator', name='variable_two'),
        migrations.RemoveField(
            model_name='alert',
            name='lot',
        ),
    ]
