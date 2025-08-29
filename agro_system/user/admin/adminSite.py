# myapp/admin.py
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from datetime import datetime
#from dateutil.relativedelta import relativedelta
from input.models.purchaseReceptionDetail import PurchaseReceptionDetail
from input.models.input import Input

class MiAdmin(AdminSite):
    # site_header = "Mi Panel de Administración"
    # site_title = "Admin"
    # index_title = "Bienvenido al Dashboard"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        # Date Now
        date = datetime.now().date()

        # Date -3 months
        date_first_day = date.replace(day=1)
        
        filter_kwargs = {
            f"{'date'}__range": (date_first_day, date)
        }
        all_receipts = PurchaseReceptionDetail.objects.values('input').annotate(res=Sum('amount'))
        
        list_product_ammount = []
        list_product_receipt = []
        
        for prod in all_receipts:
            list_product_receipt.append(Input.objects.filter(id=prod['input']).first().name)
            list_product_ammount.append(prod['res'])
        

        # all_receipts = Receipt.objects.values('product').filter(**filter_kwargs).annotate(res=Sum('price'))
        
        # list_product_ammount = []
        # list_product_receipt = []
        
        # for prod in all_receipts:
        #     list_product_receipt.append(Product.objects.filter(id=prod['product']).first().name)
        #     list_product_ammount.append(prod['res'])
        
        # all_delivery = Delivery.objects.values('product').filter(**filter_kwargs).annotate(res=Sum('price'))
        
        # list_product_delivery = []
        # list_product_delivery_ammount = []
        
        # for prod in all_delivery:
        #     list_product_delivery.append(Product.objects.filter(id=prod['product']).first().name)
        #     list_product_delivery_ammount.append(prod['res'])    

        # all_tasks = RegisterTask.objects.values('task').filter(**filter_kwargs).annotate(res=Sum('hours'))
        # list_tasks = []
        # list_tasks_hours = []
        
        # for task in all_tasks:
        #     list_tasks.append(Task.objects.filter(id=task['task']).first().name)
        #     h = task['res'].total_seconds() / 3600
        #     list_tasks_hours.append(h)
        

        # extra_context['product_receipt'] = list_product_receipt
        # extra_context['ammount_receipt'] = list_product_ammount
        
        # extra_context['product_delivery'] = list_product_delivery
        # extra_context['ammount_delivery'] = list_product_delivery_ammount

        # extra_context['tasks'] = list_tasks
        # extra_context['tasks_hours'] = list_tasks_hours

        extra_context['product_receipt'] = list_product_receipt
        extra_context['ammount_receipt'] = list_product_ammount
        return super().index(request, extra_context=extra_context)


adminSite = MiAdmin(name='miadmin')
