from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("operation", "0025_remove_stage_phen_fk"),
        ("producer", "0012_lot_external_station"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Activity",
            new_name="Variety",
        ),
    ]
