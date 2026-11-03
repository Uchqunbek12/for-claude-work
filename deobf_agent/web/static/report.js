/* "Mutaxassis uchun" / "Oddiy tilda" almashtirgichi: faqat ko'rinish, server so'rovi yo'q.
   Bu fayl Web UI'da /static/report.js sifatida, saqlangan HTML hisobotda esa ichiga joylashtirilgan holda ishlaydi. */
(function () {
  function setView(simple) {
    document.body.classList.toggle("view-simple", simple);
    document.querySelectorAll(".mode button").forEach(function (b) {
      b.setAttribute("aria-pressed", String((b.dataset.view === "simple") === simple));
    });
    // Oddiy tilda kod bo'laklari yig'iladi, mutaxassis uchun ochiq
    document.querySelectorAll("details.code-diff").forEach(function (d) { d.open = !simple; });
  }
  document.querySelectorAll(".mode button").forEach(function (btn) {
    btn.addEventListener("click", function () { setView(btn.dataset.view === "simple"); });
  });
  setView(false);
})();
