// Load order for Agent City's plain-script files. Add new building files to the buildings list.
window.City = {
  version: '2026-10-08n',
  lib: {},
  files: [
    'js/core.js', 'js/roles.js',
    ...['library', 'office', 'townhall', 'market', 'clocktower', 'postoffice', 'studyhall', 'promptworkshop',
        'workshop', 'archive', 'reviewboard', 'council', 'treasury', 'newsroom', 'skillforge', 'statstower', 'noticeboard', 'kiosk'].map(b => `js/buildings/${b}.js`),
    'js/world.js', 'js/daynight.js', 'js/agents.js', 'js/panels.js', 'js/minimap.js', 'js/ui.js', 'js/visuals.js', 'js/hud.js', 'js/streaks.js', 'js/main.js', 'js/deeplink.js',
  ],
};
