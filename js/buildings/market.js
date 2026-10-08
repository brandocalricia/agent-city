// Market: the Scout's finds, freshest first. New finds (<3 days) get a badge; approve one to hand it to the Toolsmith.
City.building({
  id: 'market', name: 'Market', icon: '🛒', block: [0, 1], role: 'scout', key: 4,
  sub: () => City.DATA.finds.length ? City.plural(City.DATA.finds.length, 'find') : 'scouts start tomorrow',
  build(g) {
    const C = City, M = C.M, y0 = C.BASE;
    C.box(g, 28, 8, 13, C.mat(0xf1e6cf), 0, y0 + 4, -1.5, true);
    C.box(g, 29, 0.8, 14, C.mat(0xc0563a), 0, y0 + 8.3, -1.5);
    const glow = new THREE.MeshStandardMaterial({ color: 0x3a2a14, emissive: 0xffd99a, emissiveIntensity: 1.1 }); C.emissiveMats.push(glow);
    C.box(g, 24, 4.6, 0.3, glow, 0, y0 + 2.8, 5.05);
    const stripes = document.createElement('canvas'); stripes.width = 256; stripes.height = 16; const sg = stripes.getContext('2d');
    for (let k = 0; k < 16; k++) { sg.fillStyle = k % 2 ? '#f5f1e8' : '#2e9b5f'; sg.fillRect(k * 16, 0, 16, 16); }
    const st = new THREE.CanvasTexture(stripes); st.colorSpace = THREE.SRGBColorSpace;
    C.box(g, 28, 0.2, 4, new THREE.MeshStandardMaterial({ map: st }), 0, y0 + 6, 6.9).rotation.x = 0.35;
    C.sign(g, [{ text: 'MARKET', font: 'bold 84px system-ui' }], { w: 14, h: 2.6, y: y0 + 10, z: 4.85, bg: '#0f2a1c', fg: '#8dffb9' });
    for (const s of [-1, 1]) C.box(g, 0.3, 2.2, 0.3, M.dark, s * 5, y0 + 9, 4.6);
    const fruit = new THREE.SphereGeometry(0.28, 8, 6), fm = [0xe8463a, 0xf39a2d, 0xf3d23a, 0x6cc04a].map(c => C.mat(c, { roughness: 0.5 }));
    for (let k = 0; k < 6; k++) {
      const x = -10 + k * 4, z = 9.5; C.box(g, 2.4, 1, 1.6, M.wood, x, y0 + 0.5, z);
      for (let f = 0; f < 10; f++) { const m = new THREE.Mesh(fruit, fm[k % 4]); m.position.set(x - 0.9 + (f % 5) * 0.45, y0 + 1.15, z - 0.35 + Math.floor(f / 5) * 0.6); g.add(m); }
    }
    return 13;
  },
  panel() {
    const C = City, { esc } = C, F = C.DATA.finds, now = Date.now();
    const age = f => (now - new Date(f.date + 'T12:00:00').getTime()) / 864e5;
    return `<h2>🛒 The Market</h2><p class="sub">The Scout researches useful tools and resources and brings the best finds back here, freshest first.</p>
      <h4>Finds (${F.length})</h4>` + (F.length
        ? F.map(f => C.card((f.url ? `<a href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.title)}</a>` : esc(f.title)) + (age(f) < 3 ? '<span class="badge new">new</span>' : '') + (f.status === 'approved' ? '<span class="badge">approved</span>' : ''),
            `${esc(f.source)}${f.date ? ' · ' + esc(f.date) : ''}`, (f.why_useful ? `<pre>${esc(f.why_useful)}</pre>` : '') + (f.status !== 'approved' ? C.copyBtn(`Approve the Market find "${f.title}" for the Toolsmith.`) : ''))).join('')
          + `<p class="m">Like one? Copy its approval line and send it to Grok Bot; the Toolsmith only works on approved finds.</p>`
        : C.empty('Scouts start shopping tomorrow', 'Finds appear here once finds.json gets its first entry.'));
  },
});
