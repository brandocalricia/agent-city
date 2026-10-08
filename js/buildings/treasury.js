// Treasury: the Auditor's cost reviews. Savings are always labeled estimates.
City.building({
  id: 'treasury', name: 'Treasury', icon: '🧾', block: [0, 2], role: 'auditor', small: true,
  sub: () => 'cost ledger · 3 cost agents',
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
    const C = City, { esc } = C, K = (C.DATA.costs || {}), L = K.ledger || [], S = K.savings || [];
    const max = Math.max(1, ...L.map(e => e.kb_pushed || 0));
    const trend = L.length > 1 ? Math.round(((L[L.length - 1].kb_pushed || 0) / (L[0].kb_pushed || 1) - 1) * 100) : null;
    const bar = e => `<div class="m" style="display:flex;gap:6px;align-items:center"><span style="min-width:120px">${esc(e.date)} ${esc(e.session || '')}</span><span style="display:inline-block;height:9px;border-radius:4px;background:#7dffb2;width:${Math.round(150 * (e.kb_pushed || 0) / max)}px"></span><span>${esc(e.kb_pushed)} KB · ~${esc(e.est_tokens)} tok</span></div>${e.note ? `<div class="m" style="opacity:.7;margin:-2px 0 4px 126px">${esc(e.note)}</div>` : ''}`;
    const latest = ['auditor', 'meter', 'optimizer'].map(id => { const a = C.latestFor(id), r = C.roleById[id]; return C.card(`${r.icon} ${r.name}`, esc(a ? `${a.date}: ${a.action}` : (r.idle || '')), ''); }).join('');
    return `<h2>🧾 Treasury</h2><p class="sub">Three cost agents keep Agent City cheap so you have tokens for real work: the Auditor reviews, the Meter Reader measures, the Optimizer cuts. Token numbers are estimates (bytes / 4), never exact counts.</p>`
      + latest
      + `<h4>📏 Cost ledger (content pushed per session)</h4>`
      + (L.length ? L.map(bar).join('') + (trend !== null ? `<p class="sub">Trend: ${trend >= 0 ? '+' : ''}${trend}% from first to latest entry. ${esc(K.method || '')}</p>` : '') : C.empty('No measured sessions yet'))
      + `<h4>✂️ Savings</h4>`
      + (S.length ? S.map(x => C.card(esc(x.change), esc(`${x.date} · ${x.status}${x.est_saving ? ' · ' + x.est_saving : ''}`), x.evidence ? `<div class="m">Evidence: ${esc(x.evidence)}</div>` : '')).join('') : C.empty('No savings yet'));
  },
});
