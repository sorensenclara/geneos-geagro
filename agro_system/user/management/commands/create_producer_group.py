from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


VAC = Q(codename__startswith='view_') | Q(codename__startswith='add_') | Q(codename__startswith='change_')
VIEW_ONLY = Q(codename__startswith='view_')


class Command(BaseCommand):
    help = 'Crea/actualiza el grupo Productor con sus permisos.'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='Productor')
        action = 'Creado' if created else 'Actualizado'

        perms = Permission.objects.none()

        # Apps completas: ver + crear + editar (sin borrar)
        cts_main = ContentType.objects.filter(
            app_label__in=['producer', 'input', 'operation', 'sale', 'storage', 'alert']
        )
        perms |= Permission.objects.filter(content_type__in=cts_main).filter(VAC)

        # Weather: solo ver (weatherdata y weatherstation)
        cts_weather = ContentType.objects.filter(
            app_label='weather', model__in=['weatherdata', 'weatherstation']
        )
        perms |= Permission.objects.filter(content_type__in=cts_weather).filter(VIEW_ONLY)

        # Parameter completo: solo ver (para navegar especies, campañas, etc.)
        cts_param = ContentType.objects.filter(app_label='parameter')
        perms |= Permission.objects.filter(content_type__in=cts_param).filter(VIEW_ONLY)

        # Tasa de cambio: también puede crear y editar
        cts_param_exchangerate = ContentType.objects.filter(app_label='parameter', model='exchangerate')
        perms |= Permission.objects.filter(content_type__in=cts_param_exchangerate).filter(VAC)

        group.permissions.set(perms)

        self.stdout.write(self.style.SUCCESS(
            f"{action} grupo 'Productor' con {perms.count()} permisos."
        ))
