// Treasury: the Auditor's cost reviews. Savings are always labeled estimates.
City.building({
  id: 'treasury', name: 'Treasury', icon: '🧾', block: [0, 2], role: 'auditor', small: true,
  sub: () => 'token budget',
  build(g) {
    const C = City, y0 = C.BASE;
    C.box(g, 24, 1, 16, C.M.stone, 0, y0 + 0.5, -1);
    C.box(g, 20, 9, 12, C.M.white, 0, y0 + 5.5, -2.5, true);
    C.columns(g, 6, 16, 4.5, 8, y0 + 1, 0.5);
    C.box(g, 21, 1, 14, C.M.white, 0, y0 + 9.5, -1.5);
    C.gable(g, 21, 3, 14, -8.5, y0 + 10, C.M.white);
    C.box(g, 3, 5, 0.3, C.M.warm, 0, y0 + 3.5, 3.6);
    const coin = new THREE.Mesh(new THREE.CylinderGeometry(2, 2, 0.5, 28), C.M.gold); coin.rotation.x = Math.PI / 2; coin.position.set(0, y0 + 16.5, -2); g.add(coin);
    C.onFrame((dt, t) => { coin.rotation.z = 0; coin.rotation.y = t * 1.2; });
    return y0 + 19;
  },
  panel() {
    return `<h2>🧾 Treasury</h2><p class="sub">The Auditor looks for ways to spend fewer tokens on Agent City so you have more for real work. Savings shown are estimates, never exact counts.</p>`;
  },
});
