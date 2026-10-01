from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_alter_notification_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='read',
            field=models.BooleanField(default=False, verbose_name='read'),
        ),
        migrations.AddField(
            model_name='notification',
            name='read_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='read at'),
        ),
        migrations.AlterModelOptions(
            name='notification',
            options={'ordering': ['-date', '-id'], 'verbose_name': 'notification', 'verbose_name_plural': 'notifications'},
        ),
    ]
