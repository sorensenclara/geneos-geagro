from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0024_inputworkorder_exchange_rate_value_real_base'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='contractor_cost',
            field=models.FloatField(blank=True, null=True, verbose_name='contractor cost'),
        ),
    ]
