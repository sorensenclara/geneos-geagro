from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0026_add_contractor_cost_real'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Activity',
            new_name='Variety',
        ),
        migrations.AlterModelOptions(
            name='variety',
            options={'verbose_name': 'variety', 'verbose_name_plural': 'varieties'},
        ),
        migrations.RenameField(
            model_name='crop',
            old_name='activity',
            new_name='variety',
        ),
        migrations.RenameField(
            model_name='stage',
            old_name='activity',
            new_name='variety',
        ),
        migrations.RenameField(
            model_name='technicalplan',
            old_name='activity',
            new_name='variety',
        ),
        migrations.AlterField(
            model_name='crop',
            name='variety',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='operation.variety', verbose_name='variety'),
        ),
        migrations.AlterField(
            model_name='stage',
            name='variety',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='operation.variety', verbose_name='variety'),
        ),
        migrations.AlterField(
            model_name='technicalplan',
            name='variety',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='operation.variety', verbose_name='variety'),
        ),
    ]
