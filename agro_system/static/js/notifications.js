// Notificaciones: marcar como leídas sin recargar y actualizar el número de la campana.
(function () {
  'use strict';

  var menu = document.querySelector('[data-notif-read-url]');
  if (!menu) return;

  var csrf = menu.getAttribute('data-notif-csrf');
  var readUrlTemplate = menu.getAttribute('data-notif-read-url');   // .../notifications/0/read
  var readAllUrl = menu.getAttribute('data-notif-read-all-url');

  function readUrl(id) {
    return readUrlTemplate.replace('/0/read', '/' + id + '/read');
  }

  function post(url) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': csrf, 'X-Requested-With': 'XMLHttpRequest' },
    }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  function toggle(el, visible) {
    if (el) el.classList.toggle('d-none', !visible);
  }

  function updateCount(count) {
    document.querySelectorAll('.js-notif-badge').forEach(function (el) {
      el.textContent = count;
      toggle(el, count > 0);
    });
    document.querySelectorAll('.js-notif-header-count').forEach(function (el) {
      el.textContent = count > 0 ? ' (' + count + ')' : '';
    });
    document.querySelectorAll('.js-notif-badge-plain').forEach(function (el) {
      el.textContent = count;
    });
    document.querySelectorAll('.js-notif-read-all, .js-notif-read-all-form').forEach(function (el) {
      toggle(el, count > 0);
    });
  }

  // Deja una notificación (en la campana y/o en la página) con aspecto de leída
  function markElementsRead(elements) {
    elements.forEach(function (el) {
      el.classList.remove('geagro-notif-unread', 'js-notif-unread');
      el.querySelectorAll('.js-notif-dot, .js-notif-read-form').forEach(function (x) { x.remove(); });
      var state = el.querySelector('.js-notif-state');
      if (state) state.innerHTML = '<span class="badge rounded-pill bg-light text-dark border">Leída</span>';
    });
  }

  function markRead(id) {
    return post(readUrl(id)).then(function (data) {
      markElementsRead(document.querySelectorAll('[data-notif-id="' + id + '"]'));
      updateCount(data.unread_count);
    });
  }

  function markAllRead() {
    return post(readAllUrl).then(function (data) {
      markElementsRead(document.querySelectorAll('.js-notif-unread'));
      updateCount(data.unread_count);
    });
  }

  document.addEventListener('click', function (e) {
    // Click en una notificación no leída de la campana: se marca y después se abre la página
    var item = e.target.closest('a.notification-item.js-notif-unread[data-notif-id]');
    if (item) {
      e.preventDefault();
      var href = item.getAttribute('href');
      markRead(item.getAttribute('data-notif-id'))
        .catch(function () {})
        .then(function () { window.location.href = href; });
      return;
    }

    var readAllBtn = e.target.closest('.js-notif-read-all');
    if (readAllBtn) {
      e.preventDefault();
      e.stopPropagation();  // que no se cierre el menú de la campana
      markAllRead().catch(function () {});
    }
  });

  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (form.classList.contains('js-notif-read-form')) {
      e.preventDefault();
      var row = form.closest('[data-notif-id]');
      markRead(row.getAttribute('data-notif-id')).catch(function () { form.submit(); });
    } else if (form.classList.contains('js-notif-read-all-form')) {
      e.preventDefault();
      markAllRead().catch(function () { form.submit(); });
    }
  });
})();
