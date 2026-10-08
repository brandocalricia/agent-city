// Visual polish that stays cheap: crosswalks and curb lines, grass and lawn texture, neon roof accents on the tallest towers,
// time-of-day bloom, and automatic quality (phones start in saver mode; any device drops to saver if FPS stays low).
City.initVisuals = () => {
const C = City, { S, N, B, BASE, EXTENT, rnd } = C, scene = C.scene, o = new THREE.Object3D();

// Grass and lawns: a soft noise texture instead of flat color (one small canvas, repeated)
const noiseTex = (base, spread, size = 128) => {
  const c = document.createElement('canvas'); c.width = c.height = size; const g = c.getContext('2d'), col = new THREE.Color(base), hsl = {};
  col.getHSL(hsl);
  for (let y = 0; y < size; y += 2) for (let x = 0; x < size; x += 2) { g.fillStyle = `hsl(${hsl.h * 360},${hsl.s * 100}%,${(hsl.l + (Math.random() - 0.5) * spread) * 100}%)`; g.fillRect(x, y, 2, 2); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; return t;
};
C.M.grass.map = noiseTex(0x3f5a3a, 0.06); C.M.grass.map.repeat.set(220, 220); C.M.grass.color.set(0xffffff); C.M.grass.needsUpdate = true;
C.M.lawn.map = noiseTex(0x4d7d44, 0.07); C.M.lawn.map.repeat.set(10, 10); C.M.lawn.color.set(0xffffff); C.M.lawn.needsUpdate = true;
C.M.asphalt.color.set(0x2a2c33); C.M.asphalt.roughness = 0.9;

// Crosswalk stripes at every intersection, white curb lines along the blocks (instanced: 2 draw calls)
{
  const stripes = [], curbs = [];
  for (let i = -N - 1; i <= N; i++) for (let j = -N - 1; j <= N; j++) {
    const x = (i + 0.5) * S, z = (j + 0.5) * S;
    for (const [dx, dz, rot] of [[0, -8.5, 0], [0, 8.5, 0], [-8.5, 0, 1], [8.5, 0, 1]])
      for (let k = -2; k <= 2; k++) stripes.push([x + dx + (rot ? 0 : k * 1.5), z + dz + (rot ? k * 1.5 : 0), rot]);
  }
  for (let i = -N; i <= N; i++) for (let j = -N; j <= N; j++) {
    const e = B / 2 + 0.15; for (const [dx, dz, r] of [[0, -e, 0], [0, e, 0], [-e, 0, 1], [e, 0, 1]]) curbs.push([i * S + dx, j * S + dz, r]);
  }
  const sm = new THREE.InstancedMesh(new THREE.BoxGeometry(0.8, 0.03, 4.2), new THREE.MeshStandardMaterial({ color: 0xd9d6cc, roughness: 0.8 }), stripes.length);
  stripes.forEach(([x, z, r], k) => { o.position.set(x, 0.05, z); o.rotation.set(0, r ? Math.PI / 2 : 0, 0); o.updateMatrix(); sm.setMatrixAt(k, o.matrix); });
  const cm = new THREE.InstancedMesh(new THREE.BoxGeometry(B + 0.3, 0.08, 0.3), new THREE.MeshStandardMaterial({ color: 0xb8b2a7, roughness: 0.85 }), curbs.length);
  curbs.forEach(([x, z, r], k) => { o.position.set(x, BASE + 0.02, z); o.rotation.set(0, r ? Math.PI / 2 : 0, 0); o.updateMatrix(); cm.setMatrixAt(k, o.matrix); });
  sm.receiveShadow = cm.receiveShadow = true; scene.add(sm, cm);
}

// Neon roof accents: thin glowing rings on the tallest towers (picked up by bloom at night)
{
  const tops = (C.antennaTops || []).slice(0, 40);
  if (tops.length) {
    const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0x5ee7ff).multiplyScalar(1.6), transparent: true, opacity: 0.8 });
    const im = new THREE.InstancedMesh(new THREE.TorusGeometry(1.6, 0.06, 4, 24), mat, tops.length);
    tops.forEach(([x, y, z], k) => { o.position.set(x, y - 7.6, z); o.rotation.set(Math.PI / 2, 0, 0); o.scale.setScalar(1); o.updateMatrix(); im.setMatrixAt(k, o.matrix); });
    scene.add(im); C.neonAccent = mat;
  }
}

// Time of day: stronger bloom and neon at night, subtle by day (wraps applyTime from daynight.js)
const apply = C.applyTime;
C.applyTime = () => {
  apply();
  const night = C.scene.fog.color.getHSL({}).l < 0.25, dusk = !night && C.sun.intensity < 2.6;
  if (C.bloom) { C.bloom.strength = night ? 0.6 : dusk ? 0.45 : 0.2; C.bloom.threshold = 0.85; C.bloom.radius = night ? 0.5 : 0.4; }
  if (C.neonAccent) C.neonAccent.opacity = night ? 0.9 : dusk ? 0.6 : 0.25;
  C.hemi.intensity *= night ? 1.15 : 1;
};

// Automatic quality: phones and small touch screens start in saver mode; if FPS stays under 32 for ~5 s in high mode, drop to saver.
const pref = C.settings && C.settings.quality;
if (pref === 'saver' || (pref !== 'high' && C.isTouch)) C.setQuality('saver');
let acc = 0, frames = 0, low = 0;
C.fps = 60;
C.onFrame(dt => {
  acc += dt; frames++;
  if (acc < 1) return;
  C.fps = Math.round(frames / acc); acc = 0; frames = 0;
  if (C.isHighQ() && (!C.settings || C.settings.quality !== 'high') && document.visibilityState === 'visible') {
    low = C.fps < 32 ? low + 1 : 0;
    if (low >= 5) { C.setQuality('saver'); C.toast && C.toast('🔋 Switched to saver graphics to keep things smooth (Settings to change)'); low = 0; }
  }
});
};
