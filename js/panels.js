// Side panel: buildings, role agents, assistants, skills.
(() => {
const C = City, { esc } = C;
const panel = document.getElementById('panel'), body = document.getElementById('panelBody');
const VIEWS = {
  building: id => { const b = C.buildings[id]; return b.panel() + (b.role ? C.roleSection(b.role) : ''); },
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
C.openKey = null;
C.openPanel = (kind, arg) => { C.openKey = [kind, arg]; body.innerHTML = VIEWS[kind](arg); body.scrollTop = 0; panel.classList.add('open'); if (C.walk && C.walk.active) C.controlsPL.unlock(); };
C.closePanel = () => { panel.classList.remove('open'); C.openKey = null; };
document.getElementById('panelClose').onclick = C.closePanel;
body.addEventListener('click', e => {
  const t = e.target.closest('[data-copy],[data-skill],[data-role],[data-building]'); if (!t) return;
  e.preventDefault();
  if (t.dataset.copy != null) { navigator.clipboard?.writeText(t.dataset.copy).then(() => { t.textContent = '✅ Copied'; setTimeout(() => (t.textContent = '📋 Copy'), 1500); }, () => { t.textContent = 'Select & copy manually'; }); }
  else if (t.dataset.skill != null) C.openPanel('skill', +t.dataset.skill);
  else if (t.dataset.role) C.openPanel('role', t.dataset.role);
  else if (t.dataset.building) { C.fly(t.dataset.building); C.openPanel('building', t.dataset.building); }
});
})();
