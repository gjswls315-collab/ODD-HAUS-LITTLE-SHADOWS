/* Vin 최종 모델 → assets/characters/vin/chr_vin.glb
   검은 LP판 몸(트랙 · 런아웃 · 외곽 비드 형상 + 미세 홈 노멀맵 + 원형 이방성 반사) · 큰 흰 타원 눈 · 흰 4손가락 장갑 ·
   검은 고무호스 팔다리(뼈 7개 스킨) · 빨간 하이탑(밑창 트레드 · 토캡 · 끈 · 아일릿 · 발목 패치) · 손전등.
   키 24 cm(원판 꼭대기 25.6 cm). 게임 리그(묶음 자세)를 그대로 거울 노드로 → 게임에서는 리그가 움직인다. */
window.GLBA_JOB = async () => {
  const L = GLBA, T = L.T, D = ODD2.dev, V3 = L.V3, TAU = Math.PI * 2;
  // ---------- 리그: 새 Vin 리그를 만들어 정면 · 가만히 선 묶음 자세로 ----------
  const V = D.buildHero('vin'); if (V.root.parent) V.root.parent.remove(V.root);
  const st = { t: 0, grounded: true, pos: V3(), vel: V3(), face: 1, crouch: 0, scared: 0, caught: false, mode: 'free', md: {}, runRef: 1.2, landImpulse: 0, jumped: false, vy: 0, light: false, yawOverride: 0, groundY: 0, lookAt: { x: 0, y: 0 } };
  V.blinkT = 1e9; V.blink = 0; V.dir.set(0, 0, 1);       // 묶음 자세: 신발도 정면
  for (let i = 0; i < 120; i++) { st.t = i / 60; D.animateVin(V, st, 1 / 60); }
  D.hoseRig(V); V.root.updateMatrixWorld(true);
  const boneNames = new Set(); D.HOSE_LIMBS.forEach(l => { for (let k = 0; k <= D.HOSE_N; k++) boneNames.add(l + '_' + k); });
  const mir = L.mirror(V.root, 'VIN', boneNames);
  Object.assign(mir.root.userData, { oddRig: 'hero', character: 'vin', height: .24, unit: 'm', note: 'ODD HAUS Vin — 노드 extras.link = 게임 리그 이름' });
  const scene = new T.Scene(); scene.name = 'chr_vin'; scene.add(mir.root);
  const M = mir.map, add = (node, geo, mat, name) => { const m = new T.Mesh(geo, mat); m.name = name; m.castShadow = true; m.receiveShadow = true; M[node].add(m); return m; };

  // ---------- 재질 ----------
  // LP 미세 홈: 반지름 방향(v)으로 0.5 mm 간격 홈 · 트랙 사이 띠 · 런아웃(홈 없음)
  const R0 = .08, TH = .035, RF = .0735, RH = .0036, RLBL = .026, RG0 = .0285, RG1 = .0712;
  const gaps = [.0395, .0505, .0610];
  const vOf = r => (r - RH) / (RF - RH);
  const grooveH = v => { const r = RH + v * (RF - RH); if (r < RG0 || r > RG1) return .5; for (const g of gaps) if (Math.abs(r - g) < .0007) return .5; const ph = (r - RG0) / .00052; return .5 + .5 * Math.sin(ph * TAU) * (.8 + .2 * Math.sin(ph * .37)); };
  const vinylN = L.tex(L.normalCanvas(8, 2048, (u, v) => grooveH(v) * .9, 3.2), { color: false });
  const vinylR = L.tex(L.grayCanvas(8, 1024, (u, v) => { const r = RH + v * (RF - RH); return r < RG0 || r > RG1 ? .3 : .44; }), { color: false });
  const vinyl = L.phys({ name: 'Vin_Vinyl', color: 0x0a0a0c, roughness: 1, roughnessMap: vinylR, normalMap: vinylN, normalScale: new T.Vector2(.45, .45), clearcoat: .35, clearcoatRoughness: .3, anisotropy: .8, anisotropyRotation: 0, sheen: .12, sheenColor: new T.Color(0x2a2a34), envMapIntensity: .55 });
  const rimMat = L.phys({ name: 'Vin_VinylEdge', color: 0x111114, roughness: .32, clearcoat: .6, clearcoatRoughness: .25 });
  const holeMat = L.phys({ name: 'Vin_Spindle', color: 0x050506, roughness: .6 });
  const labelMat = L.phys({ name: 'Vin_Label', color: 0xffffff, map: D.T.label, roughness: .62, clearcoat: .25 });
  D.T.label.userData.mimeType = 'image/png';
  const white = L.phys({ name: 'Vin_EyeWhite', color: 0xf7f3eb, roughness: .18, clearcoat: 1, clearcoatRoughness: .06, sheen: .2, sheenColor: new T.Color(0xffffff) });
  const pupilM = L.phys({ name: 'Vin_Pupil', color: 0x050508, roughness: .1, clearcoat: 1, clearcoatRoughness: .04 });
  const catchM = new T.MeshBasicMaterial({ name: 'Vin_Catchlight', color: 0xffffff });
  const weave = L.tex(L.normalCanvas(128, 128, (u, v, x, y) => .5 + .25 * Math.sin(x / 128 * TAU * 32) * Math.sin(y / 128 * TAU * 32 + .5) + .12 * Math.sin(y / 128 * TAU * 64), 1.4), { color: false, repeat: [3, 3] });
  const glove = L.phys({ name: 'Vin_Glove', color: 0xece8de, roughness: .72, normalMap: weave, normalScale: new T.Vector2(.35, .35), sheen: .9, sheenColor: new T.Color(0xffffff), sheenRoughness: .55, clearcoat: .1 });
  const stitch = L.phys({ name: 'Vin_Stitch', color: 0xb9b2a4, roughness: .8 });
  const rubberHose = L.phys({ name: 'Vin_RubberHose', color: 0x101013, roughness: .34, clearcoat: .55, clearcoatRoughness: .3, sheen: .3, sheenColor: new T.Color(0x3a3a46) });
  const canvasN = L.tex(L.normalCanvas(128, 128, (u, v, x, y) => .5 + .3 * Math.sin(x / 128 * TAU * 24) * .5 + .3 * Math.sin(y / 128 * TAU * 24) * .5 + (L.rng(x * 131 + y)() - .5) * .08, 1.6), { color: false, repeat: [2, 2] });
  const redCanvas = L.phys({ name: 'Vin_ShoeCanvas', color: 0xc22a22, roughness: .84, normalMap: canvasN, normalScale: new T.Vector2(.45, .45), sheen: .45, sheenColor: new T.Color(0xff8a70), sheenRoughness: .6 });
  const sole = L.phys({ name: 'Vin_ShoeRubber', color: 0xf2ece0, roughness: .52, clearcoat: .15 });
  const tread = L.phys({ name: 'Vin_ShoeTread', color: 0x3a3632, roughness: .9 });
  const lace = L.phys({ name: 'Vin_Lace', color: 0xf6f2ea, roughness: .85, sheen: .5, sheenColor: new T.Color(0xffffff) });
  const metal = L.phys({ name: 'Vin_Eyelet', color: 0xc8ccd2, metalness: 1, roughness: .28 });
  const stripeRed = L.phys({ name: 'Vin_SoleStripe', color: 0x9a1c18, roughness: .6 });
  const lamp = L.phys({ name: 'Vin_Flashlight', color: 0x2c2f35, metalness: .85, roughness: .32 });
  const lensM = new T.MeshBasicMaterial({ name: 'Vin_Lens', color: 0x5a4a30 });

  // ---------- 몸: 앞 · 뒤 레코드 면 (극좌표 링: u = 각도, v = 반지름) ----------
  const polar = (r0, r1, nT, nR, zf, dzf, back) => {
    const pos = [], nor = [], uv = [], idx = [];
    for (let i = 0; i <= nR; i++) { const r = r0 + (r1 - r0) * i / nR, z = zf(r), dz = dzf(r);
      for (let j = 0; j <= nT; j++) { const a = j / nT * TAU, c = Math.cos(a), s = Math.sin(a); pos.push(c * r, s * r, back ? -z : z); const n = V3(-dz * c, -dz * s, 1).normalize(); nor.push(n.x, n.y, back ? -n.z : n.z); uv.push(back ? 1 - j / nT : j / nT, vOf(r)); } }
    for (let i = 0; i < nR; i++) for (let j = 0; j < nT; j++) { const a = i * (nT + 1) + j, b = a + 1, c = a + nT + 1, d = c + 1; if (back) idx.push(a, b, c, b, d, c); else idx.push(a, c, b, b, c, d); }
    const g = new T.BufferGeometry(); g.setAttribute('position', new T.Float32BufferAttribute(pos, 3)); g.setAttribute('normal', new T.Float32BufferAttribute(nor, 3)); g.setAttribute('uv', new T.Float32BufferAttribute(uv, 2)); g.setIndex(idx); return g;
  };
  // 형상: 라벨 고원(+0.4 mm) → 런아웃 골(−0.25) → 홈 구간(트랙 사이 얕은 띠) → 외곽 비드(+0.6)
  const sm = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  const prof = r => TH / 2 + .0004 * (1 - sm(RLBL - .0006, RLBL + .0004, r)) - .00025 * sm(RLBL, RLBL + .0008, r) * (1 - sm(RG0 - .0006, RG0, r)) + gaps.reduce((a, g) => a - .00018 * Math.exp(-(((r - g) / .0006) ** 2)), 0) + .0006 * Math.exp(-(((r - .0727) / .0007) ** 2));
  const dprof = r => (prof(r + 1e-5) - prof(r - 1e-5)) / 2e-5;
  add('spin', polar(RH, RF, 96, 80, prof, dprof, false), vinyl, 'Vin_RecordFront');
  const profB = r => prof(r) - (r < .0295 ? .0004 : 0);
  add('spin', polar(.0298, RF, 96, 60, profB, r => (profB(r + 1e-5) - profB(r - 1e-5)) / 2e-5, true), vinyl, 'Vin_RecordBack');
  add('spin', polar(RH, .0298, 64, 10, () => TH / 2 + .0002, () => 0, true), labelMat, 'Vin_Label').geometry.attributes.uv.array.forEach((_, i, a) => {});
  { // 뒷면 라벨 uv: 평면 투영 (라벨 그림이 그대로)
    const lb = M.spin.getObjectByName('Vin_Label'), p = lb.geometry.attributes.position, uv = lb.geometry.attributes.uv;
    for (let i = 0; i < p.count; i++) uv.setXY(i, .5 - p.getX(i) / (2 * .0298), .5 + p.getY(i) / (2 * .0298));
  }
  // 둥근 테두리 (타원 단면) + 스핀들 구멍 벽
  { const pts = []; for (let i = 0; i <= 16; i++) { const a = -Math.PI / 2 + Math.PI * i / 16; pts.push([RF + (R0 - RF) * Math.cos(a) + .00001, (TH / 2 + .0003) * Math.sin(a)]); }
    const g = L.lathe(pts.reverse(), 112); g.rotateX(Math.PI / 2); add('spin', g, rimMat, 'Vin_RecordEdge'); }
  { const g = new T.CylinderGeometry(RH, RH, TH, 24, 1, true); g.rotateX(Math.PI / 2); g.scale(-1, 1, 1); add('spin', g, holeMat, 'Vin_SpindleHole'); }

  // ---------- 눈 (리그의 눈 그룹 · 동공 그룹 공간) ----------
  const k = V.eyeK;
  for (const i of [0, 1]) {
    add('eye' + i, L.blob(.0222, .0325, .0118, d => 1 - .06 * Math.max(0, -d.z), 36, 28), white, 'Vin_EyeWhite' + i);
    add('pupil' + i, L.blob(.0112 * k, .0156 * k, .0046 * k, () => 1, 24, 18), pupilM, 'Vin_Pupil' + i);
    const c1 = new T.SphereGeometry(.0026 * k, 14, 10); c1.scale(1, 1, .45); c1.translate(-.0032 * k, .0052 * k, .0042 * k); add('pupil' + i, c1, catchM, 'Vin_Catch' + i + 'a');
    const c2 = new T.SphereGeometry(.0012 * k, 10, 8); c2.scale(1, 1, .45); c2.translate(.0028 * k, -.004 * k, .0042 * k); add('pupil' + i, c2, catchM, 'Vin_Catch' + i + 'b');
  }

  // ---------- 장갑 (손 그룹 공간: −Y = 팔 방향 = 손가락 쪽, +Z = 카메라 쪽) ----------
  const gloveGeo = side => {
    const S = 1.42, parts = [];
    const palm = L.blob(.0172 * S, .0168 * S, .0128 * S, d => 1 + .05 * Math.max(0, d.z) - .04 * Math.max(0, -d.y) ** 2, 28, 20); palm.translate(0, -.008 * S, 0); parts.push(palm);
    for (let f = 0; f < 3; f++) { const x = (f - 1) * .0104 * S, len = (f === 1 ? .0118 : .0102) * S, a = (f - 1) * .14; const b = [x, -.016 * S, .001 * S], tip = [x + Math.sin(a) * len, -.016 * S - Math.cos(a) * len, .004 * S];
      parts.push(L.capsule(b, tip, .0069 * S, 10)); const kn = new T.SphereGeometry(.0072 * S, 10, 8); kn.translate(b[0], b[1] + .002, b[2]); parts.push(kn); }
    parts.push(L.capsule([side * .011 * S, -.006 * S, .007 * S], [side * .019 * S, -.016 * S, .013 * S], .0062 * S, 12));      // 엄지 (카메라 쪽 · 바깥으로)
    // 말린 커프 (넓게 벌어진 고리) + 손목 띠
    const cuff = L.lathe([[.0118 * S, -.004 * S], [.0158 * S, -.002 * S], [.0192 * S, .004 * S], [.0205 * S, .009 * S], [.0192 * S, .0125 * S], [.0158 * S, .013 * S], [.0128 * S, .011 * S]], 40); cuff.translate(0, .002 * S, 0); parts.push(cuff);
    return L.merge(parts);
  };
  const stitchGeo = () => { const S = 1.42, parts = []; for (const x of [-.0058, 0, .0058]) parts.push(L.tube([[x * S, -.002 * S, -.0118 * S], [x * S * 1.05, -.009 * S, -.0128 * S], [x * S * 1.1, -.016 * S, -.0112 * S]], .00055, 10, 5)); return L.merge(parts); };
  for (const i of [0, 1]) { const s = i ? 1 : -1; add('hand' + i, gloveGeo(s), glove, 'Vin_Glove' + i); add('hand' + i, stitchGeo(), stitch, 'Vin_GloveStitch' + i); }

  // ---------- 운동화 (신발 그룹 공간: +Z = 앞코, y = 0 바닥) ----------
  const shoeParts = () => {
    const P = { canvas: [], rubber: [], tread: [], lace: [], metal: [], stripe: [] };
    // 밑창: 둥근 판 + 앞코 범퍼 + 바닥 트레드
    const so = L.sbox(.0545, .017, .094, 7, 28, 12); so.translate(0, .0085, .0115); P.rubber.push(so);
    const toe = L.blob(.0262, .019, .026, d => 1, 22, 14); toe.translate(0, .016, .041); P.rubber.push(toe);
    for (let z = -.03; z < .056; z += .0072) { const r = new T.BoxGeometry(.046, .0022, .0034); r.translate(0, .0003, z); P.tread.push(r); }
    const strp = L.sbox(.0556, .0026, .0956, 8, 28, 4); strp.translate(0, .0118, .0115); P.stripe.push(strp);
    // 캔버스 갑피 + 하이탑 발목
    const up = L.blob(.0232, .0215, .043, d => 1 + .06 * Math.max(0, d.y), 28, 18); up.translate(0, .029, .002); P.canvas.push(up);
    const shaft = L.lathe([[.0232, .034], [.0234, .046], [.0228, .058], [.0218, .068], [.021, .0735]], 36); shaft.translate(0, 0, -.009); P.canvas.push(shaft);
    const pad = new T.TorusGeometry(.0212, .0042, 10, 36); pad.rotateX(Math.PI / 2); pad.translate(0, .0738, -.009); P.canvas.push(pad);
    const tongue = L.sbox(.019, .036, .0055, 5, 14, 10); tongue.rotateX(-.38); tongue.translate(0, .066, .0125); P.canvas.push(tongue);
    const heel = L.sbox(.012, .022, .004, 5, 10, 8); heel.translate(0, .062, -.0318); P.rubber.push(heel);
    // 끈 · 아일릿 (앞쪽 경사면 위)
    for (let n = 0; n < 4; n++) { const y = .036 + n * .0085, z = .036 - n * .0105;
      for (const s of [-1, 1]) { const e = new T.TorusGeometry(.0021, .0007, 6, 12); e.rotateY(Math.PI / 2 - .5); e.rotateX(-.55); e.translate(s * .0082, y, z); P.metal.push(e); }
      const a = L.tube([[-.0082, y, z + .002], [0, y + .0018, z + .0042], [.0082, y + .0035, z - .002]], .0011, 8, 5, false); const b = L.tube([[.0082, y, z + .002], [0, y + .0018, z + .0042], [-.0082, y + .0035, z - .002]], .0011, 8, 5, false); P.lace.push(a, b); }
    const bow = L.tube([[-.006, .07, .016], [-.012, .074, .02], [-.005, .076, .018], [0, .073, .017], [.005, .076, .018], [.012, .074, .02], [.006, .07, .016]], .0011, 24, 5, false); P.lace.push(bow);
    // 발목 패치 (양옆 흰 원)
    for (const s of [-1, 1]) { const c = new T.CylinderGeometry(.0072, .0072, .0012, 24); c.rotateZ(Math.PI / 2); c.translate(s * .0236, .054, -.008); P.rubber.push(c); }
    return P;
  };
  for (const i of [0, 1]) { const P = shoeParts();
    add('shoe' + i, L.merge(P.canvas), redCanvas, 'Vin_ShoeCanvas' + i); add('shoe' + i, L.merge(P.rubber), sole, 'Vin_ShoeRubber' + i); add('shoe' + i, L.merge(P.tread), tread, 'Vin_ShoeTread' + i);
    add('shoe' + i, L.merge(P.lace), lace, 'Vin_ShoeLace' + i); add('shoe' + i, L.merge(P.metal), metal, 'Vin_ShoeEyelet' + i); add('shoe' + i, L.merge(P.stripe), stripeRed, 'Vin_ShoeStripe' + i); }

  // ---------- 손전등 (손전등 그룹 공간: −Y 방향) ----------
  { const P = []; const body = new T.CylinderGeometry(.0056, .0058, .03, 20); body.translate(0, -.011, 0); P.push(body);
    for (let n = 0; n < 5; n++) { const r = new T.TorusGeometry(.0058, .0006, 6, 20); r.rotateX(Math.PI / 2); r.translate(0, -.004 - n * .0035, 0); P.push(r); }
    const head = L.lathe([[.0058, -.026], [.0066, -.028], [.0086, -.0385], [.0088, -.0402], [.0078, -.0404]], 24); P.push(head);
    const tail = new T.CylinderGeometry(.0052, .0056, .004, 16); tail.translate(0, .006, 0); P.push(tail);
    const sw = L.sbox(.003, .005, .002, 4, 8, 6); sw.translate(0, -.018, .0058); P.push(sw);
    add('flash', L.merge(P), lamp, 'Vin_Flashlight');
    const lens = new T.CircleGeometry(.0078, 20); lens.rotateX(Math.PI / 2); lens.translate(0, -.0403, 0); const lm = add('flash', lens, lensM, 'Vin_FlashLens'); lm.userData.swapMat = 'lens'; lm.castShadow = false; }

  // ---------- 고무호스 팔다리 (스킨: 곡선을 따라 뼈 7개) ----------
  const HN = D.HOSE_N, RS = 28, RAD = 12;
  V.limbRig.forEach((Lb, li) => {
    const h = Lb.h, r0 = li < 2 ? .006 : .0067, bones = Lb.bones.map(o => M[o.userData.rig]);
    const pos = [], nor = [], idx = [], tval = [], tmp = new T.Object3D();
    for (let i = 0; i <= RS; i++) { const t = i / RS; D.hoseFrame(h, t, tmp); const X = V3(1, 0, 0).applyQuaternion(tmp.quaternion), Z = V3(0, 0, 1).applyQuaternion(tmp.quaternion), rr = r0 * (1 - .12 * Math.sin(t * Math.PI));
      for (let j = 0; j <= RAD; j++) { const a = j / RAD * TAU, n = X.clone().multiplyScalar(Math.cos(a)).addScaledVector(Z, Math.sin(a)); pos.push(tmp.position.x + n.x * rr, tmp.position.y + n.y * rr, tmp.position.z + n.z * rr); nor.push(n.x, n.y, n.z); tval.push(t); } }
    for (let i = 0; i < RS; i++) for (let j = 0; j < RAD; j++) { const a = i * (RAD + 1) + j, b = a + 1, c = a + RAD + 1, d = c + 1; idx.push(a, c, b, b, c, d); }
    // 끝 막음 (반구)
    for (const e of [0, 1]) { D.hoseFrame(h, e, tmp); const Y = V3(0, 1, 0).applyQuaternion(tmp.quaternion).multiplyScalar(e ? 1 : -1), base = pos.length / 3; const s = new T.SphereGeometry(r0 * .99, RAD, 6, 0, TAU, 0, Math.PI / 2); s.applyQuaternion(new T.Quaternion().setFromUnitVectors(V3(0, 1, 0), Y)); s.translate(tmp.position.x, tmp.position.y, tmp.position.z);
      const sp = s.attributes.position, sn = s.attributes.normal; for (let q = 0; q < sp.count; q++) { pos.push(sp.getX(q), sp.getY(q), sp.getZ(q)); nor.push(sn.getX(q), sn.getY(q), sn.getZ(q)); tval.push(e); } for (let q = 0; q < s.index.count; q++) idx.push(s.index.getX(q) + base); }
    const g = new T.BufferGeometry(); g.setAttribute('position', new T.Float32BufferAttribute(pos, 3)); g.setAttribute('normal', new T.Float32BufferAttribute(nor, 3)); g.setIndex(idx);
    const sk = L.skinned(g, rubberHose, bones, (p, i) => { const tt = tval[i] * HN, k0 = Math.min(HN - 1, Math.floor(tt)), u = tt - k0; return [[k0, 1 - u], [k0 + 1, u]]; });
    sk.mesh.name = 'Vin_' + D.HOSE_LIMBS[li] + '_Hose'; sk.mesh.castShadow = true; sk.mesh.receiveShadow = true; scene.add(sk.mesh); scene.updateMatrixWorld(true); sk.bind();
  });

  // ---------- 클립: 실제 게임 리그를 움직여 녹화 (가만히 · 걷기 · 달리기 · 점프 · 숙이기) ----------
  const snap = L.snap(mir), clips = [], H = ODD2.HERO_DEFS.vin;
  const drive = (s, secs, warm = 1.5) => { Object.assign(st, { yawOverride: undefined, lookAt: undefined, face: 1 }, s); let t = 0; for (let i = 0; i < warm * 60; i++) { st.t = (t += 1 / 60); D.animateVin(V, st, 1 / 60); } return () => { st.t = (t += 1 / 30); D.animateVin(V, st, 1 / 30); D.hoseRigUpdate(V); }; };
  const cyc = (spd, Lstride) => Math.max(8, Math.round(Lstride / spd * 30));
  let step = drive({ vel: V3(0, 0, 0), grounded: true }, 0); clips.push(L.record('Idle', mir, 60, () => step()));
  step = drive({ vel: V3(H.walk, 0, 0), grounded: true }); clips.push(L.record('Walk', mir, cyc(H.walk, .3) + 1, () => step()));
  step = drive({ vel: V3(H.run, 0, 0), grounded: true }); clips.push(L.record('Run', mir, cyc(H.run, .52) + 1, () => step()));
  step = drive({ vel: V3(0, 0, 0), grounded: false, vy: 1.4 }, .3); clips.push(L.record('Jump', mir, 18, () => step()));
  step = drive({ vel: V3(0, 0, 0), grounded: true, crouch: 1 }, .6); clips.push(L.record('Crouch', mir, 30, () => step()));
  L.restore(snap);
  const info = Object.assign({ character: 'vin' }, L.stats(scene), { clips: clips.map(c => c.name + ':' + c.tracks.length), nodes: mir.list.length });
  const b64 = await L.export(scene, clips);
  return { b64, info };
};
