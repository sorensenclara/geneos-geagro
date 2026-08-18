from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("weather", "0018_add_derived_fields_to_open_meteo_hourly"),
    ]

    operations = [
        migrations.AddField(
            model_name="dailysummary",
            name="wind_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                max_digits=5,
                null=True,
                verbose_name="max wind speed (km/h)",
            ),
        ),
        migrations.AddField(
            model_name="dailysummary",
            name="wind_gusts_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                max_digits=5,
                null=True,
                verbose_name="max wind gusts (km/h)",
            ),
        ),
    ]
