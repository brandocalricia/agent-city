// Treasury: plain-language cost dashboard (lifetime savings, cost per build, weekly limit vs plan, trend, biggest savings).
// All figures come from data.js treasury (tools/treasury.py over costs.json); estimates are always labeled.
City.building({
  id: 'treasury', name: 'Treasury', icon: '🧾', block: [0, 2], role: 'auditor', small: true,
  sub: () => { const t = (City.DATA.treasury || {}).lifetime; return t && t.saved_tokens ? `~${Math.round(t.saved_tokens / 1000)}k tokens saved · 3 cost agents` : 'cost ledger · 3 cost agents'; },
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
    const C = City, { esc } = C, K = C.DATA.costs || {}, L = K.ledger || [], T = C.DATA.treasury || {}, LT = T.lifetime || {}, W = T.week;
    const k = n => n == null ? '–' : n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : n >= 1e4 ? Math.round(n / 1e3) + 'k' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'k' : String(n);
    const usd = n => n == null ? 'n/a' : '$' + (n < 1 ? n.toFixed(2) : n.toFixed(2));
    const price = (T.price || {}).usd_per_mtok;
    const tile = (big, label, hint) => `<div class="tile"><b>${big}</b><span>${label}</span><small>${hint}</small></div>`;
    const tr = T.trend || [], max = Math.max(1, ...tr.map(e => Math.max(e.est_tokens, e.saved_tokens)));
    const spark = tr.length ? `<div class="spark" role="img" aria-label="Tokens written and saved per build">${tr.map(e => `<i class="cost" style="height:${Math.max(3, Math.round(e.est_tokens / max * 100))}%" title="${esc(e.session)}: ~${e.est_tokens} tokens written"></i><i style="height:${Math.max(3, Math.round(e.saved_tokens / max * 100))}%;margin-right:6px" title="${esc(e.session)}: ~${e.saved_tokens} tokens saved"></i>`).join('')}</div><div class="legend"><span style="--c:#ffb36b">written per build</span><span style="--c:#7dffb2">saved per build</span><span>oldest → newest</span></div>` : '';
    const reset = W ? (([Y, Mo, Da, h, mi]) => new Date(Date.UTC(Y, Mo - 1, Da, h, mi)).toLocaleString('en-US', { timeZone: 'UTC', weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }))(W.reset.split(/[-T:]/).map(Number)) : '';   // reset is Mountain local time
    const latest = ['auditor', 'meter', 'optimizer'].map(id => { const a = C.latestFor(id), r = C.roleById[id]; return C.card(`${r.icon} ${r.name}`, esc(a ? `${a.date}: ${a.action}` : (r.idle || ''))); }).join('');
    const max2 = Math.max(1, ...L.map(e => e.kb_pushed || 0));
    const bar = e => `<div class="m" style="display:flex;gap:6px;align-items:center"><span style="min-width:128px">${esc(e.session || e.date)}</span><span style="display:inline-block;height:9px;border-radius:4px;background:#ffb36b;width:${Math.round(130 * (e.kb_pushed || 0) / max2)}px"></span><span>${esc(e.kb_pushed)} KB · ~${k(e.est_tokens)} tok</span></div>`;
    return `<h2>🧾 Treasury</h2><p class="sub">Where the city's tokens go, and what its cost agents have saved. Numbers come from the Meter Reader's measured ledger. Tokens are estimates (file bytes ÷ 4); dollars are estimates too.</p>`
      + `<div class="big">`
      + tile('~' + k(LT.saved_tokens), 'tokens saved, lifetime', 'what the city did not have to write thanks to its savings (est.)')
      + tile(usd(LT.saved_usd), 'money saved (est.)', price ? `at $${price} per million tokens, API list price` : 'no price set')
      + tile(LT.sessions ?? '–', 'builds measured', `${(C.DATA.totals || {}).sessions || 0} sessions logged in total`)
      + tile('~' + k(LT.avg_tokens_per_build), 'cost per build', `≈ ${usd(LT.avg_usd_per_build)} each, average (est.)`)
      + `</div>`
      + `<h4>This week's Grok Bot limit</h4>`
      + (W ? `<div class="card"><div class="t">${W.est_used_pct}% used · plan ${W.pace_line_pct}% by now</div><div class="meter" role="img" aria-label="${W.est_used_pct}% used of the weekly limit"><i style="width:${Math.min(100, W.est_used_pct)}%"></i><b style="left:${Math.min(100, W.pace_line_pct)}%" title="plan by now"></b></div>`
          + `<div class="m">Latest real reading ${W.reading_at ? `${W.reading_pct}% at ${esc(W.reading_at.replace('T', ' '))}` : 'none this week'}, plus logged work since. The yellow mark is a straight line to the ${W.target_pct}% target by the reset (${esc(reset)} MT). ${W.sessions_left} sessions left, each sized from this (next: ${esc(W.recommend)}). As of ${esc(W.now.replace('T', ' '))} MT.</div></div>`
        : C.empty('Weekly numbers appear after the next local rebuild', 'They come from the local pacing file and are rebuilt every session.'))
      + `<h4>Savings trend</h4>` + (spark || C.empty('No measured builds yet'))
      + `<h4>Biggest savings</h4>` + ((T.biggest || []).length ? T.biggest.map(x => C.card(esc(x.change), `${x.tokens_saved ? '~' + k(x.tokens_saved) + ' tokens saved so far' : 'nothing measured yet'} · ${esc(x.status || '')}`, (x.est_saving ? `<div class="m">${esc(x.est_saving)}</div>` : '') + (x.link ? `<div class="m"><a href="${esc(x.link)}" target="_blank" rel="noopener">See the change</a></div>` : ''))).join('') : C.empty('No savings yet'))
      + `<h4>How these numbers are made</h4><div class="card"><div class="m">${esc(T.method || K.method || '')}</div><div class="m">${esc(T.saved_method || '')}</div><div class="m">Price: ${esc((T.price || {}).basis || 'not set')}${(T.price || {}).source ? ` <a href="${esc(T.price.source)}" target="_blank" rel="noopener">source</a>` : ''}</div>${T.cap_saved_kb_now != null ? `<div class="m">data.js cap right now: saves ${T.cap_saved_kb_now} KB per push.</div>` : ''}</div>`
      + `<h4>Cost agents</h4>` + latest
      + `<h4>Ledger (written per build)</h4>` + (L.length ? L.map(bar).join('') : C.empty('No measured sessions yet'));
  },
});
