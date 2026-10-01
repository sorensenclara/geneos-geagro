from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0030_workorder_surface'),
        ('parameter', '0012_add_symbol_to_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='inputworkorder',
            name='unit_measure',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='parameter.maensureunit', verbose_name='unit of measure'),
        ),
        migrations.AddField(
            model_name='inputworkorder',
            name='total_quantity',
            field=models.FloatField(blank=True, null=True, verbose_name='total quantity'),
        ),
        migrations.AlterField(
            model_name='inputworkorder',
            name='dose',
            field=models.FloatField(verbose_name='technical dose (planned)'),
        ),
        migrations.AlterField(
            model_name='inputworkorder',
            name='dose_applied',
            field=models.FloatField(blank=True, null=True, verbose_name='real dose'),
        ),
    ]
