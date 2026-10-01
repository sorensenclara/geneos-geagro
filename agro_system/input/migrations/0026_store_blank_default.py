from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0025_input_cost_update_mode'),
        ('producer', '0013_default_cost_center_store'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchaseorder',
            name='store',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='producer.store', verbose_name='store'),
        ),
        migrations.AlterField(
            model_name='purchasereception',
            name='store',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='producer.store', verbose_name='store'),
        ),
    ]
