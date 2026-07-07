(function () {
  'use strict';

  var RATE_URL = '/input/api/exchange-rate/';

  // Moneda con la que se cargó la página (para distinguir cambios reales de eventos espurios de Select2)
  var initialCurrency = null;

  function getCurrencySelect() {
    return document.getElementById('id_currency');
  }

  function getRateField() {
    return document.getElementById('id_exchange_rate');
  }

  function fetchAndFillRate(currencyId) {
    var rateField = getRateField();
    if (!rateField || !currencyId) return;

    // Si la moneda no cambió respecto a la carga inicial y ya hay una tasa guardada, no sobreescribir.
    // Esto evita que el evento 'change' espurio de Select2 al inicializarse pise una tasa editada.
    if (currencyId === initialCurrency && rateField.value && parseFloat(rateField.value) !== 0) return;

    fetch(RATE_URL + '?currency_id=' + currencyId)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.rate !== null && data.rate !== undefined) {
          rateField.value = data.rate;
        } else {
          rateField.value = '';
        }
      })
      .catch(function () {});
  }

  function bindCurrencySelect() {
    var sel = getCurrencySelect();
    if (!sel || sel._rateBound) return;
    sel._rateBound = true;

    sel.addEventListener('change', function () {
      fetchAndFillRate(sel.value);
    });

    var seen = [];
    [window.django && window.django.jQuery, window.jQuery, window.$].forEach(function (jq) {
      if (jq && typeof jq === 'function' && seen.indexOf(jq) === -1) {
        seen.push(jq);
        jq(sel).on('change', function () { fetchAndFillRate(sel.value); });
      }
    });

    // Polling fallback para Select2
    var last = sel.value;
    setInterval(function () {
      if (sel.value !== last) {
        // El usuario cambió la moneda: actualizar initialCurrency para que la nueva selección
        // siempre traiga la tasa de la API, incluso si vuelve a la moneda original.
        initialCurrency = last;
        last = sel.value;
        fetchAndFillRate(sel.value);
      }
    }, 200);
  }

  function init() {
    var sel = getCurrencySelect();
    if (sel) initialCurrency = sel.value;
    bindCurrencySelect();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
