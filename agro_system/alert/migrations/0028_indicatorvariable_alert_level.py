from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("alert", "0027_indicator_recommendation"),
    ]

    operations = [
        migrations.AddField(
            model_name="indicatorvariable",
            name="alert_level",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Any level (no restriction)"),
                    ("warning", "Warning"),
                    ("alert", "Alert"),
                    ("critical", "Critical"),
                ],
                default="",
                help_text="Level this threshold triggers. Empty = applies to all levels.",
                max_length=10,
                verbose_name="alert level",
            ),
        ),
    ]
