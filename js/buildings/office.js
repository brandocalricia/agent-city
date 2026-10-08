// Office: where work gets done. Routines board + work log; the Builder's home.
City.building({
  id: 'office', name: 'Office', icon: '🏢', block: [1, 0], role: 'builder', key: 2,
  sub: () => 'where work gets done',
  build(g) {
    const C = City, M = C.M, BASE = C.BASE;
    const glass = C.windowTexture('#2b3a52', 0.72, '#0e1a2b', true);
    const th = 45;
    const tower = new THREE.Mesh(C.buildingGeo(18, th, 16, 0, BASE + th / 2, -3), glass); tower.castShadow = tower.receiveShadow = true; tower.userData.solid = true; g.add(tower);
    C.box(g, 20, 6, 6, new THREE.MeshStandardMaterial({ color: 0x1d2a3a, emissive: 0x6fb7ff, emissiveIntensity: 0.35, metalness: 0.5, roughness: 0.2 }), 0, BASE + 3, 8, true);
    C.box(g, 5, 4, 0.3, M.warm, 0, BASE + 2, 11.05);
    C.box(g, 22, 0.6, 8, M.dark, 0, BASE + 6.3, 8);
    C.box(g, 14, 2, 10, M.dark, 0, BASE + th + 1, -3);
    const pad = new THREE.Mesh(new THREE.CylinderGeometry(4, 4, 0.4, 24), M.metal); pad.position.set(0, BASE + th + 2.2, -3); g.add(pad);
    const b = C.latestFor('builder'), R = C.DATA.routines;
    C.sign(g, [
      { text: 'WORK LOG', font: 'bold 44px system-ui', color: '#5ee7ff', y: 30 },
      { text: b ? b.action : 'No work logged yet', font: 'bold 30px system-ui', color: '#ffffff', y: 78 },
      { text: `${C.plural(C.activityFor('builder').length, 'build')} · ${C.plural(R.length, 'routine')}`, font: '26px system-ui', color: '#9fb3c8', y: 122 },
    ], { w: 14, h: 4.4, y: BASE + 10.5, z: 5.1, bg: '#0b1420' });
    return th + 6;
  },
  panel() {
    const C = City, { esc } = C, R = C.DATA.routines;
    return `<h2>🏢 The Office</h2><p class="sub">Where work gets done: saved routines, the work log, and the Builder's desk.</p>
      <h4>Routines board (${R.length})</h4>` + (R.length
        ? R.map(r => C.card(esc(r.name), esc([r.schedule, r.owner].filter(Boolean).join(' · ')), r.description ? `<pre>${esc(r.description)}</pre>` : '')).join('')
        : C.empty('No saved routines on this computer yet', 'Ask Grok Bot to schedule something (for example a morning brief at 7am) and it will show up here.'))
      + `<h4>Work log</h4>` + (C.DATA.changelog.length ? C.DATA.changelog.slice(0, 5).map(e => C.card(esc(e.title), '', `<pre>${e.items.map(i => '• ' + esc(i)).join('\n')}</pre>`)).join('') : C.empty('Nothing logged yet'));
  },
});
