// Stats Tower: each floor lights up for a real count (skills, active roles, finds, actions, sessions, build days).
City.building({
  id: 'statstower', name: 'Stats Tower', icon: '📊', block: [2, -1], small: true,
  sub: () => `${City.stats().find(s => s.k === 'actions').v} actions logged`,
  build(g) {
    const C = City, y0 = C.BASE, st = C.stats();
    C.box(g, 12, 1, 12, C.M.dark, 0, y0 + 0.5, -2);
    st.forEach((s, k) => {
      const lit = Math.min(1, s.v / (s.max || 10));
      const m = new THREE.MeshStandardMaterial({ color: 0x1b2333, emissive: new THREE.Color().setHSL(0.52 - k * 0.07, 0.8, 0.55), emissiveIntensity: 0.15 + lit * 1.6, metalness: 0.4, roughness: 0.3 });
      C.box(g, 9 - k * 0.6, 3.6, 9 - k * 0.6, m, 0, y0 + 1 + 1.9 + k * 4, -2, k === 0);
      C.box(g, 9.4 - k * 0.6, 0.35, 9.4 - k * 0.6, C.M.dark, 0, y0 + 1 + 3.9 + k * 4, -2);
    });
    const top = y0 + 1 + st.length * 4;
    C.box(g, 0.2, 6, 0.2, C.M.metal, 0, top + 3, -2);
    return top + 6;
  },
  panel() {
    const C = City;
    return `<h2>📊 Stats Tower</h2><p class="sub">Each floor glows brighter as its number grows. All counts come from real files.</p>`
      + C.stats().map(s => `<div class="stat"><span>${s.label}</span><b>${s.v}</b></div>`).join('');
  },
});
City.stats = () => {
  const D = City.DATA, act = D.activity;
  return [
    { k: 'skills', label: '📚 Saved skills', v: D.skills.length, max: 10 },
    { k: 'roles', label: '🧑‍🏭 Roles that have worked', v: City.ROLES.filter(r => act.some(a => a.role === r.id)).length, max: City.ROLES.length },
    { k: 'finds', label: '🛒 Market finds', v: D.finds.length, max: 20 },
    { k: 'actions', label: '📝 Logged actions', v: act.length, max: 60 },
    { k: 'sessions', label: '🔁 Work sessions', v: new Set(act.map(a => a.session).filter(Boolean)).size, max: 30 },
    { k: 'days', label: '🗓 Days built', v: new Set(D.changelog.map(e => (e.title.match(/\d{4}-\d{2}-\d{2}/) || [])[0]).filter(Boolean)).size, max: 30 },
  ];
};
