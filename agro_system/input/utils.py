from django.utils import timezone


def update_input_cost(input_obj):
    """
    Actualiza cost y currency del insumo al confirmar una compra, siempre en moneda base.
    La tasa histórica usada para la conversión queda registrada en la orden de compra.
    - manual: no hace nada
    - last_purchase: cost = total_base / amount de la última compra confirmada
    - campaign_avg: cost = Σtotal_base / Σamount de todas las compras de la campaña actual
    """
    if input_obj.cost_update_mode == 'manual':
        return

    from input.models.purchase_order_detail import PurchaseOrderDetail
    from parameter.models.currency import Currency

    base_currency = Currency.objects.filter(is_base=True).first()

    confirmed_details = PurchaseOrderDetail.objects.filter(
        input=input_obj,
        purchase_order__state='confirm',
        amount__gt=0,
        total_base__isnull=False,
    )

    new_cost = None

    if input_obj.cost_update_mode == 'last_purchase':
        detail = confirmed_details.order_by('-purchase_order__date', '-pk').first()
        if detail and detail.amount:
            new_cost = round(detail.total_base / detail.amount, 4)

    elif input_obj.cost_update_mode == 'campaign_avg':
        from parameter.models.campaign import Campaing
        today = timezone.now().date()
        campaign = Campaing.objects.filter(date_init__lte=today, date_final__gte=today).order_by('-date_init').first()
        if not campaign:
            return

        from django.db.models import Sum
        agg = confirmed_details.filter(
            purchase_order__date__gte=campaign.date_init,
            purchase_order__date__lte=campaign.date_final,
        ).aggregate(total_base_sum=Sum('total_base'), amount_sum=Sum('amount'))

        if agg['total_base_sum'] and agg['amount_sum']:
            new_cost = round(agg['total_base_sum'] / agg['amount_sum'], 4)

    if new_cost is not None:
        update_kwargs = {'cost': new_cost, 'cost_base': new_cost}
        if base_currency:
            update_kwargs['currency_id'] = base_currency.pk
        input_obj.__class__.objects.filter(pk=input_obj.pk).update(**update_kwargs)
