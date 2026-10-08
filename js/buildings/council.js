// The Council's verdicts section (shown in Town Hall) and redirects for old links: the Council Chamber and City Hall were
// merged into Town Hall (Council) at the center of the city, so #council and #cityhall open #townhall.
// Verdicts come from activity.json entries with role 'council' ({question, size, verdict, confidence, reason}).
(() => {
const C = City;
C.buildingAliases = Object.assign(C.buildingAliases || {}, { council: 'townhall', cityhall: 'townhall', 'city-hall': 'townhall', 'council-chamber': 'townhall' });
C.councilSection = () => {
  const { esc } = C, V = C.activityFor('council').filter(a => a.verdict);
  const yes = V.filter(a => /^yes/i.test(a.verdict)).length, no = V.length - yes;
  const badge = (txt, bg, fg) => `<span class="badge" style="background:${bg};color:${fg}">${esc(txt)}</span>`;
  return `<h4>How the Council decides</h4>${C.card('Quick or Full', '', `<pre>Quick Council (minor): 3 seats, by default the Pragmatist, Risk Officer and Resource Realist, plus a short King verdict and one Red Team strike.
Full Council (important: hard to undo, costs money, publishes under your name, deletes data, raises recurring cost, or changes direction): 14 seats + King + Red Team.
YES: built right away. NO: the item is closed with a reason.
Actions only you can take (sign-ups, payments, messages) stay on the Notice Board.</pre>`)}
    ${(C.DATA.ideals || []).length ? `<div class="card"><div class="m">Ideals it rules by: ${C.DATA.ideals.map(i => `<b>${i.n}. ${esc(i.title)}</b>`).join(' · ')}</div><div class="m">Full text in IDEALS.md. Every verdict notes how it fits.</div></div>` : ''}
    ${C.newsFor ? C.newsFor('council', 3) : ''}<h4>Verdicts (${V.length}) ${badge(yes + ' YES', 'rgba(125,255,178,.2)', '#7dffb2')}${badge(no + ' NO', 'rgba(255,92,92,.2)', '#ff8a8a')}</h4>`
    + (V.length ? V.map(a => C.card(esc(a.question || a.action),
        `${esc(a.date)} · ${esc(a.size || 'Quick')} Council`,
        `<div>${/^yes/i.test(a.verdict) ? badge('YES', 'rgba(125,255,178,.2)', '#7dffb2') : badge('NO', 'rgba(255,92,92,.2)', '#ff8a8a')}${a.confidence ? badge('confidence ' + a.confidence + '/10', 'rgba(94,231,255,.15)', '#5ee7ff') : ''}</div>`
        + (a.reason ? `<div class="m">${esc(a.reason)}</div>` : '') + (a.ideals ? `<div class="m">Ideals: ${esc(a.ideals)}</div>` : '') + (a.details ? `<div class="m">${esc(a.details)}</div>` : ''))).join('')
      : C.empty('No verdicts yet', 'The Council takes its first decisions in the next session.'));
};
})();
