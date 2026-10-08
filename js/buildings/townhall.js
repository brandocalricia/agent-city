// City Hall (was Town Hall): agent roster, role directory, the Inspector's home. Clock shows Denver time.
City.building({
  id: 'townhall', name: 'City Hall', icon: '🏛', block: [0, -1], role: 'inspector', key: 3,
  sub: () => `${City.plural(City.DATA.agents.length, 'agent')} · ${City.ROLES.length} roles`,
  build(g) {
    const C = City, M = C.M, BASE = C.BASE;
    C.box(g, 30, 1, 22, M.stone, 0, BASE + 0.5, 0);
    const y0 = BASE + 1;
    C.box(g, 26, 10, 14, M.white, 0, y0 + 5, -2.5, true);
    C.columns(g, 6, 14, 6.5, 8.5, y0, 0.6);
    C.box(g, 16, 1.2, 4, M.white, 0, y0 + 9.1, 5.5);
    C.gable(g, 16, 3, 4, 3.6, y0 + 9.7, M.white);
    C.box(g, 4, 6, 0.3, M.warm, 0, y0 + 3, 4.55);
    for (const k of [-8.5, -4.5, 4.5, 8.5]) C.box(g, 2, 3.5, 0.3, M.warm, k, y0 + 5.5, 4.55);
    const drum = new THREE.Mesh(new THREE.CylinderGeometry(5.2, 5.6, 4.5, 24), M.white); drum.position.set(0, y0 + 12.2, -2.5); drum.castShadow = true; g.add(drum);
    const dome = new THREE.Mesh(new THREE.SphereGeometry(5.2, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), M.copper); dome.position.set(0, y0 + 14.4, -2.5); dome.castShadow = true; g.add(dome);
    C.box(g, 0.25, 6, 0.25, M.metal, 0, y0 + 22, -2.5);
    const flag = new THREE.Mesh(new THREE.PlaneGeometry(3, 1.8), new THREE.MeshStandardMaterial({ color: 0x5ee7ff, side: THREE.DoubleSide, emissive: 0x0b4050 }));
    flag.position.set(1.55, y0 + 24, -2.5); g.add(flag);
    C.onFrame((dt, t) => { flag.rotation.y = Math.sin(t * 1.7) * 0.25; });
    C.makeClock(g, new THREE.Vector3(0, y0 + 12.2, 2.75), 1.8);
    return 27;
  },
  panel() {
    const C = City, { esc } = C, A = C.DATA.agents;
    return `<h2>🏛 City Hall</h2><p class="sub">The roster of your assistants and the city's working roles. The clock shows real Denver time.</p>
      <h4>Assistants (${A.length})</h4>` + (A.length ? A.map(a => C.card(`${esc(a.name)}${a.active ? '<span class="badge">primary</span>' : ''}`, esc(a.title || (a.active ? 'Primary assistant' : 'Assistant')), a.description ? `<pre>${esc(a.description)}</pre>` : '')).join('') : C.empty('No agents found'))
      + `<h4>Roles (${C.ROLES.length})</h4>` + C.ROLES.map(r => { const l = C.latestFor(r.id); return C.card(`<a href="#" data-role="${r.id}">${r.icon} ${r.name}</a>${r.private ? '<span class="badge lockb">private</span>' : ''}`, esc(l ? `${l.date}: ${l.action}` : (r.idle || 'Starts work next session'))); }).join('');
  },
});
