// HUD: top bar, quick-jump search (/ or Ctrl/Cmd+K), dashboard (city overview), settings, shortcuts overlay,
// first-visit welcome (dismissible, remembered), and toasts. Settings persist in localStorage on this device only.
(() => {
const C = City, KEY = 'agentcity.settings';
const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } };
C.settings = Object.assign({ quality: 'auto', streaks: undefined, motion: 'auto', labels: true, minimap: true }, load());
C.saveSetting = (k, v) => { C.settings[k] = v; try { localStorage.setItem(KEY, JSON.stringify(C.settings)); } catch (e) { /* private mode */ } };
C.viewLinks = ['dashboard', 'settings'];
})();

City.initHUD = () => {
const C = City, { esc, plural } = C, D = C.DATA, $ = id => document.getElementById(id);
const T = D.treasury || {}, LT = T.lifetime || {};
const fmtK = n => n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? Math.round(n / 1e3) + 'k' : String(n || 0);
const usd = n => n == null ? 'n/a' : '$' + (n < 10 ? n.toFixed(2) : Math.round(n));

// ---------- Top bar ----------
const needs = () => C.needsYou().length + ((C.PRIV && C.PRIV.notices) || []).length;
$('dayTag').textContent = D.changelog[0] ? (D.changelog[0].title.split(' - ')[1] || '').split(':')[0] : '';
const active = C.ROLES.filter(r => C.activityFor(r.id).length).length;
$('chips').innerHTML = [
  `<button class="chip" data-go="townhall" title="Roles that have done real work">🧑‍🏭 ${active}/${C.ROLES.length} roles active</button>`,
  `<button class="chip ${needs() ? 'warn' : 'ok'}" data-go="noticeboard" title="Things waiting on you">📌 ${needs() ? needs() + ' need you' : 'All clear'}</button>`,
  LT.saved_tokens != null ? `<button class="chip" data-go="treasury" title="Estimated tokens saved, lifetime">🧾 ~${fmtK(LT.saved_tokens)} tokens saved</button>` : '',
  C.PRIV ? '<span class="chip" title="private.js loaded">🔒 local</span>' : '',
].join('');
$('chips').addEventListener('click', e => { const b = e.target.closest('[data-go]'); if (b) { C.fly(b.dataset.go); C.openPanel('building', b.dataset.go); } });
$('btnSearch').onclick = () => C.openSearch();
$('btnDash').onclick = () => C.openPanel('dashboard');
$('btnOverview').onclick = () => { C.closePanel(); C.fly('overview'); };
$('btnWalk').onclick = () => C.setWalk(!C.walk.active);
$('btnTime').onclick = () => C.cycleTime();
$('btnSettings').onclick = () => C.openPanel('settings');
$('btnKeys').onclick = () => C.toggleShortcuts();
if (C.isTouch) $('btnWalk').classList.add('hidden');

// ---------- Toasts ----------
C.toast = (html, roleId) => {
  const t = document.createElement('div'); t.className = 'toast glass'; t.setAttribute('role', 'status'); t.innerHTML = html;
  if (roleId && C.roleById[roleId]) t.style.borderLeftColor = '#' + new THREE.Color(C.roleById[roleId].color).getHexString();
  $('toasts').appendChild(t); while ($('toasts').children.length > 3) $('toasts').firstChild.remove();
  setTimeout(() => t.classList.add('out'), 4200); setTimeout(() => t.remove(), 4800);
};

// ---------- Search / quick jump ----------
const items = [
  { icon: '🏠', name: 'Dashboard', sub: 'city overview: numbers, news, verdicts, districts', run: () => C.openPanel('dashboard') },
  { icon: '🗺', name: 'Overview', sub: 'fly back to the skyline', run: () => { C.closePanel(); C.fly('overview'); } },
  { icon: '⚙️', name: 'Settings', sub: 'graphics, neon streaks, motion, labels', run: () => C.openPanel('settings') },
  { icon: '⌨️', name: 'Keyboard shortcuts', sub: 'all keys', run: () => C.toggleShortcuts(true) },
  ...C.buildingOrder.map(id => { const b = C.buildings[id]; return { icon: b.icon, name: b.name, sub: (b.sub ? b.sub() : '') + ' · #' + id, kind: 'building', id, run: () => { C.fly(id); C.openPanel('building', id); } }; }),
  ...C.ROLES.map(r => ({ icon: r.icon, name: r.name, sub: 'role · ' + r.job, kind: 'role', id: r.id, run: () => { if (C.LANDMARKS[r.building]) C.fly(r.building); C.openPanel('role', r.id); } })),
];
const pal = $('palette'), input = $('paletteInput'), list = $('paletteList'); let shown = [], sel = 0;
C.searchItems = q => { const words = q.toLowerCase().split(/\s+/).filter(Boolean);
  return items.map(it => { const hay = (it.name + ' ' + it.sub + ' ' + (it.id || '')).toLowerCase();
    if (!words.every(w => hay.includes(w))) return null;
    return [it, words.reduce((s, w) => s + (it.name.toLowerCase().startsWith(w) ? 3 : it.name.toLowerCase().includes(w) ? 2 : 0), 0)]; })
    .filter(Boolean).sort((a, b) => b[1] - a[1]).map(x => x[0]); };
const render = () => {
  shown = C.searchItems(input.value).slice(0, 9); sel = Math.min(sel, Math.max(0, shown.length - 1));
  list.innerHTML = shown.length ? shown.map((it, k) => `<li role="option" id="pi${k}" aria-selected="${k === sel}" class="${k === sel ? 'sel' : ''}" data-k="${k}"><span class="pi">${it.icon}</span><span><b>${esc(it.name)}</b><small>${esc(it.sub.slice(0, 90))}</small></span></li>`).join('')
    : '<li class="none">No match. Try a building, a role, or "settings".</li>';
  input.setAttribute('aria-activedescendant', shown.length ? 'pi' + sel : '');
};
C.openSearch = () => { pal.classList.add('open'); input.value = ''; sel = 0; render(); setTimeout(() => input.focus(), 0); };
const closeSearch = () => { pal.classList.remove('open'); input.blur(); };
const choose = k => { const it = shown[k]; if (!it) return; closeSearch(); it.run(); };
input.addEventListener('input', () => { sel = 0; render(); });
input.addEventListener('keydown', e => {
  if (e.key === 'ArrowDown') { e.preventDefault(); sel = Math.min(shown.length - 1, sel + 1); render(); }
  else if (e.key === 'ArrowUp') { e.preventDefault(); sel = Math.max(0, sel - 1); render(); }
  else if (e.key === 'Enter') { e.preventDefault(); choose(sel); }
  else if (e.key === 'Escape') { e.preventDefault(); closeSearch(); }
});
list.addEventListener('click', e => { const li = e.target.closest('li[data-k]'); if (li) choose(+li.dataset.k); });
pal.addEventListener('click', e => { if (e.target === pal) closeSearch(); });

// ---------- Shortcuts overlay + welcome ----------
C.toggleShortcuts = force => { const el = $('shortcuts'), on = force ?? !el.classList.contains('open'); el.classList.toggle('open', on); };
$('shortcuts').addEventListener('click', e => { if (e.target.id === 'shortcuts' || e.target.closest('.close')) C.toggleShortcuts(false); });
const onboard = $('onboard');
const hideWelcome = () => { onboard.classList.remove('open'); try { localStorage.setItem('agentcity.onboarded', '1'); } catch (e) { /* ignore */ } };
C.showWelcome = () => onboard.classList.add('open');
$('onboardOk').onclick = hideWelcome;
$('onboardTour').onclick = () => { hideWelcome(); C.openPanel('dashboard'); };
let seenWelcome = false; try { seenWelcome = localStorage.getItem('agentcity.onboarded') === '1'; } catch (e) { /* ignore */ }
if (!seenWelcome && !/[?&]nowelcome\b/.test(location.search)) setTimeout(C.showWelcome, 900);
C.closeOverlays = () => {
  let any = false;
  if (pal.classList.contains('open')) { closeSearch(); any = true; }
  if ($('shortcuts').classList.contains('open')) { C.toggleShortcuts(false); any = true; }
  if (onboard.classList.contains('open')) { hideWelcome(); any = true; }
  return any;
};

// ---------- Labels and minimap ----------
C.toggleLabels = on => { on = on ?? !C.settings.labels; C.saveSetting('labels', on); document.body.classList.toggle('no-labels', !on); };
document.body.classList.toggle('no-labels', !C.settings.labels);
document.body.classList.toggle('no-minimap', !C.settings.minimap);
if (C.settings.quality === 'high') C.setQuality('high'); else if (C.settings.quality === 'saver') C.setQuality('saver');

// ---------- Dashboard (city overview) ----------
const tile = (big, label, hint, go) => `<button class="tile" ${go ? `data-building="${go}"` : 'disabled'}><b>${big}</b><span>${label}</span>${hint ? `<small>${hint}</small>` : ''}</button>`;
C.registerView('dashboard', () => {
  const W = T.week, last = D.changelog[0], verdict = C.activityFor('council').find(a => a.verdict), n = needs();
  const news = (D.news || []).slice(0, 3);
  return `<h2>🏠 Dashboard</h2><p class="sub">Agent City at a glance. Tap any tile to fly there. Data as of ${esc(D.generatedAt)}.</p>`
    + `<div class="tiles">`
    + tile(n ? n : '✓', n ? 'need you' : 'All clear', 'Notice Board', 'noticeboard')
    + tile((D.totals || {}).sessions || 0, 'sessions run', `${(D.totals || {}).actions || 0} real actions logged`, 'townhall')
    + tile(`${active}/${C.ROLES.length}`, 'roles active', 'see the crew in Town Hall', 'townhall')
    + tile(LT.saved_tokens != null ? '~' + fmtK(LT.saved_tokens) : '–', 'tokens saved', LT.saved_usd != null ? `≈ ${usd(LT.saved_usd)} API value (est.)` : '', 'treasury')
    + (W ? tile(`${Math.round(W.est_used_pct)}%`, 'weekly limit used', `plan ${Math.round(W.pace_line_pct)}% by now (est.)`, 'treasury') : '')
    + tile((D.news || []).length, 'news stories', 'Newsroom digest', 'newsroom')
    + `</div>`
    + `<h4>Latest build</h4>` + (last ? C.card(esc(last.title), '', `<ul class="m">${last.items.slice(0, 4).map(i => `<li>${esc(i)}</li>`).join('')}</ul>`) : C.empty('No builds yet'))
    + `<h4>Latest verdict</h4>` + (verdict ? C.card(esc(verdict.question || verdict.action), `${esc(verdict.size || 'Quick')} Council · ${esc(verdict.verdict)}${verdict.confidence ? ' ' + verdict.confidence + '/10' : ''}`, `<div class="m"><a href="#" data-building="townhall">Open Town Hall (Council)</a></div>`) : C.empty('No verdicts yet'))
    + `<h4>News</h4>` + (news.length ? news.map(s => C.card(`<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>`, esc(s.why))).join('') : C.empty('No news yet'))
    + `<h4>Districts</h4><div class="districts">` + C.buildingOrder.map(id => { const b = C.buildings[id]; return `<button data-building="${id}">${b.icon} ${esc(b.name)}</button>`; }).join('') + `</div>`;
});

// ---------- Settings ----------
const opt = (k, v, label) => `<button data-set="${k}:${v}" class="${String(C.settings[k]) === String(v) ? 'on' : ''}">${label}</button>`;
C.registerView('settings', () => {
  const s = C.settings;
  return `<h2>⚙️ Settings</h2><p class="sub">Saved on this device only.</p>`
    + C.card('Graphics', `Auto starts in saver mode on phones and drops to saver if the frame rate stays low. Now: ${C.isHighQ() ? 'High' : 'Saver'}, ${C.fps || '…'} FPS.`, `<div class="seg">${opt('quality', 'auto', 'Auto')}${opt('quality', 'high', '✨ High')}${opt('quality', 'saver', '🔋 Saver')}</div>`)
    + C.card('Neon streaks', 'A thin light trail from a role\'s building to Town Hall whenever it finishes a task. Off by default if your system asks for reduced motion.', `<div class="seg">${opt('streaks', 'undefined', 'Auto')}${opt('streaks', 'true', 'On')}${opt('streaks', 'false', 'Off')}</div><button data-act="streak" class="copy">✨ Send a test streak</button>`)
    + C.card('Motion', 'Reduced makes camera moves instant and turns streaks off.', `<div class="seg">${opt('motion', 'auto', 'Auto')}${opt('motion', 'reduced', 'Reduced')}${opt('motion', 'full', 'Full')}</div>`)
    + C.card('Labels and minimap', '', `<div class="seg">${opt('labels', 'true', 'Labels on')}${opt('labels', 'false', 'Labels off')}</div><div class="seg">${opt('minimap', 'true', 'Minimap on')}${opt('minimap', 'false', 'Minimap off')}</div>`)
    + C.card('Welcome tips', '', `<button data-act="welcome">Show the welcome card again</button>`);
});
$('panelBody').addEventListener('click', e => {
  const b = e.target.closest('[data-set],[data-act]'); if (!b) return; e.preventDefault();
  if (b.dataset.act === 'streak') { const R = C.ROLES.filter(r => r.building !== 'townhall'); C.streaks && C.streaks.fire(R[Math.floor(Math.random() * R.length)].id, { force: true }); return; }
  if (b.dataset.act === 'welcome') { C.showWelcome(); return; }
  const [k, raw] = b.dataset.set.split(':'), v = raw === 'true' ? true : raw === 'false' ? false : raw === 'undefined' ? undefined : raw;
  C.saveSetting(k, v);
  if (k === 'quality') C.setQuality(v === 'saver' ? 'saver' : v === 'high' ? 'high' : (C.isTouch ? 'saver' : 'high'));
  if (k === 'labels') C.toggleLabels(v);
  if (k === 'minimap') document.body.classList.toggle('no-minimap', !v);
  if (k === 'streaks' && v === false && C.streaks) C.streaks.clear();
  C.openPanel('settings');
});
};
