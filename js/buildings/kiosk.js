// Morning Brief kiosk (plaza): the Courier's and Timekeeper's local notes in one look at the day.
// Private notes only come from private.js on the local copy; the public site shows a clean empty state.
City.building({
  id: 'kiosk', name: 'Morning Brief', icon: '☀️', pos: [14.5, 14.5], rot: Math.PI / 4, small: true,
  sub: () => { const n = City.briefCount(); return n == null ? 'local copy only' : `${n} note${n === 1 ? '' : 's'} today`; },
  build(g) {
    const C = City, y0 = C.BASE, n = C.briefCount(), frame = C.mat(0x2b3550);
    C.box(g, 3.2, 0.5, 2.2, C.M.stone, 0, y0 + 0.25, 0, true);
    C.box(g, 0.5, 3.4, 0.5, frame, 0, y0 + 2.2, -0.3);
    C.box(g, 5.6, 3.6, 0.35, frame, 0, y0 + 4.9, 0);
    C.box(g, 6.2, 0.3, 1.4, C.mat(0xf2b544), 0, y0 + 6.85, 0.2);
    C.sign(g, [{ text: '☀ MORNING BRIEF', font: 'bold 42px system-ui', color: '#ffd27a', y: 40 }, { text: n == null ? 'local copy only' : `${n} note${n === 1 ? '' : 's'} today`, font: '36px system-ui', color: '#e8eeff', y: 96 }], { w: 5.1, h: 3.1, y: y0 + 4.9, z: 0.19, bg: '#141b33' });
    return 7;
  },
  panel() {
    const C = City, { esc } = C, P = C.PRIV, c = C.privateFor('courier'), t = C.privateFor('timekeeper'), today = C.denverDate();
    const prompt = 'Using my calendar for today and my flagged emails, give me a 3-line plan for the day with study blocks for Calc I, Econ, and intro to CS.';
    let h = `<h2>☀️ Morning Brief</h2><p class="sub">The Timekeeper's calendar notes and the Courier's inbox flags, combined into one look at your day.</p>`;
    if (!P) return h + C.empty('🔒 Private - visible on your local copy only', 'Your calendar and inbox notes never go to the public site. Open your local copy of Agent City to see today\'s brief.', 'lock')
      + `<div class="m"><a href="#" data-role="timekeeper">⏰ Timekeeper</a> · <a href="#" data-role="courier">✉️ Courier</a></div>`;
    const sec = (icon, label, role, p) => `<h4>${icon} ${label} <span class="badge lockb">🔒 local only</span></h4>` + (p
      ? (/^\d{4}-\d{2}-\d{2}/.test(p.updated || '') && !String(p.updated).startsWith(today) ? `<p class="m">⏳ Not refreshed yet today (last: ${esc(p.updated)})</p>` : '')
        + (p.summary ? C.card(esc(p.summary), esc(p.updated || '')) : '')
        + ((p.items || []).map(it => C.card(esc(it.title), esc(it.when || ''), (it.detail ? `<pre>${esc(it.detail)}</pre>` : '') + (it.link ? `<div class="m"><a href="${esc(it.link)}" target="_blank" rel="noopener">Open</a></div>` : ''))).join('') || C.empty('Nothing flagged'))
      : C.empty(`No ${label.toLowerCase()} notes yet`, `<a href="#" data-role="${role}">Open the ${C.roleById[role].name}</a>`));
    const n = C.briefCount(), needs = (P.notices || []).length;
    return h + C.card(`${n} note${n === 1 ? '' : 's'} for ${esc(today)}`, needs ? `${needs} on the <a href="#" data-building="noticeboard">Notice Board</a>` : 'Notice Board: all clear', C.copyBtn(prompt))
      + sec('📅', 'Calendar', 'timekeeper', t) + sec('✉️', 'Inbox', 'courier', c);
  },
});
City.denverDate = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Denver', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
City.briefCount = () => City.PRIV ? ['courier', 'timekeeper'].reduce((s, r) => s + (((City.PRIV[r] || {}).items) || []).length, 0) : null;
