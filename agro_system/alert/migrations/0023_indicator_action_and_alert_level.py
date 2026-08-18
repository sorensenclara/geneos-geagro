from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alert', '0022_add_max_forecast_days_and_is_forecast'),
        ('input', '0019_provider_default_provider_producer'),
        ('operation', '0021_remove_json_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='alert',
            name='level',
            field=models.CharField(
                blank=True,
                choices=[
                    ('warning', 'Warning'),
                    ('alert', 'Alert'),
                    ('critical', 'Critical'),
                ],
                default='',
                max_length=10,
                verbose_name='level',
            ),
            preserve_default=False,
        ),

        migrations.CreateModel(
            name='IndicatorAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_level', models.CharField(
                    blank=True,
                    choices=[
                        ('', 'All levels'),
                        ('warning', 'Warning'),
                        ('alert', 'Alert'),
                        ('critical', 'Critical'),
                    ],
                    max_length=10,
                    verbose_name='alert level',
                )),
                ('bbch_from', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='BBCH from')),
                ('bbch_to', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='BBCH to')),
                ('days_to_complete', models.PositiveSmallIntegerField(default=3, verbose_name='days to complete')),
                ('create_on_forecast', models.BooleanField(default=False, verbose_name='create on forecast')),
                ('indicator', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='actions',
                    to='alert.indicator',
                    verbose_name='indicator',
                )),
                ('service', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='operation.service',
                    verbose_name='service',
                )),
                ('stage', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='operation.stage',
                    verbose_name='stage',
                )),
            ],
            options={
                'verbose_name': 'indicator action',
                'verbose_name_plural': 'indicator actions',
                'ordering': ['indicator', 'alert_level', 'bbch_from'],
            },
        ),

        migrations.CreateModel(
            name='IndicatorActionInput',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dose', models.FloatField(verbose_name='planned dose')),
                ('action', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='inputs',
                    to='alert.indicatoraction',
                    verbose_name='action',
                )),
                ('input', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='input.input',
                    verbose_name='input',
                )),
            ],
            options={
                'verbose_name': 'indicator action input',
                'verbose_name_plural': 'indicator action inputs',
            },
        ),

        migrations.RunSQL(
            sql="""
                INSERT INTO parameter_otstate (name, is_default)
                VALUES ('Contingente', false)
                ON CONFLICT (name) DO NOTHING;
            """,
            reverse_sql="DELETE FROM parameter_otstate WHERE name = 'Contingente';",
        ),
    ]
