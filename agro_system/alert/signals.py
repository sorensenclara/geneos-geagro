from django.db.models.signals import post_save
from django.dispatch import receiver
from .models.variable_register import VariableRegister
from .models.indicator import Indicator
from .models.alert import Alert
from django.db import models
from user.notifications import active_staff_users, notify
from operation.models.crop import Crop
from operation.models.technical_crop_detail import TechnicalCropDetail

# Señalaes para crear alertas cuando se reistram variables generales (CLIMA) o técnicas (DETALLES DEL CULTIVO) y evaluar los indicadores asociados a cada cultivo.

def get_variable_value(crop, variable, date, hour=None):

    # Variable técnica del cultivo
    tech_reg = TechnicalCropDetail.objects.filter(
        crop=crop,
        varTechnique=variable,
        date__lte=date
    )

    tech_reg = tech_reg.order_by('-date', '-id').first()

    if tech_reg:
        return tech_reg.value

    # Variable general/climática
    climate_reg = VariableRegister.objects.filter(
        variable=variable,
        station=crop.lot.station,
        date=date
    )

    if climate_reg and hour:
        climate_reg = climate_reg.filter(hour=hour)

    climate_reg = climate_reg.order_by('-id').first()

    if climate_reg:
        return climate_reg.value

    return None



def evaluate_indicators_for_crop(crop, date, hour=None):

    indicators = crop.indicators.all()

    variable_configs = [
        ('variable_one', 'min_var_one', 'max_var_one'),
        ('variable_two', 'min_var_two', 'max_var_two'),
        ('variable_three', 'min_var_three', 'max_var_three'),
    ]

    for indicator in indicators:

        all_conditions_met = True
        details = []

        for var_field, min_field, max_field in variable_configs:

            var_obj = getattr(indicator, var_field)

            if not var_obj:
                continue

            value = get_variable_value(
                crop=crop,
                variable=var_obj,
                date=date,
                hour=hour
            )

            if value is None:
                all_conditions_met = False
                break

            min_value = getattr(indicator, min_field)
            max_value = getattr(indicator, max_field)

            condition_met = True

            if min_value is not None:
                condition_met = condition_met and value >= min_value

            if max_value is not None:
                condition_met = condition_met and value <= max_value

            if not condition_met:
                all_conditions_met = False
                break

            details.append(
                f"{var_obj.name}: {value} "
                f"(rango {min_value}-{max_value})"
            )

        if all_conditions_met and details:

            # Las notificaciones las crea notify_alert_created (post_save de Alert)
            Alert.objects.get_or_create(
                crop=crop,
                indicator=indicator,
                date=date,
                defaults={
                    "name": f'Alerta {indicator.name} - {date} - {crop.name}',
                    "detail": '; '.join(details),
                }
            )


# NOTIFICACIONES CUANDO SE CREA UNA ALERTA (automática por indicador o cargada a mano)
# Se avisa al productor del cultivo/lote, a todo su personal activo y a los usuarios del indicador.
@receiver(post_save, sender=Alert)
def notify_alert_created(sender, instance, created, **kwargs):
    if not created:
        return

    crop = instance.crop
    producer = crop.producer if crop else None

    users = [producer] + active_staff_users(producer)
    if instance.indicator:
        users += list(instance.indicator.report_user.all())

    if instance.indicator and crop:
        name = f'Notificación {instance.indicator.name} - {instance.date} - {crop.name}'
    else:
        name = f'Notificación {instance.name}'
    detail = instance.detail
    if crop:
        detail = f'Lote: {crop.lot} - Cultivo: {crop.name}. {detail}'

    notify(users, name=name, detail=detail, date=instance.date)

# SEÑAL DE ALERTA CUANDO SE CREA UNA VARIABLE CLIMATICA DESDE LA ESTACION METEOROLOGICA o GENERAL
@receiver(post_save, sender=VariableRegister)
def evaluate_from_climate(sender, instance, created, **kwargs):

    crops = Crop.objects.filter(
        lot__station=instance.station
    )

    for crop in crops:

        evaluate_indicators_for_crop(
            crop=crop,
            date=instance.date,
            hour=getattr(instance, "hour", None)
        )

# SEÑAL DE ALERTA CUANDO SE CREA UNA DETALLE TECNICO (VARIABLES) DEL CULTIVO
@receiver(post_save, sender=TechnicalCropDetail)
def evaluate_from_technical(sender, instance, created, **kwargs):

    evaluate_indicators_for_crop(
        crop=instance.crop,
        date=instance.date,
        hour=getattr(instance, "hour", None)
    )


# @receiver(post_save, sender=VariableRegister)
# def check_indicators_and_create_alert(sender, instance, created, **kwargs):

#     variable = instance.variable
#     date = instance.date
#     station = instance.station
#     if instance.hour:
#         hour = instance.hour
#     else:
#         hour = None

#     crops = Crop.objects.filter(lot__station=station).prefetch_related("indicators")

#     variable_configs = [
#         ('variable_one', 'min_var_one', 'max_var_one'),
#         ('variable_two', 'min_var_two', 'max_var_two'),
#         ('variable_three', 'min_var_three', 'max_var_three'),
#     ]

#     for crop in crops:

#         indicators = crop.indicators.all()

#         for indicator in indicators:

#             indicator_variables = [
#                 indicator.variable_one,
#                 indicator.variable_two,
#                 indicator.variable_three,
#             ]

#             if variable not in indicator_variables:
#                 continue

#             all_conditions_met = True
#             details = []

#             for var_field, min_field, max_field in variable_configs:

#                 var_obj = getattr(indicator, var_field)

#                 if not var_obj:
#                     continue

#                 reg = VariableRegister.objects.filter(
#                     variable=var_obj,
#                     hour=hour,
#                     date=date,
#                     station=station
#                 ).first()


#                 if not reg:
#                     all_conditions_met = False
#                     break

#                 min_value = getattr(indicator, min_field)
#                 max_value = getattr(indicator, max_field)

#                 value = reg.value

#                 # Evaluación dentro del rango
#                 condition_met = min_value <= value <= max_value

#                 if not condition_met:
#                     all_conditions_met = False
#                     break

#                 details.append(
#                     f"{var_obj.name}: {value} "
#                     f"(rango {min_value}-{max_value})"
#                 )

#             # Crear alerta
#             if all_conditions_met and details:

#                 alert, alert_created = Alert.objects.get_or_create(
#                     crop=crop,
#                     date=date,
#                     indicator=indicator,
#                     name=f'Alerta {indicator.name} - {date} - {crop.name}',
#                     defaults={
#                         "detail": '; '.join(details),
#                     }
#                 )

#                 # Crear notificaciones SOLO si la alerta es nueva
#                 if alert_created:
#                     # NOTIFICACION AL PRODUCTOR
#                     Notification.objects.create(
#                             name=f'Notificación {indicator.name} - {date} - {crop.name}',
#                             detail='; '.join(details),
#                             date=date,
#                             user=crop.producer
#                         )
#                     # NOTIFICACION A USUARIOS ASOCIADOS AL INDICADOR
#                     for user in indicator.report_user.all():
#                         Notification.objects.create(
#                             name=f'Notificación {indicator.name} - {date} - {crop.name}',
#                             detail='; '.join(details),
#                             date=date,
#                             user=user
#                         )
#                     # NOTIFICACION AL RESPONSABLE DEL CULTIVO
#                     if crop.responsible:
#                         Notification.objects.create(
#                             name=f'Notificación {indicator.name} - {date} - {crop.name}',
#                             detail='; '.join(details),
#                             date=date,
#                             user=crop.responsible.user
#                         )
                

# def get_variable_value(crop, variable, date):

#     # Buscar  variable técnica del cultivo
#     tech_reg = TechnicalCropDetail.objects.filter(
#         crop=crop,
#         varTechnique=variable,
#         date=date
#     ).order_by('-id').first()

#     if tech_reg:
#         return tech_reg.value

#     # Buscar variable climática
#     climate_reg = VariableRegister.objects.filter(
#         variable=variable,
#         station=crop.lot.station,
#         date=date
#     ).order_by('-id').first()

#     if climate_reg:
#         return climate_reg.value

#     return None