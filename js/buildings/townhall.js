// Town Hall (Council): the city's hub at the center of the plaza. The Council rules here (verdicts), the Inspector checks the
// city from here, and the roster of assistants and roles lives here. Merged from City Hall + Council Chamber (2026-10-08);
// old links (#council, #cityhall) redirect here (see council.js). Every neon streak ends at its beacon (City.HUB).
City.building({
  id: 'townhall', name: 'Town Hall (Council)', icon: '🏛', pos: [0, 0], rot: 0, role: 'council', roles: ['council', 'inspector'], key: 3, hub: true,
  doorDist: 11.5, frontDist: 12.5, plazaDist: 13, view: { dist: 44, side: 12, h: 26, look: 9 },
  sub: () => { const V = City.activityFor('council').filter(a => a.verdict); return `the hub · ${V.length ? City.plural(V.length, 'verdict') : 'first verdict soon'} · ${City.ROLES.length} roles`; },
  build(g) {
    const C = City, M = C.M, y0 = C.BASE;
    const cyl = (rt, rb, h, y, m, seg = 40) => { const o = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg), m); o.position.y = y + h / 2; o.castShadow = o.receiveShadow = true; g.add(o); return o; };
    cyl(11, 11.4, 0.5, y0, M.stone); cyl(10.1, 10.4, 0.5, y0 + 0.5, M.stone);
    const base = y0 + 1;
    const hall = cyl(6.6, 6.6, 9, base, M.white, 32); hall.userData.solid = true;
    const col = new THREE.CylinderGeometry(0.45, 0.52, 9, 12);
    for (let k = 0; k < 12; k++) { const a = (k + 0.5) / 12 * Math.PI * 2, c = new THREE.Mesh(col, M.white); c.position.set(Math.sin(a) * 8.6, base + 4.5, Math.cos(a) * 8.6); c.castShadow = true; g.add(c); }
    cyl(9.4, 9.4, 1.1, base + 9, M.white);
    cyl(5.8, 6.2, 3.6, base + 10.1, M.white, 32);
    const domeMat = C.mat(0x6a4fa3, { metalness: 0.35, roughness: 0.45 });
    const dome = new THREE.Mesh(new THREE.SphereGeometry(6.1, 32, 14, 0, Math.PI * 2, 0, Math.PI / 2), domeMat); dome.position.y = base + 13.7; dome.castShadow = true; g.add(dome);
    cyl(0.9, 1.1, 2.2, base + 19.4, M.white, 12);
    // Beacon: every neon streak converges here
    const lamp = new THREE.MeshStandardMaterial({ color: 0x3a1040, emissive: 0xe040fb, emissiveIntensity: 1.8 }); C.emissiveMats.push(lamp);
    const orb = new THREE.Mesh(new THREE.SphereGeometry(1.1, 20, 14), lamp); orb.position.y = base + 22.4; g.add(orb);
    C.HUB_LOCAL = new THREE.Vector3(0, base + 22.4, 0);
    C.onFrame((dt, t) => { lamp.emissiveIntensity = 1.5 + Math.sin(t * 1.4) * 0.4 + (C.hubPulse || 0); if (C.hubPulse) C.hubPulse = Math.max(0, C.hubPulse - dt * 1.5); });
    // Neon ring at the foot of the steps (soft glow at night)
    const ringMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xe040fb).multiplyScalar(1.4), transparent: true, opacity: 0.85 });
    const ring = new THREE.Mesh(new THREE.TorusGeometry(11.6, 0.09, 6, 96), ringMat); ring.rotation.x = Math.PI / 2; ring.position.y = y0 + 0.12; g.add(ring);
    C.box(g, 3, 5, 0.3, M.warm, 0, base + 2.5, 6.5);
    for (const a of [-0.5, 0.5]) { const w = C.box(g, 1.6, 2.6, 0.2, M.warm, Math.sin(a) * 6.62, base + 5.6, Math.cos(a) * 6.62); w.rotation.y = a; w.castShadow = false; }
    C.sign(g, [{ text: 'TOWN HALL · COUNCIL', font: 'bold 44px Georgia, serif', color: '#f6e7ff' }], { w: 8.5, h: 1.4, y: base + 9.55, z: 9.45, bg: '#2a1838' });
    C.makeClock(g, new THREE.Vector3(0, base + 11.9, 6.05), 1.5);
    C.makeClock(g, new THREE.Vector3(0, base + 11.9, -6.05), 1.5, Math.PI);
    return base + 24;
  },
  panel() {
    const C = City, { esc } = C, A = C.DATA.agents;
    return `<h2>🏛 Town Hall (Council)</h2><p class="sub">The heart of the city. The Council decides here, the Inspector checks the city from here, and every finished task streaks back here as a neon trail. The clocks show real Denver time.</p>`
      + (C.councilSection ? C.councilSection() : '')
      + `<h4>Assistants (${A.length})</h4>` + (A.length ? A.map(a => C.card(`${esc(a.name)}${a.active ? '<span class="badge">primary</span>' : ''}`, esc(a.title || (a.active ? 'Primary assistant' : 'Assistant')), a.description ? `<pre>${esc(a.description)}</pre>` : '')).join('') : C.empty('No agents found'))
      + `<h4>Roles (${C.ROLES.length})</h4>` + C.ROLES.map(r => { const l = C.latestFor(r.id); return C.card(`<a href="#" data-role="${r.id}">${r.icon} ${r.name}</a>${r.private ? '<span class="badge lockb">private</span>' : ''}`, esc(l ? `${l.date}: ${l.action}` : (r.idle || 'Starts work next session'))); }).join('');
  },
});
