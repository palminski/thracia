// Furigana toggle: flips a class on <html>; the readings are already in the page as <rt>.
(function () {
  var root = document.documentElement;
  var btn = document.querySelector(".furi-toggle");
  if (!btn) return;
  function sync() { btn.setAttribute("aria-pressed", root.classList.contains("furi") ? "true" : "false"); }
  btn.addEventListener("click", function () {
    var on = root.classList.toggle("furi");
    try { localStorage.setItem("furigana", on ? "1" : "0"); } catch (e) {}
    sync();
  });
  sync();
})();

// Click a speech bubble: it is highlighted and the panel shows its English translation and
// a vocabulary list. window.EN maps window number -> translation; words are
// <span class="w" data-g="id"> and window.GLOSS maps id -> [dictionary form, reading, English].
(function () {
  var panel = document.querySelector(".gloss");
  var backdrop = document.querySelector(".gloss-backdrop");
  var gloss = window.GLOSS, en = window.EN || {};
  if (!panel || !gloss) return;
  var body = panel.querySelector(".gloss-body");
  var hint = body.innerHTML;
  var wide = window.matchMedia("(min-width: 1300px)");
  var current = null;

  function surface(node) {           // text as written, without furigana
    var c = node.cloneNode(true);
    c.querySelectorAll("rt").forEach(function (rt) { rt.remove(); });
    return c.textContent;
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  function show(box) {
    if (current) current.classList.remove("on");
    current = box;
    box.classList.add("on");
    body.textContent = "";

    // speaker (shown in the mobile modal, where the bubble's own portrait is covered)
    var turn = box.closest(".turn"), who = turn && turn.querySelector(".who");
    if (who) {
      var head = el("div", "gloss-who");
      var img = document.createElement("img");
      img.src = who.querySelector("img").getAttribute("src");
      img.alt = "";
      head.appendChild(img);
      var name = el("span", "", who.querySelector("figcaption").textContent);
      name.lang = "ja";
      head.appendChild(name);
      body.appendChild(head);
    }

    var jp = el("p", "gloss-jp");
    jp.lang = "ja";
    box.querySelectorAll(".ln").forEach(function (ln, i) {
      if (i) jp.appendChild(document.createElement("br"));
      jp.appendChild(document.createTextNode(surface(ln)));
    });
    body.appendChild(jp);

    var text = en[box.dataset.n];
    body.appendChild(el("p", text ? "gloss-en" : "gloss-en none", text || "No translation yet for this line."));

    var study = window.STUDY, seen = {}, list = el("dl", "gloss-list");
    function entry(word, dict, reading, meaning, key) {
      if (seen[key]) return;
      seen[key] = true;
      var dt = el("dt");
      dt.lang = "ja";
      dt.appendChild(el("span", "gw", word));
      var info = [dict !== word ? dict : "", reading].filter(Boolean).join("・");
      if (info) dt.appendChild(el("span", "gr", info));
      list.appendChild(dt);
      list.appendChild(el("dd", meaning ? "" : "none", meaning || "no dictionary entry (name or sound?)"));
    }
    var notes = study && study.b[box.dataset.n];
    if (study) {
      // hand-picked words for this chapter: [[surface, key], ...] with key -> [form, reading, meaning]
      (notes ? notes[0] : []).forEach(function (w) {
        var v = study.v[w[1]];
        if (v) entry(w[0], v[0], v[1], v[2], w[1]);
      });
    } else {
      // chapters without hand-written notes fall back to the automatic dictionary lookup
      box.querySelectorAll(".w").forEach(function (span) {
        var g = gloss[span.dataset.g];
        if (g) { var word = surface(span); entry(word, g[0], g[1], g[2], word + "|" + span.dataset.g); }
      });
    }
    if (list.children.length) {
      body.appendChild(el("h3", "gloss-sub", "Vocabulary"));
      body.appendChild(list);
    }
    if (notes && notes[1].length) {
      body.appendChild(el("h3", "gloss-sub", "Grammar"));
      var gl = el("dl", "gloss-list grammar");
      notes[1].forEach(function (id) {
        var g = study.g[id];
        if (!g) return;
        var dt = el("dt");
        var a = el("a", "gw", g[0]);
        a.lang = "ja";
        a.href = "../grammar.html#" + encodeURIComponent(id);
        dt.appendChild(a);
        gl.appendChild(dt);
        gl.appendChild(el("dd", "", g[1]));
      });
      body.appendChild(gl);
    }
    if (!study) body.appendChild(el("p", "gloss-auto", "Vocabulary here is an automatic dictionary lookup; hand-written notes are not done for this chapter yet."));
    body.scrollTop = 0;
    panel.hidden = false;
    if (!wide.matches) { backdrop.hidden = false; document.body.classList.add("modal-open"); }
  }

  function close() {
    if (current) current.classList.remove("on");
    current = null;
    body.innerHTML = hint;
    backdrop.hidden = true;
    document.body.classList.remove("modal-open");
    panel.hidden = !wide.matches;      // desktop keeps the panel in the margin with its hint
  }

  document.addEventListener("click", function (e) {
    if (e.target.closest(".gloss")) return;
    var sel = window.getSelection();
    if (sel && !sel.isCollapsed) return;           // let people select and copy text
    var box = e.target.closest(".box");
    if (!box) return;
    if (box === current) close(); else show(box);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && current) close();
    if ((e.key === "Enter" || e.key === " ") && e.target.classList && e.target.classList.contains("box")) {
      e.preventDefault();
      show(e.target);
    }
  });
  panel.querySelector(".gloss-close").addEventListener("click", close);
  backdrop.addEventListener("click", close);
  wide.addEventListener("change", function () {
    if (current) { backdrop.hidden = wide.matches; document.body.classList.toggle("modal-open", !wide.matches); }
    else close();
  });
  close();
})();
