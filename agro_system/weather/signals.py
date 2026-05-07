from django.db.models.signals import post_save
from django.dispatch import receiver
from alert.models.variable_register import VariableRegister
from alert.models.indicator import Indicator
from alert.models.alert import Alert
from weather.models.weather_data import WeatherData
from parameter.models.var_crop_technique import VarCropTechnique

# CREA O ACTUALIZA AL MAXIMO DEL DIA
# @receiver(post_save, sender=WeatherData)
# def create_or_update_variable_registers(sender, instance, created, **kwargs):

#     station = instance.station
#     date = instance.timestamp.date()

#     variables_map = {
#         "Precipitaciones": instance.rain_total,   # acumulado
#         "Humedad": instance.humidity,             # máximo
#         "Viento": instance.wind_speed,            # máximo
#         "Temperatura": instance.temp,             # máximo
#     }

#     for var_name, new_value in variables_map.items():

#         if new_value is None:
#             continue

#         try:
#             variable = VarCropTechnique.objects.get(name__iexact=var_name)
#         except VarCropTechnique.DoesNotExist:
#             continue

#         obj, created = VariableRegister.objects.get_or_create(
#             variable=variable,
#             date=date,
#             station=station,
#             defaults={
#                 "name": f"{var_name} - {date}",
#                 "value": new_value,
#                 "detail": "Auto generado desde estación meteorológica"
#             }
#         )

#         if not created:
#             if new_value > obj.value:
#                 obj.value = new_value
#                 obj.detail += f"Actualizado. Dato anterior: {obj.value}, nuevo valor: {new_value}."
#                 obj.save(update_fields=["value", "detail"])


# CREAR SIEMPRE PARA EVALUAR INDICADORES
@receiver(post_save, sender=WeatherData)
def create_variable_registers(sender, instance, created, **kwargs):

    station = instance.station
    date = instance.timestamp.date()

    variables_map = {
        "Precipitaciones": instance.rain_total,
        "Humedad": instance.humidity,
        "Viento": instance.wind_speed,
        "Temperatura": instance.temp,
    }

    for var_name, value in variables_map.items():

        if value is None:
            continue

        try:
            variable = VarCropTechnique.objects.get(name__iexact=var_name)
        except VarCropTechnique.DoesNotExist:
            continue

        VariableRegister.objects.create(
            name=f"{var_name} - {instance.timestamp}",
            variable=variable,
            hour=instance.timestamp.time(),
            date=date,
            value=value,
            station=station,
            detail="Auto generado desde estación meteorológica"
        )