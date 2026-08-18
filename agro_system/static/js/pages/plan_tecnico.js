document.addEventListener("DOMContentLoaded", function () {

  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".plan-detail-btn");
    if (!btn) return;

    const d = btn.dataset;

    document.getElementById("activityDetailLabel").textContent = d.service || "Orden de trabajo";
    document.getElementById("activityMeta").textContent        = d.code   || "";
    document.getElementById("moDateInit").textContent          = d.dateInit || "—";
    document.getElementById("moDateFin").textContent           = d.dateFin  || "—";
    document.getElementById("moStage").textContent             = d.stage   || "—";
    document.getElementById("moStaff").textContent             = d.staff   || "—";
    document.getElementById("moState").textContent             = d.state   || "—";

    const inputsRow = document.getElementById("moInputsRow");
    const inputsEl  = document.getElementById("moInputs");
    if (d.inputs && d.inputs.trim()) {
      inputsEl.textContent = d.inputs;
      inputsRow.style.display = "";
    } else {
      inputsRow.style.display = "none";
    }

    const detailRow = document.getElementById("moDetailRow");
    const detailEl  = document.getElementById("moDetail");
    if (d.detail && d.detail.trim()) {
      detailEl.textContent = d.detail;
      detailRow.style.display = "";
    } else {
      detailRow.style.display = "none";
    }

    bootstrap.Modal.getOrCreateInstance(
      document.getElementById("activityDetailModal")
    ).show();
  });

});
