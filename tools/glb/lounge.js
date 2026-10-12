/* Lounge 최종 환경 모델 → assets/environment/lounge/env_lounge.glb
   "동선은 안 바꾸고 보이는 모양만" — 게임의 충돌 상자(W.colliders)를 그대로 읽어 가구의 윗면 · 옆면을 거기에 맞춘다.
   (충돌 · 트리거 · 매달리기 손잡이 · 숨기 구역 · 밀 수 있는 책 더미 · 문 · 펫도어 · 시계추 · 조각은 게임 코드가 그대로 갖는다)
   월드 좌표 그대로(모델 원점 = 월드 원점). 범위 x 0 … 14 (양쪽 칸막이 벽은 게임 코드).
   들어 있는 것: 어두운 월넛 바닥(널 · 이음매 · 긁힌 자국 · 먼지) · 페르시안 러그(술) · 벽지 · 웨인스코팅 · 몰딩 · 창(틀 · 창턱) · 커튼 · 라디에이터 ·
   붙박이 책장 + 책 · 벨벳 안락의자 · 스탠드 램프 · 벽등 · 액자 · 벽난로 · 괘종시계 · 버건디 벨벳 체스터필드 소파 · 책 더미 계단 ·
   커피 테이블(머그 · 책 · LP) · 사이드 테이블(테이블 램프 · 책) · LP 캐비닛(LP 줄) · 턴테이블 · 데스크 램프 · 큰 스피커 2 · LP 상자 · LP 더미 ·
   전화 탁자(다이얼 전화 · 램프) · 화분 식물 · 오래된 케이블 · 먼지 뭉치 */
window.GLBA_JOB = async () => {
  const L = GLBA, T = L.T, D = ODD2.dev, V3 = L.V3, TAU = Math.PI * 2, W = ODD2.W;
  const scene = new T.Scene(); scene.name = 'env_lounge';
  const root = new T.Group(); root.name = 'ENV_Lounge'; root.userData = { oddEnv: 'lounge', unit: 'm', range: [0, 14], note: 'ODD HAUS Lounge — 월드 좌표. 충돌 · 트리거는 게임 코드 (W.colliders)' }; scene.add(root);
  const R0 = L.rng(2024);
  // ---------- 충돌 상자 찾기 ----------
  const COL = (tag, x) => { let best = null, bd = 1e9; for (const c of W.colliders) if (c.tag === tag) { const d = Math.abs((c.min.x + c.max.x) / 2 - x); if (d < bd) { bd = d; best = c; } } if (!best) throw new Error('collider ' + tag + ' ' + x); return best; };
  // ---------- 노이즈 ----------
  const hash = (x, y, s = 0) => { let h = (x * 374761393 + y * 668265263 + s * 2147483647) | 0; h = (h ^ (h >>> 13)) * 1274126177 | 0; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
  const vn = (x, y, s = 0) => { const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf); const a = hash(xi, yi, s), b = hash(xi + 1, yi, s), c = hash(xi, yi + 1, s), d = hash(xi + 1, yi + 1, s); return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v; };
  const fbm = (x, y, s = 0, o = 4) => { let f = 0, a = .5, k = 1; for (let i = 0; i < o; i++) { f += a * vn(x * k, y * k, s + i * 17); a *= .5; k *= 2; } return f; };
  const pix = (w, h, fn) => L.canvas(w, h, g => { const id = g.createImageData(w, h), d = id.data; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const c = fn(x, y), k = (y * w + x) * 4; d[k] = c[0]; d[k + 1] = c[1]; d[k + 2] = c[2]; d[k + 3] = c[3] ?? 255; } g.putImageData(id, 0, 0); });
  const cl = v => Math.max(0, Math.min(255, v | 0));

  // =====================================================================
  // 텍스처 · 재질
  // =====================================================================
  // 어두운 월넛 바닥: 2.8 m × 1.4 m 한 장 = 널 10줄(14 cm) — 결 · 옹이 · 이음매 · 긁힌 자국 · 먼지
  const FW = 2048, FH = 1024, PL = FH / 10, joints = Array.from({ length: 10 }, (_, r) => [hash(r, 1) * FW, hash(r, 2) * FW * .5 + FW * .5].map(v => v | 0));
  const floorH = new Float32Array(FW * FH);
  const floorC = pix(FW, FH, (x, y) => {
    const row = Math.floor(y / PL), yy = y - row * PL, tone = hash(row, 9) * .35 + hash(Math.floor((x + joints[row][0]) / (FW * .55)), row, 3) * .25;
    const g = fbm(x * .004, y * .06 + row * 13, row) * 1.4 + Math.sin(x * .011 + fbm(x * .002, y * .02, row + 50) * 9) * .25;
    let r = 44 + tone * 38 + g * 26, gg = 28 + tone * 24 + g * 16, b = 17 + tone * 12 + g * 9;
    const seam = yy < 2 || yy > PL - 2, jt = joints[row].some(j => Math.abs(x - j) < 2);
    let h = .5 + g * .08;
    if (seam || jt) { r *= .35; gg *= .35; b *= .35; h = .1; }
    const knot = (() => { const kx = hash(row, 11) * FW, ky = row * PL + PL * (.3 + hash(row, 12) * .4), d = Math.hypot((x - kx) * .5, y - ky); return d < 9 ? 1 - d / 9 : 0; })();
    if (knot) { r *= 1 - knot * .5; gg *= 1 - knot * .55; b *= 1 - knot * .55; h -= knot * .05; }
    floorH[y * FW + x] = h;
    return [cl(r), cl(gg), cl(b)];
  });
  { const g = floorC.getContext('2d'), Rs = L.rng(31);
    for (let i = 0; i < 520; i++) { const x = Rs() * FW, y = Rs() * FH, l = 10 + Rs() * 90, a = (Rs() - .5) * .5; g.strokeStyle = `rgba(${170 + Rs() * 50},${140 + Rs() * 40},${100 + Rs() * 30},${.06 + Rs() * .12})`; g.lineWidth = .6 + Rs() * 1.1; g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); g.stroke(); }      // 긁힌 자국
    for (let i = 0; i < 70; i++) { const x = Rs() * FW, y = Rs() * FH, r = 8 + Rs() * 30; const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, `rgba(10,6,4,${.12 + Rs() * .12})`); gr.addColorStop(1, 'rgba(10,6,4,0)'); g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2); }     // 얼룩
  }
  const floorN = L.tex(L.normalCanvas(FW / 2, FH / 2, (u, v, x, y) => floorH[(y * 2) * FW + x * 2], 2.2), { color: false, jpeg: true });
  const floorTex = L.tex(floorC, { jpeg: true });
  const floorM = L.phys({ name: 'Lounge_FloorWalnut', map: floorTex, normalMap: floorN, normalScale: new T.Vector2(.8, .8), roughness: .52, clearcoat: .35, clearcoatRoughness: .38 });
  // 먼지 · 발자국 · 긁힘 오버레이 (바닥 전체에 한 장, 반투명): 벽 · 가구 밑에 먼지가 쌓이고 길에는 닳은 자국
  const dustTex = L.tex(L.canvas(1024, 512, g => {
    const sx = 1024 / 14, sz = 512 / 4, X = x => x * sx, Z = z => (z + 1.6) * sz;
    const blot = (x, z, rx, rz, a, c = '200,190,170') => { const gr = g.createRadialGradient(X(x), Z(z), 0, X(x), Z(z), rx * sx); gr.addColorStop(0, `rgba(${c},${a})`); gr.addColorStop(1, `rgba(${c},0)`); g.save(); g.translate(X(x), Z(z)); g.scale(1, rz / rx); g.translate(-X(x), -Z(z)); g.fillStyle = gr; g.fillRect(X(x) - rx * sx, Z(z) - rx * sx, rx * sx * 2, rx * sx * 2); g.restore(); };
    const gb = g.createLinearGradient(0, 0, 0, Z(-1.2)); gb.addColorStop(0, 'rgba(190,180,160,.28)'); gb.addColorStop(1, 'rgba(190,180,160,0)'); g.fillStyle = gb; g.fillRect(0, 0, 1024, Z(-1.2));
    for (const [x, z, rx, rz, a] of [[5.15, -.05, 1.1, .5, .3], [7.6, 0, .6, .3, .16], [12.4, -1.3, 1.2, .3, .25], [1.4, -1.35, 1.2, .25, .22], [.4, .3, .5, .6, .2], [13.7, .3, .4, .5, .2], [8.47, 0, .3, .25, .14], [13.5, .21, .3, .25, .14]]) blot(x, z, rx, rz, a);
    const Rs = L.rng(77); for (let i = 0; i < 2600; i++) { const x = Rs() * 14, z = -1.6 + Rs() * 4; const near = Math.max(0, 1 - Math.abs(z + 1.6) / .6) + (Math.abs(x - 5.15) < 1 && Math.abs(z) < .45 ? .8 : 0); if (Rs() > .2 + near) continue; g.fillStyle = `rgba(210,200,180,${.08 + Rs() * .18})`; g.fillRect(X(x), Z(z), 1 + Rs() * 2.5, 1 + Rs() * 1.5); }
    for (let i = 0; i < 40; i++) { const x = .3 + Rs() * 13.4, z = -.35 + Rs() * .7; g.fillStyle = 'rgba(20,12,8,.10)'; g.beginPath(); g.ellipse(X(x), Z(z), 5 + Rs() * 6, 2.5 + Rs() * 2, (Rs() - .5) * .4, 0, TAU); g.fill(); }      // 신발 자국
  }));
  dustTex.wrapS = dustTex.wrapT = T.ClampToEdgeWrapping;
  const dustM = new T.MeshStandardMaterial({ name: 'Lounge_FloorDust', map: dustTex, transparent: true, depthWrite: false, roughness: 1, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  // 월넛 가구 결
  const woodC = pix(1024, 512, (x, y) => { const g = fbm(x * .006, y * .05, 3) * 1.3 + Math.sin(x * .02 + fbm(x * .003, y * .015, 9) * 10) * .22; return [cl(70 + g * 46), cl(42 + g * 28), cl(24 + g * 14)]; });
  const woodTex = L.tex(woodC, { jpeg: true });
  const woodN = L.tex(L.normalCanvas(512, 256, (u, v, x, y) => .5 + fbm(x * .012, y * .1, 3) * .25, 1.2), { color: false, jpeg: true });
  const walnut = L.phys({ name: 'Lounge_Walnut', map: woodTex, normalMap: woodN, normalScale: new T.Vector2(.5, .5), roughness: .42, clearcoat: .45, clearcoatRoughness: .3 });
  const walnutDark = L.phys({ name: 'Lounge_WalnutDark', map: woodTex, color: 0x8a7a70, normalMap: woodN, normalScale: new T.Vector2(.5, .5), roughness: .48, clearcoat: .3, clearcoatRoughness: .35 });
  // 페르시안 러그 (8 m × 1.7 m): 테두리 띠 · 덩굴 · 들판(헤라티 무늬) · 메달리온 3 · 닳은 길
  const rugC = L.canvas(2048, 448, g => {
    const w = 2048, h = 448, Rs = L.rng(8);
    g.fillStyle = '#6e1a18'; g.fillRect(0, 0, w, h);
    const band = (m, c) => { g.fillStyle = c; g.fillRect(m, m, w - m * 2, h - m * 2); };
    band(0, '#2a1a2a'); band(6, '#c9b38a'); band(10, '#1e2a44'); band(44, '#c9b38a'); band(48, '#6e1a18'); band(54, '#d8c69a'); band(57, '#7a1e1c');
    // 테두리 무늬 (장미 · 덩굴)
    g.save(); for (let x = 20; x < w; x += 34) for (const y of [27, h - 27]) { g.fillStyle = '#b8862e'; g.beginPath(); g.arc(x, y, 8, 0, TAU); g.fill(); g.fillStyle = '#7a1e1c'; g.beginPath(); g.arc(x, y, 4, 0, TAU); g.fill(); g.strokeStyle = '#d8c69a'; g.lineWidth = 2; g.beginPath(); g.moveTo(x + 8, y); g.quadraticCurveTo(x + 17, y + (x % 68 ? 9 : -9), x + 26, y); g.stroke(); }
    for (let y = 20; y < h; y += 34) for (const x of [27, w - 27]) { g.fillStyle = '#b8862e'; g.beginPath(); g.arc(x, y, 8, 0, TAU); g.fill(); } g.restore();
    // 들판: 헤라티 마름모 + 꽃
    for (let y = 70; y < h - 60; y += 24) for (let x = 70 + ((y / 24) % 2) * 14; x < w - 60; x += 28) { g.fillStyle = Rs() < .5 ? '#8a2a22' : '#5a1414'; g.beginPath(); g.moveTo(x, y - 9); g.lineTo(x + 9, y); g.lineTo(x, y + 9); g.lineTo(x - 9, y); g.fill(); g.fillStyle = ['#c9b38a', '#1e2a44', '#b8862e', '#2c4a3a'][(Rs() * 4) | 0]; g.beginPath(); g.arc(x, y, 3, 0, TAU); g.fill(); }
    // 메달리온 3
    for (const cx of [w * .2, w * .5, w * .8]) { const cy = h / 2;
      for (const [rx, c] of [[150, '#1e2a44'], [132, '#c9b38a'], [124, '#2a3a5a'], [96, '#b8862e'], [88, '#6e1a18'], [56, '#c9b38a'], [48, '#1e2a44'], [20, '#b8862e']]) { g.fillStyle = c; g.beginPath(); for (let a = 0; a <= TAU + .01; a += TAU / 64) { const rr = rx * (1 + .12 * Math.cos(a * 8)); const px = cx + Math.cos(a) * rr, py = cy + Math.sin(a) * rr * .62; a === 0 ? g.moveTo(px, py) : g.lineTo(px, py); } g.fill(); }
      for (const s of [-1, 1]) { g.fillStyle = '#1e2a44'; g.beginPath(); g.moveTo(cx + s * 150, cy - 18); g.lineTo(cx + s * 205, cy); g.lineTo(cx + s * 150, cy + 18); g.fill(); g.fillStyle = '#b8862e'; g.beginPath(); g.arc(cx + s * 212, cy, 9, 0, TAU); g.fill(); } }
    // 닳은 길 (가운데 줄 — 사람이 다니던 자리) · 얼룩 · 먼지
    const gr = g.createLinearGradient(0, h * .2, 0, h * .8); gr.addColorStop(0, 'rgba(210,190,160,0)'); gr.addColorStop(.5, 'rgba(210,190,160,.16)'); gr.addColorStop(1, 'rgba(210,190,160,0)'); g.fillStyle = gr; g.fillRect(0, h * .5, w, h * .35);
    for (let i = 0; i < 9000; i++) { g.fillStyle = `rgba(${Rs() < .5 ? '0,0,0' : '230,215,190'},${Rs() * .08})`; g.fillRect(Rs() * w, Rs() * h, 1 + Rs() * 2, 1); }
    for (let i = 0; i < 6; i++) { const x = Rs() * w, y = h * .3 + Rs() * h * .4, r = 20 + Rs() * 40; const gg = g.createRadialGradient(x, y, 0, x, y, r); gg.addColorStop(0, 'rgba(30,14,8,.25)'); gg.addColorStop(1, 'rgba(30,14,8,0)'); g.fillStyle = gg; g.fillRect(x - r, y - r, r * 2, r * 2); }
  });
  const rugTex = L.tex(rugC, { jpeg: true, wrap: false });
  const pileN = L.tex(L.normalCanvas(128, 128, (u, v, x, y) => .5 + (L.rng(x * 131 + y * 7)() - .5) * .5, 1.5), { color: false, repeat: [40, 9] });
  const rugM = L.phys({ name: 'Lounge_PersianRug', map: rugTex, normalMap: pileN, normalScale: new T.Vector2(.6, .6), roughness: .95, sheen: .6, sheenColor: new T.Color(0xc89a80), sheenRoughness: .7 });
  const fringeM = L.phys({ name: 'Lounge_RugFringe', color: 0xd8ccb0, roughness: .9, sheen: .5, sheenColor: new T.Color(0xffffff) });
  // 벽지 (다마스크: 어두운 청록 + 바랜 금빛) · 웨인스코팅 · 크림 페인트(벗겨진) · 대리석
  const wallC = L.canvas(512, 512, g => { g.fillStyle = '#1d302d'; g.fillRect(0, 0, 512, 512); const Rs = L.rng(5);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { const cx = i * 128 + (j % 2) * 64 + 64, cy = j * 128 + 64; g.fillStyle = 'rgba(122,110,70,.38)'; g.beginPath(); for (let a = 0; a <= TAU + .01; a += TAU / 48) { const r = 38 + 16 * Math.cos(a * 3) + 8 * Math.cos(a * 7); const x = cx + Math.cos(a) * r * .7, y = cy + Math.sin(a) * r; a === 0 ? g.moveTo(x, y) : g.lineTo(x, y); } g.fill(); g.fillStyle = 'rgba(29,48,45,.9)'; g.beginPath(); g.ellipse(cx, cy, 14, 24, 0, 0, TAU); g.fill(); g.strokeStyle = 'rgba(122,110,70,.3)'; g.lineWidth = 3; g.beginPath(); g.moveTo(cx, cy - 62); g.lineTo(cx, cy + 62); g.stroke(); }
    for (let i = 0; i < 5000; i++) { g.fillStyle = `rgba(${Rs() < .5 ? '0,0,0' : '200,190,160'},${Rs() * .05})`; g.fillRect(Rs() * 512, Rs() * 512, 2, 2); } });
  const wallTex = L.tex(wallC, { jpeg: true });
  const wallM = L.phys({ name: 'Lounge_Wallpaper', map: wallTex, roughness: .82, sheen: .3, sheenColor: new T.Color(0x9a9070) });
  const stainTex = L.tex(L.canvas(1024, 256, g => { const Rs = L.rng(19); for (let i = 0; i < 16; i++) { const x = Rs() * 1024, y = Rs() * 100, r = 30 + Rs() * 90; const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, `rgba(40,30,15,${.15 + Rs() * .15})`); gr.addColorStop(1, 'rgba(40,30,15,0)'); g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2); } for (let i = 0; i < 9; i++) { const x = Rs() * 1024; g.fillStyle = 'rgba(30,22,12,.08)'; g.fillRect(x, 0, 3 + Rs() * 8, 256); } }), { wrap: false });
  const stainM = new T.MeshStandardMaterial({ name: 'Lounge_WallStain', map: stainTex, transparent: true, depthWrite: false, roughness: 1, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  const paintC = pix(256, 256, (x, y) => { const n = fbm(x * .03, y * .03, 4); const chip = fbm(x * .06, y * .06, 9) > .66; return chip ? [cl(90 + n * 40), cl(70 + n * 30), cl(50 + n * 20)] : [cl(205 + n * 25), cl(192 + n * 22), cl(165 + n * 18)]; });
  const cream = L.phys({ name: 'Lounge_CreamPaint', map: L.tex(paintC, { jpeg: true }), roughness: .55, clearcoat: .2 });
  const marble = L.phys({ name: 'Lounge_Marble', map: L.tex(pix(256, 256, (x, y) => { const v = Math.abs(Math.sin(x * .03 + fbm(x * .02, y * .02, 6) * 8)); return [cl(214 - v * 50), cl(206 - v * 48), cl(192 - v * 44)]; }), { jpeg: true }), roughness: .25, clearcoat: .6 });
  const brass = L.phys({ name: 'Lounge_Brass', color: 0xb08a4a, metalness: 1, roughness: .32 });
  const gilt = L.phys({ name: 'Lounge_Gilt', color: 0xc8a050, metalness: 1, roughness: .28 });
  const ironM = L.phys({ name: 'Lounge_CastIron', color: 0x8c877c, metalness: .6, roughness: .55 });
  const blackM = L.phys({ name: 'Lounge_Black', color: 0x0e0e10, roughness: .4, clearcoat: .4 });
  const bakelite = L.phys({ name: 'Lounge_Bakelite', color: 0x0c0b0a, roughness: .18, clearcoat: 1 });
  const chrome = L.phys({ name: 'Lounge_Chrome', color: 0xdedee2, metalness: 1, roughness: .12 });
  const ceramic = L.phys({ name: 'Lounge_Ceramic', color: 0xe8e0d0, roughness: .2, clearcoat: .8 });
  const ceramicG = L.phys({ name: 'Lounge_CeramicGreen', color: 0x3c5a48, roughness: .2, clearcoat: .8 });
  const terracotta = L.phys({ name: 'Lounge_Terracotta', color: 0x9a5434, roughness: .85 });
  const soil = L.phys({ name: 'Lounge_Soil', color: 0x2a1c12, roughness: 1 });
  const leafM = L.phys({ name: 'Lounge_Leaf', color: 0xffffff, vertexColors: true, roughness: .5, clearcoat: .3, side: T.DoubleSide });
  const velN = L.tex(L.normalCanvas(256, 256, (u, v, x, y) => .5 + (fbm(x * .05, y * .05, 2) - .5) * .5 + (L.rng(x * 7 + y * 131)() - .5) * .1, 1.2), { color: false, repeat: [4, 4] });
  const velvet = L.phys({ name: 'Lounge_Velvet', color: 0x7a1c1e, roughness: .8, normalMap: velN, normalScale: new T.Vector2(.5, .5), sheen: 1, sheenColor: new T.Color(0xd87a6a), sheenRoughness: .42 });
  const velvetDark = L.phys({ name: 'Lounge_VelvetDark', color: 0x52141a, roughness: .84, normalMap: velN, normalScale: new T.Vector2(.5, .5), sheen: 1, sheenColor: new T.Color(0xb85a4a), sheenRoughness: .45 });
  const curtainM = L.phys({ name: 'Lounge_Curtain', color: 0x4e1418, roughness: .8, normalMap: velN, normalScale: new T.Vector2(.4, .4), sheen: 1, sheenColor: new T.Color(0xa05040), sheenRoughness: .5, side: T.DoubleSide });
  const plaidM = L.phys({ name: 'Lounge_Plaid', map: L.tex(L.canvas(256, 256, g => { g.fillStyle = '#3a4a3a'; g.fillRect(0, 0, 256, 256); for (let i = 0; i < 256; i += 64) { g.fillStyle = 'rgba(140,40,30,.7)'; g.fillRect(i + 20, 0, 18, 256); g.fillRect(0, i + 20, 256, 18); g.fillStyle = 'rgba(220,190,120,.6)'; g.fillRect(i + 50, 0, 3, 256); g.fillRect(0, i + 50, 256, 3); } }), { jpeg: true, repeat: [2, 2] }), roughness: .9, sheen: .6, sheenColor: new T.Color(0xffe0c0) });
  const tuftM = L.phys({ name: 'Lounge_Button', color: 0x3a0c10, roughness: .6, sheen: .5, sheenColor: new T.Color(0xb85a4a) });
  const glassM = L.phys({ name: 'Lounge_SmokedGlass', color: 0x404448, roughness: .06, transparent: true, opacity: .32, clearcoat: 1, depthWrite: false });
  const clockGlass = L.phys({ name: 'Lounge_ClockGlass', color: 0xc0c8d0, roughness: .04, transparent: true, opacity: .14, clearcoat: 1, depthWrite: false });
  const grille = L.phys({ name: 'Lounge_GrilleCloth', map: L.tex(pix(128, 128, (x, y) => { const v = ((x % 3 === 0) || (y % 3 === 0)) ? 12 : 26; return [v + 2, v, v - 2]; }), { repeat: [6, 14] }), roughness: .95 });
  const coneM = L.phys({ name: 'Lounge_SpeakerCone', color: 0x1a1816, roughness: .7 });
  const vinylM = L.phys({ name: 'Lounge_Vinyl', color: 0x0b0b0d, roughness: .25, clearcoat: .6 });
  const labelM = L.phys({ name: 'Lounge_RecordLabel', map: L.tex(L.canvas(128, 128, g => { g.fillStyle = '#c8302a'; g.beginPath(); g.arc(64, 64, 62, 0, TAU); g.fill(); g.fillStyle = '#f0e2c0'; g.font = 'bold 18px Georgia, serif'; g.textAlign = 'center'; g.fillText('ODD HAUS', 64, 50); g.font = '11px Georgia, serif'; g.fillText('SIDE A  33⅓', 64, 90); g.fillStyle = '#111'; g.beginPath(); g.arc(64, 64, 4, 0, TAU); g.fill(); }), { wrap: false }), roughness: .5 });
  const cableM = L.phys({ name: 'Lounge_Cable', color: 0x121214, roughness: .55, clearcoat: .3 });
  const cableW = L.phys({ name: 'Lounge_CableCloth', color: 0x6a5a44, roughness: .9 });
  const paperM = L.phys({ name: 'Lounge_Paper', color: 0xe6dcc6, roughness: .9 });
  const fireBlack = L.phys({ name: 'Lounge_FireboxSoot', color: 0x0a0806, roughness: 1 });
  const shadeFallback = L.phys({ name: 'Lounge_LampShade', color: 0xead3a6, roughness: .85, emissive: 0xffb870, emissiveIntensity: .4, side: T.DoubleSide, sheen: .5, sheenColor: new T.Color(0xffe0b0) });
  const emberM = L.phys({ name: 'Lounge_Ember', color: 0x2a120a, emissive: 0xff5a1a, emissiveIntensity: 1.2, roughness: .9 });
  const dustBunny = L.phys({ name: 'Lounge_DustBunny', color: 0x8a847a, roughness: 1, sheen: 1, sheenColor: new T.Color(0xd8d0c0), transparent: true, opacity: .85 });
  const shadowTex = L.tex(L.canvas(128, 128, g => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(0,0,0,.75)'); gr.addColorStop(.6, 'rgba(0,0,0,.35)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); }), { wrap: false });
  const shadowM = new T.MeshBasicMaterial({ name: 'Lounge_ContactShadow', map: shadowTex, transparent: true, depthWrite: false, color: 0x000000, opacity: .7, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3 });
  // 책등 아틀라스 (16 × 4 칸) · LP 재킷 아틀라스 (4 × 4) · 그림 6장
  const BK = ['#7a2b22', '#2c4a6b', '#6b5a2c', '#3a5a3a', '#5a3a5a', '#8a6b3c', '#2a2a30', '#6a2320', '#b89a6a', '#1f3a3a', '#8a3a1c', '#c8b890', '#4a2a1a', '#224040', '#5a4a6a', '#3a2418'];
  const bookAtlas = L.tex(L.canvas(1024, 512, g => { const Rs = L.rng(14);
    for (let i = 0; i < 16; i++) for (let j = 0; j < 4; j++) { const x = i * 64, y = j * 128, c = BK[(i + j * 5) % 16];
      if (j === 3 && i >= 12) { g.fillStyle = '#e8dcc0'; g.fillRect(x, y, 64, 128); g.fillStyle = 'rgba(120,100,70,.35)'; for (let k = 0; k < 64; k += 2) g.fillRect(x + k, y, 1, 128); continue; }     // 종이(책장 · 윗면)
      g.fillStyle = c; g.fillRect(x, y, 64, 128); const gold = Rs() < .6;
      g.fillStyle = gold ? 'rgba(210,170,80,.85)' : 'rgba(230,220,200,.7)';
      for (const by of [10, 18, 110, 118]) if (Rs() < .8) g.fillRect(x + 4, y + by, 56, 2);
      if (Rs() < .7) { g.fillRect(x + 12, y + 34 + Rs() * 20, 40, 30 + Rs() * 20); g.fillStyle = c; g.fillRect(x + 15, y + 40 + Rs() * 10, 34, 18); }
      for (let k = 0; k < 400; k++) { g.fillStyle = `rgba(${Rs() < .5 ? '0,0,0' : '255,240,210'},${Rs() * .12})`; g.fillRect(x + Rs() * 64, y + Rs() * 128, 1, 1); }
      g.fillStyle = 'rgba(0,0,0,.25)'; g.fillRect(x, y, 3, 128); g.fillRect(x + 61, y, 3, 128); } }), { jpeg: true, wrap: false });
  const bookM = L.phys({ name: 'Lounge_Books', map: bookAtlas, roughness: .75, sheen: .3, sheenColor: new T.Color(0xffffff) });
  const coverAtlas = L.tex(L.canvas(1024, 1024, g => { const Rs = L.rng(21);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { const x = i * 256, y = j * 256, k = i + j * 4; const pal = [['#d8c8a0', '#2a2a30', '#c84030'], ['#1e2a44', '#e8c060', '#d8d0c0'], ['#8a2a22', '#f0e0c0', '#202020'], ['#2c4a6b', '#e0a040', '#f0f0f0'], ['#e8e0d0', '#2a2a2a', '#c03028'], ['#3a5a3a', '#e8d090', '#1a1a1a'], ['#c8a040', '#1a1a1a', '#8a2a22'], ['#5a3a5a', '#f0d0a0', '#20a0a0']][k % 8];
      g.fillStyle = pal[0]; g.fillRect(x, y, 256, 256);
      const t = k % 5; g.fillStyle = pal[1];
      if (t === 0) { g.beginPath(); g.arc(x + 128, y + 128, 80, 0, TAU); g.fill(); g.fillStyle = pal[0]; g.beginPath(); g.arc(x + 128, y + 128, 16, 0, TAU); g.fill(); }
      else if (t === 1) { for (let s = 0; s < 6; s++) g.fillRect(x + 20, y + 30 + s * 34, 216, 14); }
      else if (t === 2) { g.beginPath(); g.moveTo(x + 30, y + 220); g.lineTo(x + 128, y + 40); g.lineTo(x + 226, y + 220); g.fill(); }
      else if (t === 3) { g.fillRect(x + 40, y + 40, 176, 176); g.fillStyle = pal[2]; g.fillRect(x + 80, y + 80, 96, 96); }
      else { for (let s = 0; s < 8; s++) { g.beginPath(); g.arc(x + 128, y + 128, 110 - s * 13, 0, TAU); g.strokeStyle = s % 2 ? pal[1] : pal[2]; g.lineWidth = 6; g.stroke(); } }
      g.fillStyle = pal[2]; g.font = `bold ${22 + (k % 3) * 4}px Georgia, serif`; g.fillText(['ODD HAUS', 'SIDE B', 'LP 33', 'NIGHT', 'MOON', 'DUST', 'VINYL', 'QUIET'][k % 8], x + 18, y + 240);
      for (let n = 0; n < 1500; n++) { g.fillStyle = `rgba(${Rs() < .5 ? '0,0,0' : '255,250,230'},${Rs() * .1})`; g.fillRect(x + Rs() * 256, y + Rs() * 256, 1, 1); }
      g.strokeStyle = 'rgba(0,0,0,.25)'; g.lineWidth = 3; g.strokeRect(x + 1, y + 1, 254, 254); } }), { jpeg: true, wrap: false });
  const coverM = L.phys({ name: 'Lounge_LPCovers', map: coverAtlas, roughness: .6 });
  const paintAtlas = L.tex(L.canvas(1024, 512, g => { const Rs = L.rng(33);
    const cell = (i, draw) => { const x = (i % 4) * 256, y = Math.floor(i / 4) * 256; g.save(); g.beginPath(); g.rect(x, y, 256, 256); g.clip(); g.translate(x, y); draw(); for (let n = 0; n < 2500; n++) { g.fillStyle = `rgba(${Rs() < .5 ? '0,0,0' : '255,240,200'},${Rs() * .07})`; g.fillRect(Rs() * 256, Rs() * 256, 2, 2); } g.restore(); };
    cell(0, () => { g.fillStyle = '#2a2018'; g.fillRect(0, 0, 256, 256); g.fillStyle = '#5a4030'; g.beginPath(); g.ellipse(128, 120, 60, 72, 0, 0, TAU); g.fill(); g.fillStyle = '#1a1410'; g.beginPath(); g.ellipse(128, 70, 66, 40, 0, Math.PI, TAU); g.fill(); g.fillStyle = '#e8d8b0'; g.beginPath(); g.ellipse(108, 120, 8, 6, 0, 0, TAU); g.ellipse(148, 120, 8, 6, 0, 0, TAU); g.fill(); g.fillStyle = '#1a1410'; g.beginPath(); g.ellipse(128, 150, 40, 10, 0, 0, TAU); g.fill(); g.fillStyle = '#4a1a18'; g.fillRect(50, 200, 156, 56); });     // 수염 난 신사 초상
    cell(1, () => { const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, '#0e1a30'); gr.addColorStop(1, '#2a3a50'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); g.fillStyle = '#e8e0c0'; g.beginPath(); g.arc(190, 60, 22, 0, TAU); g.fill(); g.fillStyle = '#101820'; g.beginPath(); g.moveTo(0, 200); for (let x = 0; x <= 256; x += 16) g.lineTo(x, 170 + Math.sin(x * .05) * 20 + Rs() * 10); g.lineTo(256, 256); g.lineTo(0, 256); g.fill(); });      // 밤 풍경
    cell(2, () => { g.fillStyle = '#d8c090'; g.fillRect(0, 0, 256, 256); g.fillStyle = '#111'; g.beginPath(); g.arc(128, 128, 100, 0, TAU); g.fill(); g.fillStyle = '#c03028'; g.beginPath(); g.arc(128, 128, 34, 0, TAU); g.fill(); g.strokeStyle = 'rgba(255,255,255,.12)'; for (let r = 40; r < 100; r += 4) { g.beginPath(); g.arc(128, 128, r, 0, TAU); g.stroke(); } });      // 레코드 그림
    cell(3, () => { g.fillStyle = '#c8b890'; g.fillRect(0, 0, 256, 256); g.fillStyle = '#6a4a30'; g.beginPath(); g.ellipse(128, 150, 70, 56, 0, 0, TAU); g.fill(); g.beginPath(); g.ellipse(128, 92, 44, 40, 0, 0, TAU); g.fill(); g.fillStyle = '#4a3020'; g.beginPath(); g.ellipse(92, 100, 14, 34, .3, 0, TAU); g.ellipse(164, 100, 14, 34, -.3, 0, TAU); g.fill(); g.fillStyle = '#2c4a8a'; g.fillRect(112, 128, 32, 14); });      // 강아지 사진 (Buddy)
    cell(4, () => { g.fillStyle = '#1a1a1a'; g.fillRect(0, 0, 256, 256); g.fillStyle = '#e8c040'; g.font = 'bold 54px Impact, sans-serif'; g.fillText('LIVE', 60, 90); g.fillStyle = '#c03028'; g.font = 'bold 30px Impact, sans-serif'; g.fillText('THE ODD HAUS', 24, 150); g.fillStyle = '#e8e0d0'; g.font = '20px Georgia, serif'; g.fillText('one night only', 60, 200); });    // 공연 포스터
    cell(5, () => { g.fillStyle = '#3a2a1e'; g.fillRect(0, 0, 256, 256); g.fillStyle = '#c8a050'; g.beginPath(); g.ellipse(100, 170, 50, 30, 0, 0, TAU); g.fill(); g.fillStyle = '#8a2a22'; g.beginPath(); g.arc(160, 150, 30, 0, TAU); g.fill(); g.fillStyle = '#d8d0b0'; g.fillRect(60, 80, 24, 70); });      // 정물
    cell(6, () => { g.fillStyle = '#e0d8c8'; g.fillRect(0, 0, 256, 256); g.fillStyle = '#2a2a2a'; for (let i = 0; i < 5; i++) g.fillRect(30 + i * 42, 60 + (i % 2) * 30, 26, 150 - (i % 2) * 30); });     // 사진 (책장)
    cell(7, () => { g.fillStyle = '#e8e0cc'; g.fillRect(0, 0, 256, 256); g.strokeStyle = '#222'; g.lineWidth = 3; g.beginPath(); g.arc(128, 128, 110, 0, TAU); g.stroke(); g.font = 'bold 20px Georgia, serif'; g.fillStyle = '#222'; for (let k = 1; k <= 12; k++) { const a = k / 12 * TAU - Math.PI / 2; g.fillText(['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII'][k - 1], 118 + Math.cos(a) * 90, 134 + Math.sin(a) * 90); } });     // 시계 문자판
  }), { jpeg: true, wrap: false });
  const paintM = L.phys({ name: 'Lounge_Paintings', map: paintAtlas, roughness: .7 });

  // =====================================================================
  // 지오메트리 도우미 (월드 좌표) — 같은 재질끼리 모아 한 메시로
  // =====================================================================
  const B = new Map(); const put = (mat, g, name) => { if (!B.has(mat)) B.set(mat, { name: name || mat.name, geos: [] }); B.get(mat).geos.push(g); return g; };
  const solo = (mat, g, name, o = {}) => { const m = new T.Mesh(g, mat); m.name = name; m.castShadow = o.cast !== false; m.receiveShadow = true; if (o.ref) m.userData.matRef = o.ref; root.add(m); return m; };
  const worldUV = (g, s) => { g = g.index ? g : g; const p = g.attributes.position, n = g.attributes.normal, uv = g.attributes.uv; if (!uv) return g; for (let i = 0; i < p.count; i++) { const nx = Math.abs(n.getX(i)), ny = Math.abs(n.getY(i)), nz = Math.abs(n.getZ(i)); let u, v; if (ny >= nx && ny >= nz) { u = p.getX(i); v = p.getZ(i); } else if (nx >= nz) { u = p.getZ(i); v = p.getY(i); } else { u = p.getX(i); v = p.getY(i); } uv.setXY(i, u / s, v / s); } return g; };
  const box = (x0, x1, y0, y1, z0, z1) => { const g = new T.BoxGeometry(x1 - x0, y1 - y0, z1 - z0); g.translate((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); return g; };
  // 같은 위치 · 노멀 · uv 정점을 하나로 (RoundedBoxGeometry는 인덱스가 없어 정점이 6배)
  const weld = g => { const p = g.attributes.position, n = g.attributes.normal, u = g.attributes.uv, map = new Map(), P = [], N = [], U = [], idx = [], src = g.index;
    const cnt = src ? src.count : p.count; for (let k = 0; k < cnt; k++) { const i = src ? src.getX(k) : k; const key = [p.getX(i).toFixed(5), p.getY(i).toFixed(5), p.getZ(i).toFixed(5), n.getX(i).toFixed(2), n.getY(i).toFixed(2), n.getZ(i).toFixed(2), u ? u.getX(i).toFixed(4) : 0, u ? u.getY(i).toFixed(4) : 0].join(',');
      let j = map.get(key); if (j === undefined) { j = P.length / 3; map.set(key, j); P.push(p.getX(i), p.getY(i), p.getZ(i)); N.push(n.getX(i), n.getY(i), n.getZ(i)); if (u) U.push(u.getX(i), u.getY(i)); } idx.push(j); }
    const o = new T.BufferGeometry(); o.setAttribute('position', new T.Float32BufferAttribute(P, 3)); o.setAttribute('normal', new T.Float32BufferAttribute(N, 3)); if (u) o.setAttribute('uv', new T.Float32BufferAttribute(U, 2)); o.setIndex(idx); return o; };
  const rbox = (x0, x1, y0, y1, z0, z1, r = .01, seg = 2) => { const w = x1 - x0, h = y1 - y0, d = z1 - z0; const g = weld(new D.RoundedBoxGeometry(w, h, d, Math.min(seg, 2), Math.min(r, w / 2, h / 2, d / 2) * .98)); g.translate((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); return g; };
  const wood = (g, s = .8) => worldUV(g, s);
  const cylY = (x, z, y0, h, rTop, rBot, seg = 24, open = false) => { const g = new T.CylinderGeometry(rTop, rBot ?? rTop, h, seg, 1, open); g.translate(x, y0 + h / 2, z); return g; };
  const lathe = (x, z, y0, pts, seg = 20) => { const g = L.lathe(pts, seg); g.translate(x, y0, z); return g; };
  const leg = (x, z, h, r) => lathe(x, z, 0, [[r * .7, 0], [r * .9, h * .02], [r * .75, h * .15], [r, h * .3], [r * .6, h * .55], [r * .8, h * .8], [r, h * .92], [r * .9, h]], 14);
  const shadow = (x, z, w, d, op = .7, y = .0012) => { const g = new T.PlaneGeometry(w, d); g.rotateX(-Math.PI / 2); g.translate(x, y, z); put(shadowM, g); };
  // 책 한 권: 책등(+Z) = 아틀라스 칸, 나머지 = 종이 칸
  const bookGeo = (cx, cy, cz, w, h, d, rz = 0, ry = 0, cell = 0) => {      // 책등 = +Z 면, 표지 = 가장 얇은 축의 두 면(책 색), 나머지 = 종이
    const g = new T.BoxGeometry(w, h, d), uv = g.attributes.uv, ci = Math.abs(cell) % 60, u0 = (ci % 16) / 16, v0 = 1 - (Math.floor(ci / 16) + 1) / 4, pu0 = (12 + (Math.abs(cell) % 4)) / 16, thin = w <= h && w <= d ? 0 : h <= d ? 1 : 2;
    for (let f = 0; f < 6; f++) for (let k = 0; k < 4; k++) { const i = f * 4 + k, a = uv.getX(i), b = uv.getY(i);
      if (f === 4) uv.setXY(i, u0 + a / 16, v0 + b / 4); else if ((f >> 1) === thin) uv.setXY(i, u0 + (.3 + a * .4) / 16, v0 + (.62 + b * .1) / 4); else uv.setXY(i, pu0 + a / 16 * .9, b / 4 * .9); }
    g.rotateZ(rz); g.rotateY(ry); g.translate(cx, cy, cz); return g; };
  const sleeveGeo = (cx, cy, cz, rz, cell, face = false) => { const g = new T.BoxGeometry(face ? .315 : .0042, .315, face ? .004 : .315), uv = g.attributes.uv, ci = cell % 16, u0 = (ci % 4) / 4, v0 = 1 - (Math.floor(ci / 4) + 1) / 4;
    for (let i = 0; i < uv.count; i++) { const a = uv.getX(i), b = uv.getY(i); uv.setXY(i, u0 + (face ? a : a * .06 + .47) / 4, v0 + b / 4); }
    g.rotateZ(rz); g.translate(cx, cy, cz); return g; };

  // =====================================================================
  // 바닥 · 러그
  // =====================================================================
  { const g = new T.PlaneGeometry(14, 4, 1, 1); g.rotateX(-Math.PI / 2); g.translate(7, 0, .4);
    const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * 14 / 2.8, uv.getY(i) * 4 / 1.4); solo(floorM, g, 'Lounge_Floor', { cast: false });
    const d = new T.PlaneGeometry(14, 4); d.rotateX(-Math.PI / 2); d.translate(7, .0008, .4); solo(dustM, d, 'Lounge_FloorDustScratches', { cast: false }); }
  { const c = COL('rug', 5); const w = c.max.x - c.min.x, dz = c.max.z - c.min.z, top = c.max.y;
    const g = new T.BoxGeometry(w, top, dz, 1, 1, 1); g.translate((c.min.x + c.max.x) / 2, top / 2, (c.min.z + c.max.z) / 2); solo(rugM, g, 'Lounge_PersianRug', { cast: false });
    // 술: 양쪽 짧은 끝에 실 가닥 (바닥에 누운 리본)
    const pos = [], nor = [], uvs = [], idx = []; const Rs = L.rng(6);
    for (const [x0, s] of [[c.min.x, -1], [c.max.x, 1]]) for (let z = c.min.z + .01; z < c.max.z - .005; z += .009) { const len = .05 + Rs() * .03, a = (Rs() - .5) * .35, b = pos.length / 3, hw = .0016;
      const ex = x0 + s * Math.cos(a) * len, ez = z + Math.sin(a) * len, y0 = top * .6, y1 = .0012;
      for (const [px, py, pz] of [[x0, y0, z - hw], [x0, y0, z + hw], [ex, y1, ez - hw], [ex, y1, ez + hw]]) { pos.push(px, py, pz); nor.push(0, 1, 0); uvs.push(0, 0); }
      idx.push(b, b + 2, b + 1, b + 1, b + 2, b + 3); }
    const fg = new T.BufferGeometry(); fg.setAttribute('position', new T.Float32BufferAttribute(pos, 3)); fg.setAttribute('normal', new T.Float32BufferAttribute(nor, 3)); fg.setAttribute('uv', new T.Float32BufferAttribute(uvs, 2)); fg.setIndex(idx);
    const fm = solo(fringeM, fg, 'Lounge_RugFringe', { cast: false }); fm.material.side = T.DoubleSide; }

  // =====================================================================
  // 뒷벽: 벽지 · 웨인스코팅 · 의자 레일 · 걸레받이 · 크라운 몰딩 · 얼룩 · 창
  // =====================================================================
  const WZ = -1.6, segs = [[.06, 9.6], [11.0, 14.0]];
  const wallPlane = (x0, x1, y0, y1, z, mat, name, s = .6) => { const g = new T.PlaneGeometry(x1 - x0, y1 - y0); g.translate((x0 + x1) / 2, (y0 + y1) / 2, z); const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, (x0 + uv.getX(i) * (x1 - x0)) / s, (y0 + uv.getY(i) * (y1 - y0)) / s); put(mat, g, name); };
  for (const [x0, x1] of segs) wallPlane(x0, x1, .93, 2.46, WZ + .0005, wallM, 'Lounge_Wallpaper');
  wallPlane(9.6, 11.0, 2.1, 2.46, WZ + .0005, wallM);
  for (const [a, b] of [[.06, 9.5], [11.1, 14.0]]) { const g = new T.PlaneGeometry(b - a, 1.5), uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setX(i, (a + uv.getX(i) * (b - a)) / 14); g.translate((a + b) / 2, 1.7, WZ + .0012); solo(stainM, g, 'Lounge_WallStains', { cast: false }); }
  // 웨인스코팅: 프레임 + 오목한 패널
  for (const [x0, x1] of [[.06, 14.0]]) {
    put(walnutDark, wood(box(x0, x1, .1, .88, WZ, WZ + .012)));
    const n = Math.round((x1 - x0) / .62), pw = (x1 - x0) / n;
    for (let i = 0; i < n; i++) { const a = x0 + i * pw; put(walnut, wood(rbox(a + .05, a + pw - .05, .2, .8, WZ + .012, WZ + .03, .006))); put(walnutDark, wood(box(a + .075, a + pw - .075, .225, .775, WZ + .03, WZ + .033))); }
    put(walnut, wood(rbox(x0, x1, .88, .935, WZ, WZ + .04, .008)));      // 의자 레일
    put(walnutDark, wood(rbox(x0, x1, 0, .12, WZ, WZ + .028, .006)));    // 걸레받이
    put(walnut, wood(rbox(x0, x1, .115, .13, WZ, WZ + .034, .004)));
    put(cream, wood(rbox(x0, x1, 2.46, 2.6, WZ, WZ + .07, .02)));        // 크라운 몰딩
    put(cream, wood(rbox(x0, x1, 2.44, 2.47, WZ, WZ + .09, .01)));
  }
  // 창: 틀 · 창살 · 깊은 창턱 · 벽 두께 (유리 · 바깥 밤은 게임 코드)
  { const C2 = cream; put(C2, wood(rbox(9.52, 9.62, .88, 2.16, -1.72, -1.54, .012))); put(C2, wood(rbox(10.98, 11.08, .88, 2.16, -1.72, -1.54, .012))); put(C2, wood(rbox(9.52, 11.08, 2.08, 2.18, -1.72, -1.54, .012)));
    put(C2, wood(rbox(9.45, 11.15, .86, .93, -1.72, -1.4, .012))); put(C2, wood(rbox(9.5, 11.1, .82, .86, -1.6, -1.44, .008)));
    put(C2, wood(box(10.28, 10.32, .92, 2.1, -1.69, -1.64))); put(C2, wood(box(9.6, 11.0, 1.49, 1.53, -1.69, -1.64)));
    put(C2, wood(box(9.6, 9.62, .9, 2.1, -1.7, -1.6))); put(C2, wood(box(10.98, 11.0, .9, 2.1, -1.7, -1.6)));
    // 창턱 위: 작은 화분 · 촛대
    put(terracotta, lathe(9.75, -1.5, .93, [[.04, 0], [.05, .002], [.055, .09], [.06, .1], [.055, .1]], 16)); put(soil, cylY(9.75, -1.5, 1.02, .005, .05));
    const LV = []; const Rs = L.rng(44); for (let i = 0; i < 9; i++) { const a = i / 9 * TAU, l = L.blob(.03, .008, .016, () => 1, 10, 6); l.rotateZ(.6 + Rs() * .4); l.rotateY(a); l.translate(9.75 + Math.cos(a) * .03, 1.06 + Rs() * .03, -1.5 + Math.sin(a) * .03); LV.push(L.color(l, [0x3c6a3a, 0x4a7a40, 0x2e5a32][i % 3])); } put(leafM, L.merge(LV, ['position', 'normal', 'uv', 'color']));
    put(brass, lathe(10.85, -1.5, .93, [[.03, 0], [.03, .01], [.012, .02], [.01, .14], [.02, .15], [.02, .16]], 14)); put(paperM, cylY(10.85, -1.5, 1.09, .1, .01)); }
  // 커튼 (주름 · 바닥에 고인 밑단 · 묶은 끈) + 놋쇠 봉
  for (const [xa, xb, s] of [[9.08, 9.7, -1], [10.9, 11.52, 1]]) { const w = xb - xa, g = new T.PlaneGeometry(w, 2.38, 48, 24), p = g.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i) + 1.19, u = (x + w / 2) / w, tie = Math.exp(-(((y - .95) / .25) ** 2)), pinch = 1 - tie * .55 * (s < 0 ? u : 1 - u);
      p.setXYZ(i, (xa + xb) / 2 + x * pinch + (s < 0 ? -1 : 1) * tie * .02, y, -1.5 + Math.sin(u * TAU * 5.5) * .028 * (1 - tie * .5) + (y < .12 ? (.12 - y) * .9 : 0)); }
    g.computeVertexNormals(); put(curtainM, g);
    put(gilt, L.capsule([(xa + xb) / 2 + s * .04, .95, -1.44], [(xa + xb) / 2 - s * .02, .93, -1.47], .012, 8)); put(gilt, lathe((xa + xb) / 2, -1.44, .86, [[.0, 0], [.018, .01], [.012, .07], [0, .085]], 10)); }
  { const rod = new T.CylinderGeometry(.014, .014, 2.6, 16); rod.rotateZ(Math.PI / 2); rod.translate(10.3, 2.4, -1.5); put(brass, rod); for (const x of [8.98, 11.62]) put(brass, L.blob(.03, .03, .03, () => 1, 12, 8).translate(x, 2.4, -1.5)); for (const x of [9.1, 11.5]) put(brass, box(x - .01, x + .01, 2.4, 2.48, -1.6, -1.49)); }
  // 주철 라디에이터 (창 아래, 칠이 벗겨진 은색) + 밸브 · 바닥으로 들어가는 관
  { for (let i = 0; i < 13; i++) { const x = 9.74 + i * .075; put(ironM, rbox(x - .028, x + .028, .14, .7, -1.57, -1.46, .022, 3)); put(ironM, box(x - .006, x + .006, .2, .64, -1.585, -1.445)); }
    put(ironM, rbox(9.7, 10.72, .12, .17, -1.58, -1.45, .015)); put(ironM, rbox(9.7, 10.72, .66, .7, -1.58, -1.45, .015));
    for (const x of [9.76, 10.66]) { put(ironM, box(x - .012, x + .012, .04, .14, -1.54, -1.5)); put(ironM, box(x - .03, x + .03, .02, .05, -1.56, -1.48)); }
    put(ironM, cylY(9.66, -1.52, .0, .18, .014)); put(brass, L.blob(.022, .014, .022, () => 1, 10, 6).translate(9.66, .2, -1.52)); shadow(10.2, -1.45, 1.3, .3, .5); }

  // =====================================================================
  // 붙박이 책장 (x .3–2.5) + 책 · LP · 소품
  // =====================================================================
  { const c = COL('shelf', 1.4), x0 = c.min.x, x1 = c.max.x, z0 = WZ, z1 = c.max.z;
    for (const x of [x0, x0 + .04 - .04 + 1.08, x1 - .04]) put(walnut, wood(rbox(x, x + .04, 0, 2.12, z0, z1 + .02, .006)));
    put(walnut, wood(rbox(x0 - .02, x1 + .02, 2.08, 2.17, z0, z1 + .04, .012))); put(cream, wood(rbox(x0 - .03, x1 + .03, 2.17, 2.22, z0, z1 + .05, .01)));
    put(walnutDark, wood(rbox(x0, x1, 0, .07, z0, z1 + .02, .006))); put(walnutDark, wood(box(x0 + .04, x1 - .04, .07, 2.08, z0, z0 + .015)));
    const SY = [.07, .49, .9, 1.3, 1.69]; SY.forEach((y, i) => { if (i) put(walnut, wood(rbox(x0 + .04, x1 - .04, y - .025, y, z0, z1, .005))); });
    let cell = 0; const Rs = L.rng(70), BG = [], SG = [];
    const fill = (a, b, y, maxH) => { let x = a + .006; while (x < b - .03) { const r = Rs(); if (r < .05) { x += .03 + Rs() * .05; continue; }
        if (r < .13 && x < b - .26) { let yy = y; const n = 2 + (Rs() * 4 | 0); for (let i = 0; i < n; i++) { const hh = .026 + Rs() * .02, ww = .2 + Rs() * .05; BG.push(bookGeo(x + ww / 2, yy + hh / 2, z0 + .17, ww, hh, .26 + Rs() * .04, 0, (Rs() - .5) * .08, cell++)); yy += hh; } x += .27; continue; }
        const w = .018 + Rs() * .03, h = Math.min(maxH, .17 + Rs() * .16), d = .22 + Rs() * .08, lean = Rs() < .07 ? (Rs() < .5 ? -1 : 1) * (.12 + Rs() * .18) : 0;
        BG.push(bookGeo(x + w / 2 + (lean ? Math.sin(-lean) * h / 2 : 0), y + Math.cos(lean) * h / 2, z0 + .015 + d / 2, w, h, d, lean, 0, cell++)); x += w + (lean ? .025 : .0015); } };
    SY.forEach((y, i) => { if (i === 1) { for (let x = x0 + .07; x < x0 + 1.0; x += .0062 + Rs() * .003) SG.push(sleeveGeo(x, y + .158, -1.42, (Rs() - .5) * .05, (Rs() * 16) | 0)); fill(x0 + 1.12, x1 - .05, y, .36); } else if (i < 4) { fill(x0 + .05, x0 + 1.07, y, .36); fill(x0 + 1.12, x1 - .05, y, .36); } else { fill(x0 + .05, x0 + .8, y, .36); fill(x0 + 1.12, x1 - .4, y, .36); } });
    put(bookM, L.merge(BG)); put(coverM, L.merge(SG));
    put(ceramicG, lathe(2.2, -1.38, 1.69, [[.04, 0], [.07, .04], [.075, .1], [.045, .16], [.04, .19], [.05, .2]], 20)); put(brass, lathe(.62, -1.36, 1.3, [[.0, 0], [.05, .005], [.09, .06], [.088, .065]], 20));
    put(gilt, rbox(.86, 1.06, 1.69, 1.95, -1.55, -1.53, .006)); put(paintM, (() => { const g = new T.PlaneGeometry(.17, .22); const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, (2 + uv.getX(i)) / 4, .5 + uv.getY(i) * .5); g.translate(.96, 1.82, -1.528); return g; })());
    // 덩굴 식물 (책장 위에서 늘어진 포토스)
    put(terracotta, lathe(2.25, -1.4, 2.22, [[.06, 0], [.08, .01], [.09, .12], [.095, .13]], 16));
    { const LV = []; const Rs2 = L.rng(9); for (let v = 0; v < 5; v++) { let p = V3(2.25 + (Rs2() - .5) * .1, 2.34, -1.38 + (Rs2() - .5) * .08); const len = 6 + (Rs2() * 9 | 0); for (let k = 0; k < len; k++) { p = p.clone().add(V3((Rs2() - .5) * .05 + (v - 2) * .012, -.06 - Rs2() * .03, .012)); const l = L.blob(.022, .004, .018, () => 1, 8, 5); l.rotateX(.4 + Rs2() * .6); l.rotateY(Rs2() * TAU); l.translate(p.x, p.y, p.z); LV.push(L.color(l, [0x4a7a3a, 0x5a8a40, 0x3a6a30, 0x8a9a40][(Rs2() * 4) | 0])); } } put(leafM, L.merge(LV, ['position', 'normal', 'uv', 'color'])); }
    shadow(1.4, -1.4, 2.6, .7, .65); }
  // 벨벳 안락의자 (배경) + 발받침
  { const Vd = velvetDark, V_ = velvet;
    put(Vd, rbox(1.3, 2.25, .1, .42, -1.2, -.55, .05, 3)); put(V_, rbox(1.32, 2.23, .38, .5, -1.0, -.55, .045, 3)); put(V_, rbox(1.3, 2.25, .42, 1.02, -1.22, -.98, .07, 3));
    for (const x of [1.37, 2.18]) { put(V_, rbox(x - .09, x + .09, .38, .64, -1.2, -.55, .06, 3)); const r = new T.CylinderGeometry(.075, .075, .64, 20); r.rotateX(Math.PI / 2); r.translate(x + (x < 1.8 ? -.02 : .02), .62, -.88); put(V_, r); }
    for (const x of [1.36, 2.19]) for (const z of [-1.14, -.6]) put(walnutDark, leg(x, z, .1, .022));
    put(plaidM, (() => { const g = new T.PlaneGeometry(.5, .6, 10, 10), p = g.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i); p.setZ(i, Math.sin(x * 20) * .015 + (y < -.1 ? (-.1 - y) * .4 : 0)); } g.computeVertexNormals(); g.rotateX(-.2); g.translate(1.65, .72, -1.0); return g; })());
    shadow(1.78, -.86, 1.2, .9, .6); }
  // 스탠드 램프 (3.3, −0.8): 받침 · 기둥 · 갓(게임 재질: 꺼지면 어두워진다) · 당김 줄 · 바닥 전선
  { const LZ = -.8; put(brass, lathe(3.3, LZ, 0, [[.0, 0], [.17, 0], [.17, .015], [.12, .035], [.03, .05], [.018, .08]], 32));
    put(brass, cylY(3.3, LZ, .05, 1.22, .012)); put(brass, lathe(3.3, LZ, .5, [[.012, 0], [.022, .02], [.012, .04]], 14)); put(brass, lathe(3.3, LZ, 1.0, [[.012, 0], [.02, .015], [.012, .03]], 14));
    put(brass, cylY(3.3, LZ, 1.26, .1, .006)); put(brass, L.blob(.012, .016, .012, () => 1, 10, 8).translate(3.3, 1.56, LZ));
    const sh = L.lathe([[.21, 0], [.205, .02], [.135, .27], [.13, .28]], 40); sh.translate(3.3, 1.26, LZ); solo(shadeFallback, sh, 'Lounge_FloorLampShade', { ref: 'shade' }).material.side = T.DoubleSide;
    put(brass, (() => { const g = new T.TorusGeometry(.21, .004, 6, 40); g.rotateX(Math.PI / 2); g.translate(3.3, 1.26, LZ); return g; })());
    put(brass, cylY(3.33, LZ + .02, 1.1, .18, .0015)); put(brass, L.blob(.006, .01, .006, () => 1, 8, 6).translate(3.33, 1.1, LZ + .02));
    put(cableW, L.tube([[3.3, .02, LZ - .02], [3.2, .006, LZ - .25], [3.05, .006, -1.3], [2.9, .006, -1.5], [2.88, .08, -1.585], [2.88, .16, -1.585]], .0045, 40, 6, false)); put(cream, box(2.84, 2.92, .14, .24, -1.6, -1.592));
    shadow(3.3, LZ, .55, .55, .7); }
  // 책 더미 계단 (3.5–3.82): 충돌 높이 그대로
  const stackBooks = (c, seed, name) => { const Rs = L.rng(seed), G = []; let y = c.min.y; const n = Math.max(1, Math.round((c.max.y - c.min.y) / .055)), hh = (c.max.y - c.min.y) / n; const cx = (c.min.x + c.max.x) / 2, cz = (c.min.z + c.max.z) / 2, w = c.max.x - c.min.x, d = c.max.z - c.min.z;
    for (let i = 0; i < n; i++) { G.push(bookGeo(cx + (Rs() - .5) * .012, y + hh / 2, cz + (Rs() - .5) * .012, w - .004 - Rs() * .02, hh * .98, d - .004 - Rs() * .02, 0, (Rs() - .5) * .08, (seed * 7 + i * 3) | 0)); y += hh; }
    put(bookM, L.merge(G)); shadow(cx, cz, w * 1.8, d * 1.8, .6); };
  stackBooks(COL('books', 3.66), 118);
  // 벽등 두 개 · 액자 벽
  for (const x of [4.3, 6.0]) { put(brass, rbox(x - .045, x + .045, 1.58, 1.74, WZ, WZ + .02, .01)); put(brass, L.tube([[x, 1.62, WZ + .02], [x, 1.62, -1.5], [x, 1.66, -1.48]], .008, 10, 6, false)); const s = L.lathe([[.06, 0], [.058, .01], [.04, .12], [.038, .125]], 24); s.translate(x, 1.64, -1.5); solo(shadeFallback, s, 'Lounge_SconceShade', { ref: 'shade' }); }
  const frame = (x, y, w, h, cell, giltF) => { const m = giltF ? gilt : walnutDark, t = giltF ? .055 : .035;
    for (const [a, b, c2, d] of [[x - w / 2 - t, x + w / 2 + t, y + h / 2, y + h / 2 + t], [x - w / 2 - t, x + w / 2 + t, y - h / 2 - t, y - h / 2], [x - w / 2 - t, x - w / 2, y - h / 2, y + h / 2], [x + w / 2, x + w / 2 + t, y - h / 2, y + h / 2]]) put(m, rbox(a, b, c2, d, WZ, WZ + .035, .008, 2));
    if (giltF) for (const [a, b, c2, d] of [[x - w / 2 - .01, x + w / 2 + .01, y + h / 2, y + h / 2 + .012], [x - w / 2 - .01, x + w / 2 + .01, y - h / 2 - .012, y - h / 2]]) put(m, rbox(a, b, c2, d, WZ + .03, WZ + .045, .004));
    const g = new T.PlaneGeometry(w, h); const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, ((cell % 4) + uv.getX(i)) / 4, 1 - (Math.floor(cell / 4) + 1 - uv.getY(i)) / 2); g.translate(x, y, WZ + .02); put(paintM, g); };
  frame(5.15, 1.5, .78, .52, 1, true); frame(4.72, 2.0, .26, .32, 0, false); frame(5.55, 2.02, .3, .24, 3, false); frame(3.6, 1.95, .24, .3, 5, false); frame(7.6, 1.72, .44, .56, 0, true); frame(12.6, 1.8, .5, .66, 4, true); frame(2.95, 1.6, .2, .26, 3, false);
  // 벽난로 (6.98–8.22): 대리석 테두리 · 월넛 선반 · 그을린 화구 · 쇠 받침 · 잔불 통나무(게임 재질) · 돌판 · 선반 위 소품
  { const FZ = WZ; put(marble, rbox(6.98, 8.22, 0, 1.0, FZ, FZ + .2, .01)); put(fireBlack, box(7.22, 7.98, .06, .64, FZ + .19, FZ + .205));
    put(marble, rbox(7.16, 8.04, .62, .7, FZ + .19, FZ + .22, .006)); put(walnut, wood(rbox(6.92, 8.28, .99, 1.06, FZ, FZ + .28, .012))); put(walnut, wood(rbox(6.95, 8.25, .95, .99, FZ, FZ + .24, .008)));
    put(marble, rbox(6.88, 8.32, 0, .03, FZ + .19, FZ + .42, .006));
    for (let i = 0; i < 7; i++) put(ironM, rbox(7.3 + i * .07, 7.32 + i * .07, .06, .2, FZ + .25, FZ + .34, .004)); put(ironM, box(7.28, 7.76, .06, .08, FZ + .24, FZ + .35));
    const lg = [], eb = []; const charM = L.phys({ name: 'Lounge_CharredWood', color: 0x1a120c, roughness: .95 });
    for (const [x, a, r, y] of [[7.48, -.2, .034, .1], [7.72, .25, .03, .1], [7.6, .05, .026, .15]]) { const c2 = L.tube([[-.15, 0, 0], [-.05, .004, .003], [.05, -.003, -.002], [.15, 0, 0]], t => r * (.9 + .15 * Math.sin(t * 9)), 16, 10); c2.rotateZ(a); c2.translate(x, y, FZ + .3); lg.push(c2); }
    put(charM, L.merge(lg));
    { const bed = L.blob(.24, .02, .07, d => 1 + .25 * Math.sin(d.x * 13) * Math.sin(d.z * 9), 24, 10); bed.translate(7.6, .07, FZ + .3); eb.push(bed); const Rs = L.rng(8); for (let i = 0; i < 14; i++) { const c3 = L.blob(.012 + Rs() * .012, .008 + Rs() * .008, .012, () => 1, 8, 6); c3.translate(7.4 + Rs() * .4, .085 + Rs() * .02, FZ + .26 + Rs() * .08); eb.push(c3); } for (const [x, a, y, r] of [[7.48, -.2, .1, .034], [7.72, .25, .1, .03]]) { const g2 = L.tube([[-.12, -r * .7, 0], [.12, -r * .7, 0]], r * .45, 8, 8); g2.rotateZ(a); g2.translate(x, y, FZ + .3); eb.push(g2); } }
    solo(emberM, L.merge(eb), 'Lounge_FireEmbers', { ref: 'ember' });
    for (const x of [7.05, 8.15]) { put(brass, lathe(x, FZ + .14, 1.06, [[.035, 0], [.035, .01], [.012, .03], [.01, .2], [.025, .21], [.02, .22]], 14)); put(paperM, cylY(x, FZ + .14, 1.28, .09, .01)); }
    put(walnutDark, rbox(7.5, 7.7, 1.06, 1.24, FZ + .05, FZ + .17, .02)); put(ceramic, (() => { const g = new T.CircleGeometry(.07, 24); g.translate(7.6, 1.15, FZ + .171); return g; })());
    put(coverM, sleeveGeo(7.88, 1.06 + .157, FZ + .07, -.08, 5, true)); put(paintM, (() => { const g = new T.PlaneGeometry(.12, .16); const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, (3 + uv.getX(i)) / 4, .5 + uv.getY(i) * .5); g.translate(7.3, 1.16, FZ + .13); return g; })()); put(gilt, rbox(7.23, 7.37, 1.06, 1.25, FZ + .115, FZ + .125, .004));
    shadow(7.6, FZ + .35, 1.5, .4, .5); }
  // 괘종시계 (8.73): 받침 · 몸통(유리문 — 시계추는 게임 코드) · 머리(문자판 · 바늘) · 꼭대기 장식
  { const CX = 8.73, CZ = WZ; put(walnutDark, wood(rbox(CX - .25, CX + .25, 0, .34, CZ, CZ + .3, .012))); put(walnut, wood(rbox(CX - .2, CX + .2, .34, 1.46, CZ, CZ + .26, .01)));
    put(fireBlack, box(CX - .13, CX + .13, .46, 1.34, CZ + .26, CZ + .262)); put(walnut, wood(rbox(CX - .16, CX + .16, .44, 1.36, CZ + .26, CZ + .3, .008))); put(clockGlass, box(CX - .12, CX + .12, .48, 1.32, CZ + .298, CZ + .3));
    put(walnutDark, wood(rbox(CX - .23, CX + .23, 1.46, 1.98, CZ, CZ + .31, .015))); put(walnut, wood(rbox(CX - .26, CX + .26, 1.98, 2.05, CZ, CZ + .33, .01)));
    put(gilt, lathe(CX, CZ + .16, 2.05, [[.0, 0], [.04, .01], [.02, .05], [.03, .07], [0, .12]], 12));
    const face = new T.CircleGeometry(.15, 40); const uv = face.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, (3 + uv.getX(i)) / 4, uv.getY(i) * .5); face.translate(CX, 1.72, CZ + .312); put(paintM, face);
    put(gilt, (() => { const g = new T.TorusGeometry(.155, .012, 8, 40); g.translate(CX, 1.72, CZ + .312); return g; })());
    for (const [l, a, w] of [[.09, -.9, .012], [.12, 2.2, .008]]) { const h = new T.BoxGeometry(w, l, .004); h.translate(0, l / 2, 0); h.rotateZ(a); h.translate(CX, 1.72, CZ + .318); put(blackM, h); }
    shadow(CX, CZ + .2, .7, .45, .55); }

  // =====================================================================
  // 버건디 벨벳 체스터필드 소파 — 충돌 상자 그대로 (좌면 · 등받이 · 팔걸이 · 다리 · 밑 18 cm)
  // =====================================================================
  { const base = W.colliders.find(c => c.tag === 'sofa' && Math.abs(c.min.y - .18) < .01), back = W.colliders.find(c => c.tag === 'sofa' && c.max.y > .8), arms = W.colliders.filter(c => c.tag === 'sofa' && Math.abs(c.max.y - .64) < .01), cush = W.colliders.filter(c => c.tag === 'sofa' && Math.abs(c.max.y - .48) < .01);
    put(velvetDark, rbox(base.min.x, base.max.x, base.min.y, base.max.y, base.min.z, base.max.z, .04, 3));
    put(walnutDark, wood(rbox(base.min.x + .01, base.max.x - .01, .18, .2, base.min.z + .01, base.max.z - .01, .006)));
    for (const c of cush) { const g = weld(new D.RoundedBoxGeometry(c.max.x - c.min.x, c.max.y - c.min.y, c.max.z - c.min.z, 4, .044)); g.translate((c.min.x + c.max.x) / 2, (c.min.y + c.max.y) / 2, (c.min.z + c.max.z) / 2); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const y = p.getY(i); if (y > c.max.y - .02) { const u = (p.getX(i) - c.min.x) / (c.max.x - c.min.x), v = (p.getZ(i) - c.min.z) / (c.max.z - c.min.z); p.setY(i, y + .006 * Math.sin(u * Math.PI) * Math.sin(v * Math.PI) - .004 * Math.exp(-(((u - .5) / .2) ** 2))); } } g.computeVertexNormals(); put(velvet, g);
      const pip = L.tube([[c.min.x + .01, c.max.y - .004, c.max.z - .002], [c.max.x - .01, c.max.y - .004, c.max.z - .002]], .006, 8, 6, false); put(velvetDark, pip); }
    // 등받이: 다이아몬드 터프팅 (단추 · 주름) + 둥근 윗단
    { const x0 = back.min.x, x1 = back.max.x, y0 = back.min.y, y1 = back.max.y, z0 = back.min.z, z1 = back.max.z, RR = (z1 - z0) / 2, g = rbox(x0, x1, y0, y1 - RR, z0, z1, .05, 3); put(velvet, g);
      const top = new T.CylinderGeometry(RR, RR, x1 - x0 - .04, 32); top.rotateZ(Math.PI / 2); top.translate((x0 + x1) / 2, y1 - RR, (z0 + z1) / 2); put(velvet, top);      // 둥근 윗단: 윗면 = 충돌 높이 0.86 (z 전체)
      for (const s of [-1, 1]) { const cap = new T.SphereGeometry(RR, 20, 12); cap.scale(.25, 1, 1); cap.translate((x0 + x1) / 2 + s * ((x1 - x0) / 2 - .02), y1 - RR, (z0 + z1) / 2); put(velvet, cap); }
      const face = new T.PlaneGeometry(x1 - x0 - .3, y1 - y0 - .22, 90, 30), p = face.attributes.position, bt = [];
      const cols = 12, rows = 3, bx = (x1 - x0 - .3) / cols, by = (y1 - y0 - .22) / rows;
      for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i); let dmin = 1e9; for (let r = 0; r <= rows; r++) for (let c = 0; c <= cols; c++) { if ((r + c) % 2) continue; const bxp = -((x1 - x0 - .3) / 2) + c * bx, byp = -((y1 - y0 - .18) / 2) + r * by; dmin = Math.min(dmin, Math.hypot(x - bxp, (y - byp) * 1.2)); } p.setZ(i, .018 * Math.min(1, dmin / .07) ** .7); }
      face.computeVertexNormals(); face.translate((x0 + x1) / 2, (y0 + y1 - .04) / 2 - .02, z1 + .002); put(velvet, face);
      for (let r = 0; r <= rows; r++) for (let c = 0; c <= cols; c++) { if ((r + c) % 2) continue; const b = L.blob(.011, .011, .007, () => 1, 8, 6); b.translate((x0 + x1) / 2 - ((x1 - x0 - .3) / 2) + c * bx, (y0 + y1 - .04) / 2 - .02 - ((y1 - y0 - .22) / 2) + r * by, z1 + .006); bt.push(b); }
      put(tuftM, L.merge(bt)); }
    // 팔걸이: 윗면 = 충돌 높이 (0.64) — 말린 팔걸이
    for (const c of arms) { const cx = (c.min.x + c.max.x) / 2, RA = (c.max.x - c.min.x) / 2; put(velvet, rbox(c.min.x, c.max.x, c.min.y, c.max.y - RA, c.min.z, c.max.z, .05, 3));
      const EX = 1.3;      // 말린 팔걸이: 가로로 조금 넓은 타원 롤 — 윗면이 팔걸이 폭 전체에서 충돌 높이(0.64)와 2 cm 안
      const r = new T.CylinderGeometry(RA, RA, c.max.z - c.min.z, 32); r.rotateX(Math.PI / 2); r.scale(EX, 1, 1); r.translate(cx, c.max.y - RA, (c.min.z + c.max.z) / 2); put(velvet, r);
      const sc = new T.CircleGeometry(RA * .97, 28); sc.scale(EX, 1, 1); sc.translate(cx, c.max.y - RA, c.max.z + .001); put(velvetDark, sc);
      const sp = new T.TorusGeometry(RA * .55, .007, 6, 24); sp.scale(EX, 1, 1); sp.translate(cx, c.max.y - RA, c.max.z + .003); put(tuftM, sp); }
    for (const c of W.colliders.filter(c => c.tag === 'sofaLeg')) put(walnutDark, leg((c.min.x + c.max.x) / 2, (c.min.z + c.max.z) / 2, c.max.y, .026));
    // 쿠션 두 개 (벨벳 · 체크) — 등받이에 기대어
    const pillow = (x, mat, rz) => { const g = L.blob(.15, .13, .05, d => 1 - .25 * Math.abs(d.x * d.y), 20, 14); g.rotateX(-.2); g.rotateZ(rz); g.translate(x, .6, -.25); put(mat, g); };
    pillow(4.52, velvetDark, -.15); pillow(5.76, plaidM, .12);
    // 소파 밑: 먼지 뭉치 · 굴러 들어간 연필 · 동전
    { const db = []; const Rs = L.rng(55); for (let i = 0; i < 9; i++) { const g = L.blob(.02 + Rs() * .02, .008 + Rs() * .008, .018 + Rs() * .015, d => 1 + .25 * Math.sin(d.x * 9 + d.z * 7), 12, 8); g.translate(4.3 + Rs() * 1.7, .006, -.45 + Rs() * .8); db.push(g); } put(dustBunny, L.merge(db));
      put(L.phys({ name: 'Lounge_Pencil', color: 0xd8a830, roughness: .5 }), (() => { const g = new T.CylinderGeometry(.004, .004, .17, 6); g.rotateZ(Math.PI / 2); g.rotateY(.6); g.translate(5.6, .004, .2); return g; })()); put(brass, cylY(4.8, -.1, 0, .002, .012)); }
    shadow(5.15, -.05, 2.5, 1.3, .8); }
  // 책 더미 두 개 (6.5–7.0, 18 → 36 cm 계단)
  stackBooks(COL('books', 6.64), 11); stackBooks(COL('books', 6.89), 12);
  // =====================================================================
  // 커피 테이블 (상판 43 cm) · 머그 · 책 · LP
  // =====================================================================
  { const c = COL('table', 7.6); put(walnut, wood(rbox(c.min.x, c.max.x, c.min.y, c.max.y, c.min.z, c.max.z, .012, 3)));
    put(walnutDark, wood(rbox(c.min.x + .03, c.max.x - .03, .33, c.min.y, c.min.z + .03, c.max.z - .03, .008)));
    put(walnut, wood(rbox(c.min.x + .025, c.max.x - .025, .345, .355, c.max.z - .032, c.max.z - .026, .003)));
    for (const l of W.colliders.filter(q => q.tag === 'tableLeg')) put(walnutDark, leg((l.min.x + l.max.x) / 2, (l.min.z + l.max.z) / 2, l.max.y, .026));
    const mug = W.colliders.find(q => !q.tag && Math.abs(q.min.x - 7.26) < .01 && q.min.y > .4); const mx = (mug.min.x + mug.max.x) / 2, mz = (mug.min.z + mug.max.z) / 2;
    put(ceramic, lathe(mx, mz, mug.min.y, [[.0, 0], [.036, 0], [.04, .006], [.04, .09], [.036, .09], [.035, .012], [0, .012]], 24)); put(L.phys({ name: 'Lounge_Coffee', color: 0x1a0c06, roughness: .1, clearcoat: 1 }), cylY(mx, mz, mug.min.y + .07, .002, .035));
    put(ceramic, (() => { const g = new T.TorusGeometry(.024, .007, 8, 16, Math.PI * 1.2); g.rotateZ(-Math.PI * .6); g.rotateY(Math.PI / 2); g.translate(mx + .042, mug.min.y + .048, mz); return g; })());
    put(L.phys({ name: 'Lounge_CoffeeRing', color: 0x2a1408, roughness: .6, transparent: true, opacity: .5 }), (() => { const g = new T.RingGeometry(.03, .036, 24); g.rotateX(-Math.PI / 2); g.translate(mx - .1, c.max.y + .0006, mz - .05); return g; })());
    const bc = COL('books', 7.985); stackBooks(bc, 5);
    put(coverM, (() => { const g = sleeveGeo(0, 0, 0, 0, 2, true); g.rotateX(-Math.PI / 2); g.rotateY(.2); g.translate(7.56, c.max.y + .003, -.06); return g; })());
    put(vinylM, cylY(7.66, -.08, c.max.y + .005, .002, .15, .15, 48)); put(labelM, (() => { const g = new T.CircleGeometry(.045, 32); g.rotateX(-Math.PI / 2); g.translate(7.66, c.max.y + .0072, -.08); return g; })());
    put(paperM, (() => { const g = new T.BoxGeometry(.21, .004, .28); g.rotateY(-.3); g.translate(7.18, c.max.y + .002, -.12); return g; })());
    shadow(7.6, 0, 1.5, .9, .75); }
  // 사이드 테이블 (70 cm) · 아래 선반의 책 · 테이블 램프(갓 = 게임 재질)
  { const c = COL('sideTable', 8.47); put(walnut, wood(rbox(c.min.x, c.max.x, c.min.y, c.max.y, c.min.z, c.max.z, .01, 3)));
    put(walnutDark, wood(rbox(c.min.x + .02, c.max.x - .02, c.min.y - .05, c.min.y, c.min.z + .02, c.max.z - .02, .006)));
    for (const l of W.colliders.filter(q => !q.tag && q.min.x > 8.2 && q.max.x < 8.75 && q.max.y > .6 && q.max.y < .67)) put(walnutDark, leg((l.min.x + l.max.x) / 2, (l.min.z + l.max.z) / 2, l.max.y, .02));
    const sh = W.colliders.find(q => !q.tag && Math.abs(q.min.y - .2) < .01 && q.min.x > 8.2 && q.max.x < 8.75); put(walnut, wood(rbox(sh.min.x, sh.max.x, sh.min.y, sh.max.y, sh.min.z, sh.max.z, .006)));
    const G = []; for (let i = 0; i < 3; i++) G.push(bookGeo(8.47, sh.max.y + .016 + i * .034, 0, .22, .032, .16, 0, (i - 1) * .3, 20 + i)); put(bookM, L.merge(G));
    const k = .72, x = 8.66, y = .7, z = -.17;
    put(ceramicG, lathe(x, z, y, [[.0, 0], [.04, 0], [.045, .01], [.055, .05], [.05, .09], [.02, .11], [.012, .118]], 20)); put(brass, cylY(x, z, y + .118, .045, .006));
    const s = L.lathe([[.085 * k, 0], [.083 * k, .01], [.05 * k, .11 * k], [.048 * k, .113 * k]], 28); s.translate(x, y + .15 * k, z); solo(shadeFallback, s, 'Lounge_TableLampShade', { ref: 'DR.shade' });
    put(cableM, L.tube([[x + .02, y + .005, z - .03], [x + .05, y + .002, z - .2], [x + .07, .4, -.3], [x + .02, .005, -.5], [8.3, .005, -1.2], [8.2, .1, -1.585]], .0035, 40, 6, false));
    shadow(8.47, 0, .7, .65, .65); }

  // =====================================================================
  // LP 캐비닛 · 턴테이블 · 데스크 램프 · 큰 스피커 · LP 상자 · LP 더미 · 오래된 케이블
  // =====================================================================
  { const c = COL('recCab', 12.4), x0 = c.min.x, x1 = c.max.x, z0 = WZ, z1 = c.max.z;
    put(walnut, wood(rbox(x0 - .02, x1 + .02, .74, .8, z0, z1 + .02, .012))); put(walnut, wood(rbox(x0, x0 + .04, .06, .74, z0, z1, .006))); put(walnut, wood(rbox(x1 - .04, x1, .06, .74, z0, z1, .006)));
    put(walnut, wood(rbox(12.38, 12.42, .06, .74, z0, z1 - .02, .006))); put(walnut, wood(rbox(x0, x1, .06, .1, z0, z1, .006))); put(walnutDark, wood(box(x0 + .04, x1 - .04, .1, .74, z0, z0 + .015)));
    for (const x of [x0 + .05, x1 - .05]) for (const z of [z0 + .05, z1 - .05]) put(walnutDark, leg(x, z, .06, .022));
    const Rs = L.rng(78), G = []; for (const [a, b] of [[x0 + .06, 12.36], [12.44, x1 - .06]]) for (let x = a; x < b; x += .0058 + Rs() * .0035) G.push(sleeveGeo(x, .1 + .158, -1.37, (Rs() - .5) * .05, (Rs() * 16) | 0)); put(coverM, L.merge(G));
    // 턴테이블: 받침 · 플래터 · 레코드 · 라벨 · 톤암 · 열린 먼지 덮개
    put(walnutDark, wood(rbox(11.6, 12.1, .8, .88, -1.52, -1.24, .012))); put(blackM, box(11.62, 12.08, .878, .882, -1.5, -1.26));
    put(chrome, cylY(11.82, -1.38, .882, .012, .148, .15, 48)); put(vinylM, cylY(11.82, -1.38, .894, .003, .147, .147, 64)); put(labelM, (() => { const g = new T.CircleGeometry(.046, 32); g.rotateX(-Math.PI / 2); g.translate(11.82, .8975, -1.38); return g; })());
    put(chrome, cylY(12.02, -1.27, .882, .03, .014)); put(chrome, L.tube([[12.02, .915, -1.27], [12.0, .918, -1.33], [11.93, .912, -1.4], [11.9, .905, -1.42]], .0032, 12, 6, false)); put(blackM, rbox(11.88, 11.91, .895, .905, -1.44, -1.41, .002));
    for (const [x, z] of [[11.66, -1.28], [12.06, -1.28]]) put(chrome, cylY(x, z, .882, .006, .008));
    put(glassM, (() => { const g = new T.BoxGeometry(.48, .004, .28); g.translate(0, 0, -.14); g.rotateX(-1.25); g.translate(11.85, .9, -1.52); return g; })());
    // 데스크 램프 (놋쇠 팔)
    put(brass, cylY(12.95, -1.4, .8, .02, .07)); put(brass, L.tube([[12.95, .82, -1.4], [12.97, 1.0, -1.38], [12.9, 1.12, -1.33]], .009, 12, 8, false));
    { const s = L.lathe([[.1, 0], [.095, .015], [.05, .12], [.045, .125]], 28); s.rotateZ(.5); s.translate(12.86, 1.1, -1.3); solo(shadeFallback, s, 'Lounge_DeskLampShade', { ref: 'shade' }); }
    // LP 위에 쌓인 LP 몇 장 · 작은 다육이
    { const G2 = []; for (let i = 0; i < 6; i++) { const g = sleeveGeo(0, 0, 0, 0, (i * 5) % 16, true); g.rotateX(-Math.PI / 2); g.rotateY((Rs() - .5) * .5); g.translate(13.2 + (Rs() - .5) * .03, .8 + .0025 + i * .0046, -1.38 + (Rs() - .5) * .03); G2.push(g); } put(coverM, L.merge(G2)); }
    put(ceramicG, lathe(12.55, -1.42, .8, [[.0, 0], [.04, 0], [.045, .06], [.042, .065]], 16));
    { const LV = []; for (let i = 0; i < 10; i++) { const a = i / 10 * TAU, l = L.blob(.008, .03, .008, () => 1, 8, 6); l.rotateZ(Math.cos(a) * .4); l.rotateX(Math.sin(a) * .4); l.translate(12.55 + Math.cos(a) * .015, .89, -1.42 + Math.sin(a) * .015); LV.push(L.color(l, 0x5a8a5a)); } put(leafM, L.merge(LV, ['position', 'normal', 'uv', 'color'])); }
    shadow(12.4, -1.38, 2.4, .6, .6); }
  // 큰 스피커 두 대 (월넛 몸통 · 검은 그릴 천 · 우퍼 2 · 미드 · 트위터)
  for (const x of [11.02, 13.78]) { const z0 = -1.58, z1 = -1.2, H = 1.12; put(walnut, wood(rbox(x - .2, x + .2, 0, H, z0, z1, .012)));
    put(grille, box(x - .175, x + .175, .08, H - .04, z1, z1 + .01)); put(walnutDark, wood(rbox(x - .2, x + .2, 0, .06, z0, z1 + .02, .006)));
    for (const [y, r] of [[.28, .13], [.56, .13], [.8, .07], [.98, .03]]) { put(coneM, L.lathe([[0, .0], [r * .3, .01], [r * .9, .02], [r, .022]], 28).rotateX(Math.PI / 2).translate(x, y, z1 + .012)); put(blackM, (() => { const g = new T.TorusGeometry(r, .008, 6, 28); g.translate(x, y, z1 + .033); return g; })()); put(chrome, (() => { const g = new T.SphereGeometry(r * .22, 12, 8, 0, TAU, 0, Math.PI / 2); g.rotateX(Math.PI / 2); g.translate(x, y, z1 + .012); return g; })()); }
    put(brass, rbox(x - .03, x + .03, H - .1, H - .085, z1 + .011, z1 + .014, .002)); shadow(x, -1.39, .6, .5, .6); }
  // 스피커 선 · 턴테이블 전원선 · 멀티탭 (바닥을 따라 오래된 케이블)
  put(cableM, L.tube([[11.02, .1, -1.585], [11.1, .006, -1.57], [11.4, .006, -1.15], [11.8, .006, -1.12], [12.2, .006, -1.14], [12.6, .006, -1.1], [13.2, .006, -1.15], [13.6, .006, -1.4], [13.7, .1, -1.585]], .0045, 80, 6, false));
  put(cableM, L.tube([[12.05, .82, -1.59], [12.1, .5, -1.595], [12.2, .1, -1.59], [12.6, .006, -1.0], [13.0, .006, -.95], [13.3, .006, -1.2]], .004, 60, 6, false));
  put(L.phys({ name: 'Lounge_PowerStrip', color: 0xd8d0c0, roughness: .5 }), rbox(13.22, 13.44, 0, .04, -1.26, -1.18, .01)); for (let i = 0; i < 4; i++) put(blackM, box(13.25 + i * .05, 13.28 + i * .05, .04, .042, -1.24, -1.2));
  put(cableM, L.tube([[13.3, .02, -1.22], [13.25, .006, -1.05], [13.4, .006, -.9], [13.6, .006, -.75], [13.62, .006, -.3], [13.58, .1, .06], [13.62, .7, .1]], .0035, 60, 6, false));
  // LP 상자 두 개 (배경) — 세워 꽂힌 LP
  for (const [x, z, seed] of [[12.4, -.92, 31], [12.85, -.97, 32]]) { put(walnutDark, wood(rbox(x - .19, x + .19, 0, .06, z - .19, z + .19, .008))); for (const [a, b, c2, d] of [[x - .19, x - .17, z - .19, z + .19], [x + .17, x + .19, z - .19, z + .19], [x - .19, x + .19, z - .19, z - .17]]) put(walnutDark, wood(box(a, b, .06, .3, c2, d))); put(walnutDark, wood(box(x - .19, x + .19, .06, .22, z + .17, z + .19)));
    const Rs = L.rng(seed), G = []; for (let k = 0; k < 40; k++) { const g = new T.BoxGeometry(.31, .31, .004), uv = g.attributes.uv, ci = (Rs() * 16) | 0; for (let i = 0; i < uv.count; i++) uv.setXY(i, ((ci % 4) + uv.getX(i)) / 4, 1 - (Math.floor(ci / 4) + 1 - uv.getY(i)) / 4); g.rotateX(-.08 + (Rs() - .5) * .06); g.translate(x + (Rs() - .5) * .01, .21, z - .16 + k * .008); G.push(g); } put(coverM, L.merge(G)); shadow(x, z, .55, .55, .6); }
  // LP 더미 · 책 (바닥 앞 · 뒤 — 낮게)
  const lpPile = (x, z, n, seed) => { const Rs = L.rng(seed), G = []; for (let i = 0; i < n; i++) { const g = sleeveGeo(0, 0, 0, 0, (Rs() * 16) | 0, true); g.rotateX(-Math.PI / 2); g.rotateY((Rs() - .5) * .8); g.translate(x + (Rs() - .5) * .04, .0025 + i * .0047, z + (Rs() - .5) * .04); G.push(g); } put(coverM, L.merge(G)); shadow(x, z, .45, .45, .45); };
  lpPile(2.1, .88, 3, 115); lpPile(12.0, .9, 8, 116); lpPile(.7, -1.0, 12, 117); lpPile(6.45, -.95, 5, 119); lpPile(13.0, .95, 4, 120);
  { const Rs = L.rng(113), G = []; for (let x = 3.55; x < 3.95; x += .012 + Rs() * .02) { const g = new T.BoxGeometry(.315, .315, .004), uv = g.attributes.uv, ci = (Rs() * 16) | 0; for (let i = 0; i < uv.count; i++) uv.setXY(i, ((ci % 4) + uv.getX(i)) / 4, 1 - (Math.floor(ci / 4) + 1 - uv.getY(i)) / 4); g.rotateY(Math.PI / 2); g.rotateZ(-(.12 + Rs() * .14)); g.translate(x, .155, -1.52 + Rs() * .02); G.push(g); } put(coverM, L.merge(G)); }
  { const G = []; let y = 0; const Rs = L.rng(111); for (let i = 0; i < 7; i++) { const h = .026 + Rs() * .03; G.push(bookGeo(2.72 + (Rs() - .5) * .03, y + h / 2, -1.35, .16 + Rs() * .1, h, .12 + Rs() * .08, 0, (Rs() - .5) * .5, 30 + i)); y += h; } y = 0; for (let i = 0; i < 4; i++) { const h = .03 + Rs() * .02; G.push(bookGeo(6.9 + (Rs() - .5) * .03, y + h / 2, .9, .2, h, .15, 0, (Rs() - .5) * .5, 40 + i)); y += h; } put(bookM, L.merge(G)); shadow(2.72, -1.35, .4, .3, .5); }
  // 큰 화분 (창 왼쪽 모퉁이): 테라코타 · 몬스테라 잎
  { const x = 9.0, z = -1.05; put(terracotta, lathe(x, z, 0, [[.0, 0], [.13, 0], [.15, .02], [.17, .3], [.18, .32], [.165, .32]], 24)); put(soil, cylY(x, z, .29, .01, .16));
    const Rs = L.rng(91), LV = [], ST = [];
    for (let i = 0; i < 9; i++) { const a = i / 9 * TAU + Rs() * .4, h = .5 + Rs() * .6, r = .15 + Rs() * .25, tip = V3(x + Math.cos(a) * r, .3 + h, z + Math.sin(a) * r * .7);
      ST.push(L.tube([[x + Math.cos(a) * .03, .3, z + Math.sin(a) * .03], [x + Math.cos(a) * r * .4, .3 + h * .6, z + Math.sin(a) * r * .3], tip.toArray()], .006, 10, 5, false));
      const sh = new T.Shape(); sh.moveTo(0, 0); sh.bezierCurveTo(-.2, .06, -.24, .34, 0, .44); sh.bezierCurveTo(.24, .34, .2, .06, 0, 0);
      for (let k = 0; k < 3; k++) { const hp = new T.Path(); hp.absellipse(-.09, .1 + k * .1, .03, .012, 0, TAU, false, .5); sh.holes.push(hp); const hp2 = new T.Path(); hp2.absellipse(.09, .14 + k * .1, .03, .012, 0, TAU, false, -.5); sh.holes.push(hp2); }
      const lg = new T.ShapeGeometry(sh, 10), p = lg.attributes.position; for (let k = 0; k < p.count; k++) p.setZ(k, -Math.abs(p.getX(k)) * .3 + p.getY(k) * p.getY(k) * .3);
      lg.computeVertexNormals(); const s = .7 + Rs() * .5; lg.scale(s, s, s); lg.rotateX(-.9 + Rs() * .5); lg.rotateY(-a + Math.PI / 2); lg.translate(tip.x, tip.y, tip.z); LV.push(L.color(lg, [0x2e5a2e, 0x3a6a34, 0x24502a][i % 3])); }
    put(leafM, L.merge(LV, ['position', 'normal', 'uv', 'color'])); put(L.phys({ name: 'Lounge_Stem', color: 0x3a5a2a, roughness: .6 }), L.merge(ST)); shadow(x, z, .7, .6, .6); }
  // 전화 탁자 (70 cm) · 다이얼 전화 · 꼬인 선 · 작은 램프
  { const c = COL('phoneTable', 13.5); put(walnut, wood(rbox(c.min.x, c.max.x, c.min.y, c.max.y, c.min.z, c.max.z, .01, 3))); put(walnutDark, wood(rbox(c.min.x + .02, c.max.x - .02, c.min.y - .05, c.min.y, c.min.z + .02, c.max.z - .02, .006)));
    for (const l of W.colliders.filter(q => !q.tag && q.min.x > 13.2 && q.max.x < 13.8 && q.max.y > .6 && q.max.y < .67)) put(walnutDark, leg((l.min.x + l.max.x) / 2, (l.min.z + l.max.z) / 2, l.max.y, .02));
    put(walnut, wood(rbox(13.3, 13.7, .22, .25, .07, .35, .006)));
    const ph = COL('phone', 13.38), px = 13.38, py = c.max.y, pz = .12;
    const base = new D.RoundedBoxGeometry(.2, .08, .17, 3, .03); base.translate(0, .04, 0); const dial = new T.CylinderGeometry(.05, .05, .01, 24); dial.rotateX(Math.PI / 2 - .5); dial.translate(0, .07, .06);
    const hs = new T.CapsuleGeometry(.025, .16, 4, 10); hs.rotateZ(Math.PI / 2); hs.translate(0, .1, 0); const cups = [-.09, .09].map(s => { const g = L.blob(.03, .022, .032, () => 1, 12, 8); g.translate(s, .1, 0); return g; });
    const PH = [base, hs, ...cups].map(g => { g.rotateY(.25); g.translate(px, py, pz); return g; }); put(bakelite, L.merge(PH)); dial.rotateY(.25); dial.translate(px, py, pz); put(ceramic, dial);
    const coil = []; for (let t = 0; t <= 1; t += 1 / 180) { const p = V3(13.3, .72, .1).lerp(V3(13.27, .45, .14), t); p.y += Math.sin(t * Math.PI) * -.05; coil.push(p.add(V3(Math.cos(t * 90) * .008, 0, Math.sin(t * 90) * .008))); } put(cableM, L.tube(coil, .0022, 180, 5, false));
    const lc = COL('lamp', 13.64); put(brass, cylY(13.64, .1, .7, .02, .045, .05)); put(brass, cylY(13.64, .1, .72, .14, .008)); const s = L.lathe([[.07, 0], [.068, .01], [.046, .09], [.045, .092]], 24); s.translate(13.64, .84, .1); solo(shadeFallback, s, 'Lounge_PhoneLampShade', { ref: 'shade' });
    shadow(13.5, .21, .7, .6, .6); }
  // 먼지 뭉치 (구석 · 캐비닛 밑)
  { const db = []; const Rs = L.rng(66); for (const [x, z, n] of [[.25, -1.5, 4], [13.85, -1.15, 3], [11.6, -1.12, 3], [2.6, -1.2, 2], [8.9, -1.25, 2], [13.9, .4, 3]]) for (let i = 0; i < n; i++) { const g = L.blob(.016 + Rs() * .02, .007 + Rs() * .006, .014 + Rs() * .014, d => 1 + .3 * Math.sin(d.x * 9 + d.z * 7), 10, 6); g.translate(x + (Rs() - .5) * .25, .005, z + (Rs() - .5) * .15); db.push(g); } put(dustBunny, L.merge(db)); }

  // ---------- 모으기 ----------
  for (const [mat, b] of B) { const geos = b.geos.map(g => { if (!g.attributes.uv) { g.setAttribute('uv', new T.Float32BufferAttribute(new Float32Array(g.attributes.position.count * 2), 2)); } if (!g.attributes.normal) g.computeVertexNormals(); return g; });
    const keys = ['position', 'normal', 'uv'].concat(geos.every(g => g.attributes.color) ? ['color'] : []); const m = new T.Mesh(L.merge(geos, keys), mat); m.name = b.name.replace('Lounge_', 'Lounge_') + '_Mesh'; m.castShadow = mat !== shadowM && mat !== dustM && mat !== stainM; m.receiveShadow = true; root.add(m); }
  scene.updateMatrixWorld(true);
  const bb = new T.Box3().setFromObject(root);
  const big = []; root.traverse(o => { if (o.isMesh) big.push([o.name, o.geometry.attributes.position.count, (o.geometry.index ? o.geometry.index.count : 0)]); }); big.sort((x, y) => y[1] - x[1]);
  const info = Object.assign({ top: big.slice(0, 16).map(x => x.join(':')), env: 'lounge', box: [bb.min.toArray().map(v => +v.toFixed(2)), bb.max.toArray().map(v => +v.toFixed(2))] }, L.stats(scene));
  const b64 = await L.export(scene, []);
  return { b64, info };
};
