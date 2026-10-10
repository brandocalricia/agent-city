// office.js — Agent City as a top-down SVG office (agent-virtual-office style)
// Renders 8 fixed desks + central Town Hall, all live data in one screen
(function () {
  const C = window.City;
  if (!C) return;

  // Desk positions (x, y) in SVG coordinates (0-800, 0-600), center is (400, 300)
  const DESKS = [
    { id: 'council', name: 'Council', icon: '⚖️', x: 400, y: 120, roleIds: ['council', 'inspector'] },
    { id: 'inspector', name: 'Inspector', icon: '🔍', x: 400, y: 200, roleIds: ['inspector'] },
    { id: 'builder', name: 'Builder', icon: '🔨', x: 180, y: 200, roleIds: ['builder'] },
    { id: 'scout', name: 'Scout', icon: '🧭', x: 620, y: 200, roleIds: ['scout'] },
    { id: 'tutor', name: 'Tutor', icon: '🎓', x: 180, y: 350, roleIds: ['tutor'] },
    { id: 'librarian', name: 'Librarian', icon: '📖', x: 620, y: 350, roleIds: ['librarian'] },
    { id: 'promptsmith', name: 'Prompt Smith', icon: '✍️', x: 180, y: 500, roleIds: ['promptsmith'] },
    { id: 'newsroom', name: 'Newsroom', icon: '📰', x: 620, y: 500, roleIds: ['reporter'] },
  ];

  // Treasury desks (shared building, two roles)
  const TREASURY_DESKS = [
    { id: 'auditor', name: 'Auditor', icon: '🧾', x: 280, y: 440, roleIds: ['auditor'] },
    { id: 'meter', name: 'Meter Reader', icon: '📏', x: 520, y: 440, roleIds: ['meter'] },
  ];

  // Private roles - shown at bottom
  const PRIVATE_DESKS = [
    { id: 'courier', name: 'Courier', icon: '✉️', x: 300, y: 560, roleIds: ['courier'] },
    { id: 'timekeeper', name: 'Timekeeper', icon: '⏰', x: 500, y: 560, roleIds: ['timekeeper'] },
    { id: 'toolsmith', name: 'Toolsmith', icon: '🛠', x: 180, y: 440, roleIds: ['toolsmith'] },
    { id: 'critic', name: 'Critic', icon: '🧐', x: 620, y: 440, roleIds: ['critic'] },
    { id: 'archivist', name: 'Archivist', icon: '🗄', x: 180, y: 560, roleIds: ['archivist'] },
  ];

  const ALL_DESKS = [...DESKS, ...TREASURY_DESKS, ...PRIVATE_DESKS];

  // Role colors from roles.js
  const ROLE_COLORS = {
    inspector: '#6ad1ff', watchman: '#8fd3ff', builder: '#ffb347', scout: '#f08a24',
    courier: '#4f8cff', timekeeper: '#e6c35c', tutor: '#9b6bff', librarian: '#5cd6a0',
    promptsmith: '#ff6fb5', toolsmith: '#b0b8c8', critic: '#ff5c5c', archivist: '#c9a26b',
    council: '#e040fb', auditor: '#7dffb2', meter: '#3fd0c9', optimizer: '#c6ff3f',
    reporter: '#ffd166',
  };

  C.office = {
    init() {
      this.container = document.getElementById('app');
      this.container.innerHTML = '';
      this.container.className = 'office-container';
      this.render();
      this.bindEvents();
      this.startActivityPulse();
    },

    render() {
      // Create SVG office floor
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', '0 0 800 600');
      svg.setAttribute('width', '100%');
      svg.setAttribute('height', '100%');
      svg.id = 'office-svg';
      svg.innerHTML = this.getSvgContent();
      this.container.appendChild(svg);

      // Overlay UI
      this.renderOverlay();
    },

    getSvgContent() {
      let svg = `
        <!-- Floor grid -->
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#2a2f3e" stroke-width="0.5"/>
          </pattern>
          <filter id="desk-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>
        <rect width="800" height="600" fill="url(#grid)"/>
        <rect width="800" height="600" fill="#0d111a"/>

        <!-- Central plaza area -->
        <circle cx="400" cy="120" r="60" fill="none" stroke="#e040fb" stroke-width="2" stroke-dasharray="8,4" opacity="0.4"/>

        <!-- Town Hall at center-top -->
        <g class="desk-group" data-desk="townhall" transform="translate(400, 120)">
          <rect x="-40" y="-40" width="80" height="80" rx="8" fill="#1a0f2a" stroke="#e040fb" stroke-width="2" filter="url(#desk-glow)"/>
          <text x="0" y="8" text-anchor="middle" font-size="28" font-family="system-ui">🏛</text>
          <text x="0" y="32" text-anchor="middle" font-size="10" fill="#aaa" font-family="system-ui">TOWN HALL</text>
        </g>
      `;

      // Render all desks
      for (const desk of ALL_DESKS) {
        const role = desk.roleIds[0];
        const color = ROLE_COLORS[role] || '#888';
        const latest = C.feed.latestFor(role);
        const hasActivity = latest !== null;
        const isPrivate = C.roleById && C.roleById[role]?.private;

        svg += `
          <g class="desk-group${isPrivate ? ' private-desk' : ''}" data-desk="${desk.id}" transform="translate(${desk.x}, ${desk.y})">
            <rect x="-35" y="-35" width="70" height="70" rx="6" fill="#151a26" stroke="${color}" stroke-width="${hasActivity ? '2' : '1'}" opacity="${isPrivate ? '0.6' : '1'}" filter="${hasActivity ? 'url(#desk-glow)' : 'none'}"/>
            <text x="0" y="6" text-anchor="middle" font-size="24" font-family="system-ui">${desk.icon}</text>
            <text x="0" y="28" text-anchor="middle" font-size="9" fill="${color}" font-family="system-ui" font-weight="600">${desk.name.toUpperCase()}</text>
            ${hasActivity ? `<circle cx="30" cy="-30" r="6" fill="${color}" stroke="#0d111a" stroke-width="2"/>` : ''}
            ${isPrivate ? `<text x="0" y="46" text-anchor="middle" font-size="7" fill="#666" font-family="system-ui">🔒 LOCAL</text>` : ''}
          </g>
        `;
      }

      // Treasury label
      svg += `
        <text x="400" y="420" text-anchor="middle" font-size="10" fill="#666" font-family="system-ui" font-weight="600">TREASURY</text>
      `;

      return svg;
    },

    renderOverlay() {
      // Top bar - minimal
      const topbar = document.createElement('div');
      topbar.id = 'office-topbar';
      topbar.innerHTML = `
        <div class="brand">🏙 Agent City <small id="dayTag"></small></div>
        <div class="controls">
          <button id="btnFeed" title="Activity Feed (F)" aria-label="Activity Feed">📋</button>
          <button id="btnSettings" title="Settings (,)" aria-label="Settings">⚙️</button>
          <button id="btnKeys" title="Keyboard shortcuts (?)" aria-label="Keyboard shortcuts">⌨️</button>
        </div>
      `;
      this.container.appendChild(topbar);

      // Day tag
      this.updateDayTag();

      // Feed panel (hidden by default)
      this.feedPanel = document.createElement('div');
      this.feedPanel.id = 'feed-panel';
      this.feedPanel.className = 'panel glass';
      this.feedPanel.setAttribute('role', 'dialog');
      this.feedPanel.setAttribute('aria-hidden', 'true');
      this.feedPanel.innerHTML = `
        <button class="close" aria-label="Close feed">✕</button>
        <div id="feed-body"></div>
      `;
      this.container.appendChild(this.feedPanel);

      // Settings modal
      this.settingsModal = document.createElement('div');
      this.settingsModal.id = 'settings-modal';
      this.settingsModal.className = 'modal glass';
      this.settingsModal.setAttribute('role', 'dialog');
      this.settingsModal.setAttribute('aria-modal', 'true');
      this.settingsModal.setAttribute('aria-hidden', 'true');
      this.settingsModal.innerHTML = `
        <div class="modal-box">
          <button class="close" aria-label="Close settings">✕</button>
          <h3>⚙️ Settings</h3>
          <label><input type="checkbox" id="setting-reduced-motion" ${localStorage.getItem('reducedMotion') === 'true' ? 'checked' : ''}> Reduce motion</label>
          <label><input type="checkbox" id="setting-saver-mode" ${localStorage.getItem('saverMode') === 'true' ? 'checked' : ''}> Graphics saver mode</label>
          <label><input type="checkbox" id="setting-show-private" ${localStorage.getItem('showPrivate') !== 'false' ? 'checked' : ''}> Show private desks (local only)</label>
          <label><input type="checkbox" id="setting-auto-refresh" ${localStorage.getItem('autoRefresh') !== 'false' ? 'checked' : ''}> Auto-refresh feed</label>
          <hr>
          <button id="btnClearLocal" class="danger">Clear all localStorage</button>
          <p class="mute">Data loads from data.js (generated by build_data.py). Private data only on local copy.</p>
        </div>
      `;
      this.container.appendChild(this.settingsModal);

      // Keyboard shortcuts modal
      this.keysModal = document.createElement('div');
      this.keysModal.id = 'keys-modal';
      this.keysModal.className = 'modal glass';
      this.keysModal.setAttribute('role', 'dialog');
      this.keysModal.setAttribute('aria-modal', 'true');
      this.keysModal.setAttribute('aria-hidden', 'true');
      this.keysModal.innerHTML = `
        <div class="modal-box">
          <button class="close" aria-label="Close shortcuts">✕</button>
          <h3>⌨️ Keyboard Shortcuts</h3>
          <dl>
            <dt><kbd>F</kbd></dt><dd>Toggle activity feed</dd>
            <dt><kbd>,</kbd></dt><dd>Settings</dd>
            <dt><kbd>?</kbd> <kbd>H</kbd></dt><dd>This list</dd>
            <dt><kbd>Esc</kbd></dt><dd>Close any panel</dd>
            <dt>Click desk</dt><dd>Open role popover</dd>
          </dl>
        </div>
      `;
      this.container.appendChild(this.keysModal);

      // Popover element (reused)
      this.popover = document.createElement('div');
      this.popover.id = 'desk-popover';
      this.popover.className = 'popover glass';
      this.popover.setAttribute('role', 'dialog');
      this.popover.setAttribute('aria-hidden', 'true');
      this.container.appendChild(this.popover);

      // Toasts
      this.toasts = document.createElement('div');
      this.toasts.id = 'toasts';
      this.toasts.setAttribute('aria-live', 'polite');
      this.container.appendChild(this.toasts);

      // Update day tag periodically
      setInterval(() => this.updateDayTag(), 60000);
    },

    updateDayTag() {
      const tag = document.getElementById('dayTag');
      if (tag) {
        const now = new Date();
        const denver = new Date(now.toLocaleString('en-US', { timeZone: 'America/Denver' }));
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        tag.textContent = ` · ${days[denver.getDay()]} ${denver.getHours().toString().padStart(2, '0')}:${denver.getMinutes().toString().padStart(2, '0')} MT`;
      }
    },

    bindEvents() {
      // Desk clicks -> popover
      document.querySelectorAll('.desk-group').forEach(g => {
        g.style.cursor = 'pointer';
        g.addEventListener('click', (e) => this.openPopover(e.currentTarget.dataset.desk, e));
        g.addEventListener('mouseenter', (e) => this.showPreview(e.currentTarget.dataset.desk, e));
        g.addEventListener('mouseleave', () => this.hidePreview());
      });

      // Feed button
      document.getElementById('btnFeed').addEventListener('click', () => this.toggleFeed());
      this.feedPanel.querySelector('.close').addEventListener('click', () => this.closeFeed());

      // Settings button
      document.getElementById('btnSettings').addEventListener('click', () => this.openSettings());
      this.settingsModal.querySelector('.close').addEventListener('click', () => this.closeSettings());
      this.settingsModal.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.addEventListener('change', () => this.saveSettings());
      });
      document.getElementById('btnClearLocal').addEventListener('click', () => {
        if (confirm('Clear all localStorage? This resets settings and private.js cache.')) {
          localStorage.clear();
          this.toast('localStorage cleared', 'info');
          this.closeSettings();
        }
      });

      // Keys button
      document.getElementById('btnKeys').addEventListener('click', () => this.openKeys());
      this.keysModal.querySelector('.close').addEventListener('click', () => this.closeKeys());

      // Close on Escape
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          this.closeFeed();
          this.closeSettings();
          this.closeKeys();
          this.closePopover();
        }
        if (e.key === 'f' || e.key === 'F') {
          if (!e.ctrlKey && !e.metaKey && !e.altKey && document.activeElement.tagName !== 'INPUT') {
            e.preventDefault();
            this.toggleFeed();
          }
        }
        if (e.key === ',') {
          if (document.activeElement.tagName !== 'INPUT') {
            e.preventDefault();
            this.openSettings();
          }
        }
        if (e.key === '?' || (e.key === 'h' && (e.ctrlKey || e.metaKey))) {
          e.preventDefault();
          this.openKeys();
        }
      });

      // Click outside modals to close
      [this.feedPanel, this.settingsModal, this.keysModal].forEach(m => {
        m.addEventListener('click', (e) => {
          if (e.target === m) this.closeAll();
        });
      });

      // Show/hide private desks based on setting
      this.applyPrivateVisibility();
    },

    applyPrivateVisibility() {
      const show = localStorage.getItem('showPrivate') !== 'false';
      document.querySelectorAll('.private-desk').forEach(d => {
        d.style.display = show ? '' : 'none';
      });
    },

    saveSettings() {
      localStorage.setItem('reducedMotion', document.getElementById('setting-reduced-motion').checked);
      localStorage.setItem('saverMode', document.getElementById('setting-saver-mode').checked);
      localStorage.setItem('showPrivate', document.getElementById('setting-show-private').checked);
      localStorage.setItem('autoRefresh', document.getElementById('setting-auto-refresh').checked);
      this.applyPrivateVisibility();
      this.toast('Settings saved', 'info');
    },

    openPopover(deskId, event) {
      const desk = ALL_DESKS.find(d => d.id === deskId);
      if (!desk) return;

      const roleId = desk.roleIds[0];
      const role = C.roleById[roleId];
      const latest = C.feed.latestFor(roleId);
      const acts = C.feed.activity.filter(a => desk.roleIds.includes(a.role)).slice(0, 10);
      const isPrivate = role?.private;

      let html = `
        <h4>${desk.icon} ${desk.name}${isPrivate ? ' <span class="badge lockb">🔒 Local only</span>' : ''}</h4>
        <div class="m">${role?.job || 'No description'}</div>
      `;

      if (latest) {
        html += `<h4>Latest</h4>${C.entryCard(latest)}`;
      }

      if (acts.length > 1) {
        html += `<h4>Recent (${acts.length})</h4>` + acts.slice(1).map(C.entryCard).join('');
      } else if (!latest) {
        html += `<div class="card empty">${role?.idle || 'Starts work next session'}</div>`;
      }

      if (isPrivate) {
        const p = C.privateFor(roleId);
        if (p) {
          html += `<h4>Local notes</h4>`;
          if (p.summary) html += C.card(p.summary, p.updated || '');
          (p.items || []).forEach(it => {
            html += C.card(it.title, it.when || '', (it.detail ? `<pre>${it.detail}</pre>` : '') + (it.link ? `<a href="${it.link}" target="_blank" rel="noopener">Open</a>` : ''));
          });
        } else {
          html += `<div class="card empty">🔒 Private - open local copy to see notes</div>`;
        }
      }

      this.popover.innerHTML = html + `<button class="close" aria-label="Close">✕</button>`;
      this.popover.querySelector('.close').addEventListener('click', () => this.closePopover());

      // Position near click
      const rect = event.currentTarget.getBoundingClientRect();
      const containerRect = this.container.getBoundingClientRect();
      this.popover.style.left = `${rect.left - containerRect.left + rect.width / 2}px`;
      this.popover.style.top = `${rect.top - containerRect.top - 10}px`;
      this.popover.style.transform = 'translateX(-50%) translateY(-100%)';
      this.popover.setAttribute('aria-hidden', 'false');

      // Close on outside click
      setTimeout(() => {
        document.addEventListener('click', this.closePopover.bind(this), { once: true });
      }, 0);
    },

    closePopover() {
      this.popover.setAttribute('aria-hidden', 'true');
    },

    showPreview(deskId, event) {
      const desk = ALL_DESKS.find(d => d.id === deskId);
      if (!desk) return;
      const roleId = desk.roleIds[0];
      const latest = C.feed.latestFor(roleId);
      if (latest) {
        this.toast(`${desk.icon} ${desk.name}: ${latest.action}`, 'preview');
      }
    },

    hidePreview() {
      // Toasts auto-dismiss
    },

    toggleFeed() {
      const isOpen = this.feedPanel.getAttribute('aria-hidden') === 'false';
      if (isOpen) this.closeFeed(); else this.openFeed();
    },

    openFeed() {
      this.renderFeed();
      this.feedPanel.setAttribute('aria-hidden', 'false');
    },

    closeFeed() {
      this.feedPanel.setAttribute('aria-hidden', 'true');
    },

    renderFeed() {
      const body = document.getElementById('feed-body');
      const feed = C.feed;
      let html = '<h2>📋 Activity Feed</h2>';

      // Tabs: All | By Role | News | Costs | Grok Build
      html += `
        <div class="feed-tabs">
          <button class="active" data-tab="all">All</button>
          <button data-tab="roles">By Role</button>
          <button data-tab="news">News</button>
          <button data-tab="costs">Costs</button>
          <button data-tab="gb">Grok Build</button>
        </div>
        <div id="feed-content"></div>
      `;
      body.innerHTML = html;

      // Tab switching
      body.querySelectorAll('.feed-tabs button').forEach(btn => {
        btn.addEventListener('click', () => {
          body.querySelectorAll('.feed-tabs button').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          this.renderFeedTab(btn.dataset.tab, body.querySelector('#feed-content'));
        });
      });

      this.renderFeedTab('all', body.querySelector('#feed-content'));
    },

    renderFeedTab(tab, container) {
      const feed = C.feed;
      let html = '';

      if (tab === 'all') {
        const acts = feed.activity.slice(0, 50);
        html = acts.length ? acts.map(C.entryCard).join('') : '<div class="card empty">No activity yet</div>';
      } else if (tab === 'roles') {
        const counts = feed.countByRole();
        html = '<h4>Activity by Role</h4>';
        for (const role of C.ROLES) {
          const c = counts[role.id] || 0;
          if (c > 0 || role.id === 'council') {
            const latest = feed.latestFor(role.id);
            html += C.card(`${role.icon} ${role.name} (${c})`, latest ? `${latest.date}: ${latest.action}` : (role.idle || '—'));
          }
        }
      } else if (tab === 'news') {
        html = feed.news.length ? feed.news.map(n => `
          <div class="card">
            <div class="m"><strong>${n.title}</strong> <span class="badge">${n.tag}</span></div>
            <div class="m mute">${n.source} · ${n.date} · for: ${(n.for || []).join(', ')}</div>
            <div class="m">${n.why}</div>
            <div class="m"><a href="${n.url}" target="_blank" rel="noopener">Read →</a></div>
          </div>
        `).join('') : '<div class="card empty">No news yet</div>';
      } else if (tab === 'costs') {
        const c = feed.costs;
        const totalSaved = (c.savings || []).reduce((s, x) => s + (x.saved_tokens || 0), 0);
        const totalLedger = (c.ledger || []).reduce((s, x) => s + (x.tokens || 0), 0);
        html = `
          <div class="card"><strong>Lifetime tokens saved:</strong> ${totalSaved.toLocaleString()}</div>
          <div class="card"><strong>Lifetime tokens spent:</strong> ${totalLedger.toLocaleString()}</div>
          <h4>Recent Savings</h4>
          ${c.savings.slice(-5).reverse().map(s => `
            <div class="card"><strong>${s.method}</strong> — ${s.saved_tokens.toLocaleString()} tokens
              <div class="m mute">${s.reason}</div>
            </div>
          `).join('') || '<div class="card empty">No savings yet</div>'}
          <h4>Recent Ledger</h4>
          ${c.ledger.slice(-5).reverse().map(l => `
            <div class="card"><strong>${l.role}</strong> — ${l.tokens.toLocaleString()} tokens (${l.bytes} bytes)
              <div class="m mute">${l.action} · ${l.date}</div>
            </div>
          `).join('') || '<div class="card empty">No ledger entries</div>'}
        `;
      } else if (tab === 'gb') {
        html = feed.gb.length ? feed.gb.map(g => `
          <div class="card">
            <div class="m"><strong>${g.change}</strong> <span class="badge">${g.size}</span></div>
            <div class="m mute">target: ${g.target} · checks: ${g.checks?.length || 0} · tests: ${g.tests?.length || 0}</div>
            <div class="m">${g.why}</div>
          </div>
        `).join('') : '<div class="card empty">No Grok Build items</div>';
      }

      container.innerHTML = html;
    },

    openSettings() {
      this.settingsModal.setAttribute('aria-hidden', 'false');
    },

    closeSettings() {
      this.settingsModal.setAttribute('aria-hidden', 'true');
    },

    openKeys() {
      this.keysModal.setAttribute('aria-hidden', 'false');
    },

    closeKeys() {
      this.keysModal.setAttribute('aria-hidden', 'true');
    },

    closeAll() {
      this.closeFeed();
      this.closeSettings();
      this.closeKeys();
      this.closePopover();
    },

    toast(msg, type = 'info') {
      const t = document.createElement('div');
      t.className = `toast ${type}`;
      t.textContent = msg;
      this.toasts.appendChild(t);
      setTimeout(() => t.classList.add('show'), 10);
      setTimeout(() => {
        t.classList.remove('show');
        setTimeout(() => t.remove(), 300);
      }, 3000);
    },

    startActivityPulse() {
      // Pulse desks with recent activity
      setInterval(() => {
        document.querySelectorAll('.desk-group').forEach(g => {
          const deskId = g.dataset.desk;
          const desk = ALL_DESKS.find(d => d.id === deskId);
          if (!desk) return;
          const latest = C.feed.latestFor(desk.roleIds[0]);
          const rect = g.querySelector('rect');
          if (latest && rect) {
            const now = Date.now();
            const activityTime = new Date(latest.date + ' ' + (latest.time || '00:00')).getTime();
            if (now - activityTime < 3600000) { // within 1 hour
              rect.style.animation = 'pulse 2s ease-in-out infinite';
            } else {
              rect.style.animation = '';
            }
          }
        });
      }, 30000);
    },
  };

  // Auto-init when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => C.office.init());
  } else {
    C.office.init();
  }
})();