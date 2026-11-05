(function () {
  "use strict";
  var API = "/api/suggest";
  var $ = function (id) { return document.getElementById(id); };
  var lexicons = {};
  var polling = null;
  var DEFAULT_LEX = (document.currentScript && document.currentScript.getAttribute("data-lexicon")) || "";   // page d'un lexique créé par new_lexicon.py
  var MAIN_LEX = "";      // lexique principal du serveur (réponse de /lexicons, clé « defaut »)
  function currentLex() { return $("domain").value || DEFAULT_LEX || MAIN_LEX; }

  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "class") e.className = attrs[k];
      else if (k === "text") e.textContent = attrs[k];
      else if (typeof attrs[k] === "function") e[k] = attrs[k];
      else e.setAttribute(k, attrs[k]);
    });
    (kids || []).forEach(function (c) { if (c) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }

  var reviewer = false;   // session relecteur (cookie HttpOnly posé par le serveur)

  var simQ = [], simActive = 0, pvRunning = false;
  function simPump() {
    while (simActive < 3 && simQ.length && !pvRunning && !$("proposals").hidden) {
      simActive++;
      simQ.shift()(function () { simActive--; simPump(); });
    }
  }
  function api(method, path, body, raw) {
    var opt = { method: method, headers: {}, credentials: "same-origin" };
    if (body !== undefined) {
      if (raw) { opt.body = body; }
      else { opt.body = JSON.stringify(body); opt.headers["Content-Type"] = "application/json"; }
    }
    return fetch(API + path, opt).then(function (r) {
      return r.json().catch(function () { return { error: "réponse illisible" }; }).then(function (j) {
        if (r.status === 401 && (path.indexOf("/proposals") === 0 || path.indexOf("/prevalidate") === 0)) { setReviewer(false); }
        if (!r.ok) { var err = new Error(j.error || ("HTTP " + r.status)); err.status = r.status; throw err; }
        return j;
      });
    });
  }

  function say(text, isErr) {
    var m = $("msg");
    m.hidden = !text; m.textContent = text || ""; m.className = "msg" + (isErr ? " err" : "");
  }

  // ---------- espace relecteur (mot de passe) ----------
  function setReviewer(on) {
    reviewer = on;
    $("tab-review").hidden = !on; $("btn-logout").hidden = !on; $("btn-login").hidden = on;
    if (!on) { $("login-box").hidden = true; if (!$("pane-review").hidden) tab("submit"); }
  }
  $("btn-login").onclick = function () { $("login-box").hidden = !$("login-box").hidden; if (!$("login-box").hidden) $("pw").focus(); };
  function doLogin() {
    var pw = $("pw").value; if (!pw) return;
    $("login-msg").textContent = "";
    api("POST", "/login", { password: pw }).then(function () {
      $("pw").value = ""; $("login-box").hidden = true; setReviewer(true); refreshPending(); tab("review");
    }).catch(function (e) { $("login-msg").textContent = e.message; $("pw").value = ""; });
  }
  $("login-go").onclick = doLogin;
  $("pw").addEventListener("keydown", function (e) { if (e.key === "Enter") doLogin(); });
  $("btn-logout").onclick = function () { api("POST", "/logout", {}).then(function () { setReviewer(false); }); };

  // ---------- cartouche de la simulation (source du corpus) ----------
  function simSummary(sim) {
    if (sim.generique) return "simulation générique (aucun corpus configuré) — " + sim.n + " nouveau(x) soulignement(s) dans les définitions du lexique";
    return sim.n + " nouveau(x) soulignement(s) dans " + sim.seances + " " + (sim.unite || "document") + "(s)";
  }

  // ---------- corpus du lexique (relecteur) ----------
  function showCorpus(c) {
    var box = $("corpus-box");
    box.hidden = false;
    $("corpus-msg").textContent = c.message || "";
    var remote = c.configure === "sitemap" || c.configure === "urls", fixed = remote || c.configure === "dir";
    $("corpus-actions").hidden = fixed && !remote;
    $("corpus-file").parentNode.hidden = fixed;
    $("corpus-file").hidden = fixed;
    $("corpus-clear").hidden = c.type !== "upload";
    $("corpus-refresh").hidden = !remote;
    var info = $("corpus-info"), notes = c.notes || [];
    info.hidden = !notes.length; info.textContent = notes.join(" ; ");
  }
  function loadCorpus() {
    if (!reviewer) return;
    api("GET", "/corpus?domain=" + encodeURIComponent(currentLex())).then(showCorpus).catch(function (e) { $("corpus-msg").textContent = "indisponible (" + e.message + ")"; $("corpus-box").hidden = false; });
  }
  $("corpus-file").addEventListener("change", function () {
    var files = Array.prototype.slice.call(this.files || []).slice(0, 40), input = this;
    if (!files.length) return;
    Promise.all(files.map(function (f) { return f.text().then(function (t) { return { name: f.name, text: t }; }); })).then(function (items) {
      return api("POST", "/corpus", { domain: currentLex(), items: items });
    }).then(function (r) {
      showCorpus(r);
      var i = $("corpus-info"); i.hidden = false; i.textContent = r.documents + " texte(s) enregistré(s)" + (r.ignores ? ", " + r.ignores + " ignoré(s) (vides ou au-delà des plafonds)" : "") + ".";
    }).catch(function (e) { var i = $("corpus-info"); i.hidden = false; i.textContent = "Téléversement refusé : " + e.message; }).then(function () { input.value = ""; });
  });
  $("corpus-clear").onclick = function () { api("POST", "/corpus/clear", { domain: currentLex() }).then(showCorpus).catch(function (e) { alert(e.message); }); };
  $("corpus-refresh").onclick = function () { api("POST", "/corpus/refresh", { domain: currentLex() }).then(showCorpus).catch(function (e) { alert(e.message); }); };

  // ---------- onglets ----------
  function tab(name) {
    var rev = name === "review";
    $("pane-submit").hidden = rev; $("pane-review").hidden = !rev;
    $("tab-submit").classList.toggle("on", !rev); $("tab-review").classList.toggle("on", rev);
    $("tab-submit").setAttribute("aria-selected", String(!rev)); $("tab-review").setAttribute("aria-selected", String(rev));
    if (rev) { loadProposals(); loadCorpus(); }
  }
  $("tab-submit").onclick = function () { tab("submit"); };
  $("tab-review").onclick = function () { tab("review"); };
  var subStatus = "pending";
  function sub(st) {
    subStatus = st;
    $("sub-pending").classList.toggle("on", st === "pending"); $("sub-discarded").classList.toggle("on", st === "discarded");
    loadProposals();
  }
  $("sub-pending").onclick = function () { sub("pending"); };
  $("sub-discarded").onclick = function () { sub("discarded"); };

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
    hors_domaine: ["Écarté automatiquement", "ko"], non_pertinent: ["Écarté automatiquement", "ko"], ecarte: ["Écarté automatiquement", "ko"],
    limite: ["Limite atteinte", "ko"], attente: ["En cours…", ""], erreur: ["Erreur", "ko"]
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
    if (r.statut === "ecarte") kids.push(kv("Raison", r.raison), r.lien ? kv("Fiche proche", link(r.terme_proche, r.lien)) : null);
    if (r.statut === "limite") kids.push(kv("Détail", r.raison));
    if (r.statut === "alias") kids.push(kv("Alias de", link(r.terme, r.lien)), kv("Nature", r.nature));
    if (r.statut === "analyse") {
      kids.push(kv("Domaine", (r.domaine ? "oui — " : "non — ") + (r.raison_domaine || "")));
      kids.push(kv("À définir ?", (r.pertinent ? "oui — " : "non — ") + (r.raison_pertinent || "")));
      if (k !== "a_valider") { kids.push(el("p", { class: "conf", text: "Écarté : non ajouté à la file de validation." })); return el("div", { class: "res " + k }, kids); }
      if (r.origine) kids.push(kv("Développé", r.origine + (r.traduction ? " (" + r.traduction + ")" : "")));
      kids.push(kv("Définition", r.definition));
      kids.push(kv("Famille", r.famille ? famLabel(currentLex(), r.famille) : (r.famille_nouvelle ? "nouvelle : " + (r.famille_nouvelle_label || r.famille_nouvelle) : "")));
      kids.push(kv("Justification", r.famille_justification));
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

  var ORDER = { a_valider: 0, attente: 1, alias: 2, present: 3, ecarte: 4, non_pertinent: 4, hors_domaine: 4, limite: 5, erreur: 6 };
  function render(job) {
    var rs = job.resultats.slice().sort(function (a, b) { return (ORDER[kindOf(a)] || 9) - (ORDER[kindOf(b)] || 9); });
    var box = $("results"); box.textContent = "";
    rs.forEach(function (r) { box.appendChild(card(r)); });
    var c = {}; job.resultats.forEach(function (r) { var k = kindOf(r); c[k] = (c[k] || 0) + 1; });
    var parts = Object.keys(VERDICT).filter(function (k) { return c[k]; }).map(function (k) { return c[k] + " " + VERDICT[k][0].toLowerCase(); });
    var i = job.info || {};
    var nValid = c.a_valider || 0;
    var sent = $("sent");
    sent.hidden = !(nValid && job.etat !== "running");
    sent.textContent = nValid ? "Proposition envoyée pour validation : " + nValid + " terme" + (nValid > 1 ? "s" : "") + ". Elle sera relue avant d'être ajoutée au lexique." : "";
    var cost = (i.usd !== undefined && reviewer) ? " · coût " + i.usd.toFixed(4) + " $" + (i.secs ? " en " + i.secs + " s" : "") : "";
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
    say(""); $("go").disabled = true; $("results").textContent = ""; $("summary").textContent = ""; $("sent").hidden = true;
    var n = text.split(/[,;\n\r\t]+/).filter(function (s) { return s.trim(); }).length;
    $("progress").hidden = n <= 3; $("bar-fill").style.width = "3%"; $("progress-text").textContent = "Envoi…";
    api("POST", "/submit", { domain: currentLex(), text: text }).then(function (job) {
      history.replaceState(null, "", location.pathname + "?job=" + job.id);
      showJob(job);
    }).catch(function (e) { say(e.message, true); $("go").disabled = false; $("progress").hidden = true; });
  };

  // ---------- revue ----------
  function famKeys(domain) {       // familles existantes (alphabétique), « Divers » TOUJOURS en dernier
    var fams = (lexicons[domain] && lexicons[domain].familles) || {};
    var ks = Object.keys(fams).filter(function (f) { return f !== "divers"; });
    ks.sort(function (a, b) { return famLabel(domain, a).localeCompare(famLabel(domain, b), "fr"); });
    ks.push("divers");
    return ks;
  }
  function famSelect(domain, current, withNew) {
    var s = el("select", { "data-f": "famille" });
    var fams = (lexicons[domain] && lexicons[domain].familles) || {};
    if (!current) s.appendChild(el("option", { value: "", text: "— famille à choisir —" }));
    famKeys(domain).forEach(function (f) {
      var o = el("option", { value: f, text: famLabel(domain, f) + (f === "divers" ? "" : " — " + f) + " (" + (fams[f] || 0) + ")" });
      if (f === current) o.selected = true; s.appendChild(o);
    });
    if (withNew) s.appendChild(el("option", { value: "__new__", text: "nouvelle famille…" }));
    return s;
  }
  function famLabel(domain, slug) {
    if (slug === "divers") return "Divers";
    var l = lexicons[domain] && lexicons[domain].familles_labels;
    return (l && l[slug]) || slug;
  }
  function famText(domain, d) {
    if (d.famille) return famLabel(domain, d.famille) + " (" + d.famille + ")";
    if (d.famille_nouvelle) return "nouvelle : " + (d.famille_nouvelle_label || d.famille_nouvelle) + " (" + d.famille_nouvelle + ")";
    return "—";
  }
  function linkList(names, liens) {
    var s = el("span", {});
    (names || []).forEach(function (n, i) {
      if (i) s.appendChild(document.createTextNode(", "));
      var u = typeof n === "string" ? (liens || {})[n] : n.lien;
      s.appendChild(link(typeof n === "string" ? n : n.terme, u));
    });
    return s;
  }
  function kvNode(k, node) { return el("p", { class: "kv" }, [el("b", { text: k + " : " }), node]); }

  function checkPanel(rep, onForce, onOk) {
    var ul = el("ul", {}, rep.controles.map(function (c) {
      return el("li", { class: c.statut }, [document.createTextNode((c.statut === "ok" ? "✓ " : c.statut === "warn" ? "⚠ " : "✗ ") + c.nom + (c.detail ? " — " + c.detail : ""))]);
    }));
    var box = el("div", { class: "check" }, [el("b", { text: rep.ok ? (rep.avertissements.length ? "Contrôle de cohérence : avertissements" : "Contrôle de cohérence : OK") : "Contrôle de cohérence : BLOQUANT" }), ul]);
    if (!rep.ok && rep.incontournable) box.appendChild(el("p", { class: "msg err", text: "Validation impossible : corrigez la famille (menu « Famille » de la carte). Le forçage n'est pas permis pour ce contrôle." }));
    else if (!rep.ok) box.appendChild(el("button", { class: "btn ko", text: "Forcer la validation", onclick: onForce }));
    else if (rep.avertissements.length) box.appendChild(el("button", { class: "btn ok", text: "Valider malgré les avertissements", onclick: onOk }));
    else box.appendChild(el("button", { class: "btn ok", text: "Confirmer la validation", onclick: onOk }));
    return box;
  }

  // sigles : développés insérés automatiquement + nouveaux sigles (hors term_expansions.py) avec leur développé proposé
  function sigleNode(d) {
    var ins = d.sigles_inseres || [], neu = d.sigles || [];
    if (!ins.length && !neu.length) return null;
    var box = el("div", { class: "sigles" });
    if (ins.length) box.appendChild(kv("Sigles développés automatiquement", ins.join(", ")));
    neu.forEach(function (x) {
      var ok = x.coherent && x.developpe;
      box.appendChild(el("p", { class: "kv " + (ok ? "sig-new" : "sig-warn") }, [el("b", { text: "Nouveau sigle " + x.sigle + " : " }),
        document.createTextNode(ok ? x.developpe + (x.traduction_fr ? " — " + x.traduction_fr : "") + " (sera ajouté à term_expansions.py à la validation)"
          : "⚠ " + (x.developpe_modele ? "initiales de « " + x.developpe_modele + " » incohérentes avec " + x.sigle : "développé inconnu") + " : à développer à la main")]));
    });
    return box;
  }

  function proposalCard(p) {
    var d = p.data, disc = subStatus === "discarded", box = el("div", { class: "res " + (disc ? "ecarte" : "a_valider") });
    if (disc) {
      var h = el("h3", {}, [document.createTextNode(p.terme), el("span", { class: "badge ko", text: "écarté automatiquement" })]);
      var rb = el("button", { class: "btn", text: "Repêcher" });
      rb.onclick = function () {
        rb.disabled = true; rb.textContent = "Analyse…";
        api("POST", "/proposals/" + p.id + "/rescue", {}).then(loadProposals).catch(function (e) { alert(e.message); rb.disabled = false; rb.textContent = "Repêcher"; });
      };
      box.appendChild(h);
      box.appendChild(kv("Raison", d.raison || d.raison_pertinent || d.raison_domaine));
      if (d.definition) box.appendChild(kv("Définition proposée", d.definition));
      box.appendChild(el("div", { class: "actions" }, [rb]));
      return box;
    }
    var liens = p.liens || {};
    var title = el("h3", {}, [document.createTextNode(p.terme), el("span", { class: "badge ok", text: "à valider" }),
      el("span", { class: "conf", text: "confiance " + Math.round((d.confiance || 0) * 100) + " %" }),
      d.version ? el("span", { class: "badge", text: "v" + d.version }) : null, selBox(p.id)]);
    var retained = d.rattachements_retenus || d.rattachements || [];
    var boxes = [];
    var attach = null;
    if ((d.rattachements || []).length && (d.famille || d.famille_nouvelle)) {
      attach = el("div", { class: "attach" }, [el("p", { class: "kv" }, [el("b", { text: "Fiches à rattacher à cette famille" }), el("span", { class: "hint", text: " (sans famille aujourd'hui ; cochées = rattachées à la validation)" })])]);
      d.rattachements.forEach(function (n, i) {
        var cb = el("input", { type: "checkbox", id: "att-" + p.id + "-" + i, value: n });
        cb.checked = retained.indexOf(n) >= 0; boxes.push(cb);
        attach.appendChild(el("label", { class: "chk", for: "att-" + p.id + "-" + i }, [cb, document.createTextNode(" "), link(n, liens[n])]));
      });
    }
    // menu « Famille » sur la carte : changement immédiat (aucun appel au modèle)
    var famMsg = el("p", { class: "msg err", hidden: "" });
    var famSel = famSelect(p.domaine, d.famille, true);
    famSel.setAttribute("data-card-fam", "1"); famSel.id = "fam-" + p.id;
    if (!d.famille && d.famille_nouvelle) famSel.value = "__new__";
    var newBox = el("div", { class: "newfam", hidden: "" }, [
      el("label", { text: "Libellé de la nouvelle famille" }), el("input", { type: "text", "data-nf": "label", value: d.famille_nouvelle_label || "" }),
      el("label", { text: "Justification (obligatoire)" }), el("input", { type: "text", "data-nf": "just", value: d.famille_justification || "" }),
      el("label", { class: "chk" }, [el("input", { type: "checkbox", "data-nf": "accord" }), document.createTextNode(" J'accepte cette famille (même avec moins de 2 rattachements)")]),
      el("div", { class: "actions" }, [el("button", { class: "btn small", "data-nf": "save", text: "Enregistrer la famille" })])]);
    newBox.querySelector('[data-nf="accord"]').checked = !!d.famille_accord;
    if (!d.famille && d.famille_nouvelle) newBox.hidden = false;
    function saveFam(data) {
      famMsg.hidden = true; famSel.disabled = true;
      api("POST", "/proposals/" + p.id + "/edit", { data: data }).then(loadProposals).catch(function (e) {
        famMsg.hidden = false; famMsg.textContent = "Famille non modifiée : " + e.message; famSel.disabled = false;
      });
    }
    famSel.onchange = function () {
      if (famSel.value === "__new__") { newBox.hidden = false; return; }
      newBox.hidden = true;
      if (famSel.value) saveFam({ famille: famSel.value });
    };
    newBox.querySelector('[data-nf="save"]').onclick = function () {
      var lab = newBox.querySelector('[data-nf="label"]').value.trim();
      if (!lab) { famMsg.hidden = false; famMsg.textContent = "Donnez un libellé à la nouvelle famille."; return; }
      saveFam({ famille_nouvelle: lab, famille_nouvelle_label: lab, famille_justification: newBox.querySelector('[data-nf="just"]').value,
                famille_accord: newBox.querySelector('[data-nf="accord"]').checked });
    };
    // ── règles de qualité : forme de base, variantes d'appel (cases), fiche existante, soulignements simulés ──
    var qual = el("div", { class: "qual" });
    if (d.forme_base_proposee) {
      var bUse = el("button", { class: "btn small", text: "Utiliser « " + d.forme_base_proposee + " » comme terme" });
      bUse.onclick = function () {
        bUse.disabled = true;
        api("POST", "/proposals/" + p.id + "/edit", { term: d.forme_base_proposee, data: {} }).then(loadProposals).catch(function (e) { alert(e.message); bUse.disabled = false; });
      };
      qual.appendChild(el("div", { class: "kv warn" }, [el("b", { text: "Forme de base : " }),
        document.createTextNode("⚠ « " + p.terme + " » → « " + d.forme_base_proposee + " » (" + (d.forme_base_motif || "accents / singulier") + ") "), bUse]));
    }
    var vlist = (d.variantes || []).filter(function (v) { return v && v.forme; });
    var simLine = el("div", { class: "kv sim", id: "sim-" + p.id }, [el("b", { text: "Soulignements simulés : " }), document.createTextNode("calcul…")]);
    function showSim(rep) {
      simLine.textContent = "";
      var cls = rep.statut === "ko" ? "ko" : rep.statut === "warn" ? "warn" : "ok";
      simLine.className = "kv sim " + cls;
      simLine.appendChild(el("b", { text: "Soulignements simulés : " }));
      simLine.appendChild(document.createTextNode((cls === "ok" ? "✓ " : cls === "warn" ? "⚠ " : "✗ BLOQUANT — ") + (rep.simulation && rep.simulation.disponible === false ? rep.detail : (rep.simulation ? simSummary(rep.simulation) : rep.detail))));
      if (rep.simulation && rep.simulation.generique) simLine.appendChild(el("span", { class: "pill gen", text: "générique", title: "Aucun corpus configuré : simulation sur les définitions du lexique, les homographes français courants et les règles de casse et d'unités." }));
      if (cls === "ko") simLine.appendChild(el("p", { class: "msg err", text: rep.detail }));
      var ex = (rep.simulation && rep.simulation.exemples) || [];
      if (ex.length) simLine.appendChild(el("ul", { class: "ex" }, ex.map(function (e) { return el("li", {}, [el("span", { class: "hint", text: e.seance + " : " }), document.createTextNode(e.texte)]); })));
    }
    function runSim() {
      simQ.push(function (done) {                        // file d'attente : 3 simulations à la fois, jamais pendant une pré-validation
        api("POST", "/proposals/" + p.id + "/simulate", {}).then(showSim)
          .catch(function (e) { simLine.textContent = "Soulignements simulés : indisponible (" + e.message + ")"; }).then(done, done);
      });
      simPump();
    }
    if (vlist.length) {
      var vbox = el("div", { class: "variants" }, [el("p", { class: "kv" }, [el("b", { text: "Variantes d'appel proposées" }), el("span", { class: "hint", text: " (cochées = ajoutées à la fiche ; décochez celles qui souligneraient à tort)" })])]);
      vlist.forEach(function (v, i) {
        var cb = el("input", { type: "checkbox", id: "var-" + p.id + "-" + i, value: v.forme });
        cb.checked = v.coche !== false;
        cb.onchange = function () {
          var keep = Array.prototype.slice.call(vbox.querySelectorAll("input[type=checkbox]")).filter(function (c) { return c.checked; }).map(function (c) { return c.value; });
          api("POST", "/proposals/" + p.id + "/edit", { data: { variantes_cochees: keep } }).then(runSim).catch(function (e) { alert(e.message); });
        };
        vbox.appendChild(el("label", { class: "chk", for: "var-" + p.id + "-" + i }, [cb, document.createTextNode(" " + v.forme + " "), el("span", { class: "badge", text: v.type })]));
      });
      if ((d.variantes_ecartees || []).length) vbox.appendChild(el("p", { class: "hint", text: "Écartées automatiquement : " + d.variantes_ecartees.map(function (x) { return x.forme + " (" + x.raison + ")"; }).join(" ; ") }));
      qual.appendChild(vbox);
    }
    if ((d.contexte_requis || []).length || d.homographe_courant) {
      qual.appendChild(kv("Contexte requis", ((d.contexte_requis || []).join(", ") || "(aucun mot fourni)") + (d.homographe_courant ? "  — homographe courant : le terme ne sera souligné qu'avec l'un de ces mots à proximité" : "")));
    }
    qual.appendChild(simLine);
    (d.variante_candidats || []).slice(0, 2).forEach(function (c) {
      var bVar = el("button", { class: "btn small ok", text: "Ajouter comme variante de « " + c.fiche + " »" });
      var vm = el("p", { class: "msg err", hidden: "" });
      bVar.onclick = function () {
        if (!confirm("Ajouter « " + p.terme + " » (et ses variantes cochées) comme formes d'appel de la fiche « " + c.fiche + " » ? Aucune nouvelle fiche ne sera créée ; sauvegarde et contrôles automatiques.")) return;
        bVar.disabled = true; bVar.textContent = "Ajout + rebuild…"; vm.hidden = true;
        api("POST", "/proposals/" + p.id + "/as-variant", { fiche: c.fiche }).then(function (r) {
          $("review-msg").textContent = "Ajouté comme variante de « " + r.fiche + " » : " + (r.variantes_ajoutees || []).join(", ") + ".";
          loadProposals();
        }).catch(function (e) { vm.hidden = false; vm.textContent = e.message; bVar.disabled = false; bVar.textContent = "Ajouter comme variante de « " + c.fiche + " »"; });
      };
      qual.appendChild(el("div", { class: "kv exist" }, [el("b", { text: "Fiche existante : " }), document.createTextNode("« " + p.terme + " » semble être une forme d'appel de "),
        link(c.fiche, liens[c.fiche]), document.createTextNode(" (" + c.raison + "). "), bVar, vm]));
    });
    setTimeout(runSim, 0);
    var famRow = el("div", { class: "famrow" }, [el("label", { for: "fam-" + p.id, text: "Famille" }), famSel, famMsg, newBox]);
    var view = el("div", {}, [
      d.origine ? kv("Développé", d.origine + (d.traduction ? " (" + d.traduction + ")" : "")) : null,
      kv("Définition", d.definition),
      sigleNode(d),
      kv("Famille proposée", famText(p.domaine, d)),
      kv("Justification", d.famille_justification),
      famRow,
      (d.voir_aussi || []).length ? kvNode("Voir aussi proposés", linkList(d.voir_aussi, liens)) : null,
      vlist.length ? null : kv("Synonymes", (d.synonymes || []).join(", ")),
      qual,
      (d.voisins_consultes || []).length ? kvNode("Fiches voisines consultées", linkList(d.voisins_consultes)) : null,
      attach
    ]);
    var edit = el("div", { class: "edit", hidden: "" }, [
      el("label", { text: "Terme" }), el("input", { type: "text", "data-f": "term", value: p.terme }),
      el("label", { text: "Définition" }), el("textarea", { rows: "4", "data-f": "definition" }),
      el("label", { text: "Famille" }), famSelect(p.domaine, d.famille, false),
      d.famille_nouvelle ? el("label", { text: "Libellé de la nouvelle famille" }) : null,
      d.famille_nouvelle ? el("input", { type: "text", "data-f": "famille_nouvelle_label", value: d.famille_nouvelle_label || "" }) : null,
      el("label", { text: "Voir aussi (fiches existantes, virgules)" }), el("input", { type: "text", "data-f": "voir_aussi", value: (d.voir_aussi || []).join(", ") }),
      el("label", { text: "Synonymes (virgules)" }), el("input", { type: "text", "data-f": "synonymes", value: (d.synonymes || []).join(", ") }),
      el("label", { text: "Contexte requis (mots déclencheurs, virgules : le terme n'est souligné que près d'un de ces mots)" }), el("input", { type: "text", "data-f": "contexte_requis", value: (d.contexte_requis || []).join(", ") }),
      el("label", { text: "Ajouter une variante d'appel (virgules ; refusée si < 3 lettres en minuscules ou mot grammatical)" }), el("input", { type: "text", "data-f": "variantes_ajout", value: "" })
    ]);
    edit.querySelector("textarea").value = d.definition || "";
    function checked() { return boxes.filter(function (b) { return b.checked; }).map(function (b) { return b.value; }); }
    function collect() {
      var data = {
        definition: edit.querySelector("textarea").value, famille: edit.querySelector("select").value,
        synonymes: edit.querySelector('[data-f="synonymes"]').value,
        contexte_requis: edit.querySelector('[data-f="contexte_requis"]').value,
        voir_aussi: edit.querySelector('[data-f="voir_aussi"]').value.split(",").map(function (s) { return s.trim(); }).filter(Boolean)
      };
      var lab = edit.querySelector('[data-f="famille_nouvelle_label"]'); if (lab) data.famille_nouvelle_label = lab.value;
      if (boxes.length) data.rattachements_retenus = checked();
      var va = edit.querySelector('[data-f="variantes_ajout"]').value.trim(); if (va) data.variantes_ajout = va;
      return { term: edit.querySelector('[data-f="term"]').value, data: data };
    }
    var bVal = el("button", { class: "btn ok", text: "Valider" });
    var bMod = el("button", { class: "btn", text: "Modifier" });
    var bRej = el("button", { class: "btn ko", text: "Rejeter" });
    var bChk = el("button", { class: "btn", text: "Contrôler" });
    var panel = el("div", {});
    // relance commentée + historique des versions
    var cmt = el("textarea", { rows: "3", id: "cmt-" + p.id, placeholder: "ex. mets-la dans la même famille que bord d'attaque, et ajoute bord de fuite en voir aussi" });
    var bRel = el("button", { class: "btn", text: "Relancer avec ce commentaire" });
    var relMsg = el("p", { class: "msg err", hidden: "" });
    var busy = function (b) { [bVal, bMod, bRej, bRel, bChk].forEach(function (x) { x.disabled = b; }); };
    bRel.onclick = function () {
      var c = cmt.value.trim();
      if (c.length < 3) { relMsg.hidden = false; relMsg.textContent = "Écrivez d'abord un commentaire pour le modèle."; return; }
      relMsg.hidden = true; busy(true); bRel.textContent = "Relance en cours…";
      api("POST", "/proposals/" + p.id + "/relaunch", { comment: c }).then(loadProposals).catch(function (e) {
        relMsg.hidden = false; relMsg.textContent = "Relance impossible : " + e.message; busy(false); bRel.textContent = "Relancer avec ce commentaire";
      });
    };
    var relBox = el("div", { class: "relance" }, [
      el("label", { for: "cmt-" + p.id, text: "Commentaire pour le modèle" }), cmt,
      el("div", { class: "actions" }, [bRel]), relMsg]);
    var vers = p.versions || [];
    var verBox = null;
    if (vers.length > 1) {
      verBox = el("div", { class: "versions" }, [el("p", { class: "kv" }, [el("b", { text: "Historique des versions : " })])]);
      vers.forEach(function (v) {
        var cur = v.v === d.version;
        var row = el("div", { class: "ver" + (cur ? " cur" : "") }, [
          el("span", { class: "badge" + (cur ? " ok" : ""), text: "v" + v.v + (cur ? " · affichée" : "") }),
          el("span", { class: "hint", title: v.commentaire || "", text: v.commentaire ? " « " + (v.commentaire.length > 80 ? v.commentaire.slice(0, 80) + "…" : v.commentaire) + " »" : " proposition initiale" })]);
        if (!cur) {
          var br = el("button", { class: "btn small", text: "Revenir à v" + v.v });
          br.onclick = function () {
            busy(true);
            api("POST", "/proposals/" + p.id + "/revert", { version: v.v }).then(loadProposals).catch(function (e) { alert(e.message); busy(false); });
          };
          row.appendChild(br);
        }
        verBox.appendChild(row);
      });
    }
    bMod.onclick = function () {
      if (edit.hidden) { edit.hidden = false; view.hidden = true; bMod.textContent = "Enregistrer"; return; }
      busy(true);
      api("POST", "/proposals/" + p.id + "/edit", collect()).then(loadProposals).catch(function (e) { alert(e.message); busy(false); });
    };
    bRej.onclick = function () {
      busy(true);
      api("POST", "/proposals/" + p.id + "/reject", {}).then(loadProposals).catch(function (e) { alert(e.message); busy(false); });
    };
    function doValidate(force) {
      bVal.textContent = "Ajout + rebuild…"; busy(true); panel.textContent = "";
      api("POST", "/validate", { ids: [p.id], force: !!force }).then(function (r) {
        var att = (r.rattaches || []).length ? " Rattaché à la famille : " + r.rattaches.map(function (a) { return a[0]; }).join(", ") + "." : "";
        $("review-msg").textContent = (r.valides.length ? "Ajouté : " + r.valides.join(", ") + "." : "") + att + (r.ignores.length ? " Ignoré : " + r.ignores.map(function (i) { return i.terme + " (" + i.raison + ")"; }).join(", ") : "");
        loadProposals();
      }).catch(function (e) { alert(e.message); busy(false); bVal.textContent = "Valider"; });
    }
    bChk.onclick = function () {       // contrôle de cohérence seul : n'écrit rien, aucun bouton de validation
      busy(true); bChk.textContent = "Contrôle…"; panel.textContent = "";
      var pre = !edit.hidden ? api("POST", "/proposals/" + p.id + "/edit", collect()) : Promise.resolve();
      pre.then(function () { return api("POST", "/proposals/" + p.id + "/check", {}); }).then(function (rep) {
        var pn = checkPanel(rep, null, null);
        Array.prototype.slice.call(pn.querySelectorAll("button")).forEach(function (b) { b.remove(); });
        panel.appendChild(pn);
        busy(false); bChk.textContent = "Contrôler";
      }).catch(function (e) { alert(e.message); busy(false); bChk.textContent = "Contrôler"; });
    };
    bVal.onclick = function () {
      busy(true); bVal.textContent = "Contrôle…"; panel.textContent = "";
      var pre = !edit.hidden ? api("POST", "/proposals/" + p.id + "/edit", collect())
        : boxes.length ? api("POST", "/proposals/" + p.id + "/edit", { data: { rattachements_retenus: checked() } }) : Promise.resolve();
      pre.then(function () { return api("POST", "/proposals/" + p.id + "/check", {}); }).then(function (rep) {
        var nAtt = boxes.length && edit.hidden ? checked().length : 0;
        if (rep.ok && !rep.avertissements.length && !nAtt) { doValidate(false); return; }
        panel.appendChild(checkPanel(rep, function () { doValidate(true); }, function () { doValidate(false); }));
        busy(false); bVal.textContent = "Valider";
      }).catch(function (e) { alert(e.message); busy(false); bVal.textContent = "Valider"; });
    };
    box.appendChild(title); box.appendChild(view); box.appendChild(edit); box.appendChild(relBox); if (verBox) box.appendChild(verBox);
    box.appendChild(panel);
    box.appendChild(el("div", { class: "actions" }, [bVal, bChk, bMod, bRej]));
    return box;
  }
  function loadProposals() {
    return api("GET", "/proposals?status=" + subStatus).then(function (r) {
      var box = $("proposals"); box.textContent = ""; simQ = [];
      if (!r.propositions.length) box.appendChild(el("p", { class: "hint", text: subStatus === "pending" ? "Aucune proposition en attente." : "Aucun terme écarté." }));
      r.propositions.forEach(function (p) { box.appendChild(proposalCard(p)); });
      if (subStatus === "pending") setPending(r.propositions.length); else { var c = $("discarded-count"); c.hidden = !r.propositions.length; c.textContent = r.propositions.length; }
      pvShow(); if (subStatus === "pending" && !$("pv-summary").firstChild) loadPvSummary();
    }).catch(function (e) { $("review-msg").textContent = e.message; });
  }
  function setPending(n) { var p = $("pending-count"); p.hidden = !n; p.textContent = n; }
  function refreshPending() { if (!reviewer) return; api("GET", "/proposals?status=pending").then(function (r) { setPending(r.propositions.length); }).catch(function () {}); }
  $("refresh").onclick = loadProposals;

  // ---------- pré-validation en lot (relecteur) ----------
  var selected = {};
  var pvTimer = null;
  var PV_FIELD = { terme: "Terme", definition: "Définition", famille: "Famille", voir_aussi: "Voir aussi", variantes: "Variantes retenues", contexte_requis: "Contexte requis" };
  function nSel() { return Object.keys(selected).length; }
  function updateSel() {
    var n = nSel(), b = $("pv-sel");
    b.disabled = !n || $("pv-all").disabled;
    b.textContent = n ? "Pré-valider la sélection (" + n + ")" : "Pré-valider la sélection";
  }
  function selBox(id) {
    var cb = el("input", { type: "checkbox", "aria-label": "Sélectionner pour la pré-validation" });
    cb.checked = !!selected[id];
    cb.onchange = function () { if (cb.checked) selected[id] = true; else delete selected[id]; updateSel(); };
    return el("label", { class: "sel" }, [cb, document.createTextNode(" sélection")]);
  }
  function pvMsg(text, isErr, ok) {
    var m = $("pv-msg");
    m.hidden = !text; m.textContent = text || ""; m.className = "msg" + (isErr ? " err" : (ok ? " ok" : ""));
  }
  function pvIdle() {
    pvRunning = false; simPump();
    $("pv-all").disabled = false; $("pv-progress").hidden = true; updateSel();
  }
  function eur(n) { return (n || 0).toFixed(4).replace(".", ",") + " $"; }
  function pct(c) { return c === null || c === undefined ? "" : " · confiance " + Math.round(c * 100) + " %"; }

  // diff lisible : mots (texte) ou éléments (listes) ; <del> retiré, <ins> ajouté
  function wordDiff(a, b) {
    var x = String(a || "").split(/(\s+)/).filter(Boolean), y = String(b || "").split(/(\s+)/).filter(Boolean);
    var n = x.length, m = y.length, L = [], i, j;
    for (i = 0; i <= n; i++) { L.push(new Array(m + 1).fill(0)); }
    for (i = n - 1; i >= 0; i--) for (j = m - 1; j >= 0; j--) L[i][j] = x[i] === y[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
    var out = document.createElement("span"); i = 0; j = 0;
    function put(tag, txt) {
      var last = out.lastChild;
      if (tag && last && last.nodeName.toLowerCase() === tag) { last.textContent += txt; return; }
      if (!tag && last && last.nodeType === 3) { last.textContent += txt; return; }
      out.appendChild(tag ? el(tag, { text: txt }) : document.createTextNode(txt));
    }
    while (i < n && j < m) {
      if (x[i] === y[j]) { put("", x[i]); i++; j++; }
      else if (L[i + 1][j] >= L[i][j + 1]) { put("del", x[i]); i++; }
      else { put("ins", y[j]); j++; }
    }
    while (i < n) put("del", x[i++]);
    while (j < m) put("ins", y[j++]);
    return out;
  }
  function listDiff(a, b) {
    var out = document.createElement("span"), first = true;
    function add(node) { if (!first) out.appendChild(document.createTextNode(", ")); first = false; out.appendChild(node); }
    (a || []).forEach(function (v) { add(b.indexOf(v) >= 0 ? document.createTextNode(v) : el("del", { text: v })); });
    (b || []).forEach(function (v) { if (a.indexOf(v) < 0) add(el("ins", { text: v })); });
    if (first) out.textContent = "—";
    return out;
  }
  function fixNode(f) {
    var body;
    if (Array.isArray(f.avant) || Array.isArray(f.apres)) body = listDiff(f.avant || [], f.apres || []);
    else if (f.champ === "famille") body = wordDiff(famLabel(currentLex(), f.avant) || "—", famLabel(currentLex(), f.apres) || "—");
    else body = wordDiff(f.avant, f.apres);
    var src = f.origine + (f.motif ? " — " + f.motif.slice(0, 170) : "");
    return el("div", { class: "pv-diff" }, [el("b", { text: (PV_FIELD[f.champ] || f.champ) + " " }), el("span", { class: "src", text: "(" + src + ")" }), el("br"), body]);
  }
  function avisNode(it) {
    if (!it.avis || !it.avis.length) return null;
    return el("p", { class: "pv-avis", text: it.avis.map(function (a) {
      return "Avis " + a.etape + " (" + a.modele + ") : " + a.verdict + ", " + Math.round(a.confiance * 100) + " % — " + a.raison; }).join("  |  ") });
  }
  function pvItem(it, st) {
    var term = it.terme + (it.terme_initial && it.terme_initial !== it.terme ? "" : "");
    var kids = [el("h4", {}, [document.createTextNode(term), it.terme_initial && it.terme_initial !== it.terme ? el("span", { class: "conf", text: "(proposé : « " + it.terme_initial + " »)" }) : null,
                               el("span", { class: "conf", text: pct(it.confiance).replace(/^ · /, "") })])];
    if (st === "douteuse" && it.question) kids.push(el("p", { class: "pv-q", text: it.question }));
    kids.push(el("p", { class: "pv-why", text: it.raison || "" }));
    (it.corrections || []).forEach(function (f) { kids.push(fixNode(f)); });
    var av = avisNode(it); if (av) kids.push(av);
    var box = el("div", { class: st === "douteuse" ? "res pv-doubt" : "pv-item" }, kids);
    if (st === "douteuse" || st === "a_rejeter") {
      var open = el("button", { class: "btn small", type: "button", text: "Relire la fiche" });
      var rej = el("button", { class: "btn small ko", type: "button", text: "Rejeter" });
      var holder = el("div", { class: "pv-open" });
      open.onclick = function () {
        open.disabled = true;
        api("GET", "/proposals?status=pending").then(function (r) {
          var p = r.propositions.filter(function (x) { return x.id === it.id; })[0];
          if (!p) { holder.textContent = "Proposition introuvable (déjà traitée ?)."; return; }
          holder.textContent = ""; holder.appendChild(proposalCard(p));
        }).catch(function (e) { holder.textContent = e.message; open.disabled = false; });
      };
      rej.onclick = function () {
        rej.disabled = true;
        api("POST", "/proposals/" + it.id + "/reject", {}).then(function () { loadPvSummary(); loadProposals(); }).catch(function (e) { alert(e.message); rej.disabled = false; });
      };
      box.appendChild(el("div", { class: "actions" }, [open, rej]));
      box.appendChild(holder);
    }
    return box;
  }
  function pvApply(ids, label) {
    if (!ids.length) return;
    pvMsg(""); pvRunning = true; $("pv-all").disabled = true; updateSel();
    $("pv-progress").hidden = false; $("pv-fill").style.width = "45%"; $("pv-ptext").textContent = "Validation de " + ids.length + " fiche(s) : sauvegarde, reconstruction, tests…";
    api("POST", "/prevalidate/apply", { domain: currentLex(), ids: ids }).then(function (r) { pvPoll(r.job, "apply"); })
      .catch(function (e) { pvMsg(e.message, true); pvIdle(); });
  }
  function group(st, title, items, actionBtn) {
    var d = el("details", { class: "pv-group " + st }, [el("summary", { text: title + " (" + items.length + ")" })]);
    if (actionBtn) d.appendChild(el("div", { class: "pv-item" }, [actionBtn]));
    items.forEach(function (it) { d.appendChild(pvItem(it, st)); });
    return d;
  }
  function renderSummary(s) {
    var box = $("pv-summary"); box.textContent = "";
    var c = s.comptes || {}, total = (c.prete || 0) + (c.corrigee_prete || 0) + (c.douteuse || 0) + (c.a_rejeter || 0);
    if (!s.job || !total) return;
    var G = s.groupes, nReady = (c.prete || 0) + (c.corrigee_prete || 0);
    var ids = function (arr) { return arr.map(function (x) { return x.id; }); };
    var head = el("div", { class: "card pv-sum" }, [
      el("h2", { class: "pv-title", text: "Résultat de la pré-validation" }),
      el("div", { class: "pv-chips" }, [
        el("span", { class: "chip prete", text: (c.prete || 0) + " prête" + ((c.prete || 0) > 1 ? "s" : "") }),
        el("span", { class: "chip corrigee_prete", text: (c.corrigee_prete || 0) + " corrigée" + ((c.corrigee_prete || 0) > 1 ? "s" : "") }),
        el("span", { class: "chip douteuse", text: (c.douteuse || 0) + " douteuse" + ((c.douteuse || 0) > 1 ? "s" : "") }),
        el("span", { class: "chip a_rejeter", text: (c.a_rejeter || 0) + " à rejeter" })]),
      el("p", { class: "pv-meta", text: "Coût " + eur(s.job.usd) + " · durée " + Math.round(s.job.secs || 0) + " s · " + (s.job.appels || 0) + " appel(s)"
        + (s.job.modeles && s.job.modeles.premier ? " · " + s.job.modeles.premier : "")
        + (s.job.deuxieme_avis ? " · 2e avis (" + s.job.modeles.second + ") sur " + s.job.deuxieme_avis + " cas" : "")
        + (s.modifiees_depuis ? " · " + s.modifiees_depuis + " modifiée(s) depuis : à re-pré-valider" : "") })]);
    var bVal = el("button", { class: "btn ok", type: "button", text: "Valider les " + nReady + " prêtes" + (c.corrigee_prete ? " (dont " + c.corrigee_prete + " corrigée" + (c.corrigee_prete > 1 ? "s" : "") + ")" : "") });
    bVal.disabled = !nReady;
    bVal.onclick = function () { pvApply(ids(G.prete).concat(ids(G.corrigee_prete))); };
    var bRej = el("button", { class: "btn ko", type: "button", text: "Rejeter les " + (c.a_rejeter || 0) + " à rejeter" });
    bRej.disabled = !c.a_rejeter;
    bRej.onclick = function () {
      if (!window.confirm("Rejeter " + c.a_rejeter + " proposition(s) classée(s) « à rejeter » ? Elles passeront dans les termes écartés (repêchage possible).")) return;
      bRej.disabled = true;
      api("POST", "/prevalidate/reject", { domain: currentLex(), ids: ids(G.a_rejeter) }).then(function (r) {
        pvMsg(r.rejetes.length + " proposition(s) rejetée(s).", false, true); loadPvSummary(); loadProposals();
      }).catch(function (e) { pvMsg(e.message, true); bRej.disabled = false; });
    };
    head.appendChild(el("div", { class: "pv-actions pv-sticky" }, [bVal, bRej]));
    var list = $("proposals"), tog = el("button", { class: "btn small", type: "button" });
    function togText() { tog.textContent = list.hidden ? "Afficher la file complète (" + s.pending_total + ")" : "Masquer la file complète"; }
    list.hidden = true; togText();
    tog.onclick = function () { list.hidden = !list.hidden; togText(); simPump(); };
    head.appendChild(el("div", { class: "row" }, [tog]));
    box.appendChild(head);
    if (G.douteuse.length) {                         // les douteuses d'abord : une carte avec la question posée
      box.appendChild(el("h3", { class: "pv-title", text: "À trancher : " + G.douteuse.length + " douteuse" + (G.douteuse.length > 1 ? "s" : "") }));
      G.douteuse.forEach(function (it) { box.appendChild(pvItem(it, "douteuse")); });
    }
    var bRej2 = el("button", { class: "btn small ko", type: "button", text: "Rejeter les " + (c.a_rejeter || 0) + " à rejeter" }); bRej2.onclick = function () { bRej.click(); };
    if (G.a_rejeter.length) box.appendChild(group("a_rejeter", "À rejeter", G.a_rejeter, bRej2));
    if (G.corrigee_prete.length) {
      var b2 = el("button", { class: "btn small ok", type: "button", text: "Valider ces " + G.corrigee_prete.length + " corrigées" });
      b2.onclick = function () { pvApply(ids(G.corrigee_prete)); };
      box.appendChild(group("corrigee_prete", "Corrigées-prêtes", G.corrigee_prete, b2));
    }
    if (G.prete.length) {
      var b3 = el("button", { class: "btn small ok", type: "button", text: "Valider ces " + G.prete.length + " prêtes" });
      b3.onclick = function () { pvApply(ids(G.prete)); };
      box.appendChild(group("prete", "Prêtes", G.prete, b3));
    }
  }
  function loadPvSummary() {
    if (!reviewer) return Promise.resolve();
    return api("GET", "/prevalidate/summary?domain=" + encodeURIComponent(currentLex())).then(renderSummary).catch(function () {});
  }
  function pvPoll(jid, kind) {
    api("GET", "/prevalidate/job/" + jid).then(function (j) {
      var i = j.info || {};
      if (kind === "prevalidate") {
        var frac = i.progress !== undefined ? i.progress : (j.total ? j.fait / j.total : 0);
        $("pv-fill").style.width = Math.max(3, Math.round(100 * frac)) + "%";
        $("pv-ptext").textContent = (i.etape || "") + " — " + j.total + " proposition(s)" + (i.usd ? " · " + eur(i.usd) : "") + " · " + Math.round(j.duree) + " s";
      } else { $("pv-ptext").textContent = i.etape || "Validation…"; }
      if (j.etat === "running") { clearTimeout(pvTimer); pvTimer = setTimeout(function () { pvPoll(jid, kind); }, 1500); return; }
      pvIdle();
      if (j.etat !== "done") { pvMsg("Échec : " + (i.erreur || "erreur inconnue"), true); loadPvSummary(); return; }
      if (kind === "apply") {
        var r = i.resultat || {};
        if (r.ok) pvMsg(r.valides.length + " fiche(s) ajoutée(s) en " + Math.round(r.secs || j.duree) + " s (une sauvegarde, une reconstruction, tests réussis)." + (r.ignorees && r.ignorees.length ? " Ignorée(s) : " + r.ignorees.map(function (x) { return x.terme + " (" + x.raison + ")"; }).join(" ; ") : ""), false, true);
        else pvMsg((r.restaure ? "Validation annulée, site restauré : " : "Rien n'a été validé : ") + (r.erreur || "erreur"), true);
        selected = {}; updateSel(); refreshPending(); loadProposals();
      } else { pvMsg(""); refreshPending(); loadProposals(); }
      loadPvSummary();
    }).catch(function (e) { pvMsg("Suivi interrompu : " + e.message, true); pvIdle(); });
  }
  function pvStart(ids) {
    pvMsg(""); $("pv-summary").textContent = ""; $("proposals").hidden = false; pvRunning = true;
    $("pv-all").disabled = true; updateSel();
    $("pv-progress").hidden = false; $("pv-fill").style.width = "3%"; $("pv-ptext").textContent = "Démarrage…";
    api("POST", "/prevalidate", { domain: currentLex(), ids: ids }).then(function (r) { pvPoll(r.job, "prevalidate"); })
      .catch(function (e) { pvMsg(e.message, true); pvIdle(); });
  }
  $("pv-all").onclick = function () { pvStart("all"); };
  $("pv-sel").onclick = function () { pvStart(Object.keys(selected).map(Number)); };
  function pvShow() { $("pv-box").hidden = !(reviewer && subStatus === "pending"); if ($("pv-box").hidden) { $("pv-summary").textContent = ""; $("proposals").hidden = false; } }

  // ---------- init ----------
  function init() {
    fetch(API + "/lexicons").then(function (r) { return r.json(); }).then(function (j) {
      var sel = $("domain"); sel.textContent = "";
      MAIN_LEX = j.defaut || "";
      j.lexiques.forEach(function (l) { lexicons[l.id] = l; sel.appendChild(el("option", { value: l.id, text: l.label })); });
      var d = new URLSearchParams(location.search).get("lexicon") || DEFAULT_LEX; if (d && lexicons[d]) sel.value = d;
    }).catch(function () { say("API indisponible.", true); });
    fetch(API + "/session", { credentials: "same-origin" }).then(function (r) { return r.json(); }).then(function (j) {
      setReviewer(!!j.relecteur); refreshPending();
      var job = new URLSearchParams(location.search).get("job");
      if (job) poll(job);
    }).catch(function () { setReviewer(false); });
  }
  init();
})();
