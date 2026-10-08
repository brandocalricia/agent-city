// Side panel: buildings, role agents, assistants, skills, plus registered views (dashboard, settings).
// Long panels get tabs automatically: "All" plus one tab per <h4> section.
(() => {
const C = City, { esc } = C;
const panel = document.getElementById('panel'), body = document.getElementById('panelBody');
const VIEWS = {
  building: id => { const b = C.buildings[id]; return b.panel() + (b.roles || (b.role ? [b.role] : [])).map(C.roleSection).join(''); },
  role: id => { const r = C.roleById[id], b = C.buildings[r.building];
    return `<h2>${r.icon} ${r.name}</h2><p class="sub">Works at the <a href="#" data-building="${b.id}">${b.icon} ${b.name}</a></p>` + C.roleSection(id); },
  agent: k => { const w = C.walkers[k], a = w.agent;
    return `<h2>🤖 ${esc(a.name)}${a.active ? '<span class="badge">primary</span>' : ''}</h2><p class="sub">${esc(w.role)}</p>${C.card('Right now', esc(w.status))}`
      + (a.description ? `<h4>About</h4><div class="card"><pre>${esc(a.description)}</pre></div>` : '')
      + `<h4>The crew</h4><p class="m">${C.ROLES.length} roles work around the city on your behalf. Click any glowing character to see what it has done.</p>`; },
  skill: k => { const s = C.DATA.skills[k];
    return `<h2>📖 ${esc(s.name)}</h2><p class="sub">${esc(s.description)}</p>${s.updated ? `<p class="m">Updated ${esc(s.updated)}</p>` : ''}`
      + (s.preview ? `<h4>SKILL.md preview</h4><div class="card"><pre>${esc(s.preview)}</pre></div>` : '')
      + C.card('Use it', '', `<pre>Use my ${esc(s.name)} skill on: </pre>${C.copyBtn(`Use my ${s.name} skill on: `)}`); },
};
C.registerView = (kind, fn) => { VIEWS[kind] = fn; };
// Tabs: wrap each <h4> and what follows it in a section; show a tab bar when there are 3+ sections.
const tabify = () => {
  const kids = [...body.children], heads = kids.filter(k => k.tagName === 'H4');
  if (heads.length < 3) return;
  const bar = document.createElement('div'); bar.className = 'tabs'; bar.setAttribute('role', 'tablist');
  const secs = []; let cur = null;
  for (const k of kids) {
    if (k.tagName === 'H4') { cur = document.createElement('section'); cur.className = 'psec'; k.before(cur); secs.push([k, cur]); }
    if (cur) cur.appendChild(k);
  }
  const first = secs[0][1]; first.before(bar);
  const show = i => { secs.forEach(([, s], k) => s.classList.toggle('hidden', i >= 0 && k !== i));
    bar.querySelectorAll('button').forEach((b, k) => { const on = k === i + 1; b.classList.toggle('on', on); b.setAttribute('aria-selected', on); }); };
  const add = (label, i) => { const b = document.createElement('button'); b.type = 'button'; b.setAttribute('role', 'tab'); b.textContent = label; b.onclick = () => { show(i); body.scrollTop = 0; }; bar.appendChild(b); };
  add('All', -1);
  secs.forEach(([h], i) => add(h.textContent.replace(/\s*\(\d+\).*$/, '').replace(/^[^\w]*(?=\w)/u, '').slice(0, 26) || 'Section', i));
  show(-1);
};
C.openKey = null;
C.openPanel = (kind, arg) => {
  C.openKey = [kind, arg]; body.innerHTML = VIEWS[kind](arg); tabify(); body.scrollTop = 0; panel.classList.add('open');
  panel.setAttribute('aria-hidden', 'false'); document.body.classList.add('panel-open');
  if (C.walk && C.walk.active) C.controlsPL.unlock();
  const h = body.querySelector('h2'); if (h) { h.id = 'panelTitle'; panel.setAttribute('aria-labelledby', 'panelTitle'); }
};
C.closePanel = () => { panel.classList.remove('open'); panel.setAttribute('aria-hidden', 'true'); document.body.classList.remove('panel-open'); C.openKey = null; };
document.getElementById('panelClose').onclick = C.closePanel;
body.addEventListener('click', e => {
  const t = e.target.closest('[data-copy],[data-skill],[data-role],[data-building],[data-view]'); if (!t) return;
  e.preventDefault();
  if (t.dataset.copy != null) { navigator.clipboard?.writeText(t.dataset.copy).then(() => { t.textContent = '✅ Copied'; setTimeout(() => (t.textContent = '📋 Copy'), 1500); }, () => { t.textContent = 'Select & copy manually'; }); }
  else if (t.dataset.skill != null) C.openPanel('skill', +t.dataset.skill);
  else if (t.dataset.role) { const r = C.roleById[t.dataset.role]; if (r && C.LANDMARKS[r.building]) C.fly(r.building); C.openPanel('role', t.dataset.role); }
  else if (t.dataset.building) { C.fly(t.dataset.building); C.openPanel('building', t.dataset.building); }
  else if (t.dataset.view) C.openPanel(t.dataset.view);
});
})();
