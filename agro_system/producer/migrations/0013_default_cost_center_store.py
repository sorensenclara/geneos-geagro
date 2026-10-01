from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('producer', '0012_rename_activity_variety'),
    ]

    operations = [
        migrations.AddField(
            model_name='costcenter',
            name='default',
            field=models.BooleanField(default=False, verbose_name='default'),
        ),
        migrations.AlterField(
            model_name='countryside',
            name='cost_center',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='producer.costcenter', verbose_name='cost center'),
        ),
        migrations.AlterField(
            model_name='countryside',
            name='store',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='producer.store', verbose_name='store'),
        ),
        migrations.AlterField(
            model_name='lot',
            name='cost_center',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='producer.costcenter', verbose_name='cost center'),
        ),
    ]
