from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0029_workorder_code_auto'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='surface',
            field=models.FloatField(blank=True, null=True, verbose_name='surface (ha)'),
        ),
    ]
