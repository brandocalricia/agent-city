// Core: data, helpers, renderer/scene/camera, shared materials and geometry helpers.
(() => {
const C = window.City, L = C.lib;
C.DATA = Object.assign({ skills: [], agents: [], changelog: [], finds: [], activity: [], routines: [], generatedAt: 'never' }, window.CITY_DATA || {});
C.PRIV = window.CITY_PRIVATE || null;
C.esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
C.plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
C.S = 48; C.B = 36; C.N = 4; C.BASE = 0.3; C.EXTENT = (C.N + 0.5) * C.S;
let seed = 20261008; C.rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
C.solids = [];        // walk-mode collision footprints {x0,x1,z0,z1}
C.interactive = [];   // raycast targets (objects with userData.kind somewhere up the tree)
C.updaters = [];      // per-frame callbacks (dt, t)
C.onFrame = fn => C.updaters.push(fn);

// ---------- Renderer, scene, camera ----------
const r = C.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
r.setPixelRatio(Math.min(devicePixelRatio, 1.5)); r.setSize(innerWidth, innerHeight);
r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
r.toneMapping = THREE.ACESFilmicToneMapping; r.toneMappingExposure = 1.05;
document.getElementById('app').appendChild(r.domElement);
C.labelRenderer = new L.CSS2DRenderer();
C.labelRenderer.setSize(innerWidth, innerHeight); C.labelRenderer.domElement.className = 'labels';
document.body.appendChild(C.labelRenderer.domElement);
C.scene = new THREE.Scene();
C.scene.fog = new THREE.FogExp2(0xd99a86, 0.0028);
C.camera = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.5, 2500);
C.HOME = { pos: new THREE.Vector3(-105, 120, 175), tgt: new THREE.Vector3(0, 4, 0) };
C.camera.position.copy(C.HOME.pos);

// ---------- Materials & helpers ----------
C.mat = (color, o = {}) => new THREE.MeshStandardMaterial(Object.assign({ color, roughness: 0.85 }, o));
C.M = {
  grass: C.mat(0x3f5a3a), asphalt: C.mat(0x2b2d33, { roughness: 0.95 }), sidewalk: C.mat(0x8e8a86), lawn: C.mat(0x4d7d44),
  plaza: C.mat(0xbdb3a3), stone: C.mat(0xe3d5b8), white: C.mat(0xeee8dc), roof: C.mat(0x7a5446), wood: C.mat(0x6b4a2f),
  copper: C.mat(0x5fae96, { roughness: 0.5, metalness: 0.3 }), dark: C.mat(0x3b3f48), metal: C.mat(0x9aa0aa, { metalness: 0.6, roughness: 0.4 }),
  gold: C.mat(0xe0b44a, { metalness: 0.8, roughness: 0.3, emissive: 0x3a2a05 }),
  warm: new THREE.MeshStandardMaterial({ color: 0x442a10, emissive: 0xffc070, emissiveIntensity: 1.6 }),
  water: new THREE.MeshStandardMaterial({ color: 0x3a8fb7, emissive: 0x1b6f9a, emissiveIntensity: 0.6, roughness: 0.1, metalness: 0.2 }),
};
C.emissiveMats = [C.M.warm];   // dimmed by day, brightened at night (see daynight.js)
C.box = (parent, w, h, d, m, x, y, z, solid = false) => {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
  mesh.position.set(x, y, z); mesh.castShadow = mesh.receiveShadow = true;
  if (solid) mesh.userData.solid = true;
  parent.add(mesh); return mesh;
};
C.columns = (g, count, span, z, h, y0, r = 0.55, m = C.M.white) => {
  const geo = new THREE.CylinderGeometry(r, r * 1.1, h, 12);
  for (let k = 0; k < count; k++) { const c = new THREE.Mesh(geo, m); c.position.set(-span / 2 + span * k / (count - 1), y0 + h / 2, z); c.castShadow = true; g.add(c); }
};
C.gable = (g, w, h, depth, z, y, m) => {
  const sh = new THREE.Shape(); sh.moveTo(-w / 2, 0); sh.lineTo(w / 2, 0); sh.lineTo(0, h); sh.closePath();
  const mesh = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth, bevelEnabled: false }), m);
  mesh.position.set(0, y, z); mesh.castShadow = true; g.add(mesh); return mesh;
};
// Canvas text texture; each line auto-shrinks to fit the width.
C.textTexture = (lines, { w = 512, h = 128, bg = '#10202a', fg = '#7dffb2', font = 'bold 64px system-ui' } = {}) => {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d');
  g.fillStyle = bg; g.fillRect(0, 0, w, h); g.textAlign = 'center'; g.textBaseline = 'middle';
  lines.forEach((ln, k) => {
    let f = ln.font || font, size = parseInt(f.match(/(\d+)px/)[1]);
    g.font = f; while (g.measureText(ln.text).width > w - 30 && size > 10) { size -= 2; g.font = f.replace(/\d+px/, size + 'px'); }
    g.fillStyle = ln.color || fg; g.fillText(ln.text, w / 2, ln.y ?? (h / (lines.length + 1)) * (k + 1));
  });
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
};
C.sign = (g, text, { w = 10, x = 0, y, z, bg = '#10202a', fg = '#7dffb2', h } = {}) => {
  const hh = h || w / 4;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, hh), new THREE.MeshBasicMaterial({ map: C.textTexture(Array.isArray(text) ? text : [{ text }], { w: 512, h: Math.round(512 * hh / w), bg, fg }) }));
  m.position.set(x, y, z); g.add(m); return m;
};
C.addLabel = (parent, html, y, cls, onClick) => {
  const div = document.createElement('div'); div.className = cls; div.innerHTML = html;
  if (onClick) div.addEventListener('click', e => { e.stopPropagation(); onClick(); });
  const obj = new L.CSS2DObject(div); obj.position.set(0, y, 0); parent.add(obj); return obj;
};
// Procedural lit-window facade material.
C.TW = 16; C.TH = 24;
C.windowTexture = (facade, litChance, glass = '#1a2232', cool = false) => {
  const make = () => { const c = document.createElement('canvas'); c.width = c.height = 256; return c; };
  const cm = make(), ce = make(), a = cm.getContext('2d'), e = ce.getContext('2d');
  a.fillStyle = facade; a.fillRect(0, 0, 256, 256); e.fillStyle = '#000'; e.fillRect(0, 0, 256, 256);
  const lit = cool ? ['#cfe8ff', '#a8d4ff', '#fff1c9'] : ['#ffd27a', '#ffe7ad', '#ffc56a', '#cfe6ff'];
  for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) {
    const px = x * 32 + 7, py = y * 32 + 6;
    if (C.rnd() < litChance) { const col = lit[Math.floor(C.rnd() * lit.length)]; a.fillStyle = col; e.fillStyle = col; e.fillRect(px, py, 18, 20); }
    else a.fillStyle = glass;
    a.fillRect(px, py, 18, 20);
  }
  const t = [cm, ce].map(c => { const tx = new THREE.CanvasTexture(c); tx.wrapS = tx.wrapT = THREE.RepeatWrapping; tx.anisotropy = 4; tx.colorSpace = THREE.SRGBColorSpace; return tx; });
  const m = new THREE.MeshStandardMaterial({ map: t[0], emissiveMap: t[1], emissive: 0xffffff, emissiveIntensity: 1.5, roughness: 0.7, metalness: 0.1 });
  C.emissiveMats.push(m); return m;
};
// Box with UVs scaled to world size (constant window size); roof/floor map to plain facade.
C.buildingGeo = (w, h, d, x, y, z) => {
  const g = new THREE.BoxGeometry(w, h, d), uv = g.attributes.uv, ou = Math.floor(C.rnd() * 8) / 8;
  for (let i = 0; i < 24; i++) {
    const face = Math.floor(i / 4);
    if (face === 2 || face === 3) { uv.setXY(i, 0.002, 0.002); continue; }
    uv.setXY(i, uv.getX(i) * (face < 2 ? d : w) / C.TW + ou, uv.getY(i) * h / C.TH);
  }
  g.translate(x, y, z); return g;
};
// Quick civic building: body, door, lit windows, roof style, optional sign. Returns roof height.
C.simpleBuilding = (g, o) => {
  const { w = 20, d = 14, h = 9, z = -2, color = 0xdddddd, roofColor = 0x555a63, roof = 'flat' } = o, y0 = C.BASE;
  C.box(g, w, h, d, C.mat(color), 0, y0 + h / 2, z, true);
  const front = z + d / 2;
  C.box(g, 3.2, 4.6, 0.3, C.M.warm, 0, y0 + 2.3, front + 0.05);
  const floors = Math.max(1, Math.floor((h - 3.5) / 3.2));
  for (let f = 0; f < floors; f++) for (let x = -w / 2 + 3; x <= w / 2 - 2.9; x += 4)
    if (Math.abs(x) > 2.6 || f > 0) { const b = C.box(g, 1.8, 1.8, 0.2, C.rnd() < 0.8 ? C.M.warm : C.M.dark, x, y0 + 3.4 + f * 3.2, front + 0.05); b.castShadow = false; }
  let top = y0 + h;
  if (roof === 'gable') { C.gable(g, w + 1, 3.5, d + 1, z - d / 2 - 0.5, top, C.mat(roofColor)); top += 3.5; }
  else if (roof === 'pyramid') { const p = new THREE.Mesh(new THREE.ConeGeometry(Math.max(w, d) * 0.72, 4.5, 4), C.mat(roofColor)); p.rotation.y = Math.PI / 4; p.position.set(0, top + 2.25, z); p.castShadow = true; g.add(p); top += 4.5; }
  else C.box(g, w + 0.6, 0.6, d + 0.6, C.mat(roofColor), 0, top + 0.3, z);
  if (o.sign) C.sign(g, o.sign.text, Object.assign({ w: Math.min(w - 4, 14), y: y0 + h - 1.5, z: front + 0.12 }, o.sign));
  return top;
};

// ---------- Building registry ----------
// Each js/buildings/*.js calls City.building({ id, name, icon, block:[i,j] | pos:[x,z], role, sub(), build(g) -> top, panel() -> html })
C.buildings = {}; C.buildingOrder = [];
C.building = def => { C.buildings[def.id] = def; C.buildingOrder.push(def.id); };
C.isLandmarkBlock = (i, j) => (i === 0 && j === 0) || Object.values(C.buildings).some(b => b.block && b.block[0] === i && b.block[1] === j);
// Small UI helpers shared by panels
C.card = (t, m, extra = '') => `<div class="card"><div class="t">${t}</div>${m ? `<div class="m">${m}</div>` : ''}${extra}</div>`;
C.empty = (title, body = '', cls = '') => `<div class="empty ${cls}"><b>${title}</b>${body}</div>`;
C.copyBtn = text => `<button class="copy" data-copy="${C.esc(text)}">📋 Copy</button>`;
})();
