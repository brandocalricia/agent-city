// Review Board: the Critic's checks of everyone else's output.
City.building({
  id: 'reviewboard', name: 'Review Board', icon: '🧐', block: [0, -2], role: 'critic', small: true,
  sub: () => { const c = City.latestFor('critic'); return c ? 'last review ' + c.date : 'reviews start next session'; },
  build(g) {
    const C = City, y0 = C.BASE;
    const top = C.simpleBuilding(g, { w: 20, d: 14, h: 10, color: 0xd8d2c4, roofColor: 0x5a3b3b, roof: 'gable', sign: { text: 'REVIEW BOARD', bg: '#3b1515', fg: '#ffd0d0' } });
    const check = new THREE.Group(), m = C.mat(0x7dffb2, { emissive: 0x2a9a5a, emissiveIntensity: 1.2 });
    C.box(check, 0.6, 1.6, 0.4, m, -0.6, 0, 0).rotation.z = 0.7; C.box(check, 0.6, 3.2, 0.4, m, 0.65, 0.6, 0).rotation.z = -0.6;
    check.position.set(0, top + 2.4, -2); g.add(check); C.onFrame((dt, t) => { check.rotation.y = t * 0.8; });
    return top + 4.5;
  },
  panel() { return `<h2>🧐 Review Board</h2><p class="sub">The Critic checks the other roles' outputs for mistakes, broken links, and claims the sources don't support.</p>`; },
});
