(function () {
  'use strict';

  function getRow(fieldName) {
    var input = document.querySelector('[name="' + fieldName + '"]');
    if (!input) return null;
    var formRow = input.closest('.form-row');
    if (formRow) return formRow;
    var fieldDiv = input.closest('.field-' + fieldName);
    if (fieldDiv) return fieldDiv.parentElement || fieldDiv;
    return input.closest('tr') || input.parentElement;
  }

  function init() {
    var typeSelect = document.getElementById('id_type');
    if (!typeSelect) return;

    var destinationRow = getRow('destination_silo');
    var relatedSaleRow = getRow('related_sale');

    function update() {
      var val = typeSelect.value;
      if (destinationRow) destinationRow.style.display = (val === 'transfer') ? '' : 'none';
      if (relatedSaleRow) relatedSaleRow.style.display = (val === 'exit') ? '' : 'none';
    }

    // Bindear native + todas las instancias de jQuery (django.jQuery y window.jQuery pueden ser distintas)
    typeSelect.addEventListener('change', update);
    var seen = [];
    [window.django && window.django.jQuery, window.jQuery, window.$].forEach(function (jq) {
      if (jq && typeof jq === 'function' && seen.indexOf(jq) === -1) {
        seen.push(jq);
        jq(typeSelect).on('change', update);
      }
    });

    // Polling de fallback: Select2 actualiza typeSelect.value aunque no propague el evento
    var lastVal = typeSelect.value;
    setInterval(function () {
      if (typeSelect.value !== lastVal) {
        lastVal = typeSelect.value;
        update();
      }
    }, 150);

    update();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
