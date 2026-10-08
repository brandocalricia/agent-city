// Main: place landmarks, build the world, start the loop.
City.main = () => {
const C = City, { S, BASE } = C;
C.initWorld();
// Landmarks: doors face the central plaza (or use an explicit pos/rot)
C.LANDMARKS = {};
for (const id of C.buildingOrder) {
  const def = C.buildings[id];
  let center, rot;
  if (def.pos) { center = new THREE.Vector3(def.pos[0], 0, def.pos[1]); rot = def.rot || 0; }
  else { const [i, j] = def.block; center = new THREE.Vector3(i * S, 0, j * S);
    const dir = Math.abs(i) >= Math.abs(j) ? new THREE.Vector3(-Math.sign(i), 0, 0) : new THREE.Vector3(0, 0, -Math.sign(j)); rot = Math.atan2(dir.x, dir.z); }
  const L = { id, def, center, rot, dir: new THREE.Vector3(Math.sin(rot), 0, Math.cos(rot)) };
  L.door = center.clone().addScaledVector(L.dir, def.doorDist ?? 14); L.front = center.clone().addScaledVector(L.dir, def.frontDist ?? S / 2); L.plaza = center.clone().addScaledVector(L.dir, def.plazaDist ?? S - 13);
  const g = new THREE.Group(); g.position.copy(center); g.rotation.y = rot; C.scene.add(g);
  L.top = def.build(g); g.userData = { kind: 'landmark', id }; C.interactive.push(g); L.group = g;
  const holder = new THREE.Object3D(); holder.position.copy(center); C.scene.add(holder);
  L.label = C.addLabel(holder, `<b>${def.icon} ${def.name}</b><span>${C.esc(def.sub ? def.sub() : '')}</span>`, L.top + (def.small ? 3 : 4), 'lm-label' + (def.small ? ' small' : ''), () => C.openPanel('building', id));
  C.LANDMARKS[id] = L;
}
C.scene.updateMatrixWorld(true);
C.scene.traverse(o => { if (o.userData.solid) { const b = new THREE.Box3().setFromObject(o); C.solids.push({ x0: b.min.x, x1: b.max.x, z0: b.min.z, z1: b.max.z }); } });
if (C.LANDMARKS.townhall && C.HUB_LOCAL) C.HUB = C.LANDMARKS.townhall.group.localToWorld(C.HUB_LOCAL.clone());
C.initAgents(); C.initUI(); C.initMinimap(); C.initVisuals && C.initVisuals(); C.initHUD && C.initHUD(); C.initStreaks && C.initStreaks(); C.applyTime();
const clock = new THREE.Clock(); let frames = 0;
(function loop() {
  requestAnimationFrame(loop);
  const dt = Math.min(clock.getDelta(), 0.05), t = clock.elapsedTime;
  C.sky.position.copy(C.camera.position);
  for (const f of C.updaters) f(dt, t);
  if (C.isHighQ()) C.composer.render(); else C.renderer.render(C.scene, C.camera);
  C.labelRenderer.render(C.scene, C.camera);
  if (++frames === 3) { window.__cityReady = true; document.body.classList.add('ready'); }
})();
window.__city = C;
};
