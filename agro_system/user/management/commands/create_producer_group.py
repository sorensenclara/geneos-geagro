from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Crea el grupo Productor y asigna permisos de las apps indicadas.'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name="Productor")
        apps_to_include = ["producer", "input", "operation", "sale", "alert"]
        cts = ContentType.objects.filter(app_label__in=apps_to_include)
        permissions = Permission.objects.filter(content_type__in=cts)
        group.permissions.add(*permissions)
        
        weather_data_ct = ContentType.objects.filter(app_label="weather", model="weatherdata")
        permissions = Permission.objects.filter(content_type__in=weather_data_ct, codename__startswith="view_")
        group.permissions.add(*permissions)

        # Monitoreo del cultivo: biofix y observaciones fenológicas completos (los admins filtran por productor)
        monitoring_ct = ContentType.objects.filter(app_label="crop_monitoring",
                                                   model__in=["biofix", "phenologicalobservation"])
        group.permissions.add(*Permission.objects.filter(content_type__in=monitoring_ct))
        # Acumulador GDD: ver y corregir el offset / recalcular desde el biofix
        gdd_ct = ContentType.objects.filter(app_label="crop_monitoring", model="gddaccumulator")
        group.permissions.add(*Permission.objects.filter(content_type__in=gdd_ct,
                                                         codename__regex=r"^(view|change)_"))
        # Resumen diario del lote y clima de la estación externa: solo lectura
        weather_ro_ct = ContentType.objects.filter(app_label="weather", model__in=["dailysummary", "openmeteohourly"])
        group.permissions.add(*Permission.objects.filter(content_type__in=weather_ro_ct, codename__startswith="view_"))


        group.save()
        self.stdout.write(self.style.SUCCESS(f"Grupo 'Productor' creado/asignado con {group.permissions.count()} permisos."))
