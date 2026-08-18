from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0021_remove_json_fields'),
        ('alert', '0023_indicator_action_and_alert_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='alert',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='work_orders',
                to='alert.alert',
                verbose_name='alert',
            ),
        ),
    ]
