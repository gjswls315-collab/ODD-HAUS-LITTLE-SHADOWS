// 게임 리그(묶음 자세)의 관절 위치 · 방향을 JSON으로 — Blender 새 모델의 관절 기준
window.GLBA_JOB = async () => {
  const L = GLBA, T = L.T, D = ODD2.dev, V3 = L.V3;
  const dump = root => { root.updateMatrixWorld(true); const inv = new T.Matrix4().copy(root.matrixWorld).invert(), out = {};
    root.traverse(o => { if (!o.userData.rig) return; const m = new T.Matrix4().multiplyMatrices(inv, o.matrixWorld), p = new T.Vector3(), q = new T.Quaternion(), s = new T.Vector3(); m.decompose(p, q, s);
      let par = o.parent; while (par && !par.userData.rig) par = par.parent;
      out[o.userData.rig] = { parent: par ? par.userData.rig : null, p: p.toArray().map(v => +v.toFixed(5)), q: q.toArray().map(v => +v.toFixed(5)), s: s.toArray().map(v => +v.toFixed(4)) }; });
    return out; };
  const R = {};
  // Vin
  { const V = D.buildHero('vin'); if (V.root.parent) V.root.parent.remove(V.root);
    const st = { t: 0, grounded: true, pos: V3(), vel: V3(), face: 1, crouch: 0, scared: 0, caught: false, mode: 'free', md: {}, runRef: 1.2, landImpulse: 0, jumped: false, vy: 0, light: false, yawOverride: 0, groundY: 0, lookAt: { x: 0, y: 0 } };
    V.blinkT = 1e9; V.blink = 0; V.dir.set(0, 0, 1); for (let i = 0; i < 120; i++) { st.t = i / 60; D.animateVin(V, st, 1 / 60); }
    D.hoseRig(V); R.vin = dump(V.root); R.vinLimbs = D.HOSE_LIMBS; R.vinN = D.HOSE_N; }
  // Buddy
  { const B = ODD2.BUDDY; Object.assign(B, { state: 'idle', stT: 0, yaw: 0, prevYaw: 0, visYaw: 0, moving: 0, onGround: true, vy: 0, happyT: 0, warnT: 0, barkT: 1, lastBarkT: 1, barkPulse: 0, landT: 0, mode: 'idle' });
    B.pos.set(0, 0, 0); B.prev.set(0, 0, 0); B.root.visible = true; ODD2.P.pos.set(0, .35, 3);
    for (let i = 0; i < 90; i++) { B.tAcc = (B.tAcc || 0) + 1 / 60; if (B.state !== 'off') B.stT += 1 / 60; D.buddyAnimate(1 / 60, B.tAcc, 1); }
    R.buddy = dump(B.root); }
  // Bully
  { const B = ODD2.BULLY; Object.assign(B, { state: 'leave', stT: 9, yaw: 0, prevYaw: 0, visYaw: 0, moving: 0, phase: 'play', phaseT: 0, act: null, peek: false, xray: 0 });
    B.pos.set(0, 0, 0); B.prev.set(0, 0, 0); B.root.position.set(0, 0, 0); B.root.visible = true; B.look.set(0, 1.38, 4); ODD2.P.pos.set(0, .1, 3); ODD2.P.center.set(0, .2, 3);
    for (let i = 0; i < 200; i++) { B.tA = (B.tA || 0) + 1 / 60; B.stT += 1 / 60; D.bullyAnimate(1 / 60, B.tA, 1); } B.p.tongue = 0; D.bullyAnimate(1 / 60, B.tA, 1);
    R.bully = dump(B.root); }
  const s = JSON.stringify(R, null, 1);
  return { b64: btoa(unescape(encodeURIComponent(s))), info: { vin: Object.keys(R.vin).length, buddy: Object.keys(R.buddy).length, bully: Object.keys(R.bully).length } };
};
