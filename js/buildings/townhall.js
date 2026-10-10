// Town Hall (Council): central hub of the office. In the SVG office, this is the center desk.
// Old 3D build() removed; panel() data exposed for feed/popover.
City.building({
  id: 'townhall', name: 'Town Hall (Council)', icon: '🏛', pos: [0, 0], role: 'council', roles: ['council', 'inspector'],
  sub: () => { const V = City.activityFor('council').filter(a => a.verdict); return `the hub · ${V.length ? City.plural(V.length, 'verdict') : 'first verdict soon'} · ${City.ROLES.length} roles`; },
  // No 3D build() in new architecture
  panel() {
    const C = City, { esc } = C, A = C.DATA.agents;
    return `<h2>🏛 Town Hall (Council)</h2><p class="sub">The heart of the city. The Council decides here, the Inspector checks the city from here. The clocks show real Denver time.</p>`
      + (C.councilSection ? C.councilSection() : '')
      + `<h4>Assistants (${A.length})</h4>` + (A.length ? A.map(a => C.card(`${esc(a.name)}${a.active ? '<span class="badge">primary</span>' : ''}`, esc(a.title || (a.active ? 'Primary assistant' : 'Assistant')), a.description ? `<pre>${esc(a.description)}</pre>` : '')).join('') : C.empty('No agents found'))
      + `<h4>Roles (${C.ROLES.length})</h4>` + C.ROLES.map(r => { const l = C.latestFor(r.id); return C.card(`<a href="#" data-role="${r.id}">${r.icon} ${r.name}</a>${r.private ? '<span class="badge lockb">private</span>' : ''}`, esc(l ? `${l.date}: ${l.action}` : (r.idle || 'Starts work next session'))); }).join('');
  },
});