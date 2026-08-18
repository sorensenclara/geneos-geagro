# Generated manually — reemplaza el 0013 original que dependía de vineyard.Season (eliminado).
# Agrega los FKs a IndicatorVariable y elimina Alert.lot (redundante via crop.lot).

import django.db.models.deletion
from django.db import migrations, models


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
        migrations.RemoveField(
            model_name='alert',
            name='lot',
        ),
    ]
