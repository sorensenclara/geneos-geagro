from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


VAC_DEL = (
    Q(codename__startswith='view_') |
    Q(codename__startswith='add_') |
    Q(codename__startswith='change_') |
    Q(codename__startswith='delete_')
)
VIEW_ONLY = Q(codename__startswith='view_')
VAC = Q(codename__startswith='view_') | Q(codename__startswith='add_') | Q(codename__startswith='change_')


class Command(BaseCommand):
    help = 'Crea/actualiza el grupo Organizacion con permisos ver+crear+editar+borrar.'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='Organizacion')
        action = 'Creado' if created else 'Actualizado'

        perms = Permission.objects.none()

        # Apps principales: ver + crear + editar + borrar
        cts_main = ContentType.objects.filter(
            app_label__in=['producer', 'input', 'operation', 'sale', 'storage', 'alert']
        )
        perms |= Permission.objects.filter(content_type__in=cts_main).filter(VAC_DEL)

        # Weather: solo ver
        cts_weather = ContentType.objects.filter(
            app_label='weather', model__in=['weatherdata', 'weatherstation']
        )
        perms |= Permission.objects.filter(content_type__in=cts_weather).filter(VIEW_ONLY)

        # Parameter completo: solo ver (para poder navegar campos, especies, campañas, etc.)
        cts_param = ContentType.objects.filter(app_label='parameter')
        perms |= Permission.objects.filter(content_type__in=cts_param).filter(VIEW_ONLY)

        # Tasa de cambio: también puede crear y editar
        cts_exchangerate = ContentType.objects.filter(app_label='parameter', model='exchangerate')
        perms |= Permission.objects.filter(content_type__in=cts_exchangerate).filter(VAC)

        group.permissions.set(perms)

        self.stdout.write(self.style.SUCCESS(
            f"{action} grupo 'Organizacion' con {perms.count()} permisos."
        ))
