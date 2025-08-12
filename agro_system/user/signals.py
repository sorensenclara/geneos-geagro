from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models.userProducer import UserProducer
from .models.userOrganization import UserOrganization

@receiver(post_save, sender=UserProducer)
def add_producer_group(sender, instance, created, **kwargs):
    producer_group, _ = Group.objects.get_or_create(name="Productor")
    if not instance.groups.filter(id=producer_group.id).exists():
        instance.groups.add(producer_group)


@receiver(post_save, sender=UserOrganization)
def add_organization_group(sender, instance, created, **kwargs):
    organization_group, created = Group.objects.get_or_create(name="Organizacion")
    if not instance.groups.filter(id=organization_group.id).exists():
        instance.groups.add(organization_group)