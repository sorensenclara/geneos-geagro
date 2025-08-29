from django.contrib import admin
from user.admin.adminSite import adminSite
from sale.models.salesReceipt import SalesReceipt
from sale.models.typeSalesReceipt import TypeSalesReceipt


adminSite.register(SalesReceipt)
adminSite.register(TypeSalesReceipt)