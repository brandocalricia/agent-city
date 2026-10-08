// World: sky, lights, ground, roads, procedural skyline, lamps, trees, plaza and fountain.
City.initWorld = () => {
const C = City, L = C.lib, scene = C.scene, { S, B, N, BASE, EXTENT, rnd, M } = C;

// Sky dome (colors driven by daynight.js)
C.sky = new THREE.Mesh(new THREE.SphereGeometry(1500, 32, 16), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { top: { value: new THREE.Color(0x16204a) }, mid: { value: new THREE.Color(0x6a5aa0) }, bottom: { value: new THREE.Color(0xd99a86) },
    sunDir: { value: new THREE.Vector3(0.3, 0.2, -0.9).normalize() }, glow: { value: new THREE.Color(1, 0.7, 0.45) } },
  vertexShader: `varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform vec3 top, mid, bottom, sunDir, glow; varying vec3 vP;
    void main(){ vec3 d = normalize(vP); float h = d.y;
      vec3 c = mix(bottom, mid, smoothstep(0.0, 0.28, h)); c = mix(c, top, smoothstep(0.28, 0.85, h));
      float s = max(dot(d, normalize(sunDir)), 0.0);
      c += glow * (pow(s, 400.0) * 3.0 + pow(s, 8.0) * 0.4);
      gl_FragColor = vec4(c, 1.0);
      #include <colorspace_fragment>
    }`
}));
scene.add(C.sky);
{
  const n = 600, pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const th = rnd() * Math.PI * 2, y = 0.3 + rnd() * 0.7, r = Math.sqrt(1 - y * y); pos.set([Math.cos(th) * r * 1400, y * 1400, Math.sin(th) * r * 1400], i * 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  C.stars = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 1.7, sizeAttenuation: false, transparent: true, opacity: 0.7, fog: false }));
  C.sky.add(C.stars);
}
C.hemi = new THREE.HemisphereLight(0xa9b8ff, 0x4a3a32, 1.15); scene.add(C.hemi);
C.sun = new THREE.DirectionalLight(0xffc690, 2.2);
C.sun.castShadow = true; C.sun.shadow.mapSize.set(2048, 2048);
Object.assign(C.sun.shadow.camera, { left: -150, right: 150, top: 150, bottom: -150, near: 10, far: 600 });
C.sun.shadow.bias = -0.0004; C.sun.shadow.normalBias = 0.6;
scene.add(C.sun, C.sun.target);

// Ground and roads
const ground = new THREE.Mesh(new THREE.PlaneGeometry(4000, 4000), M.grass); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
const asphalt = new THREE.Mesh(new THREE.PlaneGeometry(EXTENT * 2 + 12, EXTENT * 2 + 12), M.asphalt);
asphalt.rotation.x = -Math.PI / 2; asphalt.position.y = 0.02; asphalt.receiveShadow = true; scene.add(asphalt);
{
  const dashes = [];
  for (let k = -N - 1; k <= N; k++) { const line = (k + 0.5) * S;
    for (let t = -EXTENT; t < EXTENT; t += 6) { if (Math.abs(((t + S / 2) % S + S) % S - S / 2) > S / 2 - 8) continue; dashes.push([line, t, 0], [t, line, 1]); } }
  const im = new THREE.InstancedMesh(new THREE.BoxGeometry(0.35, 0.03, 3), new THREE.MeshStandardMaterial({ color: 0xe8d58a, emissive: 0x332a10 }), dashes.length);
  const o = new THREE.Object3D();
  dashes.forEach(([x, z, r], i) => { o.position.set(x, 0.05, z); o.rotation.y = r ? Math.PI / 2 : 0; o.updateMatrix(); im.setMatrixAt(i, o.matrix); });
  scene.add(im);
}

// Procedural skyline (merged per material for few draw calls)
const facadeMats = [['#8d8f99', .45], ['#a39385', .4], ['#6f7787', .5], ['#b5aa98', .35], ['#5d6470', .55], ['#9aa3ad', .4]].map(([c, l]) => C.windowTexture(c, l));
const geosByMat = facadeMats.map(() => []), roofGeos = [], sidewalkGeos = [], lawnGeos = [];
C.antennaTops = [];
for (let i = -N; i <= N; i++) for (let j = -N; j <= N; j++) {
  const cx = i * S, cz = j * S;
  if (C.isLandmarkBlock(i, j)) { lawnGeos.push(new THREE.BoxGeometry(B, BASE, B).translate(cx, BASE / 2, cz)); continue; }
  sidewalkGeos.push(new THREE.BoxGeometry(B, BASE, B).translate(cx, BASE / 2, cz));
  const hot = Math.exp(-((i - 2) ** 2 + (j + 3.2) ** 2) / 3.5) + 0.7 * Math.exp(-((i + 3) ** 2 + (j + 3.2) ** 2) / 3);
  const ring = Math.max(Math.abs(i), Math.abs(j));
  const lots = rnd() < 0.22 ? [[0, 0, 22 + rnd() * 8, 22 + rnd() * 8]]
    : [[-1, -1], [1, -1], [-1, 1], [1, 1]].filter(() => rnd() < 0.88).map(([qx, qz]) => [qx * B / 4, qz * B / 4, 9 + rnd() * 5, 9 + rnd() * 5]);
  for (const [lx, lz, w, d] of lots) {
    let h = 7 + rnd() * 10 + hot * (25 + rnd() * 60) + (rnd() < 0.06 ? 22 : 0);
    if (ring <= 2) h = Math.min(h, 16);
    h = Math.round(h / 3) * 3;
    const x = cx + lx, z = cz + lz, m = Math.floor(rnd() * facadeMats.length);
    geosByMat[m].push(C.buildingGeo(w, h, d, x, BASE + h / 2, z));
    C.solids.push({ x0: x - w / 2, x1: x + w / 2, z0: z - d / 2, z1: z + d / 2 });
    if (h > 30 && rnd() < 0.65) { const h2 = Math.round(h * (0.15 + rnd() * 0.2) / 3) * 3; geosByMat[m].push(C.buildingGeo(w * 0.7, h2, d * 0.7, x, BASE + h + h2 / 2, z)); h += h2; }
    if (h > 45) { roofGeos.push(new THREE.CylinderGeometry(0.15, 0.25, 8, 5).translate(x, BASE + h + 4, z)); C.antennaTops.push([x, BASE + h + 8.2, z]); }
    else if (rnd() < 0.7) roofGeos.push(new THREE.BoxGeometry(2.5, 1.4, 2).translate(x + (rnd() - .5) * w * .5, BASE + h + 0.7, z + (rnd() - .5) * d * .5));
  }
}
facadeMats.forEach((m, k) => { if (!geosByMat[k].length) return; const mesh = new THREE.Mesh(L.mergeGeometries(geosByMat[k]), m); mesh.castShadow = mesh.receiveShadow = true; scene.add(mesh); });
[[roofGeos, M.dark], [sidewalkGeos, M.sidewalk], [lawnGeos, M.lawn]].forEach(([gs, m]) => { if (!gs.length) return; const mesh = new THREE.Mesh(L.mergeGeometries(gs), m); mesh.castShadow = m === M.dark; mesh.receiveShadow = true; scene.add(mesh); });
C.blinkMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xff3030).multiplyScalar(3) });
{
  const im = new THREE.InstancedMesh(new THREE.SphereGeometry(0.45, 8, 6), C.blinkMat, Math.max(1, C.antennaTops.length));
  const o = new THREE.Object3D(); C.antennaTops.forEach((p, k) => { o.position.set(...p); o.updateMatrix(); im.setMatrixAt(k, o.matrix); });
  im.count = C.antennaTops.length; scene.add(im);
  C.onFrame((dt, t) => C.blinkMat.color.setRGB(Math.sin(t * 3) > 0.3 ? 3 : 0.25, 0.1, 0.1));
}

// Street lamps & trees (instanced)
{
  const lamps = [], trees = [];
  for (let i = -N; i <= N; i++) for (let j = -N; j <= N; j++) {
    const cx = i * S, cz = j * S, e = B / 2 - 1.2, lm = C.isLandmarkBlock(i, j);
    for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) lamps.push([cx + sx * e, cz + sz * e]);
    for (let t = -B / 2 + 6; t <= B / 2 - 6; t += 7) for (const side of [0, 1, 2, 3]) {
      if (!lm && rnd() > 0.35) continue;
      if (lm && Math.abs(t) < 7) continue;
      const p = [[t, -e], [t, e], [-e, t], [e, t]][side];
      trees.push([cx + p[0], cz + p[1], 0.8 + rnd() * 0.5]);
    }
  }
  const o = new THREE.Object3D();
  const pole = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.12, 0.16, 5.5, 6), M.dark, lamps.length);
  C.bulbMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffcf8a).multiplyScalar(2.5) });
  const bulb = new THREE.InstancedMesh(new THREE.SphereGeometry(0.38, 10, 8), C.bulbMat, lamps.length);
  lamps.forEach(([x, z], k) => { o.position.set(x, BASE + 2.75, z); o.updateMatrix(); pole.setMatrixAt(k, o.matrix); o.position.y = BASE + 5.6; o.updateMatrix(); bulb.setMatrixAt(k, o.matrix); });
  pole.castShadow = true; scene.add(pole, bulb);
  const trunk = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.2, 0.3, 2, 6), M.wood, trees.length);
  const leaves = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1.7, 0), new THREE.MeshStandardMaterial({ color: 0xffffff, flatShading: true, roughness: 0.9 }), trees.length);
  const col = new THREE.Color();
  trees.forEach(([x, z, s], k) => {
    o.position.set(x, BASE + s, z); o.scale.setScalar(s); o.rotation.y = rnd() * 6; o.updateMatrix(); trunk.setMatrixAt(k, o.matrix);
    o.position.y = BASE + 3 * s; o.updateMatrix(); leaves.setMatrixAt(k, o.matrix);
    // October in Denver: mix of green and autumn gold/orange
    leaves.setColorAt(k, rnd() < 0.45 ? col.setHSL(0.07 + rnd() * 0.06, 0.75, 0.45) : col.setHSL(0.25 + rnd() * 0.1, 0.45, 0.3));
  });
  trunk.castShadow = leaves.castShadow = true; scene.add(trunk, leaves);
}

// Central plaza (Town Hall stands in the middle; see js/buildings/townhall.js)
{
  const g = new THREE.Group(); scene.add(g);
  C.box(g, B, BASE + 0.05, B, M.plaza, 0, (BASE + 0.05) / 2, 0);
  // Four low planters with autumn shrubs on the plaza corners
  const shrub = new THREE.MeshStandardMaterial({ color: 0x5f7f3a, flatShading: true, roughness: 0.9 }), gold = new THREE.MeshStandardMaterial({ color: 0xc98b2b, flatShading: true, roughness: 0.9 });
  for (const [sx, sz] of [[1, 1], [1, -1], [-1, -1]]) {
    C.box(g, 5, 0.8, 5, M.stone, sx * 14.5, BASE + 0.4, sz * 14.5);
    for (let k = 0; k < 3; k++) { const b = new THREE.Mesh(new THREE.IcosahedronGeometry(1.1 + rnd() * 0.4, 0), k % 2 ? gold : shrub); b.position.set(sx * 14.5 + (rnd() - 0.5) * 2.6, BASE + 1.5, sz * 14.5 + (rnd() - 0.5) * 2.6); b.castShadow = true; g.add(b); }
    C.solids.push({ x0: sx * 14.5 - 2.5, x1: sx * 14.5 + 2.5, z0: sz * 14.5 - 2.5, z1: sz * 14.5 + 2.5 });
  }
}
};
