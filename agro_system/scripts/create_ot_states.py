"""
Crea los estados de Orden de Trabajo si no existen.

Uso:
    python scripts/create_ot_states.py

Correr desde la raíz del proyecto Django (donde está manage.py).
Es idempotente: se puede correr N veces sin efecto secundario.
"""

import os
import sys
import django

# Permite correr desde cualquier subdirectorio
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agro_system.settings.dev")
django.setup()

from parameter.models.ot_state import OTState  # noqa: E402

STATES = [
    {"name": "Pendiente",   "is_default": True},
    {"name": "En curso",    "is_default": False},
    {"name": "Finalizada",  "is_default": False},
    {"name": "Contingente", "is_default": False},
    {"name": "Cancelada",   "is_default": False},
]

for s in STATES:
    obj, created = OTState.objects.get_or_create(
        name=s["name"],
        defaults={"is_default": s["is_default"]},
    )
    status = "creado" if created else "ya existía"
    print(f"  {'✓' if created else '·'} {obj.name:15}  ({status})")

print("\nListo.")
