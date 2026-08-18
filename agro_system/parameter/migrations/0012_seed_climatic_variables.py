from django.db import migrations

CLIMATIC_VARIABLES = [
    "Temperatura",
    "Humedad relativa",
    "Velocidad del viento",
    "Dirección del viento",
    "Ráfagas de viento",
    "Precipitación (mm)",
    "ETo",
    "CAPE",
]


def seed_climatic_variables(apps, schema_editor):
    VarCropTechnique = apps.get_model("parameter", "VarCropTechnique")
    for name in CLIMATIC_VARIABLES:
        VarCropTechnique.objects.get_or_create(
            name=name,
            defaults={"is_climatic": True},
        )


def unseed_climatic_variables(apps, schema_editor):
    VarCropTechnique = apps.get_model("parameter", "VarCropTechnique")
    VarCropTechnique.objects.filter(name__in=CLIMATIC_VARIABLES, is_climatic=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("parameter", "0011_var_crop_technique_is_climatic"),
    ]

    operations = [
        migrations.RunPython(seed_climatic_variables, unseed_climatic_variables),
    ]
