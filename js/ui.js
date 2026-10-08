// UI core: camera controls (orbit + walk), smooth fly-to, picking/hover, keyboard shortcuts, quality, post-processing.
// The top bar, search, dashboard, settings and onboarding live in hud.js.
City.initUI = () => {
const C = City, L = C.lib, { esc } = C, cam = C.camera, $ = id => document.getElementById(id);
const D = C.DATA;
C.isTouch = matchMedia('(pointer: coarse)').matches;
C.reducedMotion = () => (C.settings && C.settings.motion === 'reduced') || (!(C.settings && C.settings.motion === 'full') && matchMedia('(prefers-reduced-motion: reduce)').matches);

// Controls
C.orbit = new L.OrbitControls(cam, C.renderer.domElement);
C.orbit.target.copy(C.HOME.tgt); C.orbit.enableDamping = true; C.orbit.dampingFactor = 0.08;
C.orbit.maxPolarAngle = 1.45; C.orbit.minDistance = 8; C.orbit.maxDistance = 420;
C.orbit.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };
C.controlsPL = new L.PointerLockControls(cam, document.body);
const walk = C.walk = { active: false, keys: {}, eye: 3.0 };
let tween = null;
C.flyTo = (pos, tgt) => {
  if (walk.active) setWalk(false, true);
  const dist = cam.position.distanceTo(pos), dur = C.reducedMotion() ? 1 : Math.min(1900, 700 + dist * 4);
  tween = { start: performance.now(), dur, p0: cam.position.clone(), t0: C.orbit.target.clone(), p1: pos, t1: tgt };
};
C.fly = id => {
  if (id === 'overview') return C.flyTo(C.HOME.pos.clone(), C.HOME.tgt.clone());
  const Lm = C.LANDMARKS[id]; if (!Lm) return;
  const side = new THREE.Vector3(Lm.dir.z, 0, -Lm.dir.x), small = !!Lm.def.pos, narrow = innerWidth < 700 ? 1.25 : 1, v = Lm.def.view;
  if (v) return C.flyTo(Lm.center.clone().addScaledVector(Lm.dir, v.dist * narrow).addScaledVector(side, v.side).setY(v.h * narrow), Lm.center.clone().setY(v.look));
  C.flyTo(Lm.center.clone().addScaledVector(Lm.dir, (small ? 18 : 50) * narrow).addScaledVector(side, small ? 6 : 16).setY(small ? 9 : Math.max(22, Lm.top * 0.55) * narrow),
    Lm.center.clone().setY(small ? 3 : Math.min(Lm.top * 0.45, 14)));
};
function setWalk(on, quiet) {
  if (on && C.isTouch) return;   // pointer lock does not exist on phones; orbit + tap works there
  walk.active = on; C.orbit.enabled = !on; tween = null;
  $('btnWalk')?.classList.toggle('on', on);
  $('walkhint').style.display = $('crosshair').style.display = on ? 'block' : 'none';
  if (on) { cam.position.set(0, walk.eye, 24); cam.lookAt(0, walk.eye, -40); C.closePanel(); C.controlsPL.lock(); }
  else { C.controlsPL.unlock(); if (!quiet) C.fly('overview'); }
}
C.setWalk = setWalk;
C.renderer.domElement.addEventListener('click', () => { if (walk.active && !C.controlsPL.isLocked) C.controlsPL.lock(); });

// Quality: 'high' = bloom + shadows + up to 1.5x pixels; 'saver' = none of those (phones, slow laptops).
let highQ = true;
C.setQuality = q => {
  highQ = q !== 'saver'; C.bloom.enabled = highQ; C.sun.castShadow = highQ;
  C.renderer.setPixelRatio(highQ ? Math.min(devicePixelRatio, 1.5) : Math.min(devicePixelRatio, 1)); onResize();
  const b = $('btnQuality'); if (b) { b.classList.toggle('on', highQ); b.innerHTML = (highQ ? '✨ High' : '🔋 Saver') + ' <kbd>Q</kbd>'; }
  document.dispatchEvent(new CustomEvent('city:quality', { detail: highQ ? 'high' : 'saver' }));
};
C.isHighQ = () => highQ;
C.toggleQuality = () => { C.setQuality(highQ ? 'saver' : 'high'); if (C.saveSetting) C.saveSetting('quality', highQ ? 'high' : 'saver'); };

// Keyboard shortcuts (listed in the ? overlay)
const keyed = Object.fromEntries(C.buildingOrder.filter(id => C.buildings[id].key).map(id => [C.buildings[id].key, id]));
addEventListener('keydown', e => {
  if (/INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
  if ((e.metaKey || e.ctrlKey) && e.code === 'KeyK') { e.preventDefault(); C.openSearch && C.openSearch(); return; }
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  walk.keys[e.code] = true;
  if (e.code === 'Tab') { e.preventDefault(); setWalk(!walk.active); }
  else if (e.key === '/') { e.preventDefault(); C.openSearch && C.openSearch(); }
  else if (e.key === '?' || e.code === 'KeyH') C.toggleShortcuts && C.toggleShortcuts();
  else if (e.code === 'KeyQ') C.toggleQuality();
  else if (e.code === 'KeyT') C.cycleTime();
  else if (e.code === 'Escape') { if (C.closeOverlays && C.closeOverlays()) return; C.closePanel(); }
  else if (e.code === 'KeyE' && walk.active) { const u = pick(new THREE.Vector2(0, 0)); if (u) openHit(u); }
  else if (walk.active) return;
  else if (e.code === 'KeyD') C.openPanel('dashboard');
  else if (e.key === ',') C.openPanel('settings');
  else if (e.code === 'KeyL') C.toggleLabels && C.toggleLabels();
  else if (/^Digit\d$/.test(e.code)) { const n = +e.code.slice(5); if (n === 0) C.fly('overview'); else if (keyed[n]) C.fly(keyed[n]); }
});
addEventListener('keyup', e => { walk.keys[e.code] = false; });

// Picking (mouse and touch: a tap is a pointerup that barely moved)
const ray = new THREE.Raycaster(), mouse = new THREE.Vector2(), tip = $('tip'); let moved = false, mxy = [0, 0], down = null;
function pick(ndc) {
  ray.setFromCamera(ndc, cam);
  for (const h of ray.intersectObjects(C.interactive, true)) { let o = h.object; while (o && !o.userData.kind) o = o.parent; if (o) return o.userData; }
  return null;
}
const hitLabel = u => {
  if (u.kind === 'landmark') { const b = C.buildings[u.id]; return `<b>${b.icon} ${b.name}</b> · click to open`; }
  if (u.kind === 'role') { const r = C.roleById[u.id]; return `<b>${r.icon} ${r.name}</b><br><span class="mute">${esc(C.bubbleFor(r.id))}</span>`; }
  if (u.kind === 'skill') return `<b>📖 ${esc(D.skills[u.idx].name)}</b>`;
  const w = C.walkers[u.idx]; return `<b>${esc(w.agent.name)}</b> · ${esc(w.role)}<br><span class="mute">${esc(w.status)}</span>`;
};
function openHit(u) {
  if (u.kind === 'landmark') { C.fly(u.id); C.openPanel('building', u.id); }
  else if (u.kind === 'role') C.openPanel('role', u.id); else C.openPanel(u.kind, u.idx);
}
const el = C.renderer.domElement;
const setMouse = e => { mouse.set(e.clientX / innerWidth * 2 - 1, -e.clientY / innerHeight * 2 + 1); mxy = [e.clientX, e.clientY]; };
el.addEventListener('pointermove', e => { setMouse(e); moved = e.pointerType === 'mouse'; });
el.addEventListener('pointerdown', e => { down = [e.clientX, e.clientY]; });
el.addEventListener('pointerup', e => {
  if (walk.active || !down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > (e.pointerType === 'mouse' ? 5 : 12)) return;
  setMouse(e); const u = pick(mouse); if (u) openHit(u);
});

// Post-processing
C.composer = new L.EffectComposer(C.renderer);
C.composer.addPass(new L.RenderPass(C.scene, cam));
C.bloom = new L.UnrealBloomPass(new THREE.Vector2(innerWidth / 2, innerHeight / 2), 0.5, 0.45, 0.85);
C.composer.addPass(C.bloom); C.composer.addPass(new L.OutputPass());
function onResize() {
  cam.aspect = innerWidth / innerHeight; cam.fov = innerWidth < innerHeight ? 68 : 55; cam.updateProjectionMatrix();
  C.renderer.setSize(innerWidth, innerHeight); C.composer.setPixelRatio(C.renderer.getPixelRatio()); C.composer.setSize(innerWidth, innerHeight); C.labelRenderer.setSize(innerWidth, innerHeight);
}
addEventListener('resize', onResize); onResize();

// Walk movement + camera tween + hover, every frame
const blocked = (x, z) => C.solids.some(s => x > s.x0 - 0.6 && x < s.x1 + 0.6 && z > s.z0 - 0.6 && z < s.z1 + 0.6);
C.onFrame(dt => {
  if (tween) { const t = Math.min(1, (performance.now() - tween.start) / tween.dur), e = t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2;
    cam.position.lerpVectors(tween.p0, tween.p1, e); C.orbit.target.lerpVectors(tween.t0, tween.t1, e);
    if (t < 1) cam.position.y += Math.sin(t * Math.PI) * Math.min(40, tween.p0.distanceTo(tween.p1) * 0.12);   // gentle arc over the rooftops
    if (t >= 1) tween = null; }
  if (walk.active) {
    const k = walk.keys, sp = (k.ShiftLeft || k.ShiftRight ? 22 : 10) * dt;
    const f = (k.KeyW || k.ArrowUp ? 1 : 0) - (k.KeyS || k.ArrowDown ? 1 : 0), r = (k.KeyD || k.ArrowRight ? 1 : 0) - (k.KeyA || k.ArrowLeft ? 1 : 0);
    if (f || r) { const old = cam.position.clone(); C.controlsPL.moveForward(f * sp); C.controlsPL.moveRight(r * sp); const p = cam.position;
      if (blocked(p.x, p.z)) { if (!blocked(p.x, old.z)) p.z = old.z; else if (!blocked(old.x, p.z)) p.x = old.x; else p.copy(old); }
      p.x = THREE.MathUtils.clamp(p.x, -C.EXTENT - 30, C.EXTENT + 30); p.z = THREE.MathUtils.clamp(p.z, -C.EXTENT - 30, C.EXTENT + 30); p.y = walk.eye; }
  } else C.orbit.update();
  if (!walk.active && moved) { moved = false; const u = pick(mouse);
    if (u) { tip.innerHTML = hitLabel(u); tip.style.display = 'block'; tip.style.left = Math.min(mxy[0] + 14, innerWidth - 260) + 'px'; tip.style.top = mxy[1] + 14 + 'px'; el.style.cursor = 'pointer'; }
    else { tip.style.display = 'none'; el.style.cursor = ''; } }
});
};
