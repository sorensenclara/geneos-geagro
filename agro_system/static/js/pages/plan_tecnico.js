document.addEventListener("DOMContentLoaded", function () {

  function scrollToActiveStageInstant() {
    const active = document.querySelector(".accordion-collapse.show");
    if (!active) return;

    const yOffset = -110;
    const y = active.getBoundingClientRect().top + window.pageYOffset + yOffset;

    window.scrollTo(0, y);
  }

  function openActivityById(activityId) {
    const el = document.getElementById(activityId);
    if (!el) return;

    document.getElementById("activityDetailLabel").innerText = el.dataset.title || "Actividad";

    document.getElementById("activityMeta").innerText =
      (el.dataset.cat ? el.dataset.cat + " · " : "") +
      (el.dataset.priority ? "Prioridad " + el.dataset.priority : "");

    document.getElementById("activityWhat").innerText = el.dataset.what || "";
    document.getElementById("activityWhy").innerText = el.dataset.why || "";
    document.getElementById("activityInputs").innerText = el.dataset.inputs || "";
    document.getElementById("activityWhen").innerText = el.dataset.when || "";
    document.getElementById("activityRisks").innerText = el.dataset.risks || "";

    const modalEl = document.getElementById("activityDetailModal");
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }

  document.addEventListener("click", function (e) {
    const target = e.target.closest("[data-open-activity]");
    if (!target) return;

    e.preventDefault();

    const actId = target.dataset.openActivity;

    if (target.dataset.scroll === "1") {
      scrollToActiveStageInstant();
    }

    openActivityById(actId);
  });

});