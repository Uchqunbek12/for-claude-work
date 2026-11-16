/* Mavzu: standart — oq fon. Qorong'i fon tugma bilan yoqiladi va shu brauzerda eslab qolinadi. */
(function () {
  var KEY = "deobf-theme", root = document.documentElement;
  function load() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function save(v) { try { localStorage.setItem(KEY, v); } catch (e) { /* eslab qolinmaydi, lekin ishlayveradi */ } }
  root.dataset.theme = load() === "dark" ? "dark" : "light";        // sahifa chizilishidan oldin: miltillamaydi

  document.addEventListener("DOMContentLoaded", function () {
    var header = document.querySelector("header");
    if (!header) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "link";
    function label() {
      var dark = root.dataset.theme === "dark";
      btn.textContent = dark ? "Oq fon" : "Qorong'i fon";
      btn.setAttribute("aria-label", dark ? "Oq fonga o'tish" : "Qorong'i fonga o'tish");
    }
    btn.addEventListener("click", function () {
      var next = root.dataset.theme === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      save(next);
      label();
    });
    label();
    var tools = document.createElement("div");
    tools.className = "hdr-tools";
    var logout = header.querySelector("form");                       // "Chiqish" tugmasi bo'lsa, yoniga qo'yamiz
    tools.appendChild(btn);
    if (logout) { logout.style.marginLeft = ""; tools.appendChild(logout); }
    header.appendChild(tools);
  });
})();
