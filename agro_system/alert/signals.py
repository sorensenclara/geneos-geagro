from django.db.models.signals import post_save
from django.dispatch import receiver
from .models.variable_register import VariableRegister
from .models.indicator import Indicator
from .models.alert import Alert
from django.db import models
from user.models.notification import Notification


@receiver(post_save, sender=VariableRegister)
def check_indicators_and_create_alert(sender, instance, created, **kwargs):
    print("ENTROOOOOOO")
    # CUANDO CREA O SI EDITA TAMBIEN?

    # if not created:
    #     return

    variable = instance.variable
    date = instance.date

    indicators = Indicator.objects.filter(
        models.Q(variable_one=variable) |
        models.Q(variable_two=variable) |
        models.Q(variable_three=variable)
    )

    for indicator in indicators:
        all_out_of_range = True
        details = []
        for var_field, min_field, max_field in [
            ('variable_one', 'min_var_one', 'max_var_one'),
            ('variable_two', 'min_var_two', 'max_var_two'),
            ('variable_three', 'min_var_three', 'max_var_three'),
        ]:
            var_obj = getattr(indicator, var_field)
            if var_obj:
                reg = VariableRegister.objects.filter(variable=var_obj, date=date).first()
                if not reg:
                    all_out_of_range = False  # Falta registro para esa variable ese día
                    break
                min_value = getattr(indicator, min_field)
                max_value = getattr(indicator, max_field)
                if not (reg.value < min_value or reg.value > max_value):
                    all_out_of_range = False  # No está fuera de rango
                    break
                details.append(f"{var_obj.name}: {reg.value} fuera de rango ({min_value}-{max_value})")
        if all_out_of_range and details:
            Alert.objects.create(
                name=f'Alerta {indicator.name} - {date}',
                indicator=indicator,
                date=date,
                detail='; '.join(details)
            )
            for user in indicator.report_user.all():
                Notification.objects.create(
                    name=f'Notificación {indicator.name} - {date}',
                    detail='; '.join(details),
                    date=date,
                    user=user
                )