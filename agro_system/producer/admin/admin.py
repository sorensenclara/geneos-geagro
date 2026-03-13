from django.contrib import admin
from user.admin.adminSite import adminSite
from producer.models.cost_center import CostCenter
from producer.models.store import Store
from producer.models.typeStaff import TypeStaff
# Register your models here.

adminSite.register(CostCenter)
adminSite.register(Store)
adminSite.register(TypeStaff)