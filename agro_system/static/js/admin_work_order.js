(function () {
  'use strict';

  function getContractorSelect() {
    return document.getElementById('id_contractor');
  }

  function getContractorCostRow() {
    // Django admin genera una clase .field-{nombre} en cada fila de campo
    return document.querySelector('.field-contractor_cost');
  }

  function toggleContractorCost() {
    var sel = getContractorSelect();
    var row = getContractorCostRow();
    if (!sel || !row) return;

    if (sel.value) {
      row.style.display = '';
    } else {
      row.style.display = 'none';
      var field = document.getElementById('id_contractor_cost');
      if (field) field.value = '';
    }
  }

  function init() {
    var sel = getContractorSelect();
    if (!sel) return;

    toggleContractorCost();

    sel.addEventListener('change', toggleContractorCost);

    var jq = (window.django && window.django.jQuery) || window.jQuery || window.$;
    if (jq && typeof jq === 'function') {
      jq(sel).on('change', toggleContractorCost);
    }

    var last = sel.value;
    setInterval(function () {
      if (sel.value !== last) {
        last = sel.value;
        toggleContractorCost();
      }
    }, 200);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
