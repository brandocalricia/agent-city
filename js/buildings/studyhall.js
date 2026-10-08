// Study Hall: the Tutor's practice problem of the day (solution hidden until you click).
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
      + (t ? `<h4>Today's problem${t.course ? ' · ' + City.esc(t.course) : ''}</h4>` + City.entryCard(t) : '');
  },
});
