from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0028_workorder_optional_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workorder',
            name='code',
            field=models.CharField(blank=True, help_text='If left empty, it is numbered automatically (0001, 0002...).', max_length=100, verbose_name='code'),
        ),
    ]
