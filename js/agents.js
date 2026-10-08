// Characters: assistants (from agent profiles) walk between landmarks; role agents work at their buildings
// and show their latest real action in a speech bubble (bubbles hide when you're far away).
City.initAgents = () => {
const C = City, { BASE, rnd, esc } = C, LM = C.LANDMARKS;
const COLORS = { black: 0x26262c, white: 0xe8e8ee, gray: 0x8a8f99, grey: 0x8a8f99, blue: 0x3b6fe0, green: 0x37b36b, red: 0xd9473f, orange: 0xf08a24, yellow: 0xf2c94c, purple: 0x8b5cf6, pink: 0xec6fb0, teal: 0x2bb3a8 };
C.makeFigure = (bodyColor, accent, scale = 1.35) => {
  const g = new THREE.Group();
  const bm = new THREE.MeshStandardMaterial({ color: bodyColor, roughness: 0.45, metalness: 0.25, flatShading: true, emissive: bodyColor, emissiveIntensity: 0.12 });
  const am = new THREE.MeshStandardMaterial({ color: accent, emissive: accent, emissiveIntensity: 2.2 });
  const add = (geo, m, x, y, z, parent = g) => { const o = new THREE.Mesh(geo, m); o.position.set(x, y, z); o.castShadow = true; parent.add(o); return o; };
  add(new THREE.CapsuleGeometry(0.42, 0.6, 3, 8), bm, 0, 1.2, 0);
  add(new THREE.IcosahedronGeometry(0.38, 1), bm, 0, 2.05, 0);
  add(new THREE.BoxGeometry(0.52, 0.13, 0.12), am, 0, 2.08, 0.31);
  add(new THREE.CylinderGeometry(0.03, 0.03, 0.35, 4), bm, 0, 2.55, 0);
  add(new THREE.SphereGeometry(0.08, 8, 6), am, 0, 2.75, 0);
  add(new THREE.BoxGeometry(0.5, 0.08, 0.2), am, 0, 1.35, 0.4);
  const limb = (x, y, len, r) => { const p = new THREE.Group(); p.position.set(x, y, 0); g.add(p); add(new THREE.CapsuleGeometry(r, len, 2, 6), bm, 0, -len / 2 - r, 0, p); return p; };
  const legs = [limb(-0.18, 0.8, 0.45, 0.13), limb(0.18, 0.8, 0.45, 0.13)], arms = [limb(-0.56, 1.55, 0.45, 0.1), limb(0.56, 1.55, 0.45, 0.1)];
  const ring = new THREE.Mesh(new THREE.RingGeometry(0.75, 0.95, 32), new THREE.MeshBasicMaterial({ color: new THREE.Color(accent).multiplyScalar(2), transparent: true, opacity: 0.85, side: THREE.DoubleSide }));
  ring.rotation.x = -Math.PI / 2; ring.position.y = 0.06; g.add(ring);
  g.scale.setScalar(scale); g.userData.parts = { legs, arms };
  return g;
};
const step = (fig, target, speed, dt, t, work = false) => {
  const d = target.clone().sub(fig.position); d.y = 0; const dist = d.length(), moving = dist > 0.05;
  if (moving) { fig.position.addScaledVector(d.normalize(), Math.min(dist, speed * dt));
    let diff = Math.atan2(d.x, d.z) - fig.rotation.y; diff = Math.atan2(Math.sin(diff), Math.cos(diff)); fig.rotation.y += diff * Math.min(1, dt * 8); }
  const { legs, arms } = fig.userData.parts, sw = moving ? Math.sin(t * 9) * 0.6 : 0;
  legs[0].rotation.x = sw; legs[1].rotation.x = -sw;
  arms[0].rotation.x = moving ? -sw * 0.8 : (work ? -1.2 + Math.sin(t * 7) * 0.25 : 0); arms[1].rotation.x = moving ? sw * 0.8 : (work ? -1.2 - Math.sin(t * 7) * 0.25 : 0);
  fig.position.y = BASE + (moving ? Math.abs(Math.sin(t * 9)) * 0.08 : Math.sin(t * 2) * 0.03);
  return !moving;
};

// Assistants walk Library <-> Office <-> City Hall via the plaza
C.walkers = [];
const IDS = ['library', 'office', 'townhall'];
const route = (a, b) => { const A = LM[a], Bm = LM[b], pts = [A.front, A.plaza];
  if (A.dir.dot(Bm.dir) < -0.5) pts.push(new THREE.Vector3(A.dir.z, 0, -A.dir.x).multiplyScalar(11));
  pts.push(Bm.plaza, Bm.front, Bm.door); return pts.map(p => p.clone().setY(BASE)); };
C.DATA.agents.forEach((a, k) => {
  const fig = C.makeFigure(COLORS[(a.color || '').toLowerCase()] ?? 0x2bb3a8, 0x5ee7ff);
  const role = a.title || (a.active ? 'Primary assistant' : 'Assistant'), start = IDS[k % IDS.length];
  fig.position.copy(LM[start].door).setY(BASE); fig.userData.kind = 'agent'; fig.userData.idx = k;
  C.scene.add(fig); C.interactive.push(fig);
  const tag = C.addLabel(fig, `<b>${esc(a.name)}</b><span>${esc(role)}</span>`, 3.1, 'agent-tag', () => C.openPanel('agent', k));
  C.walkers.push({ fig, tag, agent: a, role, at: start, path: [], wait: 1 + k * 2, status: 'at the ' + C.buildings[start].name });
});
const setStatus = (w, s) => { if (w.status === s) return; w.status = s; w.tag.element.querySelector('span').textContent = s; };

// Role agents at their buildings
C.roleChars = C.ROLES.map((r, k) => {
  const L = LM[r.building]; if (!L) return null;
  const side = new THREE.Vector3(L.dir.z, 0, -L.dir.x);
  const home = L.center.clone().addScaledVector(L.dir, 15.6).addScaledVector(side, r.building === 'library' ? 4 : -4.5).setY(BASE);
  const col = new THREE.Color(r.color);
  const fig = C.makeFigure(col.clone().multiplyScalar(0.45).getHex(), r.color, 1.3);
  fig.position.copy(home); fig.rotation.y = Math.atan2(L.dir.x, L.dir.z);
  fig.userData.kind = 'role'; fig.userData.id = r.id; C.scene.add(fig); C.interactive.push(fig);
  const has = C.activityFor(r.id).length || C.privateFor(r.id);
  const tag = C.addLabel(fig, `<span class="bubble">${esc(C.bubbleFor(r.id))}</span><span class="name" style="--rc:#${col.getHexString()}">${r.icon} ${r.name}</span>`, 3.3, 'role-tag far', () => C.openPanel('role', r.id));
  return { r, fig, tag, home, target: home.clone(), wait: rnd() * 4, work: !!has };
}).filter(Boolean);

const tmp = new THREE.Vector3();
C.onFrame((dt, t) => {
  for (const w of C.walkers) {
    if (w.path.length) { if (step(w.fig, w.path[0], 4.2, dt, t)) { w.path.shift(); if (!w.path.length) { setStatus(w, 'at the ' + C.buildings[w.at].name); w.wait = 5 + rnd() * 6; } } }
    else if ((w.wait -= dt) <= 0) { const next = IDS.filter(x => x !== w.at)[Math.floor(rnd() * (IDS.length - 1))]; w.path = route(w.at, next); w.at = next; setStatus(w, 'heading to the ' + C.buildings[next].name); }
    else step(w.fig, w.fig.position, 0, dt, t);
  }
  const cam = C.camera.position;
  for (const c of C.roleChars) {
    if (step(c.fig, c.target, 1.6, dt, t, c.work && c.target.distanceTo(c.home) < 0.3) && (c.wait -= dt) <= 0) {
      c.target.copy(c.home); if (rnd() < 0.5) c.target.add(tmp.set(rnd() * 5 - 2.5, 0, rnd() * 5 - 2.5)); c.wait = 2 + rnd() * 5;
    }
    const dd = cam.distanceTo(c.fig.position); c.tag.element.classList.toggle('far', dd > 85); c.tag.element.classList.toggle('hidden', dd > 170);
  }
  for (const w of C.walkers) w.tag.element.classList.toggle('hidden', cam.distanceTo(w.fig.position) > 220);
});
};
