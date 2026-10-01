from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('producer', '0014_costcenter_producer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='costcenter',
            name='name',
            field=models.CharField(max_length=200, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='store',
            name='name',
            field=models.CharField(max_length=200, verbose_name='name'),
        ),
        migrations.AddConstraint(
            model_name='costcenter',
            constraint=models.UniqueConstraint(fields=('name', 'producer'), name='unique_cost_center_name_per_producer'),
        ),
        migrations.AddConstraint(
            model_name='costcenter',
            constraint=models.UniqueConstraint(condition=models.Q(('producer__isnull', True)), fields=('name',), name='unique_cost_center_name_shared'),
        ),
        migrations.AddConstraint(
            model_name='store',
            constraint=models.UniqueConstraint(fields=('name', 'producer'), name='unique_store_name_per_producer'),
        ),
        migrations.AddConstraint(
            model_name='store',
            constraint=models.UniqueConstraint(condition=models.Q(('producer__isnull', True)), fields=('name',), name='unique_store_name_shared'),
        ),
    ]
