from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('producer', '0011_add_contractor'),
        ('operation', '0027_rename_activity_variety'),
    ]

    operations = [
        migrations.RenameField(
            model_name='lot',
            old_name='activity',
            new_name='variety',
        ),
        migrations.RenameField(
            model_name='lot',
            old_name='last_activity',
            new_name='last_variety',
        ),
        migrations.AlterField(
            model_name='lot',
            name='variety',
            field=models.ManyToManyField(to='operation.variety', verbose_name='varieties'),
        ),
        migrations.AlterField(
            model_name='lot',
            name='last_variety',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lot_uact', to='operation.variety', verbose_name='last variety'),
        ),
    ]
