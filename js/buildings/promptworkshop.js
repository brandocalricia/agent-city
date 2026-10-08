// Prompt Workshop: copy-paste templates for working with agents + the Prompt Smith's latest tip.
(() => {
const TEMPLATES = [
  ['Delegate a task', 'Goal: <what you want done>\nContext: <links, files, background>\nDone when: <how we both know it is finished>\nOutput: <format, length>\nDon\'t: <things to avoid>'],
  ['Get a plan before work', 'Before doing anything, list your plan in 3-6 steps and the assumptions you are making. Wait for my OK.'],
  ['Study help', 'I am in <class>. Quiz me on <topic> one question at a time. Wait for my answer, tell me what I got wrong and why, then make the next question a bit harder.'],
  ['Check the work', 'Review your answer above as a strict grader: list any mistakes, unsupported claims, or missing steps, then give a corrected version.'],
  ['Turn it into a routine', 'Do this every <weekday/time>: <task>. Send me only what needs my attention, in under 5 bullets.'],
];
// Prompt linter (roadmap #4): checks a pasted prompt for the parts agents need. Runs on this device only.
const LINT = [
  ['goal', 'Goal', 'What you want done, as a clear ask', /\b(goal|task|i want|i need|please|help me|make|build|write|create|fix|find|explain|summari[sz]e|draft|plan|review|add|update|quiz)\b|\?/i, 'Goal: <what you want done>'],
  ['context', 'Context', 'Background, links, files, or who it is for', /\b(context|background|because|for my|i am|i'm|we are|currently|here is|here's|attached|below|file|repo|link|class|https?:\/\/)/i, 'Context: <links, files, background>'],
  ['done', 'Done when', 'How you both know it is finished', /\b(done when|finished when|success|until|so that|must|should|criteria|pass|works when|at least|no more than)\b/i, 'Done when: <how we both know it is finished>'],
  ['format', 'Output', 'The format or length you want back', /\b(output|format|bullets?|list|table|json|markdown|steps|words|sentences?|paragraphs?|short|brief|under \d+|one line|code block|csv)\b/i, 'Output: <format, length>'],
];
City.lintPrompt = text => {
  const t = String(text || ''), words = (t.match(/\S+/g) || []).length;
  const parts = LINT.map(([id, label, hint, re, fill]) => ({ id, label, hint, fill, ok: re.test(t) }));
  return { words, parts, score: parts.filter(p => p.ok).length, tooShort: words > 0 && words < 6 };
};
const lintSection = () => `<h4>🧹 Prompt linter</h4>`
  + `<p class="sub">Paste a prompt to see which parts agents rely on are missing. Checked on this device only; nothing is sent anywhere.</p>`
  + `<textarea id="lintInput" rows="5" spellcheck="false" placeholder="Paste or type a prompt..." aria-label="Prompt to check"></textarea>`
  + `<div id="lintResult" class="lint" aria-live="polite"><div class="m">Waiting for a prompt.</div></div>`;
function runLint() {
  const C = City, inp = document.getElementById('lintInput'), out = document.getElementById('lintResult');
  if (!inp || !out) return;
  const r = C.lintPrompt(inp.value);
  if (!r.words) { out.innerHTML = '<div class="m">Waiting for a prompt.</div>'; return; }
  const miss = r.parts.filter(p => !p.ok), add = miss.map(p => p.fill).join('\n');
  out.innerHTML = `<div class="m"><b>${r.score}/4</b> parts found${r.tooShort ? ' · very short: agents guess more on short prompts' : ''}</div>`
    + r.parts.map(p => `<div class="m ${p.ok ? 'ok' : 'bad'}">${p.ok ? '✅' : '⬜'} ${C.esc(p.label)}: ${C.esc(p.hint)}</div>`).join('')
    + (miss.length ? `<div class="m">Add these lines and fill the brackets:</div><pre>${C.esc(add)}</pre>${C.copyBtn(inp.value.replace(/\s*$/, '') + '\n\n' + add)}`
      : `<div class="m ok">Looks complete. Copy it to Grok Bot or Grok Build.</div>`);
}
document.addEventListener('input', e => { if (e.target && e.target.id === 'lintInput') runLint(); });
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
  sub: () => `Prompt linter · ${TEMPLATES.length} templates · Grok Build`,
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
      + (tip ? `<h4>Latest tip</h4>` + C.entryCard(tip) : '') + (C.newsFor ? C.newsFor('promptsmith', 2) : '')
      + lintSection()
      + `<h4>Templates</h4>` + TEMPLATES.map(([t, body]) => C.card(esc(t), '', `<pre>${esc(body)}</pre>${C.copyBtn(body)}`)).join('')
      + gbSection();
  },
});
})();
