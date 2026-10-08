// Post Office: the Courier's home. Email flags stay private (local copy only).
City.building({
  id: 'postoffice', name: 'Post Office', icon: '✉️', block: [-1, -1], role: 'courier', small: true,
  sub: () => 'inbox triage',
  build(g) {
    const C = City, y0 = C.BASE;
    const top = C.simpleBuilding(g, { w: 22, d: 14, h: 10, color: 0xb5513f, roofColor: 0x40464f, sign: { text: 'POST OFFICE', bg: '#13233f', fg: '#ffffff' } });
    const box = C.box(g, 1.4, 2.2, 1.2, C.mat(0x2456c9), 6, y0 + 1.1, 8); C.box(g, 1.5, 0.4, 1.3, C.mat(0x2456c9), 6, y0 + 2.4, 8);
    C.box(g, 0.2, 9, 0.2, C.M.metal, -9, y0 + 4.5, 8);
    const flag = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 1.6), new THREE.MeshStandardMaterial({ color: 0x4f8cff, side: THREE.DoubleSide, emissive: 0x0a1d44 }));
    flag.position.set(-7.6, y0 + 8.1, 8); g.add(flag); C.onFrame((dt, t) => { flag.rotation.y = Math.sin(t * 2.1 + 1) * 0.3; });
    return top;
  },
  panel() {
    return `<h2>✉️ Post Office</h2><p class="sub">The Courier reads the last few days of Gmail (read-only) and flags what actually needs you. Details never leave your computer.</p>`;
  },
});
