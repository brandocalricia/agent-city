// Label declutter: when building labels overlap on screen, the farther one fades out so every visible name stays readable.
// Town Hall's label always wins; a hovered label or the open panel's building comes next, then nearer labels beat farther ones.
// Cheap: one pass of about 20 rects every 250 ms, nothing per frame.
(() => {
  const C = window.City;
  C.initDeclutter = () => {
    const V = new THREE.Vector3(); let hovered = null, last = -1;
    document.addEventListener('pointerover', e => { const l = e.target.closest && e.target.closest('.lm-label'); if (l) hovered = l; });
    document.addEventListener('pointerout', e => { if (hovered && !hovered.contains(e.relatedTarget)) hovered = null; });
    const overlap = (a, b, p = 3) => a.left < b.right + p && b.left < a.right + p && a.top < b.bottom + p && b.top < a.bottom + p;
    C.declutter = () => {
      const items = [], open = location.hash.slice(1);
      for (const id in C.LANDMARKS) {
        const L = C.LANDMARKS[id], el = L.label && L.label.element;
        if (!el || el.style.display === 'none') continue;
        L.label.getWorldPosition(V);
        const pri = id === 'townhall' ? -2 : (el === hovered || id === open) ? -1 : C.camera.position.distanceTo(V);
        items.push({ el, pri });
      }
      document.querySelectorAll('.labels .mini-sign').forEach(el => { if (el.style.display !== 'none') items.push({ el, pri: 1e9 }); });
      items.sort((a, b) => a.pri - b.pri);
      const kept = [];
      for (const it of items) {
        const r = it.el.getBoundingClientRect(), hide = r.width > 0 && kept.some(k => overlap(r, k));
        it.el.classList.toggle('lbl-hidden', hide);
        if (!hide) kept.push(r);
      }
      return items.filter(it => it.el.classList.contains('lbl-hidden')).length;
    };
    C.onFrame((dt, t) => { if (t - last < 0.25 || document.body.classList.contains('no-labels')) return; last = t; C.declutter(); });
  };
})();
