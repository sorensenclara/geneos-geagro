from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('producer', '0013_default_cost_center_store'),
        ('user', '0005_alter_notification_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='costcenter',
            name='producer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='user.userproducer', verbose_name='producer'),
        ),
    ]
