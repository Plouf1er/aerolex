(function () {
  "use strict";
  var API = "/api/suggest";
  var $ = function (id) { return document.getElementById(id); };
  var TOKEN_KEY = "aerolex-suggest-token";
  var lexicons = {};
  var polling = null;

  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "class") e.className = attrs[k];
      else if (k === "text") e.textContent = attrs[k];
      else e.setAttribute(k, attrs[k]);
    });
    (kids || []).forEach(function (c) { if (c) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }

  // jeton : #t=... dans l'URL (une fois), puis localStorage
  (function () {
    var m = /[#&]t=([^&]+)/.exec(location.hash);
    if (m) {
      try { localStorage.setItem(TOKEN_KEY, decodeURIComponent(m[1])); } catch (e) {}
      history.replaceState(null, "", location.pathname + location.search);
    }
  })();
  function token() { try { return localStorage.getItem(TOKEN_KEY) || ""; } catch (e) { return ""; } }

  function api(method, path, body, raw) {
    var opt = { method: method, headers: { "X-Suggest-Token": token() } };
    if (body !== undefined) {
      if (raw) { opt.body = body; }
      else { opt.body = JSON.stringify(body); opt.headers["Content-Type"] = "application/json"; }
    }
    return fetch(API + path, opt).then(function (r) {
      return r.json().catch(function () { return { error: "réponse illisible" }; }).then(function (j) {
        if (r.status === 401) { $("auth").hidden = false; }
        if (!r.ok) { var err = new Error(j.error || ("HTTP " + r.status)); err.status = r.status; throw err; }
        return j;
      });
    });
  }

  function say(text, isErr) {
    var m = $("msg");
    m.hidden = !text; m.textContent = text || ""; m.className = "msg" + (isErr ? " err" : "");
  }

  // ---------- onglets ----------
  function tab(name) {
    var rev = name === "review";
    $("pane-submit").hidden = rev; $("pane-review").hidden = !rev;
    $("tab-submit").classList.toggle("on", !rev); $("tab-review").classList.toggle("on", rev);
    $("tab-submit").setAttribute("aria-selected", String(!rev)); $("tab-review").setAttribute("aria-selected", String(rev));
    if (rev) loadProposals();
  }
  $("tab-submit").onclick = function () { tab("submit"); };
  $("tab-review").onclick = function () { tab("review"); };
  $("token-save").onclick = function () {
    try { localStorage.setItem(TOKEN_KEY, $("token").value.trim()); } catch (e) {}
    $("auth").hidden = true; init();
  };

  // ---------- compteur de termes ----------
  function countTerms() {
    var n = $("terms").value.split(/[,;\n\r\t]+/).filter(function (s) { return s.trim(); }).length;
    $("count").textContent = n ? n + " terme" + (n > 1 ? "s" : "") + (n > 300 ? " (max 300)" : "") : "";
  }
  $("terms").addEventListener("input", countTerms);

  // ---------- upload ----------
  $("file").addEventListener("change", function () {
    var f = this.files[0];
    if (!f) return;
    say("");
    $("file-info").hidden = false; $("file-info").textContent = "Lecture de " + f.name + "…";
    f.arrayBuffer().then(function (buf) {
      return api("POST", "/parse?filename=" + encodeURIComponent(f.name), buf, true);
    }).then(function (r) {
      var cur = $("terms").value.trim();
      $("terms").value = (cur ? cur + "\n" : "") + r.terms.join("\n");
      countTerms();
      $("file-info").textContent = f.name + " : " + r.terms.length + " terme(s) " +
        (r.mode === "candidats" ? "candidat(s) extrait(s) du texte — relisez et retirez ce qui ne convient pas" : "lu(s) dans la liste") +
        (r.over_limit && r.over_limit.length ? " ; " + r.over_limit.length + " au-delà de la limite ignoré(s)" : "") + ".";
    }).catch(function (e) { $("file-info").textContent = "Fichier refusé : " + e.message; });
  });

  // ---------- résultats ----------
  var VERDICT = {
    present: ["Déjà présent", ""], alias: ["Alias probable", "warn"], a_valider: ["À valider", "ok"],
    hors_domaine: ["Hors domaine", "ko"], non_pertinent: ["Non pertinent", "ko"], attente: ["En cours…", ""], erreur: ["Erreur", "ko"]
  };
  function kindOf(r) {
    if (r.statut === "analyse") return r.verdict || "a_valider";
    return r.statut;
  }
  function kv(k, v) { return v ? el("p", { class: "kv" }, [el("b", { text: k + " : " }), v]) : null; }
  function link(text, href) { return href ? el("a", { href: href, text: text }) : document.createTextNode(text); }

  function card(r) {
    var k = kindOf(r), v = VERDICT[k] || [k, ""];
    var h = el("h3", {}, [document.createTextNode(r.terme), el("span", { class: "badge " + v[1], text: v[0] })]);
    if (r.cache) h.appendChild(el("span", { class: "badge", text: "cache" }));
    var kids = [h];
    if (r.statut === "present") kids.push(kv("Fiche", link(r.terme === r.terme ? r.terme : r.terme, r.lien)), kv("Terme du lexique", r.terme));
    if (r.statut === "present") { kids = [h, kv("Fiche existante", link("« " + r.terme + " » — ouvrir", r.lien))]; }
    if (r.statut === "alias") kids.push(kv("Alias de", link(r.terme, r.lien)), kv("Nature", r.nature));
    if (r.statut === "analyse") {
      kids.push(kv("Domaine", (r.domaine ? "oui — " : "non — ") + (r.raison_domaine || "")));
      kids.push(kv("À définir ?", (r.pertinent ? "oui — " : "non — ") + (r.raison_pertinent || "")));
      if (r.origine) kids.push(kv("Développé", r.origine + (r.traduction ? " (" + r.traduction + ")" : "")));
      kids.push(kv("Définition", r.definition));
      kids.push(kv("Famille", r.famille || (r.famille_nouvelle ? "nouvelle : " + r.famille_nouvelle : "")));
      kids.push(kv("Synonymes", (r.synonymes || []).join(", ")));
      kids.push(el("p", { class: "conf", text: "Confiance " + Math.round((r.confiance || 0) * 100) + " %" + (r.modele ? " · " + r.modele : "") }));
    }
    if (r.statut === "erreur") kids.push(kv("Détail", r.erreur));
    if (r.voisins && r.voisins.length) {
      var s = el("p", { class: "kv" }, [el("b", { text: "Termes voisins déjà présents : " })]);
      r.voisins.forEach(function (n, i) { if (i) s.appendChild(document.createTextNode(", ")); s.appendChild(link(n.terme, n.lien)); });
      kids.push(s);
    }
    return el("div", { class: "res " + k }, kids);
  }

  var ORDER = { a_valider: 0, attente: 1, alias: 2, present: 3, non_pertinent: 4, hors_domaine: 5, erreur: 6 };
  function render(job) {
    var rs = job.resultats.slice().sort(function (a, b) { return (ORDER[kindOf(a)] || 9) - (ORDER[kindOf(b)] || 9); });
    var box = $("results"); box.textContent = "";
    rs.forEach(function (r) { box.appendChild(card(r)); });
    var c = {}; job.resultats.forEach(function (r) { var k = kindOf(r); c[k] = (c[k] || 0) + 1; });
    var parts = Object.keys(VERDICT).filter(function (k) { return c[k]; }).map(function (k) { return c[k] + " " + VERDICT[k][0].toLowerCase(); });
    var i = job.info || {};
    var cost = (i.usd !== undefined) ? " · coût " + i.usd.toFixed(4) + " $" + (i.secs ? " en " + i.secs + " s" : "") : "";
    $("summary").textContent = parts.join(" · ") + cost + (i.doublons ? " · " + i.doublons + " doublon(s) fusionné(s)" : "");
  }

  function showJob(job) {
    render(job);
    var running = job.etat === "running";
    $("progress").hidden = !running && job.total <= 3;
    var pct = job.total ? Math.round(100 * job.fait / job.total) : 100;
    $("bar-fill").style.width = pct + "%";
    $("progress-text").textContent = job.fait + " / " + job.total + " terme(s) traité(s)" + (running ? "…" : " — terminé");
    $("job-link").href = location.pathname + "?job=" + job.id;
    if (running) { clearTimeout(polling); polling = setTimeout(function () { poll(job.id); }, 1500); }
    else { $("go").disabled = false; refreshPending(); }
  }
  function poll(id) {
    api("GET", "/job/" + id).then(showJob).catch(function (e) { say("Suivi interrompu : " + e.message, true); $("go").disabled = false; });
  }

  $("go").onclick = function () {
    var text = $("terms").value;
    if (!text.trim()) { say("Saisissez au moins un terme.", true); return; }
    say(""); $("go").disabled = true; $("results").textContent = ""; $("summary").textContent = "";
    var n = text.split(/[,;\n\r\t]+/).filter(function (s) { return s.trim(); }).length;
    $("progress").hidden = n <= 3; $("bar-fill").style.width = "3%"; $("progress-text").textContent = "Envoi…";
    api("POST", "/submit", { domain: $("domain").value, text: text }).then(function (job) {
      history.replaceState(null, "", location.pathname + "?job=" + job.id);
      showJob(job);
    }).catch(function (e) { say(e.message, true); $("go").disabled = false; $("progress").hidden = true; });
  };

  // ---------- revue ----------
  function famSelect(domain, current) {
    var s = el("select", { "data-f": "famille" });
    s.appendChild(el("option", { value: "", text: "— aucune —" }));
    var fams = (lexicons[domain] && lexicons[domain].familles) || {};
    Object.keys(fams).forEach(function (f) { var o = el("option", { value: f, text: f + " (" + fams[f] + ")" }); if (f === current) o.selected = true; s.appendChild(o); });
    return s;
  }
  function proposalCard(p) {
    var d = p.data, box = el("div", { class: "res a_valider" });
    var title = el("h3", {}, [document.createTextNode(p.terme), el("span", { class: "badge ok", text: "à valider" }),
      el("span", { class: "conf", text: "confiance " + Math.round((d.confiance || 0) * 100) + " %" })]);
    var view = el("div", {}, [
      d.origine ? kv("Développé", d.origine + (d.traduction ? " (" + d.traduction + ")" : "")) : null,
      kv("Définition", d.definition),
      kv("Famille", d.famille || (d.famille_nouvelle ? "nouvelle : " + d.famille_nouvelle : "—")),
      kv("Synonymes", (d.synonymes || []).join(", "))
    ]);
    var edit = el("div", { class: "edit", hidden: "" }, [
      el("label", { text: "Terme" }), el("input", { type: "text", "data-f": "term", value: p.terme }),
      el("label", { text: "Définition" }), el("textarea", { rows: "4", "data-f": "definition" }),
      el("label", { text: "Famille" }), famSelect(p.domaine, d.famille),
      el("label", { text: "Synonymes (virgules)" }), el("input", { type: "text", "data-f": "synonymes", value: (d.synonymes || []).join(", ") })
    ]);
    edit.querySelector("textarea").value = d.definition || "";
    function collect() {
      var o = { term: edit.querySelector('[data-f="term"]').value, data: {
        definition: edit.querySelector("textarea").value, famille: edit.querySelector("select").value,
        synonymes: edit.querySelector('[data-f="synonymes"]').value } };
      return o;
    }
    var bVal = el("button", { class: "btn ok", text: "Valider" });
    var bMod = el("button", { class: "btn", text: "Modifier" });
    var bRej = el("button", { class: "btn ko", text: "Rejeter" });
    var busy = function (b) { [bVal, bMod, bRej].forEach(function (x) { x.disabled = b; }); };
    bMod.onclick = function () {
      if (edit.hidden) { edit.hidden = false; view.hidden = true; bMod.textContent = "Enregistrer"; return; }
      busy(true);
      api("POST", "/proposals/" + p.id + "/edit", collect()).then(loadProposals).catch(function (e) { alert(e.message); busy(false); });
    };
    bRej.onclick = function () {
      busy(true);
      api("POST", "/proposals/" + p.id + "/reject", {}).then(loadProposals).catch(function (e) { alert(e.message); busy(false); });
    };
    bVal.onclick = function () {
      busy(true); bVal.textContent = "Ajout + rebuild…";
      var pre = edit.hidden ? Promise.resolve() : api("POST", "/proposals/" + p.id + "/edit", collect());
      pre.then(function () { return api("POST", "/validate", { ids: [p.id] }); }).then(function (r) {
        $("review-msg").textContent = (r.valides.length ? "Ajouté : " + r.valides.join(", ") : "") + (r.ignores.length ? " Ignoré : " + r.ignores.map(function (i) { return i.terme + " (" + i.raison + ")"; }).join(", ") : "");
        loadProposals();
      }).catch(function (e) { alert(e.message); busy(false); bVal.textContent = "Valider"; });
    };
    box.appendChild(title); box.appendChild(view); box.appendChild(edit);
    box.appendChild(el("div", { class: "actions" }, [bVal, bMod, bRej]));
    return box;
  }
  function loadProposals() {
    return api("GET", "/proposals?status=pending").then(function (r) {
      var box = $("proposals"); box.textContent = "";
      if (!r.propositions.length) box.appendChild(el("p", { class: "hint", text: "Aucune proposition en attente." }));
      r.propositions.forEach(function (p) { box.appendChild(proposalCard(p)); });
      setPending(r.propositions.length);
    }).catch(function (e) { $("review-msg").textContent = e.message; });
  }
  function setPending(n) { var p = $("pending-count"); p.hidden = !n; p.textContent = n; }
  function refreshPending() { api("GET", "/proposals?status=pending").then(function (r) { setPending(r.propositions.length); }).catch(function () {}); }
  $("refresh").onclick = loadProposals;

  // ---------- init ----------
  function init() {
    fetch(API + "/lexicons").then(function (r) { return r.json(); }).then(function (j) {
      var sel = $("domain"); sel.textContent = "";
      j.lexiques.forEach(function (l) { lexicons[l.id] = l; sel.appendChild(el("option", { value: l.id, text: l.label })); });
      var d = new URLSearchParams(location.search).get("lexicon"); if (d && lexicons[d]) sel.value = d;
    }).catch(function () { say("API indisponible.", true); });
    if (!token()) $("auth").hidden = false; else refreshPending();
    var job = new URLSearchParams(location.search).get("job");
    if (job && token()) poll(job);
  }
  init();
})();
