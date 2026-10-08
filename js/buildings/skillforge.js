// Skill Forge: how to turn a repeated task into a saved skill (+ the Librarian's current proposal).
City.building({
  id: 'skillforge', name: 'Skill Forge', icon: '⚒', block: [-2, 1], small: true,
  sub: () => 'turn repeats into skills',
  build(g) {
    const C = City, y0 = C.BASE;
    const top = C.simpleBuilding(g, { w: 18, d: 14, h: 8, color: 0x4a3a33, roofColor: 0x2a2220, sign: { text: 'SKILL FORGE', bg: '#2a1206', fg: '#ffb35c' } });
    C.box(g, 2.4, 9, 2.4, C.mat(0x5a4038), 6, top + 4.5, -5);
    const fire = new THREE.MeshStandardMaterial({ color: 0x331100, emissive: 0xff6a1a, emissiveIntensity: 2.5 });
    C.box(g, 4, 2.4, 0.3, fire, -5.5, y0 + 1.6, 5.1);
    const anvil = C.box(g, 2, 1, 1, C.M.dark, -5.5, y0 + 1.2, 8.5); C.box(g, 0.8, 0.7, 0.6, C.M.dark, -5.5, y0 + 0.35, 8.5);
    const embers = []; for (let k = 0; k < 6; k++) { const e = C.box(g, 0.15, 0.15, 0.15, fire, -5.5, y0 + 2, 5.6); e.castShadow = false; embers.push(e); }
    C.onFrame((dt, t) => { fire.emissiveIntensity = 2.2 + Math.sin(t * 9) * 0.5; embers.forEach((e, k) => { const p = (t * 0.6 + k / 6) % 1; e.position.set(-5.5 + Math.sin(k * 7 + t) * 1.2, C.BASE + 2 + p * 5, 5.6 + p); e.visible = p < 0.9; }); });
    return top + 9;
  },
  panel() {
    const C = City, lib = C.latestFor('librarian');
    const say = 'Save what we just did as a skill called <short-name>. Include when to use it, the steps, and what the output should look like.';
    return `<h2>⚒ Skill Forge</h2><p class="sub">A skill is a saved recipe your assistants can reuse. Forge one whenever you notice yourself asking for the same thing twice.</p>
      <h4>How to forge a skill</h4>
      ${C.card('1. Spot the repeat', 'Something you ask for every week: a brief, a study quiz, an inbox sweep, a city build.')}
      ${C.card('2. Do it once, well', 'Run the task with Grok Bot until the result is exactly what you want.')}
      ${C.card('3. Save it', 'Say the line below right after a good run.', `<pre>${C.esc(say)}</pre>${C.copyBtn(say)}`)}
      ${C.card('4. Use it', 'Next time just say "use my <short-name> skill". It will show up as a book in the Library.')}`
      + (lib ? `<h4>📖 Librarian's latest</h4>` + C.entryCard(lib) : '');
  },
});
