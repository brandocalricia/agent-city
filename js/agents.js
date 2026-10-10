// agents.js — Agent data for the office (no 3D figures in new architecture)
// Exposes C.DATA.agents and role mapping for the SVG office
(() => {
  const C = window.City;
  if (!C) return;

  // Agents are loaded from data.js (C.DATA.agents)
  // This file just ensures the data is accessible and provides helpers

  C.agentById = (id) => C.DATA.agents.find(a => a.id === id) || null;

  // Role-to-desk mapping for the office
  C.deskForRole = {
    council: 'townhall',
    inspector: 'inspector',
    builder: 'builder',
    scout: 'scout',
    tutor: 'tutor',
    librarian: 'librarian',
    promptsmith: 'promptsmith',
    reporter: 'newsroom',
    auditor: 'auditor',
    meter: 'meter',
    optimizer: 'auditor', // shares auditor desk
    courier: 'courier',
    timekeeper: 'timekeeper',
    toolsmith: 'toolsmith',
    critic: 'critic',
    archivist: 'archivist',
    watchman: 'townhall', // shows at Town Hall
  };

  // Get agents assigned to a role's desk
  C.agentsAtDesk = (deskId) => {
    return C.DATA.agents.filter(a => C.deskForRole[a.role] === deskId);
  };
})();