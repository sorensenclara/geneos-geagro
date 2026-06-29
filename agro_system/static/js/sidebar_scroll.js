(function () {
    'use strict';

    var KEY = 'geagro-sidebar-scroll';

    function init() {
        var el = document.getElementById('jazzy-sidebar') || document.querySelector('.main-sidebar');
        if (!el) return;
        var nav = el.querySelector('.sidebar');
        if (!nav) return;

        function applyScroll() {
            var rect = nav.getBoundingClientRect();
            var h = window.innerHeight - rect.top;
            if (h < 100) h = window.innerHeight - 57; // fallback si top aún es 0
            nav.style.setProperty('height',     h + 'px',   'important');
            nav.style.setProperty('overflow-y', 'auto',     'important');
            nav.style.setProperty('overflow-x', 'hidden',   'important');
        }

        // primer intento inmediato
        applyScroll();
        // segundo intento tras primer frame (AdminLTE puede mover el DOM)
        requestAnimationFrame(applyScroll);
        // tercer intento tras 300 ms (animación de transición de AdminLTE)
        setTimeout(applyScroll, 300);

        window.addEventListener('resize', applyScroll);

        // restaurar posición guardada
        var saved = sessionStorage.getItem(KEY);
        if (saved) {
            nav.scrollTop = parseInt(saved, 10);
            requestAnimationFrame(function () { nav.scrollTop = parseInt(saved, 10); });
        }

        nav.addEventListener('scroll', function () {
            sessionStorage.setItem(KEY, nav.scrollTop);
        }, { passive: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
