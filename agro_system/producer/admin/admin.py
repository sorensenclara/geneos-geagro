from django.contrib import admin
from user.admin.adminSite import adminSite
from producer.models.cost_center import CostCenter
from producer.models.typeStaff import TypeStaff
# Register your models here.
# Store se registra en store.py (StoreAdmin, con filtro por productor)

adminSite.register(CostCenter)
adminSite.register(TypeStaff)