from django.contrib import admin
from user.admin.adminSite import adminSite
from sale.models.sales_receipt import SalesReceipt
from sale.models.type_sales_receipt import TypeSalesReceipt


adminSite.register(TypeSalesReceipt)