(function () {
  'use strict';

  var COST_URL = '/input/api/cost/';
  var RATE_URL = '/input/api/exchange-rate/';
  var BASE_CURRENCY_URL = '/input/api/base-currency/';

  var baseCurrencyId = null;

  function findRow(selectEl) {
    return selectEl.closest('.inline-related') || selectEl.closest('tr');
  }

  function findValueEstimatedField(selectEl) {
    var row = findRow(selectEl);
    return row ? row.querySelector('input[id$="-value_estimated"]') : null;
  }

  function findCurrencySelect(selectEl) {
    var row = findRow(selectEl);
    return row ? row.querySelector('select[id$="-currency"]') : null;
  }

  function findExchangeRateField(el) {
    var row = findRow(el);
    return row ? row.querySelector('input[id$="-exchange_rate"]') : null;
  }

  function findUnitSelect(selectEl) {
    var row = findRow(selectEl);
    return row ? row.querySelector('select[id$="-unit_measure"]') : null;
  }

  // Asigna el valor a un <select> (con o sin Select2) y dispara change.
  function setSelectValue(selectEl, value) {
    if (!selectEl || value === undefined || value === null) return;
    var jq = (window.django && window.django.jQuery) || window.jQuery || window.$;
    if (jq && typeof jq === 'function') {
      jq(selectEl).val(String(value)).trigger('change');
    } else {
      selectEl.value = value;
      selectEl.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  // Devuelve true si la fila ya fue guardada (tiene PK en el campo hidden "-id").
  function isExistingRow(el) {
    var row = findRow(el);
    if (!row) return false;
    var idInput = row.querySelector('input[name$="-id"]');
    return !!(idInput && idInput.value);
  }

  function setCurrency(selectEl, currencyId) {
    if (!currencyId) return;
    var currencySelect = findCurrencySelect(selectEl);
    if (!currencySelect) return;
    var jq = (window.django && window.django.jQuery) || window.jQuery || window.$;
    if (jq && typeof jq === 'function') {
      jq(currencySelect).val(String(currencyId)).trigger('change');
    } else {
      currencySelect.value = currencyId;
      currencySelect.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  // Busca la tasa y la pone en el campo exchange_rate.
  // overwrite=true: siempre sobreescribe (cambio explícito de moneda).
  // overwrite=false (default): solo rellena si el campo está vacío.
  function fetchAndFillRate(currencySelect, overwrite) {
    var currencyId = currencySelect.value;
    var rateField = findExchangeRateField(currencySelect);
    if (!rateField || !currencyId) return;

    if (!overwrite && rateField.value && parseFloat(rateField.value) !== 0) return;

    fetch(RATE_URL + '?currency_id=' + currencyId)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.rate !== undefined && data.rate !== null) {
          rateField.value = data.rate;
        }
      })
      .catch(function () {});
  }

  // Prefill exchange_rate en filas que tienen moneda pero tasa vacía.
  function prefillRatesOnLoad() {
    document.querySelectorAll('select[id*="inputworkorder_set"][id$="-currency"]').forEach(function (sel) {
      if (sel.id.indexOf('__prefix__') !== -1 || !sel.value) return;
      var rateField = findExchangeRateField(sel);
      if (rateField && !rateField.value) {
        fetchAndFillRate(sel, true);
      }
    });
  }

  // Pone la moneda base en filas NUEVAS (no guardadas) que no tienen moneda asignada.
  function applyDefaultCurrencyToNewRows() {
    if (!baseCurrencyId) return;
    document.querySelectorAll('select[id*="inputworkorder_set"][id$="-currency"]').forEach(function (sel) {
      if (sel.id.indexOf('__prefix__') !== -1) return;
      if (isExistingRow(sel)) return;  // nunca tocar filas ya guardadas
      if (sel.value) return;           // ya tiene moneda
      var jq = (window.django && window.django.jQuery) || window.jQuery || window.$;
      if (jq && typeof jq === 'function') {
        jq(sel).val(baseCurrencyId).trigger('change');
      } else {
        sel.value = baseCurrencyId;
        sel.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  }

  // Obtiene el ID de la moneda base una sola vez al iniciar.
  function fetchBaseCurrency() {
    fetch(BASE_CURRENCY_URL)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.id) {
          baseCurrencyId = String(data.id);
          applyDefaultCurrencyToNewRows();
        }
      })
      .catch(function () {});
  }

  // Al seleccionar un insumo: llena value_estimated (solo si vacío), unidad y moneda/tasa.
  // explicit=true cuando el usuario eligió el insumo en Select2 (no en la inicialización).
  function fetchAndFillOnChange(selectEl, explicit) {
    var inputId = selectEl.value;
    if (!inputId) return;

    fetch(COST_URL + '?id=' + inputId)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var estimatedField = findValueEstimatedField(selectEl);
        if (estimatedField && !estimatedField.value && data.cost !== undefined) {
          estimatedField.value = data.cost;
        }

        // Unidad por defecto la del insumo. En filas guardadas solo se pisa si el usuario
        // eligió el insumo explícitamente (o si la unidad está vacía), para no perder la elegida.
        var unitSelect = findUnitSelect(selectEl);
        if (unitSelect && data.unit_measure_id &&
            (!isExistingRow(selectEl) || explicit || !unitSelect.value)) {
          setSelectValue(unitSelect, data.unit_measure_id);
        }

        if (data.currency_id !== undefined && data.currency_id !== null) {
          setCurrency(selectEl, data.currency_id);
          setTimeout(function () {
            var currencySelect = findCurrencySelect(selectEl);
            if (currencySelect) fetchAndFillRate(currencySelect);
          }, 100);
        }
      })
      .catch(function () {});
  }

  function bindCurrencySelect(currencySelect) {
    if (!currencySelect || currencySelect._rateBound) return;
    currencySelect._rateBound = true;

    // Se activa cuando el usuario elige explícitamente en Select2 (no en la inicialización).
    var s2SelectPending = false;
    var jqForS2 = (window.django && window.django.jQuery) || window.jQuery || window.$;
    if (jqForS2 && typeof jqForS2 === 'function') {
      jqForS2(currencySelect).on('select2:select', function () {
        s2SelectPending = true;
      });
    }

    function onCurrencyChange() {
      var currencyId = currencySelect.value;
      if (!currencyId) return;

      var overwrite;
      if (isExistingRow(currencySelect)) {
        // Filas guardadas: solo sobreescribir si el usuario eligió explícitamente.
        overwrite = s2SelectPending;
      } else {
        overwrite = true;
      }
      s2SelectPending = false;

      fetchAndFillRate(currencySelect, overwrite);
    }

    currencySelect.addEventListener('change', onCurrencyChange);

    var seen = [];
    [window.django && window.django.jQuery, window.jQuery, window.$].forEach(function (jq) {
      if (jq && typeof jq === 'function' && seen.indexOf(jq) === -1) {
        seen.push(jq);
        jq(currencySelect).on('change', onCurrencyChange);
      }
    });

    // Polling fallback para Select2: solo filas NUEVAS.
    var polled = currencySelect.value;
    setInterval(function () {
      var current = currencySelect.value;
      if (current !== polled) {
        polled = current;
        if (current && !isExistingRow(currencySelect)) {
          fetchAndFillRate(currencySelect, true);
        }
      }
    }, 200);
  }

  function bindSelect(selectEl) {
    if (selectEl._autoCostBound) return;
    selectEl._autoCostBound = true;

    // Se activa cuando el usuario elige explícitamente en Select2 (no en la inicialización).
    var s2SelectPending = false;
    var jqForS2 = (window.django && window.django.jQuery) || window.jQuery || window.$;
    if (jqForS2 && typeof jqForS2 === 'function') {
      jqForS2(selectEl).on('select2:select', function () {
        s2SelectPending = true;
      });
    }

    function onInputChange() {
      var explicit = s2SelectPending;
      s2SelectPending = false;
      fetchAndFillOnChange(selectEl, explicit);
    }

    selectEl.addEventListener('change', onInputChange);

    var seen = [];
    [window.django && window.django.jQuery, window.jQuery, window.$].forEach(function (jq) {
      if (jq && typeof jq === 'function' && seen.indexOf(jq) === -1) {
        seen.push(jq);
        jq(selectEl).on('change', onInputChange);
      }
    });

    var last = selectEl.value;
    setInterval(function () {
      if (selectEl.value !== last) {
        last = selectEl.value;
        fetchAndFillOnChange(selectEl);
      }
    }, 200);
  }

  // ── Cantidad total = dosis (real, o técnica si no hay real) x superficie de la orden ──
  // Se recalcula sola mientras el usuario no la edite a mano. Si la borra, vuelve a ser automática.

  function parseNumber(value) {
    if (value === undefined || value === null || String(value).trim() === '') return null;
    var n = parseFloat(String(value).replace(',', '.'));
    return isNaN(n) ? null : n;
  }

  function computeTotal(row) {
    var surfaceEl = document.getElementById('id_surface');
    var surface = surfaceEl ? parseNumber(surfaceEl.value) : null;
    var doseEl = row.querySelector('input[id$="-dose"]');
    var doseAppliedEl = row.querySelector('input[id$="-dose_applied"]');
    var doseApplied = doseAppliedEl ? parseNumber(doseAppliedEl.value) : null;
    var dose = doseApplied !== null ? doseApplied : (doseEl ? parseNumber(doseEl.value) : null);
    if (dose === null || surface === null) return null;
    return Math.round(dose * surface * 100) / 100;
  }

  function refreshTotal(row) {
    var totalEl = row.querySelector('input[id$="-total_quantity"]');
    if (!totalEl || totalEl._manual) return;
    var total = computeTotal(row);
    totalEl.value = total === null ? '' : total;
  }

  function bindTotalRow(totalEl) {
    if (totalEl._totalBound || totalEl.id.indexOf('__prefix__') !== -1) return;
    totalEl._totalBound = true;
    var row = findRow(totalEl);
    if (!row) return;

    // Al cargar: si ya tiene un valor distinto al calculado, se considera cargado a mano
    var current = parseNumber(totalEl.value);
    totalEl._manual = current !== null && current !== computeTotal(row);

    totalEl.addEventListener('input', function () {
      totalEl._manual = totalEl.value.trim() !== '';
      if (!totalEl._manual) refreshTotal(row);
    });
    ['-dose', '-dose_applied'].forEach(function (suffix) {
      var el = row.querySelector('input[id$="' + suffix + '"]');
      if (el) el.addEventListener('input', function () { refreshTotal(row); });
    });
    refreshTotal(row);
  }

  function refreshAllTotals() {
    document.querySelectorAll('input[id*="inputworkorder_set"][id$="-total_quantity"]').forEach(function (el) {
      if (el.id.indexOf('__prefix__') !== -1) return;
      var row = findRow(el);
      if (row) refreshTotal(row);
    });
  }

  function bindSurface() {
    var surfaceEl = document.getElementById('id_surface');
    if (!surfaceEl || surfaceEl._totalBound) return;
    surfaceEl._totalBound = true;
    surfaceEl.addEventListener('input', refreshAllTotals);
  }

  function bindAll() {
    document.querySelectorAll('select[id*="inputworkorder_set"][id$="-input"]').forEach(bindSelect);
    document.querySelectorAll('select[id*="inputworkorder_set"][id$="-currency"]').forEach(bindCurrencySelect);
    document.querySelectorAll('input[id*="inputworkorder_set"][id$="-total_quantity"]').forEach(bindTotalRow);
    applyDefaultCurrencyToNewRows();
  }

  function init() {
    bindAll();
    bindSurface();
    prefillRatesOnLoad();
    fetchBaseCurrency();

    document.addEventListener('click', function (e) {
      if (e.target && (
        e.target.classList.contains('add-row') ||
        e.target.closest('.add-row')
      )) {
        setTimeout(bindAll, 300);
      }
    });
    document.addEventListener('formset:added', function () {
      setTimeout(bindAll, 100);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
