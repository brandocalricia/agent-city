// Deep links: open a panel from the URL hash and keep the hash in sync, so a link can point straight at something.
// Forms: #market (any building id), #role=tutor, #overview, #dashboard (any id in City.viewLinks). Unknown hashes are ignored.
(() => {
const C = City, main = C.main;
const parse = h => { h = decodeURIComponent((h || '').replace(/^#/, '')).trim().toLowerCase(); if (!h) return null;
  let [k, v] = h.includes('=') ? h.split('=', 2) : ['building', h];
  if (k === 'building' && C.buildingAliases && C.buildingAliases[v]) v = C.buildingAliases[v];   // old anchors (#council, #cityhall) redirect
  if (k === 'building' && v === 'overview') return ['overview'];
  if (k === 'building' && (C.viewLinks || []).includes(v)) return ['view', v];
  if (k === 'building' && C.buildings[v] && C.LANDMARKS && C.LANDMARKS[v]) return ['building', v];
  if (k === 'role' && C.roleById[v]) return ['role', v];
  return null; };
const hashFor = (kind, arg) => kind === 'building' ? '#' + arg : kind === 'role' ? '#role=' + arg : (C.viewLinks || []).includes(kind) ? '#' + kind : '';
const setHash = h => { if (location.hash === h) return; history.replaceState(null, '', h || location.pathname + location.search); };
let applying = false;
C.openDeepLink = h => { const p = parse(h); if (!p) return false; applying = true;
  try { if (p[0] === 'overview') { C.closePanel(); C.fly('overview'); }
    else if (p[0] === 'building') { C.fly(p[1]); C.openPanel('building', p[1]); }
    else if (p[0] === 'view') C.openPanel(p[1]);
    else { const r = C.roleById[p[1]]; if (C.LANDMARKS[r.building]) C.fly(r.building); C.openPanel('role', p[1]); } }
  finally { applying = false; }
  if (p[0] === 'building' && location.hash !== '#' + p[1]) setHash('#' + p[1]);   // redirected/normalized anchor
  return true; };
C.main = () => {
  main();
  const open = C.openPanel, close = C.closePanel;
  C.openPanel = (kind, arg) => { open(kind, arg); if (!applying) setHash(hashFor(kind, arg)); };
  C.closePanel = () => { close(); if (!applying) setHash(''); };
  document.getElementById('panelClose').onclick = C.closePanel;
  addEventListener('hashchange', () => C.openDeepLink(location.hash));
  if (location.hash) setTimeout(() => C.openDeepLink(location.hash), 400);
};
})();
