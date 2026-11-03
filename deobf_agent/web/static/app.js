/* Bosh sahifa mantig'i: namuna tanlash, fayl yuklash, kalitni tekshirish, yuborish holati. */
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var SAMPLES = {};
  try { SAMPLES = JSON.parse($("samples-data").textContent); } catch (e) { /* namunalar yo'q */ }

  if (window.hljs) { document.querySelectorAll("pre code").forEach(function (el) { window.hljs.highlightElement(el); }); }

  $("sample").addEventListener("change", function (e) {
    if (SAMPLES[e.target.value]) $("code").value = SAMPLES[e.target.value];
  });
  $("file").addEventListener("change", async function (e) {      // fayl matni maydonga yuklanadi
    var f = e.target.files[0];
    if (f) { $("code").value = await f.text(); e.target.value = ""; }
  });
  $("engine").addEventListener("change", function () {
    $("custom-wrap").hidden = $("engine").value !== "custom";
  });
  $("check").addEventListener("click", async function () {
    var model = $("engine").value === "custom" ? $("custom_model").value : $("engine").value;
    var body = new URLSearchParams({model: model});
    if ($("api_key")) body.append("api_key", $("api_key").value);
    $("status").className = "";
    $("status").textContent = "Tekshirilmoqda…";
    try {
      var resp = await fetch(document.body.dataset.checkUrl, {method: "POST", body: body});
      var data = await resp.json();
      $("status").className = data.ok ? "ok" : "bad";
      $("status").textContent = data.message;
    } catch (err) {
      $("status").className = "bad";
      $("status").textContent = "Server javob bermadi. Terminal oynasi ochiqmi?";
    }
  });
  $("form").addEventListener("submit", function () {
    $("submit").disabled = true;
    $("submit").textContent = "Ishlayapti…";
    $("status").className = "";
    $("status").textContent = $("engine").value === "offline" ? "Odatda bir necha soniya." : "Claude bilan 1–2 daqiqagacha cho'zilishi mumkin.";
  });
  var err = $("error");
  if (err) err.focus();          // xato ko'rinmay qolmasin (telefonda forma ostida qolishi mumkin)
})();
