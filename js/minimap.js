// Minimap: blocks, landmarks (role colors), characters, and the camera. Click to fly.
City.initMinimap = () => {
const C = City, cv = document.getElementById('minimap'), g = cv.getContext('2d'), W = cv.width, E = C.EXTENT + 6;
const toPx = (x, z) => [(x + E) / (2 * E) * W, (z + E) / (2 * E) * W];
const colorOf = b => { const r = b.role && C.roleById[b.role]; return r ? '#' + new THREE.Color(r.color).getHexString() : '#5ee7ff'; };
let n = 0;
C.onFrame(() => {
  if (n++ % 6) return;
  g.clearRect(0, 0, W, W); g.fillStyle = 'rgba(12,14,26,.85)'; g.fillRect(0, 0, W, W);
  const bs = C.B / (2 * E) * W;
  for (let i = -C.N; i <= C.N; i++) for (let j = -C.N; j <= C.N; j++) { const [x, y] = toPx(i * C.S, j * C.S); g.fillStyle = C.isLandmarkBlock(i, j) ? 'rgba(77,125,68,.55)' : 'rgba(255,255,255,.12)'; g.fillRect(x - bs / 2, y - bs / 2, bs, bs); }
  g.font = '11px system-ui'; g.textAlign = 'center'; g.textBaseline = 'middle';
  for (const L of Object.values(C.LANDMARKS)) { const [x, y] = toPx(L.center.x, L.center.z); g.fillStyle = colorOf(L.def); g.beginPath(); g.arc(x, y, 7, 0, 7); g.fill(); g.fillText(L.def.icon, x, y - 0.5); }
  for (const c of C.roleChars) { const [x, y] = toPx(c.fig.position.x, c.fig.position.z); g.fillStyle = '#' + new THREE.Color(c.r.color).getHexString(); g.fillRect(x - 1.5, y - 1.5, 3, 3); }
  for (const w of C.walkers) { const [x, y] = toPx(w.fig.position.x, w.fig.position.z); g.fillStyle = '#5ee7ff'; g.beginPath(); g.arc(x, y, 3, 0, 7); g.fill(); }
  const cam = C.camera, [cx, cy] = toPx(cam.position.x, cam.position.z), d = new THREE.Vector3(); cam.getWorldDirection(d);
  const a = Math.atan2(d.z, d.x); g.save(); g.translate(Math.max(6, Math.min(W - 6, cx)), Math.max(6, Math.min(W - 6, cy))); g.rotate(a);
  g.fillStyle = '#fff'; g.beginPath(); g.moveTo(8, 0); g.lineTo(-5, 5); g.lineTo(-5, -5); g.fill(); g.restore();
});
cv.addEventListener('click', e => {
  const r = cv.getBoundingClientRect(), x = (e.clientX - r.left) / r.width * 2 * E - E, z = (e.clientY - r.top) / r.height * 2 * E - E;
  let best = null, bd = 30;
  for (const L of Object.values(C.LANDMARKS)) { const dd = Math.hypot(L.center.x - x, L.center.z - z); if (dd < bd) { bd = dd; best = L.id; } }
  if (best) C.fly(best); else C.flyTo(new THREE.Vector3(x + 50, 60, z + 70), new THREE.Vector3(x, 2, z));
});
};
