// Neon streaks: when a role finishes or sends off a task, a thin neon trail arcs from its building to Town Hall (Council).
// Tasteful by design: thin, short-lived (~2 s), soft glow, one color per role, at most MAX at once (extra ones wait in a short
// queue, the rest are dropped), off under prefers-reduced-motion unless turned on in Settings, toggle in Settings.
// Live: on load the newest entries replay; every few minutes data.js is re-checked with a conditional request (304 when
// unchanged) while the tab is visible, and new activity entries fire a streak plus a small toast.
City.initStreaks = () => {
const C = City, S = C.streaks = { MAX: 4, QUEUE: 6, LIFE: 2.2, active: [], queue: [], fired: 0, dropped: 0 };
const SEG = 64, RAD = 6, HALO = 4;
const headGeo = new THREE.SphereGeometry(0.7, 12, 8);
S.enabled = () => (!C.settings || C.settings.streaks !== false) && !(C.reducedMotion && C.reducedMotion() && !(C.settings && C.settings.streaks === true));
const originFor = roleId => {
  const r = C.roleById[roleId], L = r && C.LANDMARKS[r.building];
  if (!L || !C.HUB || r.building === 'townhall') return null;
  return L.center.clone().setY(Math.max(6, L.top * 0.85));
};
S.fire = (roleId, opts = {}) => {
  if (!S.enabled() && !opts.force) return false;
  const from = originFor(roleId); if (!from) return false;
  if (S.active.length >= S.MAX) { if (S.queue.length < S.QUEUE) { S.queue.push(roleId); return true; } S.dropped++; return false; }
  const to = C.HUB.clone(), mid = from.clone().lerp(to, 0.5), d = from.distanceTo(to);
  mid.y = Math.max(from.y, to.y) + 10 + d * 0.28;
  const curve = new THREE.QuadraticBezierCurve3(from, mid, to);
  const geo = new THREE.TubeGeometry(curve, SEG, 0.3, RAD, false), hgeo = new THREE.TubeGeometry(curve, SEG, 0.95, HALO, false);
  const col = new THREE.Color(C.roleById[roleId].color);
  const mk = (c, o) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: o, blending: THREE.AdditiveBlending, depthWrite: false, fog: false });
  const mat = mk(col.clone().multiplyScalar(1.05), 0.95), hmat = mk(col.clone(), 0.3);
  const mesh = new THREE.Mesh(geo, mat), halo = new THREE.Mesh(hgeo, hmat); mesh.frustumCulled = halo.frustumCulled = false; mesh.renderOrder = 5; halo.renderOrder = 4;
  const head = new THREE.Mesh(headGeo, mat); head.renderOrder = 6;
  geo.setDrawRange(0, 0); hgeo.setDrawRange(0, 0); C.scene.add(mesh, halo, head);
  S.active.push({ mesh, halo, head, curve, geo, hgeo, mat, hmat, t: 0 }); S.fired++;
  return true;
};
const kill = s => { C.scene.remove(s.mesh, s.halo, s.head); s.geo.dispose(); s.hgeo.dispose(); s.mat.dispose(); s.hmat.dispose(); };
S.clear = () => { S.active.forEach(kill); S.active.length = 0; S.queue.length = 0; };
C.onFrame(dt => {
  for (let i = S.active.length - 1; i >= 0; i--) {
    const s = S.active[i]; s.t += dt / S.LIFE;
    const head = Math.min(1, s.t / 0.6), tail = Math.max(0, (s.t - 0.35) / 0.65);   // head races ahead, tail follows and catches up
    const a = Math.floor(tail * SEG), b = Math.ceil(head * SEG);
    s.geo.setDrawRange(a * RAD * 6, Math.max(0, b - a) * RAD * 6); s.hgeo.setDrawRange(a * HALO * 6, Math.max(0, b - a) * HALO * 6);
    s.head.visible = head < 1; if (head < 1) s.curve.getPoint(head, s.head.position);
    const fade = s.t < 0.8 ? 1 : Math.max(0, (1 - s.t) / 0.2); s.mat.opacity = 0.95 * fade; s.hmat.opacity = 0.3 * fade;
    if (head >= 1 && !s.arrived) { s.arrived = true; C.hubPulse = Math.min(1.5, (C.hubPulse || 0) + 0.8); }
    if (s.t >= 1) { kill(s); S.active.splice(i, 1); if (S.queue.length) setTimeout(() => S.fire(S.queue.shift()), 250); }
  }
});

// Replay the newest entries on load, then a gentle reminder every 40 s (one recent entry), so the city looks alive.
const recent = () => C.DATA.activity.filter(a => originFor(a.role)).slice(0, 8);
setTimeout(() => recent().slice(0, 5).reverse().forEach((a, k) => setTimeout(() => S.fire(a.role), k * 900)), 2600);
let n = 0; setInterval(() => { const R = recent(); if (R.length && document.visibilityState === 'visible') S.fire(R[n++ % R.length].role); }, 40000);

// Live: re-check data.js (conditional request) every 3 minutes; new activity entries fire a streak and a toast.
const key = a => [a.date, a.session, a.role, a.action].join('|');
const seen = new Set(C.DATA.activity.map(key));
S.ingest = acts => {
  const fresh = (acts || []).filter(a => a && !seen.has(key(a)));
  fresh.reverse().forEach((a, k) => { seen.add(key(a)); setTimeout(() => { S.fire(a.role); C.toast && C.toast(`${(C.roleById[a.role] || {}).icon || '✨'} ${C.esc(a.action)}`, a.role); }, k * 900); });
  return fresh.length;
};
if (location.protocol !== 'file:') setInterval(async () => {
  if (document.visibilityState !== 'visible') return;
  try {
    const r = await fetch('data.js', { cache: 'no-cache' }); if (!r.ok) return;
    const txt = await r.text(), i = txt.indexOf('{'), j = txt.lastIndexOf('}');
    S.ingest(JSON.parse(txt.slice(i, j + 1)).activity);
  } catch (e) { /* offline or mid-deploy: try again next time */ }
}, 180000);
};
