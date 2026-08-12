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

  // Al seleccionar un insumo: llena value_estimated (solo si vacío) y moneda/tasa.
  function fetchAndFillOnChange(selectEl) {
    var inputId = selectEl.value;
    if (!inputId) return;

    fetch(COST_URL + '?id=' + inputId)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var estimatedField = findValueEstimatedField(selectEl);
        if (estimatedField && !estimatedField.value && data.cost !== undefined) {
          estimatedField.value = data.cost;
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

    selectEl.addEventListener('change', function () { fetchAndFillOnChange(selectEl); });

    var seen = [];
    [window.django && window.django.jQuery, window.jQuery, window.$].forEach(function (jq) {
      if (jq && typeof jq === 'function' && seen.indexOf(jq) === -1) {
        seen.push(jq);
        jq(selectEl).on('change', function () { fetchAndFillOnChange(selectEl); });
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

  function bindAll() {
    document.querySelectorAll('select[id*="inputworkorder_set"][id$="-input"]').forEach(bindSelect);
    document.querySelectorAll('select[id*="inputworkorder_set"][id$="-currency"]').forEach(bindCurrencySelect);
    applyDefaultCurrencyToNewRows();
  }

  function init() {
    bindAll();
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
