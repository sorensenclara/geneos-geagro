(function ($) {
  "use strict";

  function initCalendar() {
    var calendarEl = document.getElementById("calendar");

    if (!calendarEl) return;

    var calendar = new FullCalendar.Calendar(calendarEl, {
      plugins: ["bootstrap", "interaction", "dayGrid", "timeGrid"],
      themeSystem: "bootstrap",
      defaultView: "dayGridMonth",

      editable: false,
      droppable: false,
      selectable: false,

      header: {
        left: "prev,next today",
        center: "title",
        right: "dayGridMonth,timeGridWeek,timeGridDay"
      },

      buttonText: {
        today: "Hoy",
        month: "Mes",
        week: "Semana",
        day: "Día"
      },

      events: window.calendarEvents || []
    });

    calendar.render();
  }

  $(document).ready(function () {
    initCalendar();
  });

})(window.jQuery);