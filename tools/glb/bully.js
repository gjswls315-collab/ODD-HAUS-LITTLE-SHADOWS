/* Bully 최종 모델 → assets/characters/bully/enemy_bully.glb
   실제 인간 남자아이 크기(키 약 150 cm) — 다리 = 키의 약 49%, 머리는 살짝 큰 소년 비율(키의 약 1/5.8).
   금발(캡 아래로 삐져나온 부스스한 머리), 뒤로 쓴 버건디 캡(스냅백 · 뒷면 로고), 주근깨, 얄미운 웃음,
   검은 그래픽 티셔츠(해골 + 교차한 플라잉V 프린트), 어두운 청바지(접은 밑단 · 뒷주머니), 빨간 하이탑, 빨간 손목 밴드, 빨간 전기기타(플라잉V).
   게임 리그(Bully)의 묶음 자세를 거울 노드로 — 게임에서는 리그(IK · 추격 · 연주)가 움직인다.
   스킨: 티(골반 · 척추) · 청바지 다리(골반 · 엉덩이 · 무릎) · 팔(어깨 · 팔꿈치). 나머지는 뼈에 붙은 단단한 부품.
   클립: Idle · Walk · Run · GuitarPlay · Listen · Search · Grab · Kneel · Point · Stumble · Kick */
window.GLBA_JOB = async () => {
  const L = GLBA, T = L.T, D = ODD2.dev, V3 = L.V3, TAU = Math.PI * 2, B = ODD2.BULLY;
  // ---------- 리그: 게임의 Bully를 원점 · 정면(+Z) · 선 자세(기타는 등에)로 ----------
  Object.assign(B, { state: 'leave', stT: 9, yaw: 0, prevYaw: 0, visYaw: 0, moving: 0, phase: 'play', phaseT: 0, act: null, peek: false, xray: 0 });
  B.pos.set(0, 0, 0); B.prev.set(0, 0, 0); B.root.position.set(0, 0, 0); B.root.visible = true; B.look.set(0, 1.38, 4);
  ODD2.P.pos.set(0, .1, 3); ODD2.P.center.set(0, .2, 3);
  const anim = (n, dt = 1 / 60) => { for (let i = 0; i < n; i++) { B.tA = (B.tA || 0) + dt; B.stT += dt; if (B.state === 'seated') B.phaseT += dt; D.bullyAnimate(dt, B.tA, 1); } };
  anim(200); B.p.tongue = 0; anim(1);
  B.root.updateMatrixWorld(true);
  const boneNames = new Set(['pelvis', 'spine', 'hip0', 'hip1', 'knee0', 'knee1', 'sho0', 'sho1', 'elb0', 'elb1']);
  const mir = L.mirror(B.root, 'BULLY', boneNames);
  Object.assign(mir.root.userData, { oddRig: 'bully', character: 'bully', height: 1.5, unit: 'm', note: 'ODD HAUS Bully — 실제 소년 크기 150 cm. 노드 extras.link = 게임 리그 이름' });
  const scene = new T.Scene(); scene.name = 'enemy_bully'; scene.add(mir.root);
  const M = mir.map, R = {}; B.root.traverse(o => { if (o.userData.rig) R[o.userData.rig] = o; });
  const add = (node, geo, mat, name) => { const m = new T.Mesh(geo, mat); m.name = name; m.castShadow = true; m.receiveShadow = true; M[node].add(m); return m; };
  const toRoot = (node, g) => g.applyMatrix4(R[node].matrixWorld);       // 리그 노드 로컬 → 루트(묶음 자세) 공간
  const blob = (rx, ry, rz, f, ws = 18, hs = 12) => L.blob(rx, ry, rz, f || (() => 1), ws, hs), cap = (a, b, r, rad = 8) => L.capsule(a, b, r, rad, 3);
  const sstep = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

  // ---------- 재질 ----------
  const noiseN = (seed, k = .08) => (u, v, x, y) => .5 + (L.rng(x * 131 + y * 7 + seed)() - .5) * k;
  const skinN = L.tex(L.normalCanvas(128, 128, noiseN(3, .18), .8), { color: false, repeat: [4, 4] });
  const skin = L.phys({ name: 'Bully_Skin', color: 0xeab48e, roughness: .52, normalMap: skinN, normalScale: new T.Vector2(.18, .18), sheen: .35, sheenColor: new T.Color(0xffc8a8), sheenRoughness: .5 });
  const lipM = L.phys({ name: 'Bully_Lip', color: 0xc4766a, roughness: .42 });
  const ear = L.phys({ name: 'Bully_EarInner', color: 0xd4917a, roughness: .6 });
  const freckle = L.phys({ name: 'Bully_Freckle', color: 0xb0683c, roughness: .6 });
  const white = L.phys({ name: 'Bully_EyeWhite', color: 0xf6f2ea, roughness: .15, clearcoat: 1, clearcoatRoughness: .05 });
  const irisTex = L.tex(L.canvas(128, 128, (g, w, h) => {
    g.fillStyle = '#05070a'; g.fillRect(0, 0, w, h);
    const R0 = L.rng(9);
    for (let x = 0; x < w; x++) { for (let y = Math.round(h * .17); y < h * .5; y++) { const k = (y - h * .17) / (h * .33), b = .75 + R0() * .3; const c = [40 + 60 * k, 110 + 70 * (1 - k) * b, 190 * b]; g.fillStyle = `rgb(${c[0] | 0},${c[1] | 0},${c[2] | 0})`; g.fillRect(x, y, 1, 1); } }
    g.fillStyle = 'rgba(10,20,40,.9)'; g.fillRect(0, h * .44, w, h * .06);
    g.fillStyle = '#05070a'; g.fillRect(0, 0, w, h * .17);
  }), { wrap: true });
  const irisM = L.phys({ name: 'Bully_Iris', map: irisTex, roughness: .08, clearcoat: 1, clearcoatRoughness: .02 });
  const lashM = L.phys({ name: 'Bully_Lash', color: 0x3a2814, roughness: .7 });
  const catchM = new T.MeshBasicMaterial({ name: 'Bully_Catchlight', color: 0xffffff });
  const browM = L.phys({ name: 'Bully_Brow', color: 0x7a5824, roughness: .85, sheen: .5, sheenColor: new T.Color(0xf0d088) });
  const mouthM = L.phys({ name: 'Bully_MouthInside', color: 0x4a1418, roughness: .7 });
  const teethM = L.phys({ name: 'Bully_Teeth', color: 0xf4efe2, roughness: .25, clearcoat: .6 });
  const tongueM = L.phys({ name: 'Bully_Tongue', color: 0xd8606a, roughness: .38, clearcoat: .5 });
  const hairN = L.tex(L.normalCanvas(128, 128, (u, v, x, y) => .5 + .25 * Math.sin(x * .7 + Math.sin(y * .05) * 3) + (L.rng(x * 3 + y * 977)() - .5) * .1, 1.0), { color: false, repeat: [2, 1] });
  const hairBase = L.phys({ name: 'Bully_HairBase', color: 0xcfa448, roughness: .6, normalMap: hairN, normalScale: new T.Vector2(.35, .35), sheen: 1, sheenColor: new T.Color(0xfff0b0), sheenRoughness: .35 });
  const hairM = L.phys({ name: 'Bully_Hair', color: 0xffffff, vertexColors: true, roughness: .55, sheen: 1, sheenColor: new T.Color(0xfff2b8), sheenRoughness: .35 });
  const twillN = L.tex(L.normalCanvas(128, 128, (u, v, x, y) => .5 + .3 * Math.sin((x + y) / 128 * TAU * 20) + (L.rng(x * 17 + y * 1031)() - .5) * .12, 1.3), { color: false, repeat: [3, 3] });
  const capM = L.phys({ name: 'Bully_Cap', color: 0x7a1a22, roughness: .78, normalMap: twillN, normalScale: new T.Vector2(.5, .5), sheen: .5, sheenColor: new T.Color(0xc06070), sheenRoughness: .6 });
  const capDark = L.phys({ name: 'Bully_CapBrim', color: 0x4a0c12, roughness: .7, normalMap: twillN, normalScale: new T.Vector2(.4, .4) });
  const capLogoTex = L.tex(L.canvas(128, 128, (g, w, h) => { g.fillStyle = '#7a1a22'; g.fillRect(0, 0, w, h); g.fillStyle = '#efe6d4'; g.beginPath(); g.arc(64, 64, 58, 0, TAU); g.fill(); g.fillStyle = '#16161a'; g.beginPath(); g.arc(64, 64, 50, 0, TAU); g.fill(); g.fillStyle = '#e8231c'; g.font = 'bold 76px Impact, "Arial Black", sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('B', 64, 68); }), { wrap: false });
  const capLogo = L.phys({ name: 'Bully_CapLogo', map: capLogoTex, roughness: .7 });
  const snapM = L.phys({ name: 'Bully_Snap', color: 0x101012, roughness: .35, clearcoat: .5 });
  // 티셔츠: 검은 면 + 앞면 그래픽 프린트 (해골 + 교차한 플라잉V + NOISE!) — 선반 UV: u .5 = 앞
  const teeTex = L.tex(L.canvas(1024, 512, (g, w, h) => {
    g.fillStyle = '#141416'; g.fillRect(0, 0, w, h);
    const Rn = L.rng(4); for (let i = 0; i < 9000; i++) { g.fillStyle = `rgba(${Rn() < .5 ? '60,60,70' : '0,0,0'},${.12 + Rn() * .12})`; g.fillRect(Rn() * w, Rn() * h, 1 + Rn() * 2, 1); }
    const cx = w * .5, cy = h * .4, S = h * .0021;
    g.save(); g.translate(cx, cy); g.scale(S * 1.0, S);
    const cream = '#ebe2cc', red = '#c8241e';
    for (const sgn of [-1, 1]) { g.save(); g.rotate(sgn * .62); g.fillStyle = red; g.beginPath(); g.moveTo(-8, -150); g.lineTo(8, -150); g.lineTo(8, 40); g.lineTo(46, 120); g.lineTo(24, 128); g.lineTo(0, 70); g.lineTo(-24, 128); g.lineTo(-46, 120); g.lineTo(-8, 40); g.closePath(); g.fill(); g.fillStyle = cream; g.fillRect(-5, -150, 10, 170); g.beginPath(); g.moveTo(-14, -150); g.lineTo(14, -150); g.lineTo(10, -175); g.lineTo(-10, -175); g.fill(); g.restore(); }
    g.fillStyle = cream; g.beginPath(); g.ellipse(0, -10, 70, 66, 0, 0, TAU); g.fill(); g.fillRect(-42, 30, 84, 40);
    g.fillStyle = '#141416'; for (const sgn of [-1, 1]) { g.beginPath(); g.ellipse(sgn * 27, -6, 20, 22, sgn * .2, 0, TAU); g.fill(); }
    g.beginPath(); g.moveTo(0, 18); g.lineTo(-9, 36); g.lineTo(9, 36); g.closePath(); g.fill();
    for (let i = -3; i <= 3; i++) g.fillRect(i * 11 - 2, 48, 4, 22);
    g.fillStyle = red; g.font = 'bold 64px Impact, "Arial Black", sans-serif'; g.textAlign = 'center'; g.fillText('NOISE!', 0, 150);
    g.restore();
    for (let i = 0; i < 1600; i++) { const a = Rn() * TAU, r = Math.sqrt(Rn()) * h * .36; g.fillStyle = 'rgba(20,20,22,.85)'; g.fillRect(cx + Math.cos(a) * r * 1.3, cy + Math.sin(a) * r, 1 + Rn() * 3, 1 + Rn() * 2); }
  }), { jpeg: true });
  const teeM = L.phys({ side: T.DoubleSide,  name: 'Bully_Tee', map: teeTex, color: 0xffffff, roughness: .92, normalMap: twillN, normalScale: new T.Vector2(.25, .25), sheen: .6, sheenColor: new T.Color(0x50505c), sheenRoughness: .7 });
  const teeDark = L.phys({ name: 'Bully_TeeSleeve', color: 0x161618, roughness: .92, normalMap: twillN, normalScale: new T.Vector2(.25, .25), sheen: .6, sheenColor: new T.Color(0x50505c), sheenRoughness: .7 });
  const denimN = L.tex(L.normalCanvas(128, 128, (u, v, x, y) => .5 + .32 * Math.sin((x * 2 + y) / 128 * TAU * 16) + (L.rng(x * 7 + y * 331)() - .5) * .22, 1.6), { color: false, repeat: [10, 6] });
  const denimTex = L.tex(L.canvas(128, 128, (g, w, h) => { const Rn = L.rng(12); g.fillStyle = '#262a36'; g.fillRect(0, 0, w, h); for (let i = 0; i < 1400; i++) { g.fillStyle = Rn() < .5 ? 'rgba(70,78,100,.35)' : 'rgba(10,12,18,.35)'; g.fillRect(Rn() * w, Rn() * h, 1 + Rn() * 3, 1); } }), { repeat: [6, 4], jpeg: true });
  const jeansM = L.phys({ side: T.DoubleSide,  name: 'Bully_Jeans', map: denimTex, color: 0xffffff, roughness: .88, normalMap: denimN, normalScale: new T.Vector2(.5, .5), sheen: .5, sheenColor: new T.Color(0x56607a), sheenRoughness: .6 });
  const stitchM = L.phys({ name: 'Bully_Stitch', color: 0xb08a4a, roughness: .8 });
  const rivet = L.phys({ name: 'Bully_Rivet', color: 0xb89050, metalness: 1, roughness: .35 });
  const canvasN = L.tex(L.normalCanvas(128, 128, (u, v, x, y) => .5 + .15 * Math.sin(x / 128 * TAU * 24) + .15 * Math.sin(y / 128 * TAU * 24) + (L.rng(x * 131 + y)() - .5) * .08, 1.6), { color: false, repeat: [3, 3] });
  const redCanvas = L.phys({ name: 'Bully_ShoeCanvas', color: 0xc4261f, roughness: .82, normalMap: canvasN, normalScale: new T.Vector2(.5, .5), sheen: .45, sheenColor: new T.Color(0xff8a70), sheenRoughness: .6 });
  const rubber = L.phys({ name: 'Bully_ShoeRubber', color: 0xece6da, roughness: .62, clearcoat: .15 });
  const treadM = L.phys({ name: 'Bully_ShoeTread', color: 0x6e6860, roughness: .9 });
  const laceM = L.phys({ name: 'Bully_Lace', color: 0xf3efe6, roughness: .8, sheen: .5, sheenColor: new T.Color(0xffffff) });
  const chrome = L.phys({ name: 'Bully_Chrome', color: 0xd8d8dc, metalness: 1, roughness: .18 });
  const bandM = L.phys({ name: 'Bully_Wristband', color: 0xc8231d, roughness: .95, normalMap: canvasN, normalScale: new T.Vector2(.8, .8), sheen: .8, sheenColor: new T.Color(0xff9a8a), sheenRoughness: .7 });
  const strapM = L.phys({ name: 'Bully_Strap', color: 0x141214, roughness: .5, clearcoat: .3, normalMap: canvasN, normalScale: new T.Vector2(.3, .3) });
  const lacq = L.phys({ name: 'Bully_GuitarRed', color: 0xc8121a, roughness: .2, clearcoat: 1, clearcoatRoughness: .04, sheen: .2, sheenColor: new T.Color(0xff6060) });
  const guard = L.phys({ name: 'Bully_Pickguard', color: 0xf1ede2, roughness: .3, clearcoat: .8 });
  const pickupM = L.phys({ name: 'Bully_Pickup', color: 0x0e0e10, roughness: .4, clearcoat: .4 });
  const rosewood = L.phys({ name: 'Bully_Fretboard', color: 0x2e1a10, roughness: .7, normalMap: twillN, normalScale: new T.Vector2(.2, .2) });
  const pearl = L.phys({ name: 'Bully_Inlay', color: 0xf4f0e8, roughness: .2, clearcoat: 1, iridescence: .6 });
  const nickel = L.phys({ name: 'Bully_Nickel', color: 0xcfcfc8, metalness: 1, roughness: .28 });
  const knobM = L.phys({ name: 'Bully_Knob', color: 0x18120e, roughness: .3, clearcoat: .8 });
  const stickerTex = L.tex(L.canvas(256, 96, (g, w, h) => { g.fillStyle = '#f2d43a'; g.fillRect(0, 0, w, h); g.strokeStyle = '#1a1a1a'; g.lineWidth = 6; g.strokeRect(6, 6, w - 12, h - 12); g.fillStyle = '#1a1a1a'; g.font = 'bold 64px Impact, "Arial Black", sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('BULLY', w / 2, h / 2 + 3); }), { wrap: false });
  const stickerM = L.phys({ name: 'Bully_Sticker', map: stickerTex, roughness: .5 });

  // =====================================================================
  // 머리 (머리 노드 로컬 — 노드 배율 .92)
  // =====================================================================
  { // 머리 · 얼굴: 두개골 · 뒤통수 · 턱 · 볼 · 턱끝 · 코를 매끈하게 합친 한 덩어리 (부드러운 합집합 SDF를 중심에서 광선으로 찾아 표면을 만든다)
    const ell = (c, r) => p => { const x = (p.x - c[0]) / r[0], y = (p.y - c[1]) / r[1], z = (p.z - c[2]) / r[2], k0 = Math.hypot(x, y, z), k1 = Math.hypot(x / r[0], y / r[1], z / r[2]); return k0 * (k0 - 1) / (k1 || 1e-6); };
    const smin = (a, b, k) => { const h = Math.max(k - Math.abs(a - b), 0) / k; return Math.min(a, b) - h * h * k / 4; };
    const parts = [[ell([0, .135, 0], [.104, .13, .114]), 0], [ell([0, .15, -.03], [.1, .112, .1]), .02], [ell([0, .076, .028], [.084, .068, .088]), .03], [ell([0, .032, .078], [.034, .026, .028]), .02],
      [ell([-.05, .085, .072], [.04, .03, .034]), .015], [ell([.05, .085, .072], [.04, .03, .034]), .015], [ell([0, .108, .115], [.014, .024, .018]), .008], [ell([0, .095, .122], [.019, .013, .015]), .008]];
    const sdf = p => { let d = parts[0][0](p); for (let i = 1; i < parts.length; i++) d = smin(d, parts[i][0](p), parts[i][1]); return d; };
    const C = V3(0, .118, .02), g = new T.SphereGeometry(1, 80, 60), pp = g.attributes.position, dv = V3(), q = V3();
    for (let i = 0; i < pp.count; i++) { dv.fromBufferAttribute(pp, i); let a = 0, b = .3; for (let it = 0; it < 30; it++) { const m = (a + b) / 2; q.copy(C).addScaledVector(dv, m); if (sdf(q) < 0) a = m; else b = m; } q.copy(C).addScaledVector(dv, (a + b) / 2); pp.setXYZ(i, q.x, q.y, q.z); }
    g.computeVertexNormals(); add('head', g, skin, 'Bully_Head');
    for (const s of [-1, 1]) { const n2 = blob(.005, .003, .004); n2.translate(s * .0085, .086, .127); add('head', n2, mouthM, 'Bully_Nostril' + (s + 1)); }
    for (const s of [-1, 1]) { const e = blob(.016, .033, .014, d => 1 - .15 * Math.max(0, -d.y)); e.rotateY(s * .35); e.translate(s * .103, .122, -.006); add('head', e, skin, 'Bully_Ear' + (s + 1));
      const ei = blob(.008, .022, .006); ei.rotateY(s * .35); ei.translate(s * .113, .124, -.002); add('head', ei, ear, 'Bully_EarInner' + (s + 1)); }
    // 주근깨 (볼 · 콧등)
    { const RF = L.rng(77), P = []; for (const s of [-1, 1]) for (let i = 0; i < 11; i++) { const x = s * (.028 + RF() * .04), y = .1 + RF() * .028; const z = .114 * Math.sqrt(Math.max(0, 1 - (x / .104) ** 2 - ((y - .135) / .13) ** 2)) * .95 + .0025; const f = new T.CircleGeometry(.0022 + RF() * .0012, 6); f.lookAt(V3(x / .104 ** 2, (y - .135) / .13 ** 2, z / .114 ** 2)); f.translate(x, y, Math.max(z, .1)); P.push(f); }
      add('head', L.merge(P), freckle, 'Bully_Freckles'); }
    // 목 윗부분 (머리를 숙여도 틈이 안 보이게)
    { const nk = new T.CylinderGeometry(.046, .048, .07, 20, 1, true); nk.translate(0, .01, -.01); add('head', nk, skin, 'Bully_NeckTop'); }
  }
  // 눈 (눈 노드 로컬 — 깜빡임은 노드 Y 배율): 흰자 · 파란 홍채 · 동공(텍스처) · 캐치라이트 · 윗눈꺼풀 · 속눈썹 선
  for (const [i, s] of [[0, -1], [1, 1]]) {
    const n = 'eye' + i;
    add(n, L.blob(.022, .026, .014, () => 1, 24, 18).translate(0, 0, -.003), white, 'Bully_EyeWhite' + i);
    const ir = new T.SphereGeometry(.0138, 24, 10, 0, TAU, 0, Math.PI / 2); ir.rotateX(Math.PI / 2); ir.scale(1, 1.1, .45); ir.translate(-s * .002, -.003, .0102); add(n, ir, irisM, 'Bully_Iris' + i);
    const cl = new T.SphereGeometry(.0032, 8, 6); cl.translate(-s * .006, .004, .0158); add(n, cl, catchM, 'Bully_Catch' + i);
    const lid = new T.SphereGeometry(1, 24, 10, 0, TAU, 0, Math.PI * .45); lid.scale(.0238, .0278, .0158); lid.translate(0, .001, .0005); add(n, lid, skin, 'Bully_Lid' + i);
    const lash = new T.TorusGeometry(.0205, .0016, 6, 20, Math.PI * .72); lash.rotateZ(Math.PI * .14); lash.scale(1.05, 1.0, .7); lash.translate(0, -.0045, .0088); add(n, lash, lashM, 'Bully_Lash' + i);
  }
  // 눈썹 (눈썹 노드 로컬: +Y = 안쪽 끝 — 안쪽이 굵다)
  for (const i of [0, 1]) add('brow' + i, L.tube([[0, -.021, 0], [0, -.005, .002], [0, .012, .003], [0, .022, .001]], t => .005 + .0035 * t, 12, 8), browM, 'Bully_Brow' + i);
  // 입 (입 노드 로컬): 한쪽 입꼬리가 올라간 얄미운 웃음 — 입 안 · 윗니 · 아랫입술 · 입꼬리
  { const mo = new T.CircleGeometry(.03, 24, Math.PI, Math.PI); mo.scale(1, .42, 1); mo.rotateZ(.14); mo.translate(.006, .005, .004); add('mouth', mo, mouthM, 'Bully_MouthInside');
    const th = L.sbox(.034, .007, .006, 4, 12, 8); th.rotateZ(.14); th.translate(.008, .002, .006); add('mouth', th, teethM, 'Bully_Teeth');
    const lip = L.tube([[-.024, .002, .003], [-.01, -.009, .007], [.01, -.01, .008], [.026, -.002, .006], [.036, .01, .003]], t => .003 * Math.sin(.2 + t * 2.7), 16, 6); add('mouth', lip, lipM, 'Bully_LowerLip');
    const up = L.tube([[-.026, .003, .004], [-.008, .007, .007], [.016, .009, .007], [.037, .012, .003]], .0016, 12, 6); add('mouth', up, lipM, 'Bully_UpperLip');
    const cn = cap([.034, .009, .004], [.04, .017, .001], .0026, 8); add('mouth', cn, lipM, 'Bully_SmirkCorner'); }
  // 혀 (혀 노드 로컬: +Y = 앞으로 내민 방향 — 납작해서 접히면 보이지 않는다)
  { const tg = blob(.012, .018, .0055, d => 1 - .25 * Math.max(0, -d.y)); tg.translate(0, .018, 0); add('tongue', tg, tongueM, 'Bully_Tongue'); }
  // 머리카락: 캡 아래 금발 덩어리 + 부스스한 가닥(옆 · 뒤 · 앞머리)
  { const hb = L.blob(.11, .118, .122, () => 1, 32, 24); hb.translate(0, .16, -.015); add('head', hb, hairBase, 'Bully_HairBase');
    const nape = L.blob(.096, .07, .1, () => 1, 24, 16); nape.translate(0, .102, -.036); add('head', nape, hairBase, 'Bully_HairNape');
    const BL = [0xe8c463, 0xd9ad48, 0xf0d488, 0xc89a3a, 0xe0b850, 0xf4dc98, 0xb8882e];
    const col = (u, Rr) => BL[(Rr() * BL.length) | 0];
    const side = u => { const capLine = .12 + .3 * Math.max(0, u.z); if (u.y > capLine) return false; if (u.z > .3 && u.y < .16) return false; if (Math.abs(u.x) > .55 && u.y < -.18 && u.z > -.35) return false; return u.y > -.5; };
    add('head', L.fur({ c: [0, .16, -.015], r: [.11, .118, .122], n: 420, len: [.016, .03], lift: 1.0, droop: .45, flow: [0, -.6, -.6], flowK: .55, w: .0085, segs: 3, clump: 5, jit: .45, color: col, seed: 31, mask: side, inset: .95 }), hairM, 'Bully_HairTufts');
    add('head', L.fur({ c: [0, .16, -.015], r: [.11, .118, .122], n: 90, len: [.016, .028], lift: 1.0, droop: .5, flow: [.4, -.5, .7], flowK: .6, w: .009, segs: 3, clump: 5, color: col, seed: 32, mask: u => u.z > .6 && u.y > .16 && u.y < .5, inset: .95 }), hairM, 'Bully_HairFringe');
    add('head', L.fur({ c: [0, .16, -.015], r: [.11, .118, .122], n: 110, len: [.016, .03], lift: 1.4, droop: .2, flow: [0, .2, -1], flowK: .5, w: .0085, segs: 3, clump: 4, color: col, seed: 33, mask: u => u.z < -.5 && u.y > -.42 && u.y < .1, inset: .95 }), hairM, 'Bully_HairSpikes'); }
  // 뒤로 쓴 버건디 캡 (캡 노드 로컬: 챙 = 뒤(−Z), 스냅백 구멍 = 앞(+Z))
  { const RX = .1176, RY = .1036, RZ = .1302, CY = -.01;
    const dome = new T.SphereGeometry(1, 36, 16, 0, TAU, 0, Math.PI / 2.25); dome.scale(RX, RY, RZ); dome.translate(0, CY, 0);
    { const p = dome.attributes.position, v = V3(); for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i); const ang = Math.atan2(v.x, v.z), fr = Math.exp(-(ang * ang) / .16) * Math.max(0, 1 - (v.y - CY) / .06); if (fr > .02) { p.setXYZ(i, v.x * (1 - fr * .04), v.y, v.z * (1 - fr * .04)); } } dome.computeVertexNormals(); }
    add('cap', dome, capM, 'Bully_CapCrown');
    const onDome = (az, el, off = .0015) => { const d = V3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el)); const p = V3(d.x * RX, d.y * RY + CY, d.z * RZ), nn = V3(d.x / RX, d.y / RY, d.z / RZ).normalize(); return { p: p.addScaledVector(nn, off), n: nn }; };
    // 패널 솔기 6줄 + 단추 + 통풍 구멍
    { const P = []; for (let k = 0; k < 6; k++) { const az = k / 6 * TAU + TAU / 12; const pts = []; for (let e = .2; e <= Math.PI / 2 - .02; e += .1) pts.push(onDome(az, e, .0012).p); pts.push(V3(0, RY + CY + .001, 0)); P.push(L.tube(pts, .0012, 14, 4, false)); }
      add('cap', L.merge(P), capDark, 'Bully_CapSeams');
      const bt = blob(.011, .006, .011); bt.translate(0, RY + CY + .003, 0); add('cap', bt, capM, 'Bully_CapButton');
      const E = []; for (const az of [TAU / 12 + TAU / 6, -TAU / 12 - TAU / 6, Math.PI - TAU / 12, Math.PI + TAU / 12]) { const o = onDome(az, .95, .0008), r = new T.TorusGeometry(.0042, .0013, 6, 12); r.lookAt(o.n); r.translate(o.p.x, o.p.y, o.p.z); E.push(r); } add('cap', L.merge(E), capDark, 'Bully_CapEyelets'); }
    // 스냅백 구멍(앞): 금발이 보이는 아치 + 테두리 + 똑딱이 끈
    { const arch = a => .2 + .32 * Math.cos(Math.min(1, Math.abs(a) / .5) * Math.PI / 2), NA = 20, NE = 8, pos = [], idx = [];
      for (let ia = 0; ia <= NA; ia++) for (let ie = 0; ie <= NE; ie++) { const a = -.5 + ia / NA, e = .18 + (arch(a) - .18) * ie / NE, o = onDome(a, e, .0008); pos.push(o.p.x, o.p.y, o.p.z); }
      for (let ia = 0; ia < NA; ia++) for (let ie = 0; ie < NE; ie++) { const q = ia * (NE + 1) + ie; idx.push(q, q + NE + 1, q + 1, q + 1, q + NE + 1, q + NE + 2); }
      const g = new T.BufferGeometry(); g.setAttribute('position', new T.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals(); add('cap', g, hairBase, 'Bully_CapOpeningHair');
      const pts = []; for (let a = -.5; a <= .5001; a += .05) pts.push(onDome(a, arch(a), .002).p); add('cap', L.tube(pts, .0032, 24, 6, false), capDark, 'Bully_CapOpeningEdge');
      const st = []; for (let a = -.55; a <= .5501; a += .05) st.push(onDome(a, .215, .003).p); add('cap', L.tube(st, .0045, 22, 6, false), capDark, 'Bully_CapSnapStrap');
      const S = []; for (let k = -2; k <= 2; k++) { const o = onDome(k * .1, .215, .008), c = new T.CylinderGeometry(.0034, .0034, .003, 10); c.rotateX(Math.PI / 2); c.lookAt(o.n); c.translate(o.p.x, o.p.y, o.p.z); S.push(c); } add('cap', L.merge(S), snapM, 'Bully_CapSnaps'); }
    // 아래 테 (땀받이 테두리)
    { const pts = []; for (let a = 0; a <= TAU + .001; a += TAU / 48) pts.push(onDome(a, .185, .0015).p); add('cap', L.tube(pts, .0034, 48, 6, false), capDark, 'Bully_CapRim'); }
    // 챙 (뒤로) — 휘어진 D자
    { const sh = new T.Shape(); sh.moveTo(-.082, 0); sh.bezierCurveTo(-.08, -.07, -.03, -.1, 0, -.1); sh.bezierCurveTo(.03, -.1, .08, -.07, .082, 0); sh.lineTo(-.082, 0);
      const g = new T.ExtrudeGeometry(sh, { depth: .006, bevelEnabled: true, bevelThickness: .002, bevelSize: .002, bevelSegments: 2, curveSegments: 18 }); g.rotateX(Math.PI / 2);
      const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i); p.setY(i, p.getY(i) - 1.6 * x * x - .1 * z * z); } g.computeVertexNormals();
      g.rotateX(-.12); g.translate(0, CY + .02, -RZ * .9); add('cap', g, capDark, 'Bully_CapBrim'); }
    // 로고 (앞판 = 뒤통수 쪽)
    { const o = onDome(Math.PI, .55, .0018), lg = new T.CircleGeometry(.024, 24); lg.lookAt(o.n); lg.translate(o.p.x, o.p.y, o.p.z); add('cap', lg, capLogo, 'Bully_CapLogo'); }
  }

  // =====================================================================
  // 몸: 티셔츠(스킨: 골반 · 척추) · 목 · 소매 · 기타 끈
  // =====================================================================
  const skinTo = (geo, mat, bones, wf, name) => { const sk = L.skinned(geo, mat, bones.map(b => M[b]), wf); sk.mesh.name = name; sk.mesh.castShadow = true; sk.mesh.receiveShadow = true; scene.add(sk.mesh); return sk; };
  const binds = [];
  const rAt = y => { const k = [[-.13, .15], [-.1, .147], [-.06, .142], [0, .143], [.1, .145], [.2, .151], [.29, .156], [.35, .14], [.385, .1], [.4, .05]]; if (y <= k[0][0]) return k[0][1]; for (let i = 1; i < k.length; i++) if (y <= k[i][0]) { const t = (y - k[i - 1][0]) / (k[i][0] - k[i - 1][0]); return k[i - 1][1] + (k[i][1] - k[i - 1][1]) * t; } return .05; };
  { const prof = []; const Y0 = -.13, Y1 = .4, N = 28;
    for (let i = 0; i <= N; i++) { const y = Y0 + (Y1 - Y0) * i / N; prof.push([rAt(y), y]); }
    const g = L.lathe(prof, 56, -Math.PI, TAU); g.scale(1, 1, .72);
    { const p = g.attributes.position, v = V3(), Rw = L.rng(5); for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i); const a = Math.atan2(v.x, v.z), w = (Math.sin(a * 7 + v.y * 30) * .5 + Math.sin(a * 13 - v.y * 55) * .3) * .0025 * (1 - sstep(.3, .38, v.y)) + (v.y < -.1 ? Math.sin(a * 9) * .002 : 0); const r = Math.hypot(v.x, v.z / .72) || 1; p.setXYZ(i, v.x * (1 + w / r), v.y, v.z * (1 + w / r)); } g.computeVertexNormals(); }
    const ys = []; { const p = g.attributes.position; for (let i = 0; i < p.count; i++) ys.push(p.getY(i)); }
    toRoot('spine', g);
    binds.push(skinTo(g, teeM, ['pelvis', 'spine'], (p, i) => { const w = sstep(-.05, .06, ys[i]); return [[0, 1 - w], [1, w]]; }, 'Bully_Tee'));
    // 밑단 접힘
    const hem = new T.TorusGeometry(.149, .0045, 6, 56); hem.rotateX(Math.PI / 2); hem.scale(1, 1, .72); hem.translate(0, -.128, 0); const hy = []; { const p = hem.attributes.position; for (let i = 0; i < p.count; i++) hy.push(p.getY(i)); }
    toRoot('spine', hem); binds.push(skinTo(hem, teeDark, ['pelvis', 'spine'], () => [[0, 1]], 'Bully_TeeHem'));
  }
  { const col = new T.TorusGeometry(.052, .009, 8, 28); col.rotateX(Math.PI / 2); col.scale(1, 1, .9); col.translate(0, .392, -.004); add('spine', col, teeDark, 'Bully_TeeCollar');
    const nk = new T.CylinderGeometry(.044, .05, .1, 20, 1, true); nk.translate(0, .42, -.006); add('spine', nk, skin, 'Bully_Neck');
    // 기타 끈: 가슴 앞을 가로지르는 띠 (몸통 표면을 따라 앞 · 뒤)
    const band = (front) => { const pts = []; for (let k = 0; k <= 30; k++) { const t = k / 30, x = -.135 + .27 * t, y = .34 - .38 * t; const r = rAt(y) + .004; const z = Math.sqrt(Math.max(0, r * r - x * x)) * .72 + .006; pts.push(V3(x, y, front ? z : -z)); } return L.tube(pts, .007, 30, 6, false); };
    const bf = band(true), bb = band(false); add('spine', L.merge([bf, bb]), strapM, 'Bully_GuitarStrap'); }
  // 소매 (어깨 노드: 팔 = −Y)
  for (const [i, s] of [[0, -1], [1, 1]]) {
    const capS = L.blob(.06, .062, .058, d => 1 - .1 * Math.max(0, s * d.x) ** 2, 24, 16); capS.translate(0, -.018, 0);
    const tube = new T.CylinderGeometry(.056, .059, .12, 24, 3, true); tube.translate(0, -.075, 0);
    { const p = tube.attributes.position; for (let k = 0; k < p.count; k++) { const a = Math.atan2(p.getX(k), p.getZ(k)), y = p.getY(k); const w = 1 + .025 * Math.sin(a * 5 + y * 40); p.setX(k, p.getX(k) * w); p.setZ(k, p.getZ(k) * w); } tube.computeVertexNormals(); }
    add('sho' + i, L.merge([capS, tube]), teeDark, 'Bully_Sleeve' + i);
    const hemS = new T.TorusGeometry(.058, .0045, 6, 24); hemS.rotateX(Math.PI / 2); hemS.translate(0, -.134, 0); add('sho' + i, hemS, teeDark, 'Bully_SleeveHem' + i);
  }

  // =====================================================================
  // 팔 (스킨: 어깨 · 팔꿈치) · 손목 밴드 · 손
  // =====================================================================
  const limbTube = (ptsW, radF, seg, rad) => { const c = new T.CatmullRomCurve3(ptsW); const g = new T.TubeGeometry(c, seg, 1, rad, false), p = g.attributes.position, nrm = g.attributes.normal, ring = rad + 1, tv = [];
    for (let i = 0; i <= seg; i++) { const t = i / seg, P = c.getPointAt(t), r = radF(t); for (let j = 0; j < ring; j++) { const k = i * ring + j, n = V3().fromBufferAttribute(nrm, k); p.setXYZ(k, P.x + n.x * r, P.y + n.y * r, P.z + n.z * r); tv.push(t); } }
    const tOf = q => { let best = 0, bd = 1e9; for (let i = 0; i <= 200; i++) { const d = c.getPointAt(i / 200).distanceTo(q); if (d < bd) { bd = d; best = i / 200; } } return best; };
    return { g, tv, tOf }; };
  const wp = (node, x = 0, y = 0, z = 0) => V3(x, y, z).applyMatrix4(R[node].matrixWorld);
  for (const i of [0, 1]) {
    const S0 = wp('sho' + i, 0, -.04), E = wp('elb' + i), W = wp('hand' + i, 0, .012), SA = wp('sho' + i, 0, -.15), EA = wp('elb' + i, 0, -.11);
    const A = limbTube([S0, SA, E, EA, W], t => t < .45 ? .037 - .004 * t / .45 : t < .55 ? .033 : .034 - .009 * (t - .55) / .45, 40, 16);
    const te = A.tOf(E);
    binds.push(skinTo(A.g, skin, ['sho' + i, 'elb' + i], (p, k) => { const w = sstep(te - .06, te + .05, A.tv[k]); return [[0, 1 - w], [1, w]]; }, 'Bully_Arm' + i));
    // 빨간 손목 밴드 (팔꿈치 노드)
    const bd = new T.CylinderGeometry(.036, .036, .042, 24, 4, true); { const p = bd.attributes.position; for (let k = 0; k < p.count; k++) { const a = Math.atan2(p.getX(k), p.getZ(k)), w = 1 + .03 * Math.abs(Math.sin(a * 14)); p.setX(k, p.getX(k) * w); p.setZ(k, p.getZ(k) * w); } bd.computeVertexNormals(); } bd.translate(0, -.198, 0);
    const r1 = new T.TorusGeometry(.036, .004, 6, 24); r1.rotateX(Math.PI / 2); r1.translate(0, -.177, 0); const r2 = r1.clone(); r2.translate(0, -.042, 0);
    add('elb' + i, L.merge([bd, r1, r2]), bandM, 'Bully_Wristband' + i);
  }
  // 손: 손바닥은 몸 쪽(안쪽), 엄지는 앞(+Z) — 손가락은 살짝 오므린다
  for (const [i, s] of [[0, -1], [1, 1]]) {
    const P = []; const palm = L.blob(.018, .044, .037, d => 1 - .12 * Math.max(0, d.y), 20, 14); palm.translate(0, -.04, 0); P.push(palm);
    const inward = -s;
    [[.026, .028], [.009, .031], [-.008, .029], [-.024, .024]].forEach(([z, l]) => {
      let a = V3(0, -.076, z * .95); const dirs = [V3(inward * .18, -1, 0), V3(inward * .65, -1, 0), V3(inward * 1.2, -.7, 0)], ls = [l * .48, l * .32, l * .26];
      dirs.forEach((d, k) => { const b = a.clone().addScaledVector(d.normalize(), ls[k]); P.push(L.capsule(a.toArray(), b.toArray(), .0098 - k * .0012, 9, 3)); a = b; });
    });
    { let a = V3(inward * .008, -.022, .03); for (const [d, l] of [[V3(inward * .25, -.55, .8), .026], [V3(inward * .55, -.8, .45), .022]]) { const b = a.clone().addScaledVector(d.normalize(), l); P.push(cap(a.toArray(), b.toArray(), .0112, 10)); a = b; } }
    add('hand' + i, L.merge(P), skin, 'Bully_Hand' + i);
  }

  // =====================================================================
  // 골반(청바지 엉덩이 · 주머니) · 다리(스킨: 골반 · 엉덩이 · 무릎) · 접은 밑단
  // =====================================================================
  { const hips = L.blob(.152, .104, .106, d => (1 - .12 * Math.max(0, -d.y) ** 2) * (1 + .05 * Math.max(0, -d.z) * Math.max(0, -d.y + .2)), 36, 22); hips.translate(0, -.004, 0); add('pelvis', hips, jeansM, 'Bully_JeansSeat');
    const D_ = []; for (const s of [-1, 1]) { const pk = L.sbox(.062, .07, .008, 5, 14, 10); pk.rotateZ(s * .08); pk.translate(s * .06, -.035, -.099); D_.push(pk); }
    add('pelvis', L.merge(D_), jeansM, 'Bully_BackPockets');
    const st = []; for (const s of [-1, 1]) { const pts = []; for (let k = 0; k <= 8; k++) { const t = k / 8; pts.push(V3(s * (.06 + (t - .5) * .05), -.035 - .03 * Math.sin(t * Math.PI) + .005, -.1045)); } st.push(L.tube(pts, .0011, 10, 4, false)); }
    { const pts = []; for (let k = 0; k <= 8; k++) { const t = k / 8; pts.push(V3(.012 + .006 * Math.sin(t * Math.PI), -.02 - .06 * t, .1 - .006 * t)); } st.push(L.tube(pts, .0011, 10, 4, false)); }
    for (const s of [-1, 1]) { const pts = []; for (let k = 0; k <= 8; k++) { const t = k / 8; pts.push(V3(s * (.075 + .045 * t), -.02 - .03 * Math.sin(t * Math.PI / 2), .095 - .03 * t)); } st.push(L.tube(pts, .0011, 10, 4, false)); }
    add('pelvis', L.merge(st), stitchM, 'Bully_JeansStitch');
    const rv = []; for (const s of [-1, 1]) { const r = new T.CylinderGeometry(.0035, .0035, .003, 8); r.rotateX(Math.PI / 2); r.translate(s * .085, -.022, .095); rv.push(r); } add('pelvis', L.merge(rv), rivet, 'Bully_Rivets'); }
  for (const i of [0, 1]) {
    const H0 = wp('hip' + i, 0, .045), H = wp('hip' + i), K = wp('knee' + i), A = wp('foot' + i, 0, .045), HM = wp('hip' + i, 0, -.16), KM = wp('knee' + i, 0, -.16);
    const Lg = limbTube([H0, H, HM, K, KM, A], t => t < .1 ? .078 + .006 * t / .1 : t < .5 ? .084 - .016 * (t - .1) / .4 : t < .58 ? .068 : .067 + .006 * (t - .58) / .42, 56, 18);
    // 무릎 · 엉덩이 주름
    { const p = Lg.g.attributes.position, nrm = Lg.g.attributes.normal; const tk = Lg.tOf(K); for (let k = 0; k < p.count; k++) { const t = Lg.tv[k], w = Math.exp(-(((t - tk) / .04) ** 2)) * .004 * Math.sin(k * 1.7) + Math.exp(-(((t - .82) / .03) ** 2)) * .003 * Math.sin(k * 2.3); p.setXYZ(k, p.getX(k) + nrm.getX(k) * w, p.getY(k) + nrm.getY(k) * w, p.getZ(k) + nrm.getZ(k) * w); } }
    const th = Lg.tOf(H), tk = Lg.tOf(K);
    binds.push(skinTo(Lg.g, jeansM, ['pelvis', 'hip' + i, 'knee' + i], (p, k) => { const t = Lg.tv[k], wh = sstep(th - .05, th + .08, t), wk = sstep(tk - .05, tk + .05, t); return [[0, 1 - wh], [1, wh * (1 - wk)], [2, wk]]; }, 'Bully_JeansLeg' + i));
    const cuff = new T.TorusGeometry(.071, .014, 8, 28); cuff.rotateX(Math.PI / 2); cuff.scale(1, 1.4, 1); cuff.translate(0, -.302, .004); add('knee' + i, cuff, jeansM, 'Bully_JeansCuff' + i);
    const sst = new T.TorusGeometry(.0715, .0012, 4, 28); sst.rotateX(Math.PI / 2); sst.translate(0, -.288, .004); add('knee' + i, sst, stitchM, 'Bully_CuffStitch' + i);
  }

  // =====================================================================
  // 빨간 하이탑 (발 노드: 발목 = 원점, 바닥 = −0.07, 앞 = +Z)
  // =====================================================================
  for (const i of [0, 1]) {
    const RUB = [], RED = [], LACE = [], MET = [], TRD = [];
    const sole = L.sbox(.104, .03, .262, 5, 28, 12); sole.translate(0, -.055, .05); RUB.push(sole);
    const fox = L.sbox(.108, .016, .266, 7, 28, 8); fox.translate(0, -.044, .05); RUB.push(fox);
    const toe = L.blob(.05, .03, .045, d => d.z > -.2 ? 1 : .8, 20, 12); toe.translate(0, -.042, .145); RUB.push(toe);
    const heel = L.sbox(.05, .03, .012, 4, 10, 8); heel.translate(0, -.028, -.083); RUB.push(heel);
    for (let k = 0; k < 9; k++) { const b = new T.BoxGeometry(.088, .004, .012); b.translate(0, -.0705, -.06 + k * .027); TRD.push(b); }
    const upper = L.blob(.049, .05, .118, d => (1 - .42 * Math.max(0, d.z) * Math.max(0, d.y + .1)) * (d.y < -.3 ? .98 : 1), 28, 18); upper.translate(0, -.022, .045); RED.push(upper);
    const shaft = L.lathe([[.052, -.04], [.055, -.01], [.054, .03], [.052, .065], [.05, .078]], 28); shaft.scale(1, 1, 1.12); shaft.translate(0, 0, -.004); RED.push(shaft);
    const tongue = L.sbox(.05, .1, .014, 4, 12, 10); tongue.rotateX(-.42); tongue.translate(0, .022, .058); RED.push(tongue);
    const pad = new T.TorusGeometry(.05, .009, 8, 28); pad.rotateX(Math.PI / 2); pad.scale(1, 1, 1.12); pad.translate(0, .078, -.004); RED.push(pad);
    for (const s of [-1, 1]) { const pc = new T.CircleGeometry(.02, 20); pc.rotateY(s * Math.PI / 2); pc.translate(s * .0565, .03, -.004); RUB.push(pc); const ring = new T.TorusGeometry(.016, .0018, 6, 20); ring.rotateY(s * Math.PI / 2); ring.translate(s * .058, .03, -.004); RED.push(ring); }
    for (let k = 0; k < 6; k++) { const y = -.02 + k * .017, z = .102 - k * .011;
      for (const s of [-1, 1]) { const e = new T.TorusGeometry(.0042, .0013, 6, 12); e.rotateY(s * .5); e.translate(s * .026, y, z); MET.push(e); }
      if (k < 5) { for (const s of [-1, 1]) LACE.push(cap([s * .026, y, z + .004], [-s * .026, y + .017, z - .007], .0026, 6)); } }
    { const bow = cap([0, .07, .052], [.028, .062, .062], .003, 6), bow2 = cap([0, .07, .052], [-.026, .058, .06], .003, 6), lp = new T.TorusGeometry(.009, .0026, 6, 12); lp.rotateY(.3); lp.translate(.012, .074, .056); LACE.push(bow, bow2, lp); }
    const stripe = new T.TorusGeometry(1, .0022, 4, 40); stripe.rotateX(Math.PI / 2); stripe.scale(.054, 1, .132); stripe.translate(0, -.038, .05); RED.push(stripe);
    add('foot' + i, L.merge(RUB), rubber, 'Bully_ShoeRubber' + i); add('foot' + i, L.merge(RED), redCanvas, 'Bully_ShoeCanvas' + i);
    add('foot' + i, L.merge(LACE), laceM, 'Bully_ShoeLace' + i); add('foot' + i, L.merge(MET), chrome, 'Bully_ShoeEyelet' + i); add('foot' + i, L.merge(TRD), treadM, 'Bully_ShoeTread' + i);
  }

  // =====================================================================
  // 빨간 전기기타 (플라잉V) — 기타 노드 로컬: 넥 = +X, 앞면 = +Z (노드 배율 .88)
  // =====================================================================
  { const vs = new T.Shape(); vs.moveTo(.07, .036); vs.lineTo(-.37, .205); vs.quadraticCurveTo(-.405, .215, -.43, .17); vs.lineTo(-.2, .012); vs.quadraticCurveTo(-.19, 0, -.2, -.012); vs.lineTo(-.43, -.15); vs.quadraticCurveTo(-.405, -.2, -.37, -.19); vs.lineTo(.07, -.036); vs.quadraticCurveTo(.085, 0, .07, .036);
    const body = new T.ExtrudeGeometry(vs, { depth: .032, bevelEnabled: true, bevelThickness: .006, bevelSize: .006, bevelSegments: 3, curveSegments: 10 }); body.translate(0, 0, -.019); add('guitar', body, lacq, 'Bully_GuitarBody');
    const pg = new T.Shape(); pg.moveTo(.05, .03); pg.lineTo(-.2, .13); pg.lineTo(-.24, .06); pg.lineTo(-.13, 0); pg.lineTo(-.24, -.06); pg.lineTo(-.2, -.12); pg.lineTo(.05, -.03); pg.lineTo(.05, .03);
    const pgg = new T.ExtrudeGeometry(pg, { depth: .002, bevelEnabled: false }); pgg.translate(0, 0, .0195); add('guitar', pgg, guard, 'Bully_Pickguard');
    const PU = [], NI = [], KN = [];
    for (const x of [-.03, -.1]) { const pu = L.sbox(.036, .074, .012, 6, 14, 10); pu.translate(x, 0, .026); PU.push(pu); for (let k = 0; k < 6; k++) for (const dx of [-.008, .008]) { const pl = new T.CylinderGeometry(.0022, .0022, .003, 8); pl.rotateX(Math.PI / 2); pl.translate(x + dx, (k - 2.5) * .0105, .0325); NI.push(pl); } const ring = L.sbox(.044, .084, .006, 8, 14, 8); ring.translate(x, 0, .022); KN.push(ring); }
    const br = L.sbox(.012, .082, .012, 6, 10, 8); br.translate(-.16, 0, .027); NI.push(br); const tp = L.sbox(.014, .07, .01, 6, 10, 8); tp.translate(-.2, 0, .025); NI.push(tp);
    for (let k = 0; k < 3; k++) { const kb = new T.CylinderGeometry(.011, .012, .014, 16); kb.rotateX(Math.PI / 2); kb.translate(-.28 - k * .04, -.1 + k * .012, .029); KN.push(kb); }
    const jack = new T.CylinderGeometry(.008, .008, .004, 12); jack.rotateX(Math.PI / 2); jack.translate(-.3, .09, .021); NI.push(jack);
    const sw = L.sbox(.01, .01, .02, 4, 8, 6); sw.translate(-.31, .135, .028); KN.push(sw);
    add('guitar', L.merge(PU), pickupM, 'Bully_GuitarPickups'); add('guitar', L.merge(NI), nickel, 'Bully_GuitarHardware'); add('guitar', L.merge(KN), knobM, 'Bully_GuitarKnobs');
    // 넥 · 지판 · 프렛 · 인레이 · 헤드 · 줄감개 · 줄
    const neck = L.sbox(.58, .046, .026, 5, 24, 10); neck.translate(.35, 0, -.002); add('guitar', neck, lacq, 'Bully_GuitarNeck');
    const fb = new T.BoxGeometry(.56, .046, .006); fb.translate(.35, 0, .013); add('guitar', fb, rosewood, 'Bully_Fretboard');
    const FR = [], IN = []; for (let k = 1; k <= 22; k++) { const x = .63 - .56 * (1 - Math.pow(2, -k / 12)) * 1.38; if (x < .075) break; const f = new T.BoxGeometry(.0018, .046, .002); f.translate(x, 0, .017); FR.push(f); if ([3, 5, 7, 9, 12, 15, 17].includes(k)) { const xm = x + .012; for (const dy of k === 12 ? [-.012, .012] : [0]) { const d = new T.CylinderGeometry(.0032, .0032, .001, 10); d.rotateX(Math.PI / 2); d.translate(xm, dy, .0165); IN.push(d); } } }
    add('guitar', L.merge(FR), nickel, 'Bully_Frets'); add('guitar', L.merge(IN), pearl, 'Bully_Inlays');
    const nut = new T.BoxGeometry(.004, .047, .008); nut.translate(.632, 0, .014); add('guitar', nut, guard, 'Bully_Nut');
    const hs = new T.Shape(); hs.moveTo(0, .026); hs.lineTo(.14, .064); hs.lineTo(.125, 0); hs.lineTo(.14, -.064); hs.lineTo(0, -.026); hs.lineTo(0, .026);
    const hg = new T.ExtrudeGeometry(hs, { depth: .014, bevelEnabled: true, bevelThickness: .002, bevelSize: .002, bevelSegments: 2 }); hg.translate(.63, 0, -.006); add('guitar', hg, lacq, 'Bully_Headstock');
    const TU = []; for (let k = 0; k < 6; k++) { const up = k < 3 ? 1 : -1, kk = k % 3, x = .66 + kk * .03, y = up * (.033 + kk * .009); const post = new T.CylinderGeometry(.004, .004, .016, 8); post.rotateX(Math.PI / 2); post.translate(x, y, .014); TU.push(post); const key = L.sbox(.012, .02, .006, 4, 8, 6); key.translate(x, y + up * .03, -.002); TU.push(key); const sh = new T.CylinderGeometry(.002, .002, .03, 6); sh.translate(x, y + up * .016, -.002); TU.push(sh); }
    add('guitar', L.merge(TU), chrome, 'Bully_Tuners');
    const SR = []; for (let k = 0; k < 6; k++) { const y = (k - 2.5) * .0068, a = V3(-.205, y * 1.05, .031), b = V3(.632, y * .78, .019); SR.push(L.capsule(a.toArray(), b.toArray(), .00055 + k * .00008, 4, 1)); } add('guitar', L.merge(SR), nickel, 'Bully_Strings');
    const sb = []; for (const p of [[.07, .036, 0], [-.42, -.16, 0]]) { const c = new T.CylinderGeometry(.005, .006, .01, 10); c.rotateZ(Math.PI / 2); c.translate(p[0], p[1], p[2]); sb.push(c); } add('guitar', L.merge(sb), chrome, 'Bully_StrapButtons');
    const stk = new T.PlaneGeometry(.12, .045); stk.rotateZ(.35); stk.translate(-.31, .12, .0208); add('guitar', stk, stickerM, 'Bully_GuitarSticker'); }

  // ---------- 묶음 자세 스킨 연결 ----------
  scene.updateMatrixWorld(true); binds.forEach(b => b.bind());
  // 키 표식: 캡 꼭대기 (모델 높이 검사 — 등에 멘 기타 헤드는 키에 넣지 않는다)
  { scene.updateMatrixWorld(true); const bb = new T.Box3(); ['head', 'cap'].forEach(n => M[n].traverse(o => { if (o.isMesh) { o.geometry.computeBoundingBox(); bb.union(o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld)); } }));
    const mk = new T.Object3D(); mk.name = 'BULLY_Marker_Height'; mk.userData = { marker: 'height' }; mk.position.set(0, bb.max.y, 0); mir.root.add(mk); }

  // ---------- 클립: 게임 리그를 실제 상태로 움직이며 녹화 ----------
  const snap = L.snap(mir), clips = [];
  const P0 = { seat: 0, walk: 0, run: 0, strum: 0, ear: 0, reach: 0, kneel: 0, stumble: 0, kick: 0, slung: 1, alert: 0, point: 0, climb: 0, eyes: 1, tongue: 0 };
  const set = (o, p = {}) => { Object.assign(B, { moving: 0, act: null, peek: false, phaseT: 0 }, o); Object.assign(B.p, P0, p); B.look.set(0, 1.38, 4); };
  const rec = (name, frames, pre = 90, each) => { anim(pre); clips.push(L.record(name, mir, frames, (f) => { if (each) each(f); anim(2, 1 / 60); })); };
  set({ state: 'leave', stT: 9 }); rec('Idle', 60, 90, f => B.look.set(Math.sin(f / 60 * TAU) * 1.2, 1.3, 4));
  set({ state: 'return', moving: .8 }, { walk: 1 }); rec('Walk', Math.round(1.25 / .8 * 30) + 1);
  set({ state: 'chase', moving: 2.2 }, { walk: 1, run: 1 }); rec('Run', Math.round(1.6 / 2.2 * 30) + 1);
  set({ state: 'seated', phase: 'play' }, { seat: 1, strum: 1, slung: 0, eyes: 0 }); B.look.set(-1.5, .1, .45); rec('GuitarPlay', Math.round(4 * 6.2 / 16 * 30) + 1, 150);
  set({ state: 'seated', phase: 'listen', phaseT: .5 }, { seat: 1, slung: 0 }); rec('Listen', 75, 60);
  set({ state: 'search', stT: 2 }, { alert: .6, slung: .6 }); rec('Search', 90, 90, f => B.look.set(Math.sin(f / 90 * TAU) * 2.5, .1, 2));
  set({ state: 'grab', stT: 1 }, { reach: 1, alert: 1 }); B.reachT.set(0, .25, .55); rec('Grab', 30, 60);
  set({ state: 'chase', moving: 0, peek: true }, { kneel: 1, reach: 1 }); B.reachT.set(0, .06, .6); rec('Kneel', 30, 90, () => { B.peek = true; });
  set({ state: 'rise', stT: .6 }, { alert: 1, point: 1 }); rec('Point', 30, 60, () => { B.stT = .6; });
  set({ state: 'chase', moving: 0 }); rec('Stumble', 29, 30, f => { B.p.stumble = Math.sin(f / 28 * Math.PI); });
  set({ state: 'chase', moving: 0 }); rec('Kick', 16, 30, f => { B.p.kick = Math.sin(f / 15 * Math.PI); });
  set({ state: 'leave', stT: 9 }); anim(150); L.restore(snap);
  B.root.visible = false; B.state = 'off';
  const big = []; scene.traverse(o => { if (o.isMesh) big.push([o.name, o.geometry.attributes.position.count]); }); big.sort((x, y) => y[1] - x[1]);
  const info = Object.assign({ top: big.slice(0, 14).map(x => x.join(':')), character: 'bully', heightMarker: +mir.root.children.find(o => o.userData.marker === 'height').position.y.toFixed(3) }, L.stats(scene), { clips: clips.map(c => c.name + ':' + c.tracks.length + ':' + c.duration.toFixed(2)), nodes: mir.list.length });
  const b64 = await L.export(scene, clips);
  return { b64, info };
};
