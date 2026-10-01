from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crop_monitoring", "0004_phenological_calibration_and_observation"),
    ]

    operations = [
        migrations.AddField(
            model_name="gddaccumulator",
            name="gdd_offset",
            field=models.DecimalField(
                decimal_places=1,
                default=0,
                help_text="Manual correction added after recalculation. Set it once and it persists.",
                max_digits=6,
                verbose_name="GDD offset",
            ),
        ),
    ]
