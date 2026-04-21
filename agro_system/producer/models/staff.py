from django.db import models
from django.utils.translation import gettext_lazy as _
from .typeStaff import TypeStaff
from agro_system.validacions import validation_cuit 
from parameter.models.city import City
from parameter.models.gender import Gender
from datetime import date


class Staff(models.Model):

    """ Modelo para representar el personal de un proveedor"""

    states = [
        ('active', _('active')),
        ('inactive', _('inactive')),
        ('discharged', _('discharged')),
    ]

    name = models.CharField(max_length=200, verbose_name = _('name'))
    surname = models.CharField(max_length=200, verbose_name = _('surname'))
    cuit = models.CharField(max_length=11, unique=True, validators=[validation_cuit])
    address = models.CharField(max_length=50, verbose_name = _('address'))
    city = models.ForeignKey(City, models.CASCADE, verbose_name = _('city'))
    phone = models.CharField(max_length=20, verbose_name = _('phone'))
    email = models.EmailField(null=True, blank=True, verbose_name = _('email'))
    type = models.ForeignKey(TypeStaff, models.CASCADE, verbose_name = _('type'))
    gender = models.ForeignKey(Gender, models.CASCADE, verbose_name = _('gender'))
    date_birth = models.DateField(blank=True, null=True, verbose_name = _('date of birth'))
    date_entry = models.DateField(default=date.today, verbose_name = _('date of entry') )
    state = models.CharField(max_length=15, choices=states, default="Activo", verbose_name = _('state') )
    discharged = models.DateField(null=True, blank=True, verbose_name = _('discharged') )
    producer = models.ForeignKey('user.UserProducer', models.CASCADE, verbose_name = _('producer'))
    user = models.OneToOneField('user.UserExtend', on_delete=models.CASCADE, blank=True, null=True, related_name='staff_user', verbose_name = _('user'), help_text=_('User associated with the staff member.'))

    def __str__(self):
        return f"{self.name} {self.surname}"

    class Meta:
        verbose_name = _('staff')
        verbose_name_plural = _('staff')
    

    def save(self, *args, **kwargs):
        self.email = self.user.email if self.user else self.email
        super().save(*args, **kwargs)
        
