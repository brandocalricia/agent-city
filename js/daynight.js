// Day/night cycle synced to real Denver time (or a fixed preview: day / dusk / night), plus clock faces.
(() => {
const C = City;
const fmt = new Intl.DateTimeFormat('en-US', { timeZone: 'America/Denver', hour: 'numeric', minute: 'numeric', second: 'numeric', hour12: false });
C.denverHMS = () => { const p = Object.fromEntries(fmt.formatToParts(new Date()).map(x => [x.type, x.value])); return [+p.hour % 24, +p.minute, +p.second]; };
C.fmtTime = (h, m) => `${((h + 11) % 12) + 1}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`;
const clocks = [];
// Clock face facing local +z (rotated by `rot` around y) at position p inside group g.
C.makeClock = (g, p, r, rot = 0) => {
  const holder = new THREE.Group(); holder.position.copy(p); holder.rotation.y = rot; g.add(holder);
  const face = new THREE.Mesh(new THREE.CircleGeometry(r, 32), new THREE.MeshStandardMaterial({ color: 0xfff6dc, emissive: 0xffe8a8, emissiveIntensity: 0.9 }));
  holder.add(face); C.emissiveMats.push(face.material);
  const hand = (len, wd) => { const piv = new THREE.Group(); piv.position.z = 0.05; const m = new THREE.Mesh(new THREE.BoxGeometry(wd, len, 0.05), C.M.dark); m.position.y = len / 2; piv.add(m); holder.add(piv); return piv; };
  clocks.push({ h: hand(r * 0.55, r * 0.1), m: hand(r * 0.85, r * 0.065) });
};
const tickClocks = () => { const [h, m] = C.denverHMS(); clocks.forEach(c => { c.h.rotation.z = -((h % 12) + m / 60) / 12 * Math.PI * 2; c.m.rotation.z = -m / 60 * Math.PI * 2; }); };

const P = { // palettes
  night: { fog: 0.0026, top: 0x040818, mid: 0x0d1636, bot: 0x1b2444, hemiS: 0x41508a, hemiG: 0x15131c, hemi: 0.5, sun: 0x8fa2ff, sunI: 0.35, win: 2.1, stars: 0.95, bulb: 2.6, glow: [0.5, 0.55, 0.7], exp: 1.05 },
  dusk: { fog: 0.0028,  top: 0x16204a, mid: 0x6a5aa0, bot: 0xd99a86, hemiS: 0xa9b8ff, hemiG: 0x4a3a32, hemi: 1.15, sun: 0xffc690, sunI: 2.2, win: 1.5, stars: 0.6, bulb: 2.4, glow: [1, 0.7, 0.45], exp: 1.05 },
  day:  { fog: 0.0017,  top: 0x2f6fd0, mid: 0x7fb3ea, bot: 0xd2e4f2, hemiS: 0xd4e8ff, hemiG: 0x5a5040, hemi: 1.35, sun: 0xfff1dc, sunI: 3.0, win: 0.35, stars: 0, bulb: 0.7, glow: [1, 0.95, 0.85], exp: 1.0 },
};
const c1 = new THREE.Color(), c2 = new THREE.Color();
const lerpC = (a, b, t, out) => out.copy(c1.set(a)).lerp(c2.set(b), t);
const mix = (a, b, t) => {
  const o = {}; for (const k in a) o[k] = typeof a[k] === 'number' && !/^(top|mid|bot|hemiS|hemiG|sun)$/.test(k) ? a[k] + (b[k] - a[k]) * t
    : Array.isArray(a[k]) ? a[k].map((v, i) => v + (b[k][i] - v) * t) : lerpC(a[k], b[k], t, new THREE.Color()); return o;
};
const RISE = 7.1, SET = 18.6; // approx. October sunrise/sunset in Denver (hours)
C.timeMode = 'live';
const MODES = { day: 13, dusk: 18.55, night: 23 };
C.applyTime = () => {
  const [hh, mm] = C.denverHMS(), h = C.timeMode === 'live' ? hh + mm / 60 : MODES[C.timeMode];
  const isDay = h > RISE && h < SET, f = isDay ? (h - RISE) / (SET - RISE) : ((h - SET + 24) % 24) / (24 - (SET - RISE));
  const elev = isDay ? Math.sin(f * Math.PI) : -Math.sin(f * Math.PI);
  let pal;
  if (elev < -0.12) pal = mix(P.night, P.night, 0);
  else if (elev < 0.06) pal = mix(P.night, P.dusk, (elev + 0.12) / 0.18);
  else if (elev < 0.4) pal = mix(P.dusk, P.day, (elev - 0.06) / 0.34);
  else pal = mix(P.day, P.day, 0);
  for (const k of ['top', 'mid', 'bot', 'hemiS', 'hemiG', 'sun']) if (!(pal[k] instanceof THREE.Color)) pal[k] = new THREE.Color(pal[k]);
  // Sun path: rises in the east (+z), sets in the west (-z). At night a dim moon light takes over.
  const a = isDay ? f * Math.PI : f * Math.PI;
  const dir = new THREE.Vector3(Math.sin(a) * 0.55, Math.max(0.12, Math.abs(elev) * 0.9 + 0.08), Math.cos(a)).normalize();
  const u = C.sky.material.uniforms;
  u.top.value.copy(pal.top); u.mid.value.copy(pal.mid); u.bottom.value.copy(pal.bot); u.sunDir.value.copy(dir); u.glow.value.setRGB(...pal.glow);
  C.scene.fog.color.copy(pal.bot); C.scene.fog.density = pal.fog;
  C.hemi.color.copy(pal.hemiS); C.hemi.groundColor.copy(pal.hemiG); C.hemi.intensity = pal.hemi;
  C.sun.color.copy(pal.sun); C.sun.intensity = pal.sunI; C.sun.position.copy(dir).multiplyScalar(260);
  C.stars.material.opacity = pal.stars;
  C.emissiveMats.forEach(m => { m.userData.base ??= m.emissiveIntensity; m.emissiveIntensity = m.userData.base * pal.win / 1.5; });
  C.bulbMat.color.setRGB(1, 0.81, 0.54).multiplyScalar(pal.bulb);
  C.renderer.toneMappingExposure = pal.exp;
  tickClocks();
  C.timeLabel = (C.timeMode === 'live' ? 'Live ' + C.fmtTime(hh, mm) : C.timeMode[0].toUpperCase() + C.timeMode.slice(1));
  const b = document.getElementById('btnTime'); if (b) b.innerHTML = `🕒 ${C.timeLabel} <kbd>T</kbd>`;
};
C.cycleTime = () => { const order = ['live', 'day', 'dusk', 'night']; C.timeMode = order[(order.indexOf(C.timeMode) + 1) % order.length]; C.applyTime(); };
setInterval(() => C.applyTime && C.sky && C.applyTime(), 30000);
})();
