from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from input.models.input import Input
from input.models.stock_movement import StockMovement
from input.models.purchase_order import PurchaseOrder
from input.models.purchase_order_detail import PurchaseOrderDetail
from producer.models.store import Store
from operation.models.crop import Crop

from agro_system.views.filter_helpers import read_filter, get_producer_ref


@login_required
def InputsView(request):

    _, crop_id = read_filter(request)

    # ── Filtro de almacén (propio de esta vista) ───────────
    if 'store' in request.GET:
        request.session['filter_store_id'] = request.GET.get('store') or None
    store_id = request.GET.get('store') or request.session.get('filter_store_id')

    user = request.user
    producer_ref = get_producer_ref(user)

    if getattr(user, 'type', None) == 'Organization':
        from user.models.user_producer import UserProducer
        _org_producers = UserProducer.objects.filter(organization=user)
        sf = {'producer__in': _org_producers}
        stores = Store.objects.filter(producer__in=_org_producers).order_by('name')
        inputs_qs = Input.objects.filter(producer__in=_org_producers, control_stock=True)
    elif producer_ref:
        sf = {'producer': producer_ref}
        stores = Store.objects.filter(producer=producer_ref).order_by('name')
        inputs_qs = Input.objects.filter(producer=producer_ref, control_stock=True)
    else:
        sf = {}
        stores = Store.objects.all().order_by('name')
        inputs_qs = Input.objects.filter(control_stock=True)

    selected_store = stores.filter(id=store_id).first() if store_id else None

    # ── Stock por almacén (si hay filtro activo) ───────────
    store_stock = {}
    if selected_store:
        rows = (
            StockMovement.objects
            .filter(store=selected_store, **sf)
            .values('input_id')
            .annotate(total=Sum('quantity'))
        )
        store_stock = {r['input_id']: r['total'] for r in rows}

    # ── Insumos ────────────────────────────────────────────

    inputs_qs = inputs_qs.select_related('type', 'unit_measure', 'currency').order_by('type__name', 'name')

    # Si hay almacén seleccionado: solo mostrar inputs que tuvieron movimientos ahí
    if selected_store:
        inputs_qs = inputs_qs.filter(id__in=store_stock.keys())

    inputs_data = []
    total_valor  = 0
    bajo_minimo  = []
    sin_stock    = []

    for inp in inputs_qs:
        # Stock: real del almacén si hay filtro, global si no
        stock = store_stock.get(inp.id, 0) if selected_store else inp.stock
        proyectado = stock + (inp.pending or 0)

        if stock <= 0:
            estado = 'sin_stock'
            sin_stock.append(inp.name)
        elif inp.min_stock and stock <= inp.min_stock:
            estado = 'bajo'
            bajo_minimo.append(inp.name)
        else:
            estado = 'ok'

        pct_stock = 0
        if inp.min_stock and inp.min_stock > 0:
            pct_stock = min(100, round(stock / inp.min_stock * 100))

        valor = round(stock * (inp.cost or 0), 2)
        total_valor += valor

        inputs_data.append({
            'input':      inp,
            'stock':      stock,
            'proyectado': round(proyectado, 2),
            'valor':      valor,
            'estado':     estado,
            'pct_stock':  pct_stock,
        })

    # ── KPIs ───────────────────────────────────────────────
    oc_pendientes_count = PurchaseOrder.objects.filter(state='pending', **sf).count()

    # ── Movimientos recientes ───────────────────────────────
    mov_filter = {**sf}
    if selected_store:
        mov_filter['store'] = selected_store

    movimientos = (
        StockMovement.objects
        .filter(**mov_filter)
        .select_related('input', 'input__unit_measure', 'store', 'work_order', 'purchase_reception')
        .order_by('-date', '-id')[:40]
    )

    # ── Órdenes de compra pendientes ───────────────────────
    oc_filter = {'state': 'pending', **sf}
    if selected_store:
        oc_filter['store'] = selected_store

    ordenes_pendientes = (
        PurchaseOrder.objects
        .filter(**oc_filter)
        .select_related('provider', 'store')
        .order_by('delivery_date')[:15]
    )

    ordenes_con_detalle = []
    for oc in ordenes_pendientes:
        detalles = PurchaseOrderDetail.objects.filter(
            purchase_order=oc
        ).select_related('input', 'input__unit_measure')
        ordenes_con_detalle.append({'oc': oc, 'detalles': detalles})

    # ── Consumo por cultivo seleccionado ───────────────────
    selected_crop = None
    consumo_cultivo = []

    if crop_id:
        selected_crop = Crop.objects.filter(id=crop_id).first()
        if selected_crop:
            consumo_filter = {'work_order__crop': selected_crop, 'operation': 'output', **sf}
            if selected_store:
                consumo_filter['store'] = selected_store

            consumo_qs = (
                StockMovement.objects
                .filter(**consumo_filter)
                .select_related('input', 'input__unit_measure', 'work_order')
                .order_by('-date')
            )

            consumo_por_insumo = {}
            for m in consumo_qs:
                key = m.input_id
                if key not in consumo_por_insumo:
                    consumo_por_insumo[key] = {'input': m.input, 'total': 0, 'movs': []}
                consumo_por_insumo[key]['total'] += abs(m.quantity)
                consumo_por_insumo[key]['movs'].append(m)

            consumo_cultivo = sorted(
                consumo_por_insumo.values(),
                key=lambda x: x['total'],
                reverse=True,
            )

    data = {
        'stores':             stores,
        'selected_store':     selected_store,
        'inputs_data':        inputs_data,
        'sin_stock':          sin_stock,
        'bajo_minimo':        bajo_minimo,
        'total_valor':        round(total_valor, 2),
        'oc_pendientes_count': oc_pendientes_count,
        'movimientos':        movimientos,
        'ordenes_con_detalle': ordenes_con_detalle,
        'selected_crop':      selected_crop,
        'consumo_cultivo':    consumo_cultivo,
    }

    return render(request, 'pages/inputs.html', data)
