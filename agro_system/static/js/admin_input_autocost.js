(function () {
  'use strict';

  var COST_URL = '/input/api/cost/';
  var RATE_URL = '/input/api/exchange-rate/';

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

  // Busca y completa la tasa para una moneda dada en el campo exchange_rate de la misma fila.
  // force=true ignora el guard (útil para cambios explícitos de moneda).
  function fetchAndFillRate(currencySelect, force) {
    var currencyId = currencySelect.value;
    var rateField = findExchangeRateField(currencySelect);
    if (!rateField || !currencyId) return;

    // Guard solo para el evento espurio de Select2 al inicializar (misma moneda + tasa ya seteada).
    if (!force && currencyId === currencySelect._initialCurrency && rateField.value && parseFloat(rateField.value) !== 0) return;

    fetch(RATE_URL + '?currency_id=' + currencyId)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.rate !== undefined && data.rate !== null) {
          rateField.value = data.rate;
        }
      })
      .catch(function () {});
  }

  // Prefill exchange_rate en rows existentes que tienen moneda pero tasa vacía.
  function prefillRatesOnLoad() {
    document.querySelectorAll('select[id*="inputworkorder_set"][id$="-currency"]').forEach(function (sel) {
      if (sel.id.indexOf('__prefix__') !== -1 || !sel.value) return;
      var rateField = findExchangeRateField(sel);
      if (rateField && !rateField.value) {
        fetchAndFillRate(sel, true);
      }
    });
  }

  // Al seleccionar un insumo: llena value_estimated (solo si vacío) y moneda/tasa
  // value_real NO se toca — solo el servidor lo actualiza al cambiar estado
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
    currencySelect._initialCurrency = currencySelect.value;

    currencySelect.addEventListener('change', function () {
      fetchAndFillRate(currencySelect, true);
    });

    var seen = [];
    [window.django && window.django.jQuery, window.jQuery, window.$].forEach(function (jq) {
      if (jq && typeof jq === 'function' && seen.indexOf(jq) === -1) {
        seen.push(jq);
        jq(currencySelect).on('change', function () { fetchAndFillRate(currencySelect, true); });
      }
    });

    var last = currencySelect.value;
    setInterval(function () {
      if (currencySelect.value !== last) {
        currencySelect._initialCurrency = last;
        last = currencySelect.value;
        fetchAndFillRate(currencySelect, true);
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
  }

  function init() {
    bindAll();
    prefillRatesOnLoad();

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
