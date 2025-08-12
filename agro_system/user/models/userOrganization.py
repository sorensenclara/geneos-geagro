from django.db import models
from .userExtend import UserExtend
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _


class UserOrganization(UserExtend):
    """
    Modelo que representa al usuario organizacion heredado del usuario extendido
    """

   
    company_name = models.CharField(max_length=100, verbose_name = _('company_name'))
    identification_number = models.CharField(max_length=50, verbose_name = _('identification_number'))
    address = models.CharField(max_length=50, verbose_name = _('address'))
    
    class Meta:
        verbose_name = _('userOrganization'),
        verbose_name_plural = _('usersOrganizations')

    def save(self, *args, **kwargs):
        self.type = 'Organization'
        self.is_staff = True
        super().save(*args, **kwargs)
        
        

    def __str__(self):
        return self.company_name
