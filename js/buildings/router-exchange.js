// Router Exchange: OmniRoute snapshot (providers, last route, compression, lanes). No separate app shell.
City.building({
  id: 'routerexchange', name: 'Router Exchange', icon: '🔀', block: [0, -1], small: true,
  sub: () => { const last = (City.DATA.omniroute || {}).last || {}; return last.provider ? `${last.provider} · ${last.strategy || 'route'}` : 'no route measured'; },
  build(g) {
    const C = City, y0 = C.BASE, teal = C.mat(0x1a3a40, { metalness: 0.35, roughness: 0.45 });
    C.box(g, 22, 1, 16, C.M.stone, 0, y0 + 0.5, -1);
    C.box(g, 16, 10, 12, teal, 0, y0 + 6, -2, true);
    C.box(g, 17, 0.6, 13, C.M.metal, 0, y0 + 11.3, -2);
    C.box(g, 0.35, 10, 0.35, C.M.metal, 0, y0 + 16.5, -2);
    const dishM = C.mat(0x9aa0aa, { metalness: 0.7, roughness: 0.3 });
    const dish = (x, ry) => { const o = new THREE.Mesh(new THREE.SphereGeometry(2.2, 16, 10, 0, Math.PI), dishM); o.rotation.set(-0.55, ry, 0); o.position.set(x, y0 + 14.2, -2); o.castShadow = true; g.add(o); };
    dish(-4.2, 0.4); dish(4.2, Math.PI - 0.4);
    const lamp = new THREE.MeshStandardMaterial({ color: 0x083018, emissive: 0x5ee7ff, emissiveIntensity: 1.6 }); C.emissiveMats.push(lamp);
    for (let i = 0; i < 3; i++) { const n = new THREE.Mesh(new THREE.SphereGeometry(0.42, 12, 10), lamp); n.position.set(-3 + i * 3, y0 + 8, 4.15); g.add(n); }
    C.onFrame((dt, t) => { lamp.emissiveIntensity = 1.2 + Math.sin(t * 3) * 0.55; });
    C.box(g, 3, 5, 0.3, C.M.warm, 0, y0 + 3.5, 4.15);
    C.sign(g, [{ text: 'ROUTER EXCHANGE', font: 'bold 40px system-ui', color: '#c8fff6' }], { w: 12, h: 1.3, y: y0 + 10.4, z: 4.15, bg: '#102428' });
    return y0 + 22;
  },
  panel() {
    const C = City, { esc } = C, O = C.DATA.omniroute || {}, P = O.providers || [], last = O.last || {}, lanes = O.lanes || {}, Q = O.quota || {}, S = O.swarm || {}, cmp = O.compression || {};
    const k = n => n == null || n === '' ? '–' : String(n);
    const tile = (big, label, hint) => `<div class="tile"><b>${big}</b><span>${label}</span><small>${hint}</small></div>`;
    const free = (lanes.local || 0) + (lanes.remote_free || 0);
    const grokPct = free ? 0 : 100;
    const providers = P.length ? P.map(p => C.card(esc(p.name) + (p.chat === 'up' ? '<span class="badge">chat up</span>' : '<span class="badge lockb">chat down</span>'), esc([p.state, p.model, p.note].filter(Boolean).join(' · ')))).join('') : C.empty('No provider snapshot');
    return `<h2>🔀 Router Exchange</h2><p class="sub">OmniRoute ${esc(O.version || '')} as last measured. Numbers here are a sanitized snapshot. Savings and the weekly Grok pace live in the <a href="#" data-building="treasury">🧾 Treasury Savings Hub</a>.</p>`
      + `<h4>Providers</h4>` + providers
      + `<h4>Last routing decision</h4>` + (last.provider ? `<div class="card"><div class="t">${esc(last.strategy || 'single')} · ${esc(last.provider)}${last.model ? ' · ' + esc(last.model) : ''}</div><div class="m">${esc(last.reason || '')}${last.reason ? ' · ' : ''}${k(last.latency_ms)} ms · cost ${k(last.cost)} · ${esc(O.mode || '')} · reset ${esc(O.next_reset || 'none')}</div></div>` : C.empty('No routing decision measured'))
      + `<h4>Tokens</h4><div class="big">` + tile(k(last.in), 'in', 'last routed call') + tile(k(last.out), 'out', 'last routed call') + tile(k(last.cost), 'cost', 'measured 0 on the local lane') + tile(k((P.find(p => p.context_window) || {}).context_window), 'local window', 'a Grok Build turn of about 17909 does not fit') + `</div>`
      + `<h4>Compression saved</h4>` + (cmp.mode ? `<div class="card"><div class="t">${esc(cmp.mode)} · ${esc(cmp.combo || (cmp.pipeline || []).join(' then '))}</div><div class="m">Caveman keeps code blocks: ${cmp.caveman_keeps_code ? 'yes' : 'no'}. Source ${esc(cmp.source || '–')}. Tokens saved by compression: not measured.</div></div>` : C.empty('No compression snapshot'))
      + `<h4>Quota</h4>` + (Object.keys(Q).length ? Object.keys(Q).map(n => C.card(esc(n), esc(String(Q[n])))).join('') : C.empty('Quota unknown for every pool', 'Remote free lanes: 0. Do not invent a free-tier quota.'))
      + `<h4>Swarm</h4><div class="big">` + tile(k(free), 'free lanes', `${k(lanes.local)} local · ${k(lanes.remote_free)} remote`) + tile(k(lanes.grok || 0), 'Grok lanes', `fallback ${grokPct}%`) + tile(k(S.started ?? 0), 'workers started', 'print a plan only; do not start processes') + tile(esc(S.workers_at_95pct || 'unknown'), 'at 95% of a quota', 'unknown until a real quota exists') + `</div>`
      + `<div class="m">One lane per pool. Bulk ${esc(S.bulk || 'auto/offline')}. Code ${esc(S.code || 'auto/coding')}. Re-probe every ${k(S.probe_minutes)} min. Local only while remote pools are down. Grok only when every free pool is out.</div>`;
  },
});
