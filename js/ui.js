// UI: HUD, camera controls (orbit + walk), fly-to, picking/hover, keyboard, quality, post-processing.
City.initUI = () => {
const C = City, L = C.lib, { esc, plural } = C, cam = C.camera, $ = id => document.getElementById(id);
const D = C.DATA, active = C.ROLES.filter(r => C.activityFor(r.id).length).length;
$('dayTag').textContent = D.changelog[0] ? (D.changelog[0].title.split(' - ')[1] || '').split(':')[0] : '';
$('chips').innerHTML = `<span>🤖 ${plural(D.agents.length, 'assistant')}</span><span>🧑‍🏭 ${active}/${C.ROLES.length} roles active</span><span>📚 ${plural(D.skills.length, 'skill')}</span><span>🛒 ${plural(D.finds.length, 'find')}</span>`
  + `<span title="Things waiting on you">📌 ${C.needsYou().length + ((C.PRIV && C.PRIV.notices) || []).length} need you</span>` + (C.PRIV ? '<span title="private.js loaded">🔒 local</span>' : '');
const sel = $('goto');
C.buildingOrder.forEach(id => { const b = C.buildings[id], o = document.createElement('option'); o.value = id; o.textContent = `${b.icon} ${b.name}`; sel.appendChild(o); });
sel.onchange = () => { if (sel.value) { C.fly(sel.value); C.openPanel('building', sel.value); } sel.value = ''; };

// Controls
C.orbit = new L.OrbitControls(cam, C.renderer.domElement);
C.orbit.target.copy(C.HOME.tgt); C.orbit.enableDamping = true; C.orbit.dampingFactor = 0.08;
C.orbit.maxPolarAngle = 1.45; C.orbit.minDistance = 8; C.orbit.maxDistance = 420;
C.controlsPL = new L.PointerLockControls(cam, document.body);
const walk = C.walk = { active: false, keys: {}, eye: 3.0 };
let tween = null;
C.flyTo = (pos, tgt) => { if (walk.active) setWalk(false, true); tween = { start: performance.now(), t: 0, p0: cam.position.clone(), t0: C.orbit.target.clone(), p1: pos, t1: tgt }; };
C.fly = id => {
  if (id === 'overview') return C.flyTo(C.HOME.pos.clone(), C.HOME.tgt.clone());
  const Lm = C.LANDMARKS[id], side = new THREE.Vector3(Lm.dir.z, 0, -Lm.dir.x);
  C.flyTo(Lm.center.clone().addScaledVector(Lm.dir, Lm.def.pos ? 18 : 50).addScaledVector(side, Lm.def.pos ? 6 : 16).setY(Lm.def.pos ? 9 : Math.max(22, Lm.top * 0.55)),
    Lm.center.clone().setY(Lm.def.pos ? 3 : Math.min(Lm.top * 0.45, 14)));
};
function setWalk(on, quiet) {
  walk.active = on; C.orbit.enabled = !on; tween = null;
  $('btnWalk').classList.toggle('on', on);
  $('walkhint').style.display = $('crosshair').style.display = on ? 'block' : 'none';
  if (on) { cam.position.set(0, walk.eye, 24); cam.lookAt(0, walk.eye, -40); C.closePanel(); C.controlsPL.lock(); }
  else { C.controlsPL.unlock(); if (!quiet) C.fly('overview'); }
}
C.renderer.domElement.addEventListener('click', () => { if (walk.active && !C.controlsPL.isLocked) C.controlsPL.lock(); });
$('btnWalk').onclick = () => setWalk(!walk.active);
$('btnOverview').onclick = () => C.fly('overview');
const help = $('help');
const toggleHelp = () => { const on = help.style.display === 'none'; help.style.display = on ? '' : 'none'; $('btnHelp').classList.toggle('on', on); };
$('btnHelp').onclick = toggleHelp;
$('btnTime').onclick = () => C.cycleTime();
let highQ = true;
const toggleQuality = () => {
  highQ = !highQ; C.bloom.enabled = highQ; C.sun.castShadow = highQ;
  C.renderer.setPixelRatio(highQ ? Math.min(devicePixelRatio, 1.5) : 1); onResize();
  $('btnQuality').classList.toggle('on', highQ); $('btnQuality').innerHTML = (highQ ? '✨ High' : '🔋 Saver') + ' <kbd>Q</kbd>';
};
$('btnQuality').onclick = toggleQuality;
C.isHighQ = () => highQ;
const keyed = Object.fromEntries(C.buildingOrder.filter(id => C.buildings[id].key).map(id => [C.buildings[id].key, id]));
addEventListener('keydown', e => {
  if (/INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
  walk.keys[e.code] = true;
  if (e.code === 'Tab') { e.preventDefault(); setWalk(!walk.active); }
  else if (e.code === 'KeyH') toggleHelp();
  else if (e.code === 'KeyQ') toggleQuality();
  else if (e.code === 'KeyT') C.cycleTime();
  else if (e.code === 'Escape') C.closePanel();
  else if (e.code === 'KeyE' && walk.active) { const u = pick(new THREE.Vector2(0, 0)); if (u) openHit(u); }
  else if (!walk.active && /^Digit\d$/.test(e.code)) { const n = +e.code.slice(5); if (n === 0) C.fly('overview'); else if (keyed[n]) C.fly(keyed[n]); }
});
addEventListener('keyup', e => { walk.keys[e.code] = false; });

// Picking
const ray = new THREE.Raycaster(), mouse = new THREE.Vector2(), tip = $('tip'); let moved = false, mxy = [0, 0], down = null;
function pick(ndc) {
  ray.setFromCamera(ndc, cam);
  for (const h of ray.intersectObjects(C.interactive, true)) { let o = h.object; while (o && !o.userData.kind) o = o.parent; if (o) return o.userData; }
  return null;
}
const hitLabel = u => {
  if (u.kind === 'landmark') { const b = C.buildings[u.id]; return `<b>${b.icon} ${b.name}</b> · click to open`; }
  if (u.kind === 'role') { const r = C.roleById[u.id]; return `<b>${r.icon} ${r.name}</b><br><span style="color:var(--mute)">${esc(C.bubbleFor(r.id))}</span>`; }
  if (u.kind === 'skill') return `<b>📖 ${esc(D.skills[u.idx].name)}</b>`;
  const w = C.walkers[u.idx]; return `<b>${esc(w.agent.name)}</b> · ${esc(w.role)}<br><span style="color:var(--mute)">${esc(w.status)}</span>`;
};
function openHit(u) { if (u.kind === 'landmark') C.openPanel('building', u.id); else if (u.kind === 'role') C.openPanel('role', u.id); else C.openPanel(u.kind, u.idx); }
const el = C.renderer.domElement;
el.addEventListener('pointermove', e => { mouse.set(e.clientX / innerWidth * 2 - 1, -e.clientY / innerHeight * 2 + 1); mxy = [e.clientX, e.clientY]; moved = true; });
el.addEventListener('pointerdown', e => { down = [e.clientX, e.clientY]; });
el.addEventListener('pointerup', e => { if (walk.active || !down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return; const u = pick(mouse); if (u) openHit(u); });

// Post-processing
C.composer = new L.EffectComposer(C.renderer);
C.composer.addPass(new L.RenderPass(C.scene, cam));
C.bloom = new L.UnrealBloomPass(new THREE.Vector2(innerWidth / 2, innerHeight / 2), 0.5, 0.45, 0.85);
C.composer.addPass(C.bloom); C.composer.addPass(new L.OutputPass());
function onResize() {
  cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix();
  C.renderer.setSize(innerWidth, innerHeight); C.composer.setPixelRatio(C.renderer.getPixelRatio()); C.composer.setSize(innerWidth, innerHeight); C.labelRenderer.setSize(innerWidth, innerHeight);
}
addEventListener('resize', onResize);

// Walk movement + camera tween + hover, every frame
const blocked = (x, z) => C.solids.some(s => x > s.x0 - 0.6 && x < s.x1 + 0.6 && z > s.z0 - 0.6 && z < s.z1 + 0.6);
C.onFrame(dt => {
  if (tween) { tween.t = Math.min(1, (performance.now() - tween.start) / 1400); const e = tween.t < 0.5 ? 4 * tween.t ** 3 : 1 - (-2 * tween.t + 2) ** 3 / 2;
    cam.position.lerpVectors(tween.p0, tween.p1, e); C.orbit.target.lerpVectors(tween.t0, tween.t1, e); if (tween.t >= 1) tween = null; }
  if (walk.active) {
    const k = walk.keys, sp = (k.ShiftLeft || k.ShiftRight ? 22 : 10) * dt;
    const f = (k.KeyW || k.ArrowUp ? 1 : 0) - (k.KeyS || k.ArrowDown ? 1 : 0), r = (k.KeyD || k.ArrowRight ? 1 : 0) - (k.KeyA || k.ArrowLeft ? 1 : 0);
    if (f || r) { const old = cam.position.clone(); C.controlsPL.moveForward(f * sp); C.controlsPL.moveRight(r * sp); const p = cam.position;
      if (blocked(p.x, p.z)) { if (!blocked(p.x, old.z)) p.z = old.z; else if (!blocked(old.x, p.z)) p.x = old.x; else p.copy(old); }
      p.x = THREE.MathUtils.clamp(p.x, -C.EXTENT - 30, C.EXTENT + 30); p.z = THREE.MathUtils.clamp(p.z, -C.EXTENT - 30, C.EXTENT + 30); p.y = walk.eye; }
  } else C.orbit.update();
  if (!walk.active && moved) { moved = false; const u = pick(mouse);
    if (u) { tip.innerHTML = hitLabel(u); tip.style.display = 'block'; tip.style.left = mxy[0] + 14 + 'px'; tip.style.top = mxy[1] + 14 + 'px'; el.style.cursor = 'pointer'; }
    else { tip.style.display = 'none'; el.style.cursor = ''; } }
});
};
