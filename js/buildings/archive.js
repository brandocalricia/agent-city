// Archive: the Archivist's two-line weekly summaries (Sundays).
City.building({
  id: 'archive', name: 'Archive', icon: '🗄', block: [-2, 0], role: 'archivist', small: true,
  sub: () => City.plural(City.activityFor('archivist').length, 'weekly summary').replace('summarys', 'summaries'),
  build(g) {
    const C = City, y0 = C.BASE, stone = C.mat(0xb9b2a3);
    C.box(g, 24, 0.8, 16, stone, 0, y0 + 0.4, -1);
    C.box(g, 20, 7, 12, stone, 0, y0 + 4.3, -2, true);
    C.columns(g, 4, 12, 4.8, 6, y0 + 0.8, 0.5, C.M.stone);
    C.box(g, 22, 1, 14, C.mat(0x8f887a), 0, y0 + 8.3, -1.5);
    const door = new THREE.Mesh(new THREE.CylinderGeometry(1.8, 1.8, 0.4, 20), C.M.gold); door.rotation.x = Math.PI / 2; door.position.set(0, y0 + 3.2, 4.1); g.add(door);
    return y0 + 9;
  },
  panel() { return `<h2>🗄 Archive</h2><p class="sub">Every Sunday the Archivist files a two-line summary of the week in Agent City.</p>`; },
});
