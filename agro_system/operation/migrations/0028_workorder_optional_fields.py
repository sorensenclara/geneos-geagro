from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0027_rename_activity_variety'),
        ('parameter', '0012_add_symbol_to_currency'),
        ('producer', '0015_unique_name_per_producer'),
    ]

    operations = [
        # Se completan automáticamente si quedan vacíos (siguen siendo NOT NULL)
        migrations.AlterField(
            model_name='workorder',
            name='date_emission',
            field=models.DateField(blank=True, verbose_name='date emission'),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='date_fin',
            field=models.DateField(blank=True, verbose_name='date fin'),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='campaing',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='parameter.campaing', verbose_name='campaign'),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='area',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='parameter.area', verbose_name='are'),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='stateOT',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='parameter.otstate', verbose_name='state ot'),
        ),
        # Pasan a ser opcionales
        migrations.AlterField(
            model_name='workorder',
            name='stage',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='operation.stage', verbose_name='stage'),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='service',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='operation.service', verbose_name='service'),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='staff',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='producer.staff', verbose_name='staff'),
        ),
    ]
