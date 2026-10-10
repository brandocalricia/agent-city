// Data feed: reads window.CITY_DATA and exposes a simple feed for office.js
// This runs after data.js loads, before office.js
(function () {
  const C = window.City;
  if (!C) return;
  const data = window.CITY_DATA || {};
  C.feed = {
    activity: data.activity || [],
    news: data.news || [],
    costs: data.costs || { ledger: [], savings: [], archived: [] },
    agents: data.agents || [],
    skills: data.skills || [],
    routines: data.routines || [],
    ideals: data.ideals || '',
    totals: data.totals || {},
    changelog: data.changelog || [],
    gb: data.gb || [],
    treasury: data.treasury || {},
    // Helper: latest activity per role
    latestFor: (roleId) => {
      for (let i = C.feed.activity.length - 1; i >= 0; i--) {
        if (C.feed.activity[i].role === roleId) return C.feed.activity[i];
      }
      return null;
    },
    // Helper: activity count per role
    countByRole: () => {
      const counts = {};
      for (const a of C.feed.activity) counts[a.role] = (counts[a.role] || 0) + 1;
      return counts;
    },
  };
})();