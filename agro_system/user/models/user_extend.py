from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, is_staff=False, username=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email, **extra_fields),
        )

        user.is_staff = is_staff
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password):
        """
        Creates and saves a staff user with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password,**extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
            **extra_fields
        )

        user.is_superuser= True
        user.is_staff = True
        user.admin = True
        user.save(using=self._db)
        return user

class UserExtend(AbstractUser):
    """
    Modelo que extiende de User para que inicie sesión con el campo email
    """

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    types = [
            ('Administration', _('General administration')),
            ('Organization', _('Organization')),
            ('Producer', _('Producer')),
            ('Staff', _('Staff')), 

        ]
    
    username = None
    email = models.EmailField(unique=True, verbose_name = _('email'))
    type = models.CharField(max_length=22, choices=types, null=True, blank=True, verbose_name = _('userType'))
    
  