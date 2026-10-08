// Library: home of saved skills. One clickable book per real skill on the outdoor shelf.
City.building({
  id: 'library', name: 'Library', icon: '📚', block: [-1, 0], role: 'librarian', key: 1,
  sub: () => City.plural(City.DATA.skills.length, 'skill'),
  build(g) {
    const C = City, M = C.M, BASE = C.BASE;
    C.box(g, 30, 0.6, 24, M.stone, 0, BASE + 0.3, 0); C.box(g, 28, 0.6, 22, M.stone, 0, BASE + 0.9, 0); C.box(g, 26, 0.6, 20, M.stone, 0, BASE + 1.5, -0.5);
    const y0 = BASE + 1.8;
    C.box(g, 24, 9, 13, M.stone, 0, y0 + 4.5, -2.5, true);
    C.columns(g, 8, 21, 6, 8.2, y0, 0.55, M.stone);
    C.box(g, 25.5, 1.4, 17, M.stone, 0, y0 + 8.9, -1.2);
    C.gable(g, 25.5, 4.2, 17, -9.7, y0 + 9.6, M.roof);
    C.box(g, 4, 6, 0.3, M.warm, 0, y0 + 3, 4.05);
    for (const s of [-1, 1]) for (let k = -1; k <= 1; k++) C.box(g, 0.3, 4.5, 2, M.warm, s * 12.05, y0 + 4.5, -2.5 + k * 3.8);
    const shelf = new THREE.Group(); shelf.position.set(-10.5, BASE, 14.5); g.add(shelf);
    C.box(shelf, 7, 4.6, 1.2, M.wood, 0, 2.3, -0.3);
    for (let r = 0; r < 3; r++) C.box(shelf, 6.4, 0.15, 0.9, C.mat(0x8a6440), 0, 0.6 + r * 1.4, 0.05);
    const pal = [0xd9534f, 0x5bc0de, 0xf0ad4e, 0x5cb85c, 0x9b59b6, 0xe8e8e8];
    C.DATA.skills.slice(0, 30).forEach((s, k) => {
      const r = Math.floor(k / 10), c = k % 10;
      const b = C.box(shelf, 0.45, 1.0 + (k % 3) * 0.08, 0.7, C.mat(pal[k % pal.length], { emissive: pal[k % pal.length], emissiveIntensity: 0.25 }), -2.8 + c * 0.62, 1.2 + r * 1.4, 0.1);
      b.userData = { kind: 'skill', idx: k }; C.interactive.push(b);
    });
    C.addLabel(shelf, C.DATA.skills.length ? `📖 Skill Shelf · ${C.plural(C.DATA.skills.length, 'skill')} (click a book)` : 'No skills yet - ask Grok Bot to save one', 5.8, 'mini-sign', () => C.openPanel('building', 'library'));
    return 16;
  },
  panel() {
    const C = City, { esc } = C, S = C.DATA.skills;
    return `<h2>📚 The Library</h2><p class="sub">Home of your saved skills: reusable instructions any of your assistants can pick up and follow. Click a book on the shelf to open it.</p>
      <h4>Skills on the shelf (${S.length})</h4>` + (S.length
        ? S.map((s, k) => C.card(`<a href="#" data-skill="${k}">${esc(s.name)}</a>`, esc(s.description) + (s.updated ? ` · updated ${esc(s.updated)}` : ''))).join('')
        : C.empty('No skills yet - ask Grok Bot to save one', `After a task you'll repeat, say:<br><i>"Save what we just did as a skill called weekly-inbox-cleanup."</i>`)
          + `<p class="m">See the Skill Forge for a step-by-step guide.</p>`);
  },
});
