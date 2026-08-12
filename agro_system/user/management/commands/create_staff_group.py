from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


VIEW_ONLY = Q(codename__startswith='view_')
VIEW_CHANGE = Q(codename__startswith='view_') | Q(codename__startswith='change_')


class Command(BaseCommand):
    help = 'Crea/actualiza el grupo Personal con permisos solo ver (excepto OT y movimientos de stock).'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='Personal')
        action = 'Creado' if created else 'Actualizado'

        perms = Permission.objects.none()

        # Apps principales: solo ver
        cts_main = ContentType.objects.filter(
            app_label__in=['producer', 'input', 'operation', 'sale', 'storage', 'alert']
        )
        perms |= Permission.objects.filter(content_type__in=cts_main).filter(VIEW_ONLY)

        # Ordenes de trabajo: ver + editar
        cts_wo = ContentType.objects.filter(app_label='operation', model='workorder')
        perms |= Permission.objects.filter(content_type__in=cts_wo).filter(VIEW_CHANGE)

        # Movimientos de stock: ver + editar
        cts_sm = ContentType.objects.filter(app_label='input', model='stockmovement')
        perms |= Permission.objects.filter(content_type__in=cts_sm).filter(VIEW_CHANGE)

        # Weather: solo ver
        cts_weather = ContentType.objects.filter(
            app_label='weather', model__in=['weatherdata', 'weatherstation']
        )
        perms |= Permission.objects.filter(content_type__in=cts_weather).filter(VIEW_ONLY)

        # Parameter completo: solo ver
        cts_param = ContentType.objects.filter(app_label='parameter')
        perms |= Permission.objects.filter(content_type__in=cts_param).filter(VIEW_ONLY)

        group.permissions.set(perms)

        self.stdout.write(self.style.SUCCESS(
            f"{action} grupo 'Personal' con {perms.count()} permisos."
        ))
