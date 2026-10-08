// Prompt Workshop: copy-paste templates for working with agents + the Prompt Smith's latest tip.
(() => {
const TEMPLATES = [
  ['Delegate a task', 'Goal: <what you want done>\nContext: <links, files, background>\nDone when: <how we both know it is finished>\nOutput: <format, length>\nDon\'t: <things to avoid>'],
  ['Get a plan before work', 'Before doing anything, list your plan in 3-6 steps and the assumptions you are making. Wait for my OK.'],
  ['Study help', 'I am in <class>. Quiz me on <topic> one question at a time. Wait for my answer, tell me what I got wrong and why, then make the next question a bit harder.'],
  ['Check the work', 'Review your answer above as a strict grader: list any mistakes, unsupported claims, or missing steps, then give a corrected version.'],
  ['Turn it into a routine', 'Do this every <weekday/time>: <task>. Send me only what needs my attention, in under 5 bullets.'],
];
const REPO = 'https://github.com/brandocalricia/agent-city/blob/main/grok-build/';
const INSTALL = 'curl -fsSL https://raw.githubusercontent.com/brandocalricia/agent-city/main/grok-build/install.sh | bash';
function gbSection() {
  const C = City, { esc } = C, Q = (window.CITY_DATA && CITY_DATA.gb) || [];
  const link = (f, t) => `<a href="${REPO}${f}" target="_blank" rel="noopener">${t}</a>`;
  return `<h4>🛠️ Grok Build</h4>`
    + C.card('Install once', 'Adds the city council, review-and-apply, and these prompts to Grok Build; a session-start hook keeps them current.', `<pre>${esc(INSTALL)}</pre>${C.copyBtn(INSTALL)}`)
    + C.card('Files', '', `<div class="m">${link('README.md', 'How it works')} · ${link('prompts.md', 'Grok Build prompts')} · ${link('suggestions.md', 'Suggestions feed')} · ${link('skills/city-council/SKILL.md', 'city-council')} · ${link('skills/city-apply/SKILL.md', 'city-apply')}</div>`)
    + `<p class="sub">Apply queue (${Q.length}): Grok Build's own council rules on each; YES is built only if its checks pass before and after and its tests pass, else it rolls back. NO is recorded.</p>`
    + Q.map(i => C.card(esc(i.id), esc(`${i.size} · ${i.target} · ${i.date}`), `<div class="m">${esc(i.change)}</div>`
      + `<div class="m">✔ ${(i.checks || []).length} checks · 🧪 ${(i.tests || []).length} tests</div>`)).join('');
}
City.building({
  id: 'promptworkshop', name: 'Prompt Workshop', icon: '✍️', block: [1, 1], role: 'promptsmith', small: true,
  sub: () => `${TEMPLATES.length} templates · Grok Build`,
  build(g) {
    const C = City, y0 = C.BASE;
    const top = C.simpleBuilding(g, { w: 20, d: 14, h: 9, color: 0x3b3550, roofColor: 0x222033 });
    const neon = C.sign(g, [{ text: '{ PROMPT WORKSHOP }', font: 'bold 54px ui-monospace, monospace' }], { w: 15, h: 2.4, y: y0 + 11, z: 3, bg: '#14051a', fg: '#ff6fb5' });
    C.box(g, 0.3, 1.8, 0.3, C.M.dark, -5, y0 + 9.6, 3); C.box(g, 0.3, 1.8, 0.3, C.M.dark, 5, y0 + 9.6, 3);
    C.onFrame((dt, t) => { neon.material.color.setScalar(Math.sin(t * 6) > -0.92 ? 1.6 : 0.4); });
    return top + 4;
  },
  panel() {
    const C = City, { esc } = C, tip = C.latestFor('promptsmith');
    return `<h2>✍️ Prompt Workshop</h2><p class="sub">Small habits that make agents much more reliable. Copy a template, fill the brackets, paste it to Grok Bot.</p>`
      + (tip ? `<h4>Latest tip</h4>` + C.entryCard(tip) : '')
      + `<h4>Templates</h4>` + TEMPLATES.map(([t, body]) => C.card(esc(t), '', `<pre>${esc(body)}</pre>${C.copyBtn(body)}`)).join('')
      + gbSection();
  },
});
})();
