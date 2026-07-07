from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0023_inputworkorder_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='inputworkorder',
            name='exchange_rate',
            field=models.FloatField(blank=True, null=True, verbose_name='exchange rate'),
        ),
        migrations.AddField(
            model_name='inputworkorder',
            name='value_real_base',
            field=models.FloatField(blank=True, null=True, verbose_name='real value (base currency)'),
        ),
        migrations.AlterField(
            model_name='inputworkorder',
            name='value_estimated',
            field=models.FloatField(blank=True, null=True, verbose_name='estimated value (base currency)'),
        ),
        migrations.AlterField(
            model_name='inputworkorder',
            name='currency',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=models.deletion.SET_NULL,
                to='parameter.currency',
                verbose_name='currency (real)',
            ),
        ),
    ]
