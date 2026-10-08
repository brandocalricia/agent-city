// Notice Board (plaza): what needs you, plus the latest news. Private notices only appear on the local copy.
City.building({
  id: 'noticeboard', name: 'Notice Board', icon: '📌', pos: [-13, 13], rot: -Math.PI / 4, small: true,
  sub: () => { const n = City.needsYou().length + ((City.PRIV && City.PRIV.notices) || []).length; return n ? `${n} need you` : 'all clear'; },
  build(g) {
    const C = City, y0 = C.BASE, n = C.needsYou().length + ((C.PRIV && C.PRIV.notices) || []).length;
    C.box(g, 0.3, 4.5, 0.3, C.M.wood, -2.6, y0 + 2.25, 0); C.box(g, 0.3, 4.5, 0.3, C.M.wood, 2.6, y0 + 2.25, 0);
    C.box(g, 6, 3.4, 0.25, C.mat(0x8a6440), 0, y0 + 3.2, 0);
    C.sign(g, [{ text: 'NOTICE BOARD', font: 'bold 44px system-ui', color: '#3b2a16', y: 34 }, { text: n ? `${n} item${n === 1 ? '' : 's'} need you` : 'All clear', font: 'bold 40px system-ui', color: n ? '#b3261e' : '#2e7d32', y: 92 }], { w: 5.4, h: 2.8, y: y0 + 3.2, z: 0.14, bg: '#f3ead2' });
    C.box(g, 6.6, 0.4, 0.6, C.mat(0x5a4030), 0, y0 + 5.1, 0);
    // All-clear confetti: one short burst on load (and when the panel opens) while nothing needs you
    const K = 140, pos = new Float32Array(K * 3), colr = new Float32Array(K * 3), vel = [], c = new THREE.Color();
    for (let k = 0; k < K; k++) { c.setHSL(Math.random(), 0.85, 0.6); colr.set([c.r, c.g, c.b], k * 3); vel.push(new THREE.Vector3()); }
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('color', new THREE.BufferAttribute(colr, 3));
    const pts = new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.35, vertexColors: true })); pts.visible = false; pts.frustumCulled = false; g.add(pts);
    let life = 0;
    C.noticeConfetti = () => { for (let k = 0; k < K; k++) { pos.set([0, y0 + 5.6, 0], k * 3); vel[k].set((Math.random() - 0.5) * 6, 5 + Math.random() * 5, (Math.random() - 0.5) * 6); } life = 3; pts.visible = true; };
    C.onFrame(dt => { if (life <= 0) return; life -= dt; for (let k = 0; k < K; k++) { const v = vel[k]; v.y -= 9 * dt; pos[k * 3] += v.x * dt; pos[k * 3 + 1] = Math.max(y0 + 0.1, pos[k * 3 + 1] + v.y * dt); pos[k * 3 + 2] += v.z * dt; } geo.attributes.position.needsUpdate = true; if (life <= 0) pts.visible = false; });
    if (!n) setTimeout(C.noticeConfetti, 1500);
    return 6;
  },
  panel() {
    const C = City, { esc } = C, N = C.needsYou(), P = (C.PRIV && C.PRIV.notices) || [], latest = C.DATA.changelog[0];
    if (!N.length && !P.length && C.noticeConfetti) C.noticeConfetti();
    return `<h2>📌 Notice Board</h2><p class="sub">Things waiting on you, and the latest news from the city.</p>
      <h4>Needs you (${N.length + P.length})</h4>` + (N.length || P.length
        ? N.map(a => C.card(`${C.roleById[a.role] ? C.roleById[a.role].icon + ' ' : ''}${esc(a.action)}`, esc(a.date), (a.details ? `<pre>${esc(a.details)}</pre>` : '') + (a.link ? `<div class="m"><a href="${esc(a.link)}" target="_blank" rel="noopener">${esc(a.link)}</a></div>` : ''))).join('')
          + P.map(p => C.card(`🔒 ${esc(p.title)}`, 'local only', p.detail ? `<pre>${esc(p.detail)}</pre>` : '')).join('')
        : C.empty('All clear'))
      + (C.PRIV ? '' : `<p class="m">🔒 Private reminders (email/calendar) only show on your local copy.</p>`)
      + (latest ? `<h4>Latest build</h4>` + C.card(esc(latest.title), '', `<pre>${latest.items.slice(0, 8).map(i => '• ' + esc(i)).join('\n')}</pre>`) : '');
  },
});
