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
    return 6;
  },
  panel() {
    const C = City, { esc } = C, N = C.needsYou(), P = (C.PRIV && C.PRIV.notices) || [], latest = C.DATA.changelog[0];
    return `<h2>📌 Notice Board</h2><p class="sub">Things waiting on you, and the latest news from the city.</p>
      <h4>Needs you (${N.length + P.length})</h4>` + (N.length || P.length
        ? N.map(a => C.card(`${C.roleById[a.role] ? C.roleById[a.role].icon + ' ' : ''}${esc(a.action)}`, esc(a.date), a.details ? `<pre>${esc(a.details)}</pre>` : '')).join('')
          + P.map(p => C.card(`🔒 ${esc(p.title)}`, 'local only', p.detail ? `<pre>${esc(p.detail)}</pre>` : '')).join('')
        : C.empty('All clear'))
      + (C.PRIV ? '' : `<p class="m">🔒 Private reminders (email/calendar) only show on your local copy.</p>`)
      + (latest ? `<h4>Latest build</h4>` + C.card(esc(latest.title), '', `<pre>${latest.items.slice(0, 8).map(i => '• ' + esc(i)).join('\n')}</pre>`) : '');
  },
});
