// Roles: the city's working agents. Their real actions come from activity.json (via data.js);
// private roles (Courier, Timekeeper) only show details from private.js on the local copy.
(() => {
const C = window.City;
C.ROLES = [
  { id: 'inspector', name: 'Inspector', icon: '🔍', color: 0x6ad1ff, building: 'townhall', job: 'Checks that the city still loads and renders without errors.' },
  { id: 'builder', name: 'Builder', icon: '🔨', color: 0xffb347, building: 'office', job: 'Builds one small improvement to Agent City each session.' },
  { id: 'scout', name: 'Scout', icon: '🧭', color: 0xf08a24, building: 'market', job: 'Researches genuinely useful tools and resources and brings back finds. Read-only: never installs, stars, or signs up.' },
  { id: 'courier', name: 'Courier', icon: '✉️', color: 0x4f8cff, building: 'postoffice', private: true, job: 'Reads recent Gmail (read-only) and flags emails that need your action.' },
  { id: 'timekeeper', name: 'Timekeeper', icon: '⏰', color: 0xe6c35c, building: 'clocktower', private: true, job: 'Checks today and tomorrow on Google Calendar (read-only) for clashes, early starts, and open study blocks.' },
  { id: 'tutor', name: 'Tutor', icon: '🎓', color: 0x9b6bff, building: 'studyhall', job: 'Posts one practice problem with a hidden solution, rotating Calc I, intro to CS, and econ, linked to the matching study resource when there is one.' },
  { id: 'librarian', name: 'Librarian', icon: '📖', color: 0x5cd6a0, building: 'library', job: 'Proposes at most one repeated task worth saving as a skill. Never saves one without you.' },
  { id: 'promptsmith', name: 'Prompt Smith', icon: '✍️', color: 0xff6fb5, building: 'promptworkshop', job: 'Shares one practical prompting tip or template per session.' },
  { id: 'toolsmith', name: 'Toolsmith', icon: '🛠', color: 0xb0b8c8, building: 'workshop', job: 'Builds or sets up tools only from Market finds you approved.', idle: 'Waiting for an approved find' },
  { id: 'critic', name: 'Critic', icon: '🧐', color: 0xff5c5c, building: 'reviewboard', job: "Checks the other roles' outputs for mistakes, broken links, and unsupported claims." },
  { id: 'archivist', name: 'Archivist', icon: '🗄', color: 0xc9a26b, building: 'archive', job: 'Writes a two-line weekly summary every Sunday.', idle: 'First summary on Sunday' },
  { id: 'council', name: 'Council', icon: '⚖️', color: 0xe040fb, building: 'council', job: 'Reads IDEALS.md, then decides Notice Board items and city decisions with your council skill: a 3-seat Quick Council for minor ones, the Full Council (14 seats + King + Red Team) for important ones. YES gets built right away, NO closes the item with a reason; actions only you can take stay on the board.', idle: 'Waiting for a decision' },
  { id: 'auditor', name: 'Auditor', icon: '🧾', color: 0x7dffb2, building: 'treasury', job: 'Reviews cost signals and makes one change per run that cuts token use. Estimates are always labeled as estimates.' },
];
C.roleById = Object.fromEntries(C.ROLES.map(r => [r.id, r]));
C.activityFor = id => C.DATA.activity.filter(a => a.role === id);      // newest first (build_data.py sorts)
C.latestFor = id => C.activityFor(id)[0] || null;
C.privateFor = id => (C.PRIV && C.PRIV[id]) || null;
C.bubbleFor = id => {
  const r = C.roleById[id], p = C.privateFor(id), a = C.latestFor(id);
  if (p && p.summary) return '🔒 ' + p.summary;
  if (a) return a.action;
  return r.idle || 'Starts work next session';
};
const { esc } = C;
C.entryCard = a => C.card(esc(a.action), `${esc(a.date)}${a.session ? ' · ' + esc(a.session) : ''}`,
  (a.details ? `<pre>${esc(a.details)}</pre>` : '') +
  (a.link ? `<div class="m"><a href="${esc(a.link)}" target="_blank" rel="noopener">${esc(a.link)}</a></div>` : '') +
  (a.resource ? `<div class="m">📚 Study this topic: <a href="${esc(a.resource)}" target="_blank" rel="noopener">${esc(a.resource_title || a.resource)}</a></div>` : '') +
  (a.solution ? `<details><summary class="m">Show solution</summary><pre>${esc(a.solution)}</pre></details>` : ''));
C.roleSection = id => {
  const r = C.roleById[id]; if (!r) return '';
  const acts = C.activityFor(id), p = C.privateFor(id);
  let h = `<h4>${r.icon} ${r.name}</h4><div class="card"><div class="m">${esc(r.job)}</div></div>`;
  if (r.private || p) {
    h += p ? `<h4>Local notes <span class="badge lockb">🔒 local only</span></h4>` + (p.summary ? C.card(esc(p.summary), esc(p.updated || '')) : '') +
      (p.items || []).map(it => C.card(esc(it.title), esc(it.when || ''), (it.detail ? `<pre>${esc(it.detail)}</pre>` : '') + (it.link ? `<div class="m"><a href="${esc(it.link)}" target="_blank" rel="noopener">Open</a></div>` : ''))).join('')
      : C.empty('🔒 Private - visible on the local copy only', `Open your local copy of Agent City to see the ${r.name}'s notes.`, 'lock');
  }
  h += `<h4>History (${acts.length})</h4>` + (acts.length ? acts.slice(0, 12).map(C.entryCard).join('') : C.empty(r.idle || 'Starts work next session'));
  return h;
};
C.needsYou = () => C.DATA.activity.filter(a => a.needs_user);
})();
