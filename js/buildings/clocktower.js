// Clock Tower: the Timekeeper's home. Four clock faces show real Denver time.
City.building({
  id: 'clocktower', name: 'Clock Tower', icon: '⏰', block: [1, -1], role: 'timekeeper', small: true,
  sub: () => 'calendar watch',
  build(g) {
    const C = City, y0 = C.BASE, brick = C.mat(0x9a5a44), trim = C.mat(0xe9dfc8);
    C.box(g, 14, 1, 14, trim, 0, y0 + 0.5, -2);
    C.box(g, 8, 30, 8, brick, 0, y0 + 16, -2, true);
    C.box(g, 9, 1, 9, trim, 0, y0 + 25, -2);
    C.box(g, 9, 6, 9, trim, 0, y0 + 29, -2);
    const roof = new THREE.Mesh(new THREE.ConeGeometry(6.6, 8, 4), C.mat(0x3d5a6b)); roof.rotation.y = Math.PI / 4; roof.position.set(0, y0 + 36, -2); roof.castShadow = true; g.add(roof);
    for (let k = 0; k < 4; k++) {
      const a = k * Math.PI / 2, p = new THREE.Vector3(Math.sin(a) * 4.56, y0 + 29, -2 + Math.cos(a) * 4.56);
      C.makeClock(g, p, 2.3, a);
    }
    C.box(g, 3, 4.5, 0.3, C.M.warm, 0, y0 + 3.2, 2.05);
    for (let y = 8; y < 22; y += 5) C.box(g, 1.4, 2.6, 0.2, C.M.warm, 0, y0 + y, 2.05);
    return 40;
  },
  panel() {
    return `<h2>⏰ Clock Tower</h2><p class="sub">The Timekeeper watches today and tomorrow on your calendar: clashes, early starts, and open study blocks. Mountain time.</p>`;
  },
});
