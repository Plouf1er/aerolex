(function () {
  "use strict";
  var API = "/api/suggest";
  var $ = function (id) { return document.getElementById(id); };
  var lexicons = {};
  var polling = null;

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

  function api(method, path, body, raw) {
    var opt = { method: method, headers: {}, credentials: "same-origin" };
    if (body !== undefined) {
      if (raw) { opt.body = body; }
      else { opt.body = JSON.stringify(body); opt.headers["Content-Type"] = "application/json"; }
    }
    return fetch(API + path, opt).then(function (r) {
      return r.json().catch(function () { return { error: "réponse illisible" }; }).then(function (j) {
        if (r.status === 401 && path.indexOf("/proposals") === 0) { setReviewer(false); }
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
      kids.push(kv("Famille", r.famille ? famLabel($("domain").value || "aero", r.famille) : (r.famille_nouvelle ? "nouvelle : " + (r.famille_nouvelle_label || r.famille_nouvelle) : "")));
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
    api("POST", "/submit", { domain: $("domain").value || "aero", text: text }).then(function (job) {
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
      d.version ? el("span", { class: "badge", text: "v" + d.version }) : null]);
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
    var famRow = el("div", { class: "famrow" }, [el("label", { for: "fam-" + p.id, text: "Famille" }), famSel, famMsg, newBox]);
    var view = el("div", {}, [
      d.origine ? kv("Développé", d.origine + (d.traduction ? " (" + d.traduction + ")" : "")) : null,
      kv("Définition", d.definition),
      sigleNode(d),
      kv("Famille proposée", famText(p.domaine, d)),
      kv("Justification", d.famille_justification),
      famRow,
      (d.voir_aussi || []).length ? kvNode("Voir aussi proposés", linkList(d.voir_aussi, liens)) : null,
      kv("Synonymes", (d.synonymes || []).join(", ")),
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
      el("label", { text: "Synonymes (virgules)" }), el("input", { type: "text", "data-f": "synonymes", value: (d.synonymes || []).join(", ") })
    ]);
    edit.querySelector("textarea").value = d.definition || "";
    function checked() { return boxes.filter(function (b) { return b.checked; }).map(function (b) { return b.value; }); }
    function collect() {
      var data = {
        definition: edit.querySelector("textarea").value, famille: edit.querySelector("select").value,
        synonymes: edit.querySelector('[data-f="synonymes"]').value,
        voir_aussi: edit.querySelector('[data-f="voir_aussi"]').value.split(",").map(function (s) { return s.trim(); }).filter(Boolean)
      };
      var lab = edit.querySelector('[data-f="famille_nouvelle_label"]'); if (lab) data.famille_nouvelle_label = lab.value;
      if (boxes.length) data.rattachements_retenus = checked();
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
      var box = $("proposals"); box.textContent = "";
      if (!r.propositions.length) box.appendChild(el("p", { class: "hint", text: subStatus === "pending" ? "Aucune proposition en attente." : "Aucun terme écarté." }));
      r.propositions.forEach(function (p) { box.appendChild(proposalCard(p)); });
      if (subStatus === "pending") setPending(r.propositions.length); else { var c = $("discarded-count"); c.hidden = !r.propositions.length; c.textContent = r.propositions.length; }
    }).catch(function (e) { $("review-msg").textContent = e.message; });
  }
  function setPending(n) { var p = $("pending-count"); p.hidden = !n; p.textContent = n; }
  function refreshPending() { if (!reviewer) return; api("GET", "/proposals?status=pending").then(function (r) { setPending(r.propositions.length); }).catch(function () {}); }
  $("refresh").onclick = loadProposals;

  // ---------- init ----------
  function init() {
    fetch(API + "/lexicons").then(function (r) { return r.json(); }).then(function (j) {
      var sel = $("domain"); sel.textContent = "";
      j.lexiques.forEach(function (l) { lexicons[l.id] = l; sel.appendChild(el("option", { value: l.id, text: l.label })); });
      var d = new URLSearchParams(location.search).get("lexicon"); if (d && lexicons[d]) sel.value = d;
    }).catch(function () { say("API indisponible.", true); });
    fetch(API + "/session", { credentials: "same-origin" }).then(function (r) { return r.json(); }).then(function (j) {
      setReviewer(!!j.relecteur); refreshPending();
      var job = new URLSearchParams(location.search).get("job");
      if (job) poll(job);
    }).catch(function () { setReviewer(false); });
  }
  init();
})();
