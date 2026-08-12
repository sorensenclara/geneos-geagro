from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


VAC = Q(codename__startswith='view_') | Q(codename__startswith='add_') | Q(codename__startswith='change_')

# Apps excluidas: usuarios, grupos y permisos de Django
EXCLUDED_APPS = ['user', 'auth']


class Command(BaseCommand):
    help = 'Crea/actualiza el grupo Administrador con permisos ver+crear+editar en todas las apps menos usuarios y auth.'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='Administrador')
        action = 'Creado' if created else 'Actualizado'

        cts = ContentType.objects.exclude(app_label__in=EXCLUDED_APPS)
        perms = Permission.objects.filter(content_type__in=cts).filter(VAC)

        group.permissions.set(perms)

        self.stdout.write(self.style.SUCCESS(
            f"{action} grupo 'Administrador' con {perms.count()} permisos "
            f"(excluidas apps: {', '.join(EXCLUDED_APPS)})."
        ))
