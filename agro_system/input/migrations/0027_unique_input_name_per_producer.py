from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0026_store_blank_default'),
    ]

    operations = [
        migrations.AlterField(
            model_name='input',
            name='name',
            field=models.CharField(max_length=200, verbose_name='name'),
        ),
        migrations.AddConstraint(
            model_name='input',
            constraint=models.UniqueConstraint(fields=('name', 'producer'), name='unique_input_name_per_producer'),
        ),
        migrations.AddConstraint(
            model_name='input',
            constraint=models.UniqueConstraint(condition=models.Q(('producer__isnull', True)), fields=('name',), name='unique_input_name_shared'),
        ),
    ]
