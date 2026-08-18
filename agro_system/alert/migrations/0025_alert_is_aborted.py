from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alert', '0024_indicator_action_stage_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='alert',
            name='is_aborted',
            field=models.BooleanField(
                default=False,
                verbose_name='is aborted',
                help_text=(
                    'True when the forecast expired without confirmation or the forecast changed and the event '
                    'is no longer predicted. Associated WOs are moved to \'Cancelada\'.'
                ),
            ),
        ),
    ]
