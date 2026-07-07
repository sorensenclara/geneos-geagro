from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0024_input_cost_base'),
    ]

    operations = [
        migrations.AddField(
            model_name='input',
            name='cost_update_mode',
            field=models.CharField(
                choices=[
                    ('manual', 'Manual'),
                    ('last_purchase', 'Last purchase price (in base currency)'),
                    ('campaign_avg', 'Weighted average of current campaign (in base currency)'),
                ],
                default='manual',
                help_text='Determines how the base cost is updated when a purchase is confirmed',
                max_length=20,
                verbose_name='cost update mode',
            ),
        ),
    ]
