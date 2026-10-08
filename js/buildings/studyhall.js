// Study Hall: the Tutor's practice problem of the day. Type an answer, get a local check, then the solution unlocks.
City.building({
  id: 'studyhall', name: 'Study Hall', icon: '🎓', block: [-1, 1], role: 'tutor', small: true,
  sub: () => { const t = City.latestFor('tutor'); return t && t.course ? `today: ${t.course}` : 'practice problems'; },
  build(g) {
    const C = City, t = C.latestFor('tutor');
    const top = C.simpleBuilding(g, { w: 24, d: 14, h: 11, color: 0x8c3b2e, roofColor: 0x2f3b33, roof: 'gable' });
    C.sign(g, [{ text: 'STUDY HALL', font: 'bold 50px Georgia, serif', color: '#ffffff', y: 40 }, { text: t ? `Today: ${t.course || 'practice'}` : 'Problems start next session', font: '34px Georgia, serif', color: '#cde8c8', y: 95 }], { w: 12, h: 3.2, y: C.BASE + 9.4, z: 5.15, bg: '#1f3a2a' });
    return top;
  },
  panel() {
    const t = City.latestFor('tutor');
    return `<h2>🎓 Study Hall</h2><p class="sub">One practice problem per session, rotating Calc I → intro to CS → econ. Try it before opening the solution.</p>`
      + (t ? `<h4>Today's problem${t.course ? ' · ' + City.esc(t.course) : ''}</h4>` + City.problemCard(t) : '') + (City.newsFor ? City.newsFor('tutor', 2) : '')
      + ['Calc I', 'Intro to CS', 'Econ'].map(c => { const L = City.DATA.finds.filter(f => f.status === 'adopted' && f.course === c && f.url);
          return L.length ? `<h4>📚 ${c} links</h4>` + L.map(f => City.card(`<a href="${City.esc(f.url)}" target="_blank" rel="noopener">${City.esc(f.title)}</a>`, 'set up by the Toolsmith', f.why_useful ? `<div class="m">${City.esc(f.why_useful)}</div>` : '')).join('') : ''; }).join('');
  },
});

// Answer box: checked in the browser only. Expressions in x are compared numerically at sample points
// (so x^2+2x and 2x + x*x both match); anything else is compared as normalized text against `answer` / `accept`.
{
  const C = City, { esc } = C, NAMES = ['sqrt', 'sin', 'cos', 'tan', 'exp', 'abs', 'ln', 'log', 'pi', 'e', 'x'];
  const FN = { sqrt: Math.sqrt, sin: Math.sin, cos: Math.cos, tan: Math.tan, exp: Math.exp, abs: Math.abs, ln: Math.log, log: Math.log10 };
  const norm = s => String(s).toLowerCase().replace(/π/g, 'pi').replace(/\*\*/g, '^').replace(/[−–]/g, '-').replace(/\s+/g, '').replace(/^.*=/, '').replace(/\.$/, '');
  C.parseExpr = src => {   // tiny recursive-descent parser -> f(x), or null; never uses eval
    const s = norm(src), T = []; let i = 0;
    while (i < s.length) {
      const m = /^\d*\.?\d+/.exec(s.slice(i)); if (m) { T.push(+m[0]); i += m[0].length; continue; }
      const nm = NAMES.find(n => s.startsWith(n, i)); if (nm) { T.push(nm); i += nm.length; continue; }
      if ('+-*/^()'.includes(s[i])) { T.push(s[i++]); continue; }
      return null;
    }
    let k = 0; const peek = () => T[k], starts = t => t !== undefined && (typeof t === 'number' || NAMES.includes(t) || t === '(');
    const expr = () => { let a = term(); while (peek() === '+' || peek() === '-') { const op = T[k++], l = a, r = term(); a = op === '+' ? x => l(x) + r(x) : x => l(x) - r(x); } return a; };
    const term = () => { let a = unary(); for (;;) { const op = peek(); if (op === '*' || op === '/') { k++; const l = a, r = unary(); a = op === '*' ? x => l(x) * r(x) : x => l(x) / r(x); } else if (starts(op)) { const l = a, r = power(); a = x => l(x) * r(x); } else return a; } };
    const unary = () => { if (peek() === '-') { k++; const a = unary(); return x => -a(x); } if (peek() === '+') { k++; return unary(); } return power(); };
    const power = () => { const b = primary(); if (peek() === '^') { k++; const e = unary(); return x => Math.pow(b(x), e(x)); } return b; };
    const primary = () => {
      const t = T[k++];
      if (typeof t === 'number') return () => t;
      if (t === 'x') return x => x; if (t === 'pi') return () => Math.PI; if (t === 'e') return () => Math.E;
      if (FN[t]) { const a = power(); return x => FN[t](a(x)); }
      if (t === '(') { const a = expr(); if (T[k++] !== ')') throw 0; return a; }
      throw 0;
    };
    try { const f = expr(); return k === T.length ? f : null; } catch (e) { return null; }
  };
  C.checkAnswer = (given, entry) => {
    const keys = [entry.answer, ...(entry.accept || [])].filter(a => a != null && String(a).trim());
    if (!String(given || '').trim()) return 'empty';
    if (!keys.length) return 'nokey';
    const g = C.parseExpr(given), X = [0.37, 1.3, 2.1, -0.8, 3.7];
    for (const key of keys) {
      const f = C.parseExpr(key);
      if (f && g) { let ok = 0, n = 0; for (const x of X) { const a = f(x), b = g(x); if (!isFinite(a)) continue; n++; if (isFinite(b) && Math.abs(a - b) <= 1e-6 * Math.max(1, Math.abs(a))) ok++; } if (n && ok === n) return 'right'; }
      else if (norm(key) === norm(given)) return 'right';
    }
    return 'wrong';
  };
  C.problemCard = a => C.card(esc(a.action), `${esc(a.date)}${a.session ? ' · ' + esc(a.session) : ''}`,
    (a.details ? `<pre>${esc(a.details)}</pre>` : '') +
    (a.resource ? `<div class="m">📚 Study this topic: <a href="${esc(a.resource)}" target="_blank" rel="noopener">${esc(a.resource_title || a.resource)}</a></div>` : '') +
    (a.solution ? `<div class="answer"><input id="tutorAnswer" type="text" autocomplete="off" spellcheck="false" placeholder="${a.answer ? 'Your final answer, e.g. y = 2x + 1' : 'Your answer'}" aria-label="Your answer">`
      + `<button data-tutor="check">Check</button></div><div id="tutorResult" class="m" aria-live="polite">${a.answer ? 'Checked on this device only. The solution unlocks after your first try.' : 'The solution unlocks after your first try.'}</div>`
      + `<details id="tutorSolution" hidden><summary class="m">Show solution</summary><pre>${esc(a.solution)}</pre></details>` : ''));
  const run = () => {
    const t = C.latestFor('tutor'), inp = document.getElementById('tutorAnswer'), out = document.getElementById('tutorResult'), sol = document.getElementById('tutorSolution');
    if (!t || !inp || !out) return;
    const r = C.checkAnswer(inp.value, t);
    out.textContent = { empty: 'Type an answer first.', nokey: 'No answer key for this one: compare with the solution below.', right: '✅ Correct! The solution is unlocked if you want to compare.', wrong: '❌ Not quite. Try again, or open the solution below.' }[r];
    out.className = 'm ' + (r === 'right' ? 'ok' : r === 'wrong' ? 'bad' : '');
    if (r !== 'empty' && sol) sol.hidden = false;
  };
  document.addEventListener('click', e => { if (e.target.closest('[data-tutor="check"]')) { e.preventDefault(); run(); } });
  document.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target && e.target.id === 'tutorAnswer') { e.preventDefault(); run(); } });
}
