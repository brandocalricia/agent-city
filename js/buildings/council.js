// Council Chamber: the Council decides Notice Board items and city decisions with the council skill.
// Verdicts come from activity.json entries with role 'council' ({question, size, verdict, confidence, reason}).
City.building({
  id: 'council', name: 'Council Chamber', icon: '⚖️', block: [-1, -2], role: 'council', small: true,
  sub: () => { const V = City.activityFor('council').filter(a => a.verdict); return V.length ? City.plural(V.length, 'verdict') : 'first session soon'; },
  build(g) {
    const C = City, M = C.M, y0 = C.BASE;
    const step = (r, h, y) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r + 0.4, h, 40), M.stone); m.position.set(0, y + h / 2, 0); m.receiveShadow = m.castShadow = true; g.add(m); };
    step(13, 0.6, y0); step(12, 0.6, y0 + 0.6);
    const base = y0 + 1.2;
    const hall = new THREE.Mesh(new THREE.CylinderGeometry(8, 8, 9, 32), M.white); hall.position.set(0, base + 4.5, 0); hall.castShadow = true; hall.userData.solid = true; g.add(hall);
    const col = new THREE.CylinderGeometry(0.5, 0.58, 9, 12);
    for (let k = 0; k < 14; k++) { const a = k / 14 * Math.PI * 2, c = new THREE.Mesh(col, M.white); c.position.set(Math.sin(a) * 10.6, base + 4.5, Math.cos(a) * 10.6); c.castShadow = true; g.add(c); }
    const ring = new THREE.Mesh(new THREE.CylinderGeometry(11.5, 11.5, 1.2, 40), M.white); ring.position.set(0, base + 9.6, 0); ring.castShadow = true; g.add(ring);
    const dome = new THREE.Mesh(new THREE.SphereGeometry(8.4, 32, 12, 0, Math.PI * 2, 0, Math.PI / 2), C.mat(0x6a4fa3, { metalness: 0.3, roughness: 0.5 }));
    dome.position.set(0, base + 10.2, 0); dome.castShadow = true; g.add(dome);
    const lamp = new THREE.MeshStandardMaterial({ color: 0x3a1040, emissive: 0xe040fb, emissiveIntensity: 1.6 }); C.emissiveMats && C.emissiveMats.push(lamp);
    const orb = new THREE.Mesh(new THREE.SphereGeometry(0.8, 16, 12), lamp); orb.position.set(0, base + 19.2, 0); g.add(orb);
    C.box(g, 0.25, 1.2, 0.25, M.dark, 0, base + 18.2, 0);
    C.onFrame((dt, t) => { lamp.emissiveIntensity = 1.3 + Math.sin(t * 1.5) * 0.4; });
    C.box(g, 3.2, 5, 0.3, M.warm, 0, base + 2.5, 8.05);
    C.sign(g, [{ text: 'COUNCIL CHAMBER', font: 'bold 46px Georgia, serif', color: '#f6e7ff' }], { w: 9, h: 1.6, y: base + 7.2, z: 8.12, bg: '#2a1838' });
    return base + 20;
  },
  panel() {
    const C = City, { esc } = C, V = C.activityFor('council').filter(a => a.verdict);
    const yes = V.filter(a => /^yes/i.test(a.verdict)).length, no = V.length - yes;
    const badge = (txt, bg, fg) => `<span class="badge" style="background:${bg};color:${fg}">${esc(txt)}</span>`;
    return `<h2>⚖️ Council Chamber</h2><p class="sub">The Council decides every Notice Board item and city decision on its own, using your council skill and checking each ruling against your ideals.</p>
      ${C.card('How it decides', '', `<pre>Quick Council (minor): 3 seats, by default the Pragmatist, Risk Officer and Resource Realist, plus a short King verdict and one Red Team strike.
Full Council (important: hard to undo, costs money, publishes under your name, deletes data, raises recurring cost, or changes direction): 14 seats + King + Red Team.
YES: built right away. NO: the item is closed with a reason.
Actions only you can take (sign-ups, payments, messages) stay on the Notice Board.</pre>`)}
      ${(C.DATA.ideals || []).length ? `<h4>Ideals it rules by</h4><div class="card"><div class="m">${C.DATA.ideals.map(i => `<b>${i.n}. ${esc(i.title)}</b>`).join(' · ')}</div><div class="m">Full text in IDEALS.md. Every verdict notes how it fits.</div></div>` : ''}
      ${C.newsFor ? C.newsFor('council', 3) : ''}<h4>Verdicts (${V.length}) ${badge(yes + ' YES', 'rgba(125,255,178,.2)', '#7dffb2')}${badge(no + ' NO', 'rgba(255,92,92,.2)', '#ff8a8a')}</h4>`
      + (V.length ? V.map(a => C.card(esc(a.question || a.action),
          `${esc(a.date)} · ${esc(a.size || 'Quick')} Council`,
          `<div>${/^yes/i.test(a.verdict) ? badge('YES', 'rgba(125,255,178,.2)', '#7dffb2') : badge('NO', 'rgba(255,92,92,.2)', '#ff8a8a')}${a.confidence ? badge('confidence ' + a.confidence + '/10', 'rgba(94,231,255,.15)', '#5ee7ff') : ''}</div>`
          + (a.reason ? `<div class="m">${esc(a.reason)}</div>` : '') + (a.ideals ? `<div class="m">Ideals: ${esc(a.ideals)}</div>` : '') + (a.details ? `<div class="m">${esc(a.details)}</div>` : ''))).join('')
        : C.empty('No verdicts yet', 'The Council takes its first decisions in the next session.'));
  },
});
