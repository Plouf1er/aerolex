// demo_chrome.js — pilote Chrome headless (protocole CDP, aucun module externe) pour scripts/test_demo_site.py
// usage : node scripts/demo_chrome.js <base-url> <mot-de-passe-relecteur> <chrome> <lexique>      -> JSON sur stdout
const { spawn } = require('child_process');
const os = require('os'), fs = require('fs'), path = require('path');
const [base, pw, chromeBin, lex] = process.argv.slice(2);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const port = 9400 + Math.floor(Math.random() * 400);
const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'alx-demo-chrome-'));
const chrome = spawn(chromeBin, ['--headless=new', '--remote-debugging-port=' + port, '--user-data-dir=' + prof, '--no-first-run', '--disable-gpu', '--no-sandbox', 'about:blank'], { stdio: 'ignore' });
(async () => {
  let tab;
  for (let i = 0; i < 50; i++) { try { tab = await (await fetch('http://127.0.0.1:' + port + '/json/new?about:blank', { method: 'PUT' })).json(); break; } catch (e) { await sleep(300); } }
  const ws = new WebSocket(tab.webSocketDebuggerUrl); await new Promise(r => ws.onopen = r);
  let id = 0; const pend = {}; const errors = [];
  ws.onmessage = m => {
    const d = JSON.parse(m.data);
    if (d.id && pend[d.id]) { pend[d.id](d); delete pend[d.id]; }
    else if (d.method === 'Runtime.exceptionThrown') errors.push('exception: ' + (d.params.exceptionDetails.exception && d.params.exceptionDetails.exception.description || d.params.exceptionDetails.text));
    else if (d.method === 'Runtime.consoleAPICalled' && d.params.type === 'error') errors.push('console.error: ' + d.params.args.map(a => a.value || a.description).join(' '));
    else if (d.method === 'Log.entryAdded' && d.params.entry.level === 'error' && !/favicon/.test(d.params.entry.url || '')) errors.push('log: ' + d.params.entry.text + ' ' + (d.params.entry.url || ''));
  };
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async expr => { const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }); if (r.result && r.result.exceptionDetails) return { __error: (r.result.exceptionDetails.exception || {}).description || r.result.exceptionDetails.text }; return r.result && r.result.result ? r.result.result.value : r; };
  const waitFor = async (expr, ms = 12000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await ev(expr)) return true; await sleep(200); } return false; };
  await send('Page.enable'); await send('Runtime.enable'); await send('Log.enable');
  const out = {};

  // 1. page du mini-site : soulignements
  await send('Page.navigate', { url: base + '/index.html' });
  out.site_ready = await waitFor("!!(window.AeroLex && window.AeroLex.config && document.querySelector('.glos'))");
  await sleep(500);
  out.site = await ev(`(() => {
    const zone = e => { const z = e.closest('h1,a,button,code,.cookie-banner,[data-aerolex-skip],nav,main'); return z ? (z.id || z.tagName.toLowerCase() + (z.className ? '.' + z.className : '')) : '?'; };
    const sp = [...document.querySelectorAll('.glos')].map(e => ({ term: e.getAttribute('data-term'), text: e.textContent, in: e.closest('p') ? e.closest('p').id : zone(e), zone: zone(e) }));
    return { version: window.AeroLex.version, config: window.AeroLex.config, termUrl: window.AeroLex.termUrl('safran'),
             spans: sp, inSkipped: sp.filter(s => document.querySelector('.glos[data-term="' + s.term + '"]') && [...document.querySelectorAll('h1 .glos, a .glos, button .glos, code .glos, .cookie-banner .glos, [data-aerolex-skip] .glos')].length).length,
             skippedCount: document.querySelectorAll('h1 .glos, a .glos, button .glos, code .glos, .cookie-banner .glos, [data-aerolex-skip] .glos').length,
             serverCalls: performance.getEntriesByType('resource').map(r => r.name.replace(location.origin, '')).filter(n => !/[.](css|js|ico)([?]|$)/.test(n)) };
  })()`);

  // 2. page « Suggérer » du lexique : relecteur -> file À valider -> simulation générique
  await send('Page.navigate', { url: base + '/lexique/' + lex + '/suggest.html' });
  await waitFor("!!document.getElementById('btn-login')");
  await ev("document.getElementById('btn-login').click()");
  await ev("(() => { const i = document.getElementById('pw'); i.value = " + JSON.stringify(pw) + "; document.getElementById('login-go').click(); })()");
  out.review_open = await waitFor("!document.getElementById('pane-review').hidden");
  out.corpus_msg_ok = await waitFor("(document.getElementById('corpus-msg')||{}).textContent && document.getElementById('corpus-msg').textContent.length > 3");
  out.sims_done = await waitFor("document.querySelectorAll('#proposals .sim').length > 0 && [...document.querySelectorAll('#proposals .sim')].every(e => !/calcul…/.test(e.textContent))", 25000);
  out.review = await ev(`({
    corpus_box_visible: !document.getElementById('corpus-box').hidden,
    corpus_msg: (document.getElementById('corpus-msg')||{}).textContent,
    upload_visible: !document.getElementById('corpus-file').hidden,
    n_proposals: document.querySelectorAll('#proposals .sim').length,
    sims: [...document.querySelectorAll('#proposals .sim')].map(e => e.textContent.slice(0, 260)),
    pills: document.querySelectorAll('#proposals .sim .pill.gen').length
  })`);
  out.errors = errors;
  console.log(JSON.stringify(out));
  ws.close(); chrome.kill(); process.exit(0);
})().catch(e => { console.log(JSON.stringify({ fatal: String(e && e.stack || e) })); chrome.kill(); process.exit(1); });
