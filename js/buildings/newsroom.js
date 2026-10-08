// Newsroom: the Reporter's morning digest of LLM, agent, Grok/Grok Build, and study-relevant news (news.json, 14 days).
City.building({
  id: 'newsroom', name: 'Newsroom', icon: '📰', block: [1, 2], role: 'reporter', small: true,
  sub: () => { const n = (City.DATA.news || []).length; return n ? `${n} stories · last 14 days` : 'first digest tomorrow morning'; },
  build(g) {
    const C = City, y0 = C.BASE;
    const top = C.simpleBuilding(g, { w: 20, d: 14, h: 11, color: 0x8c3b32, roofColor: 0x2f3440,
      sign: { text: 'NEWSROOM', bg: '#151515', fg: '#f4f1e8' } });
    // a rolling news ticker under the sign and a rooftop mast with a blinking light
    const cv = document.createElement('canvas'); cv.width = 1024; cv.height = 64;
    const x = cv.getContext('2d'); x.fillStyle = '#0d1117'; x.fillRect(0, 0, 1024, 64);
    x.font = 'bold 36px system-ui'; x.fillStyle = '#ffd166';
    const heads = (C.DATA.news || []).slice(0, 4).map(n => n.title).join('   •   ') || 'AGENT CITY NEWS   •   MORNING DIGEST';
    x.fillText(heads + '   •   ' + heads, 10, 45);
    const tex = new THREE.CanvasTexture(cv); tex.wrapS = THREE.RepeatWrapping; tex.repeat.set(0.5, 1); tex.colorSpace = THREE.SRGBColorSpace;
    const tick = new THREE.Mesh(new THREE.PlaneGeometry(18, 1), new THREE.MeshBasicMaterial({ map: tex }));
    tick.position.set(0, y0 + 5, 5.25); g.add(tick);
    C.box(g, 0.3, 7, 0.3, C.M.metal, 6, top + 3.5, -4);
    const lamp = new THREE.Mesh(new THREE.SphereGeometry(0.45, 10, 8), new THREE.MeshBasicMaterial({ color: 0xff4d4d })); lamp.position.set(6, top + 7.2, -4); g.add(lamp);
    C.onFrame((dt, t) => { tex.offset.x = (t * 0.04) % 1; lamp.visible = (t % 1.6) < 0.8; });
    return top + 7.6;
  },
  panel() {
    const C = City, { esc } = C, N = C.DATA.news || [];
    const dest = { council: '⚖️ Council', scout: '🧭 Scout', promptsmith: '✍️ Prompt Smith', gb: '🧩 Grok Build', tutor: '🎓 Tutor' };
    const byDate = {}; N.forEach(n => (byDate[n.date] = byDate[n.date] || []).push(n));
    return `<h2>📰 Newsroom</h2><p class="sub">Every morning the Reporter reads the latest LLM, agent, Grok and Grok Build news and keeps a short digest: what happened, why it matters for the city or Grok Build, and which role it feeds. Stories expire after 14 days.</p>`
      + (N.length ? Object.keys(byDate).map(d => `<h4>🗞 ${esc(d)} (${byDate[d].length})</h4>` + byDate[d].map(n => C.card(
          `<a href="${esc(n.url)}" target="_blank" rel="noopener">${esc(n.title)}</a> <span class="badge">${esc(n.tag)}</span>`,
          esc(n.source || ''),
          `<div class="m">${esc(n.why)}</div>` + ((n.for || []).length ? `<div class="m" style="opacity:.75">Feeds: ${(n.for || []).map(f => dest[f] || esc(f)).join(', ')}</div>` : ''))).join('')).join('')
        : C.empty('No stories yet', 'The Reporter files the first digest in the next morning session.'));
  },
});
// Other panels show the stories routed to them: City.newsFor('council'|'scout'|'promptsmith'|'gb'|'tutor')
City.newsFor = (dest, n = 3) => {
  const C = City, { esc } = C, L = (C.DATA.news || []).filter(x => (x.for || []).includes(dest)).slice(0, n);
  return L.length ? `<h4>📰 From the Newsroom</h4>` + L.map(x => C.card(`<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.title)}</a>`, esc(`${x.date} · ${x.tag}`), `<div class="m">${esc(x.why)}</div>`)).join('') : '';
};
