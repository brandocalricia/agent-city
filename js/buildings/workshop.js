// Workshop: the Toolsmith only builds from Market finds you approved.
City.building({
  id: 'workshop', name: 'Workshop', icon: '🛠', block: [2, 0], role: 'toolsmith', small: true,
  sub: () => { const n = City.DATA.finds.filter(f => f.status === 'approved').length; return n ? `${n} approved` : 'waiting for an approved find'; },
  build(g) {
    const C = City, y0 = C.BASE;
    const top = C.simpleBuilding(g, { w: 22, d: 16, h: 9, color: 0x6e737c, roofColor: 0x3a3f47, roof: 'gable', sign: { text: 'WORKSHOP', bg: '#2a2f38', fg: '#ffd27a', y: C.BASE + 7.6 } });
    C.box(g, 7, 5, 0.3, C.mat(0x9aa0aa, { metalness: 0.5 }), 6, y0 + 2.5, 6.1);
    const gear = new THREE.Mesh(new THREE.TorusGeometry(1.4, 0.45, 6, 10), C.mat(0xffd27a, { emissive: 0x4a3200, metalness: 0.6 }));
    gear.position.set(-6.5, y0 + 6.2, 6.4); g.add(gear); C.onFrame(dt => { gear.rotation.z += dt * 0.8; });
    return top;
  },
  panel() {
    const A = City.DATA.finds.filter(f => f.status === 'approved');
    return `<h2>🛠 Workshop</h2><p class="sub">The Toolsmith sets up or builds tools, but only from Market finds you have approved.</p>`
      + (A.length ? A.map(f => City.card(City.esc(f.title), City.esc(f.date))).join('') : City.empty('Waiting for an approved find', 'Open the Market and copy the approval line of a find you like.'));
  },
});
