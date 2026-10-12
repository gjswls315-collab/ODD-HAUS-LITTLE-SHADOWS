/* Buddy 최종 모델 → assets/characters/buddy/npc_buddy.glb
   네 발로 걷는 작은 shaggy dog: 갈색 · 회색 · 크림이 섞인 부스스한 털, 큰 갈색 눈, 길게 처진 귀, 부스스한 주둥이(수염),
   풍성한 가슴털 · 꼬리, 파란 넥타이(노란 사선) + 파란 목걸이 + BUDDY 이름표. 어깨 높이 약 32 cm.
   게임 리그(Buddy)의 묶음 자세를 거울 노드로 — 게임에서는 리그가 움직인다. 클립: Idle · Walk · Run · Sniff · Sit · EarsBack · TailWag · Bark */
window.GLBA_JOB = async () => {
  const L = GLBA, T = L.T, D = ODD2.dev, V3 = L.V3, TAU = Math.PI * 2, B = ODD2.BUDDY;
  // ---------- 리그: 게임의 Buddy를 정면 · 서 있는 묶음 자세로 ----------
  Object.assign(B, { state: 'idle', stT: 0, yaw: 0, prevYaw: 0, visYaw: 0, moving: 0, onGround: true, vy: 0, happyT: 0, warnT: 0, barkT: 1, lastBarkT: 1, barkPulse: 0, landT: 0, mode: 'idle' });
  B.pos.set(0, 0, 0); B.prev.set(0, 0, 0); B.root.visible = true; ODD2.P.pos.set(0, .35, 3);
  const anim = (n, dt = 1 / 60) => { for (let i = 0; i < n; i++) { B.tAcc = (B.tAcc || 0) + dt; if (B.state !== 'off') B.stT += dt; D.buddyAnimate(dt, B.tAcc, 1); } };
  anim(90);
  const mir = L.mirror(B.root, 'BUDDY');
  Object.assign(mir.root.userData, { oddRig: 'buddy', character: 'buddy', shoulder: .33, unit: 'm', note: 'ODD HAUS Buddy — 노드 extras.link = 게임 리그 이름' });
  const scene = new T.Scene(); scene.name = 'npc_buddy'; scene.add(mir.root);
  const M = mir.map, add = (node, geo, mat, name) => { const m = new T.Mesh(geo, mat); m.name = name; m.castShadow = true; m.receiveShadow = true; M[node].add(m); return m; };
  { const mk = new T.Object3D(); mk.name = 'BUDDY_Marker_Shoulder'; mk.userData = { marker: 'shoulder' }; mk.position.set(0, .134, .075); M.body.add(mk); }

  // ---------- 재질 ----------
  const furN = L.tex(L.normalCanvas(128, 128, (u, v, x, y) => { const R = L.rng(x * 7 + y * 131); return .5 + .3 * Math.sin(x * .9 + Math.sin(y * .05) * 6) + (R() - .5) * .3; }, 1.2), { color: false, repeat: [3, 3] });
  const furMat = L.phys({ name: 'Buddy_Fur', color: 0xffffff, vertexColors: true, roughness: .88, sheen: .7, sheenColor: new T.Color(0xf4e8d4), sheenRoughness: .6 });
  const skinMat = (hex, name) => L.phys({ name, color: hex, roughness: .92, normalMap: furN, normalScale: new T.Vector2(.5, .5), sheen: .8, sheenColor: new T.Color(0xe8dccb), sheenRoughness: .6 });
  const baseBrown = skinMat(0x5a4a3c, 'Buddy_CoatBase'), baseCream = skinMat(0xb8aa92, 'Buddy_CreamBase'), baseEar = skinMat(0x45321f, 'Buddy_EarBase');
  const noseM = L.phys({ name: 'Buddy_Nose', color: 0x111012, roughness: .22, clearcoat: 1, clearcoatRoughness: .08, normalMap: furN, normalScale: new T.Vector2(.25, .25) });
  const eyeM = L.phys({ name: 'Buddy_EyeIris', color: 0x5a3216, roughness: .05, clearcoat: 1, clearcoatRoughness: .02 });
  const pupilM = L.phys({ name: 'Buddy_Pupil', color: 0x0a0604, roughness: .05, clearcoat: 1 });
  const rimM = L.phys({ name: 'Buddy_EyeRim', color: 0x241a14, roughness: .6 });
  const catchM = new T.MeshBasicMaterial({ name: 'Buddy_Catchlight', color: 0xffffff });
  const mouthM = L.phys({ name: 'Buddy_Mouth', color: 0x3a1214, roughness: .6 });
  const tongueM = L.phys({ name: 'Buddy_Tongue', color: 0xd8707a, roughness: .38, clearcoat: .6 });
  const tieTex = L.tex(L.canvas(256, 256, (g, w, h) => { g.fillStyle = '#24468c'; g.fillRect(0, 0, w, h); g.strokeStyle = '#e8b83a'; g.lineWidth = 22; for (let i = -w; i < w * 2; i += 64) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i + h, h); g.stroke(); } g.strokeStyle = '#f4f0e6'; g.lineWidth = 4; for (let i = -w + 18; i < w * 2; i += 64) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i + h, h); g.stroke(); } }));
  const tieM = L.phys({ name: 'Buddy_Tie', map: tieTex, roughness: .48, sheen: .6, sheenColor: new T.Color(0xffffff), sheenRoughness: .4 });
  const collarM = L.phys({ name: 'Buddy_Collar', color: 0x23407a, roughness: .45, clearcoat: .35 });
  const brass = L.phys({ name: 'Buddy_Brass', color: 0xc9a050, metalness: 1, roughness: .3 });
  const tagTex = L.tex(L.canvas(256, 256, (g, w, h) => { g.fillStyle = '#c9a050'; g.beginPath(); g.arc(128, 128, 126, 0, TAU); g.fill(); g.fillStyle = '#2b5bb8'; g.beginPath(); g.arc(128, 128, 104, 0, TAU); g.fill(); g.strokeStyle = '#e8c86a'; g.lineWidth = 6; g.beginPath(); g.arc(128, 128, 94, 0, TAU); g.stroke(); g.fillStyle = '#f4e6b0'; g.font = 'bold 56px Impact, "Arial Black", sans-serif'; g.textAlign = 'center'; g.fillText('BUDDY', 128, 148); g.font = 'bold 22px Arial, sans-serif'; g.fillText('ODD HAUS', 128, 186); }), { wrap: false });
  const tagM = L.phys({ name: 'Buddy_Tag', map: tagTex, metalness: .35, roughness: .3, clearcoat: .8 });

  // ---------- 털 색 (부위별) ----------
  const pick = arr => (u, R) => arr[(R() * arr.length) | 0];
  const BROWN = [0x7a5a3e, 0x8a6a4c, 0x6c5642, 0x7a7068, 0x5e4a38, 0x8a7a68, 0x6a6058], CREAM = [0xe6dac4, 0xd8c8ac, 0xcfc0a4, 0xeee4d2], GRAYC = [0xa89c8c, 0x9a8e80, 0xb8ad9c, 0x8a8078, 0xc0b4a2], EAR = [0x5e3e26, 0x4e3420, 0x6e4a2e, 0x7a5636];
  const mix = (top, bottom, k = 0) => (u, R) => (u.y + (R() - .5) * .5 > k ? top : bottom)[(R() * (u.y > k ? top : bottom).length) | 0];
  const furOn = (node, o, name) => add(node, L.fur(o), furMat, name);

  // ---------- 몸 (몸 그룹 공간) ----------
  add('body', L.blob(.116, .118, .11, () => 1, 32, 22), baseBrown, 'Buddy_Chest').position.set(0, .012, .075);
  add('body', L.blob(.108, .104, .128, () => 1, 32, 22), baseBrown, 'Buddy_Belly').position.set(0, 0, -.02);
  add('body', L.blob(.112, .11, .098, () => 1, 32, 22), baseBrown, 'Buddy_Rump').position.set(0, .008, -.1);
  add('body', L.blob(.084, .096, .066, () => 1, 24, 16), baseCream, 'Buddy_ChestCream').position.set(0, -.024, .14);
  const coat = (node, c, r, n1, n2, colTop, colBot, k, seed, extra = {}) => {
    furOn(node, Object.assign({ c, r, n: n1, len: [.014, .026], lift: .45, droop: 1.0, flow: [0, 0, -1], flowK: .7, w: .0034, segs: 2, color: mix(colTop, colBot, k), seed }, extra), 'Buddy_Coat_' + node + seed);
    furOn(node, Object.assign({ c, r, n: n2, len: [.03, .05], lift: .8, droop: 1.1, flow: [0, 0, -1], flowK: .45, w: .003, color: mix(colTop, colBot, k), seed: seed + 100 }, extra), 'Buddy_Shag_' + node + seed);
  };
  coat('body', [0, .012, .075], [.116, .118, .11], 460, 150, BROWN, GRAYC, -.25, 11);
  coat('body', [0, 0, -.02], [.108, .104, .128], 460, 150, BROWN, GRAYC, -.3, 12);
  coat('body', [0, .008, -.1], [.112, .11, .098], 400, 130, BROWN, GRAYC, -.3, 13);
  furOn('body', { c: [0, -.024, .14], r: [.084, .096, .066], n: 300, len: [.034, .058], droop: 1.25, flow: [0, -1, .3], flowK: .5, color: pick(CREAM), seed: 14, mask: u => u.z > -.2 }, 'Buddy_FurChestFluff');
  furOn('body', { c: [0, -.06, 0], r: [.08, .05, .12], n: 160, len: [.03, .05], droop: 1.4, flow: [0, -1, 0], flowK: .5, color: pick(GRAYC.concat(CREAM)), seed: 24, mask: u => u.y < -.2 }, 'Buddy_FurBellyFringe');
  // ---------- 목 · 목걸이 · 넥타이 · 이름표 ----------
  add('neck', L.blob(.078, .084, .076, () => 1, 24, 16), baseBrown, 'Buddy_Neck').position.set(0, .03, .02);
  coat('neck', [0, .03, .02], [.078, .084, .076], 360, 140, BROWN, CREAM, -.15, 15, { flow: [0, -.4, -.6] });
  { const c = new T.TorusGeometry(.076, .0105, 10, 40); c.rotateX(Math.PI / 2 - .5); c.translate(0, 0, .03); add('neck', c, collarM, 'Buddy_Collar');
    const bk = L.sbox(.018, .014, .006, 5, 10, 8); bk.rotateX(-.5); bk.translate(0, -.05, .1); add('neck', bk, brass, 'Buddy_Buckle'); }
  { const knot = L.sbox(.027, .023, .017, 4, 16, 12); const uvk = knot.attributes.uv; for (let i = 0; i < uvk.count; i++) uvk.setXY(i, uvk.getX(i) * .3, uvk.getY(i) * .3); add('tie', knot, tieM, 'Buddy_TieKnot');
    const sh = new T.Shape(); sh.moveTo(-.011, 0); sh.lineTo(.011, 0); sh.lineTo(.022, -.088); sh.lineTo(0, -.11); sh.lineTo(-.022, -.088); sh.closePath();
    const bl = new T.ExtrudeGeometry(sh, { depth: .004, bevelEnabled: true, bevelThickness: .001, bevelSize: .0012, bevelSegments: 1 }); const uv = bl.attributes.uv, p = bl.attributes.position; for (let i = 0; i < uv.count; i++) uv.setXY(i, p.getX(i) / .06 + .5, p.getY(i) / .06); bl.translate(0, -.008, -.002); bl.rotateX(-.2); add('tie', bl, tieM, 'Buddy_TieBlade'); }
  { const ring = new T.TorusGeometry(.005, .0015, 6, 14); ring.translate(0, .004, 0); add('tag', ring, brass, 'Buddy_TagRing');
    const disc = new T.CylinderGeometry(.017, .017, .003, 28); disc.rotateX(Math.PI / 2); disc.translate(0, -.017, 0); const uv = disc.attributes.uv, p = disc.attributes.position; for (let i = 0; i < uv.count; i++) uv.setXY(i, .5 + p.getX(i) / .034, .5 + (p.getY(i) + .017) / .034); add('tag', disc, tagM, 'Buddy_Tag'); }
  // ---------- 머리 (머리 그룹 공간 — 리그가 1.16배) ----------
  add('head', L.blob(.116, .106, .108, d => 1 + .04 * Math.max(0, d.y), 32, 24), baseBrown, 'Buddy_Skull').position.set(0, .01, 0);
  add('head', L.blob(.054, .044, .056, () => 1, 24, 16), baseCream, 'Buddy_Muzzle').position.set(0, -.036, .096);
  for (const s of [-1, 1]) add('head', L.blob(.05, .044, .048, () => 1, 18, 12), baseCream, 'Buddy_Cheek' + (s > 0 ? 'R' : 'L')).position.set(s * .046, -.034, .062);
  { const n = L.blob(.03, .021, .02, d => 1 - .12 * Math.max(0, -d.y), 24, 16); n.translate(0, -.012, .146); add('head', n, noseM, 'Buddy_Nose');
    for (const s of [-1, 1]) { const ns = new T.SphereGeometry(.0058, 10, 8); ns.scale(1, .6, .5); ns.translate(s * .009, -.016, .164); add('head', ns, pupilM, 'Buddy_Nostril' + (s > 0 ? 'R' : 'L')); } }
  coat('head', [0, .01, 0], [.116, .106, .108], 560, 140, BROWN, GRAYC, .1, 16, { flow: [0, -.3, -1], mask: u => !(u.z > .45 && u.y < .55 && Math.abs(u.x) < .75) });
  furOn('head', { c: [0, .05, .06], r: [.07, .05, .05], n: 70, len: [.028, .042], droop: .9, flow: [0, -.2, 1], flowK: .5, color: pick(GRAYC), seed: 17, mask: u => u.y > .2 && u.z > -.2 }, 'Buddy_FurFringe');
  furOn('head', { c: [0, -.036, .096], r: [.054, .044, .056], n: 280, len: [.024, .046], droop: 1.4, flow: [0, -1, .4], flowK: .45, color: pick(GRAYC.concat(CREAM)), seed: 18, n2: 0, mask: u => !(u.z > .7 && u.y > -.1 && Math.abs(u.x) < .45) }, 'Buddy_FurBeard');
  for (const s of [-1, 1]) furOn('head', { c: [s * .046, -.034, .062], r: [.05, .044, .048], n: 70, len: [.022, .036], droop: 1.2, color: pick(GRAYC), seed: 19 + s, mask: u => u.x * s > -.2 }, 'Buddy_FurCheek' + (s > 0 ? 'R' : 'L'));
  for (const s of [-1, 1]) furOn('head', { c: [s * .046, .056, .085], r: [.024, .01, .012], n: 22, len: [.02, .03], droop: .4, flow: [s * .5, .6, .6], flowK: .7, color: pick(GRAYC), seed: 21 + s, clump: 4 }, 'Buddy_Brow' + (s > 0 ? 'R' : 'L'));
  // ---------- 눈 (눈 그룹 공간 — 리그가 1.22배) ----------
  for (const i of [0, 1]) { const s = i ? -1 : 1;
    add('eye' + i, L.blob(.027, .029, .016, () => 1, 28, 20), eyeM, 'Buddy_Iris' + i);
    const pu = L.blob(.0155, .017, .007, () => 1, 20, 14); pu.translate(-s * .002, -.002, .0112); add('eye' + i, pu, pupilM, 'Buddy_Pupil' + i);
    const c1 = new T.SphereGeometry(.0075, 12, 8); c1.scale(1, 1, .4); c1.translate(-.0085, .011, .0152); add('eye' + i, c1, catchM, 'Buddy_Catch' + i + 'a');
    const c2 = new T.SphereGeometry(.0033, 10, 6); c2.scale(1, 1, .4); c2.translate(.0075, -.0085, .0152); add('eye' + i, c2, catchM, 'Buddy_Catch' + i + 'b');
    const rim = new T.TorusGeometry(.0275, .0028, 8, 32); rim.scale(1, 1.06, 1); rim.translate(0, 0, .004); add('eye' + i, rim, rimM, 'Buddy_EyeRim' + i); }
  // ---------- 턱 · 입 · 혀 ----------
  add('jaw', L.blob(.036, .016, .04, () => 1, 18, 10), baseCream, 'Buddy_Jaw').position.set(0, -.004, .035);
  add('jaw', L.blob(.031, .011, .036, () => 1, 16, 8), mouthM, 'Buddy_MouthIn').position.set(0, .006, .036);
  furOn('jaw', { c: [0, -.004, .035], r: [.036, .016, .04], n: 70, len: [.022, .036], droop: 1.5, flow: [0, -1, 0], flowK: .6, color: pick(GRAYC.concat(CREAM)), seed: 23, mask: u => u.y < .2 }, 'Buddy_FurChin');
  { const tg = L.blob(1, 1, 1, d => 1 - .15 * Math.max(0, d.y), 16, 10); add('tongue', tg, tongueM, 'Buddy_Tongue'); }
  // ---------- 귀 (귀 그룹 공간) ----------
  for (const i of [0, 1]) { const s = i ? -1 : 1;
    const e = L.blob(.046, .098, .024, d => 1 + .08 * Math.max(0, -d.y), 22, 18); e.rotateZ(s * .08); e.translate(s * .006, -.078, .004); add('ear' + i, e, baseEar, 'Buddy_Ear' + i);
    furOn('ear' + i, { c: [s * .006, -.078, .004], r: [.046, .098, .024], n: 340, segs: 2, w: .0032, len: [.026, .046], droop: 1.6, flow: [0, -1, 0], flowK: .6, color: (u, R) => (u.y < -.75 && R() < .5 ? GRAYC : EAR)[(R() * 4) | 0], seed: 30 + i }, 'Buddy_FurEar' + i); }
  // ---------- 다리 (엉덩이 · 무릎 · 발) ----------
  for (let i = 0; i < 4; i++) { const front = i < 2;
    add('hip' + i, L.blob(.045, .062, .049, () => 1, 18, 14), baseBrown, 'Buddy_Thigh' + i).position.set(0, -.04, 0);
    coat('hip' + i, [0, -.04, 0], [.045, .062, .049], 220, 70, BROWN, GRAYC, -.1, 40 + i, { flow: [0, -1, 0] });
    add('knee' + i, L.blob(.034, .05, .036, () => 1, 16, 12), front ? baseCream : baseBrown, 'Buddy_Shin' + i).position.set(0, -.038, 0);
    furOn('knee' + i, { c: [0, -.038, 0], r: [.034, .05, .036], n: 150, segs: 2, w: .0032, len: [.02, .032], droop: 1.4, color: front ? pick(CREAM.concat(GRAYC)) : mix(GRAYC, CREAM, .2), seed: 50 + i }, 'Buddy_FurShin' + i);
    const paw = L.blob(.04, .026, .05, d => 1 - .25 * Math.max(0, -d.y) ** 2, 18, 12); paw.translate(0, -.002, .014); add('paw' + i, paw, baseCream, 'Buddy_Paw' + i);
    for (const t of [-1, 0, 1]) { const tb = new T.SphereGeometry(.013, 10, 8); tb.translate(t * .016, -.006, .052); add('paw' + i, tb, baseCream, 'Buddy_Toe' + i + '_' + (t + 1)); }
    furOn('paw' + i, { c: [0, .004, .014], r: [.04, .02, .05], n: 40, len: [.014, .022], droop: 1.2, color: pick(CREAM), seed: 60 + i, mask: u => u.y > -.3 }, 'Buddy_FurPaw' + i); }
  // ---------- 꼬리 (4마디) ----------
  for (let i = 0; i < 4; i++) { const r = [.034 - i * .003, .032 - i * .003, .05];
    add('tail' + i, L.blob(r[0], r[1], r[2], () => 1, 14, 10), baseBrown, 'Buddy_Tail' + i).position.set(0, 0, -.022);
    furOn('tail' + i, { c: [0, 0, -.022], r, n: 120, len: [.034, .056], droop: .5, flow: [0, .3, -1], flowK: .5, color: i >= 2 ? pick(CREAM.concat(GRAYC)) : pick(BROWN), seed: 70 + i }, 'Buddy_FurTail' + i); }

  // ---------- 클립: 게임 리그를 실제 상태로 움직이며 녹화 ----------
  const snap = L.snap(mir), clips = [];
  const set = (o) => { Object.assign(B, { moving: 0, happyT: 0, warnT: 0, barkPulse: 0 }, o); B.stT = o.stT ?? 0; };
  const rec = (name, frames, pre = 60, each) => { anim(pre); clips.push(L.record(name, mir, frames, (f) => { if (each) each(f); anim(2, 1 / 60); })); };
  set({ state: 'idle' }); rec('Idle', 60);
  set({ state: 'follow', moving: 1.05 }); rec('Walk', Math.round(.72 / 1.05 * 30) + 1);
  set({ state: 'run', moving: 2.3 }); rec('Run', Math.round(.72 / 2.3 * 30 * 2) + 1);
  set({ state: 'sniff' }); rec('Sniff', 60, 90);
  set({ state: 'wait' }); rec('Sit', 45, 150);
  set({ state: 'alert' }); B.warnT = 9; rec('EarsBack', 45, 90, () => { B.warnT = 9; });
  set({ state: 'greet', happyT: 9 }); rec('TailWag', 30, 60, () => { B.happyT = 9; });
  set({ state: 'bark' }); rec('Bark', 24, 30, f => { if (f % 12 === 0) { B.barkT = 1; B.lastBarkT = 0; } });
  set({ state: 'idle' }); anim(90); L.restore(snap);
  B.root.visible = false; B.state = 'off';
  const info = Object.assign({ character: 'buddy' }, L.stats(scene), { clips: clips.map(c => c.name + ':' + c.tracks.length + ':' + c.duration.toFixed(2)), nodes: mir.list.length });
  const b64 = await L.export(scene, clips);
  return { b64, info };
};
