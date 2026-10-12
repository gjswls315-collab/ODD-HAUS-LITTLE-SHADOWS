/* ODD HAUS GLB 제작 도구 — 공용 함수 (게임 페이지 안에서 실행: window.ODD2 · THREE 사용)
   리그 거울 노드(extras.link) · 단단한 부품 · 스킨 메시 · 클립 녹화 · GLB 내보내기 */
(() => {
  const O = window.ODD2, T = O.THREE, D = O.dev;
  const V3 = (x = 0, y = 0, z = 0) => new T.Vector3(x, y, z);
  const L = {};
  L.T = T; L.V3 = V3;
  // ---------- 재질 · 텍스처 ----------
  L.phys = o => new T.MeshPhysicalMaterial(o);
  L.canvas = (w, h, draw) => { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); return c; };
  L.tex = (canvas, o = {}) => { const t = new T.CanvasTexture(canvas); t.colorSpace = o.color === false ? T.NoColorSpace : T.SRGBColorSpace; t.wrapS = t.wrapT = o.wrap === false ? T.ClampToEdgeWrapping : T.RepeatWrapping; if (o.repeat) t.repeat.set(o.repeat[0], o.repeat[1]); t.userData.mimeType = o.jpeg ? 'image/jpeg' : 'image/png'; t.anisotropy = 4; t.needsUpdate = true; return t; };
  // 높이 함수(0..1) → 노멀맵 캔버스
  L.normalCanvas = (w, h, hf, strength = 2) => {
    const H = new Float32Array(w * h); for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) H[y * w + x] = hf(x / w, y / h, x, y);
    return L.canvas(w, h, (g) => { const id = g.createImageData(w, h), d = id.data; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const hx = H[y * w + (x + 1) % w] - H[y * w + (x - 1 + w) % w], hy = H[((y + 1) % h) * w + x] - H[((y - 1 + h) % h) * w + x]; let nx = -hx * strength, ny = -hy * strength, nz = 1; const l = Math.hypot(nx, ny, nz); const k = (y * w + x) * 4; d[k] = (nx / l * .5 + .5) * 255; d[k + 1] = (ny / l * .5 + .5) * 255; d[k + 2] = (nz / l * .5 + .5) * 255; d[k + 3] = 255; } g.putImageData(id, 0, 0); });
  };
  L.grayCanvas = (w, h, f) => L.canvas(w, h, (g) => { const id = g.createImageData(w, h), d = id.data; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const v = Math.max(0, Math.min(255, f(x / w, y / h, x, y) * 255)), k = (y * w + x) * 4; d[k] = d[k + 1] = d[k + 2] = v; d[k + 3] = 255; } g.putImageData(id, 0, 0); });
  L.rng = seed => { let a = seed | 0; return () => { a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; };
  // ---------- 지오메트리 ----------
  // 합치기 (위치 · 노멀 · uv · 색 · 스킨 속성, 인덱스 유지)
  L.merge = (geos, keys = ['position', 'normal', 'uv']) => {
    geos = geos.filter(Boolean).map(g => g.index ? g : g.toIndexed ? g : g);
    const ks = keys.filter(k => geos.every(g => g.attributes[k])), out = new T.BufferGeometry();
    for (const k of ks) { const sz = geos[0].attributes[k].itemSize, Ar = geos[0].attributes[k].array.constructor === Uint16Array || geos[0].attributes[k].array.constructor === Uint8Array ? geos[0].attributes[k].array.constructor : Float32Array; const arr = new Ar(geos.reduce((n, g) => n + g.attributes[k].count * sz, 0)); let o = 0; for (const g of geos) { const a = g.attributes[k]; for (let i = 0; i < a.count; i++) for (let j = 0; j < sz; j++) arr[o++] = a.getComponent(i, j); } out.setAttribute(k, new T.BufferAttribute(arr, sz, geos[0].attributes[k].normalized)); }
    const idx = []; let base = 0; for (const g of geos) { if (g.index) for (let i = 0; i < g.index.count; i++) idx.push(g.index.getX(i) + base); else for (let i = 0; i < g.attributes.position.count; i++) idx.push(i + base); base += g.attributes.position.count; }
    out.setIndex(idx); out.computeBoundingSphere(); return out;
  };
  L.xf = (g, { p = [0, 0, 0], r = [0, 0, 0], s = [1, 1, 1] } = {}) => { const m = new T.Matrix4().compose(V3(...p), new T.Quaternion().setFromEuler(new T.Euler(...r)), V3(...s)); g.applyMatrix4(m); return g; };
  L.color = (g, hex) => { const c = new T.Color(hex), n = g.attributes.position.count, a = new Float32Array(n * 3); for (let i = 0; i < n; i++) { a[i * 3] = c.r; a[i * 3 + 1] = c.g; a[i * 3 + 2] = c.b; } g.setAttribute('color', new T.BufferAttribute(a, 3)); return g; };
  // 구를 주물러 만든 덩어리 (f(dir) → 반지름 배율)
  L.blob = (rx, ry, rz, f = () => 1, ws = 40, hs = 28) => { const g = new T.SphereGeometry(1, ws, hs), p = g.attributes.position, v = V3(); for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i); const k = f(v.clone()); p.setXYZ(i, v.x * rx * k, v.y * ry * k, v.z * rz * k); } g.computeVertexNormals(); return g; };
  // 점들을 지나는 튜브 (반지름 함수 r(t)) — 끝 막음
  L.tube = (pts, rf, seg = 24, rad = 12, closed = true) => { const c = new T.CatmullRomCurve3(pts.map(p => Array.isArray(p) ? V3(...p) : p)); const g = new T.TubeGeometry(c, seg, 1, rad, false), p = g.attributes.position, nrm = g.attributes.normal; const ring = rad + 1; for (let i = 0; i <= seg; i++) { const t = i / seg, P = c.getPointAt(t), r = typeof rf === 'function' ? rf(t) : rf; for (let j = 0; j < ring; j++) { const k = i * ring + j; const n = V3().fromBufferAttribute(nrm, k); p.setXYZ(k, P.x + n.x * r, P.y + n.y * r, P.z + n.z * r); } } const parts = [g]; if (closed) { for (const e of [0, 1]) { const P = c.getPointAt(e), r = typeof rf === 'function' ? rf(e) : rf, s = new T.SphereGeometry(r, rad, 8); s.translate(P.x, P.y, P.z); parts.push(s); } } return L.merge(parts); };
  // 두 점 사이 캡슐
  L.capsule = (a, b, r, rad = 14, capSeg = 6) => { a = V3(...a); b = V3(...b); const d = b.clone().sub(a), len = d.length(), g = new T.CapsuleGeometry(r, Math.max(1e-4, len), capSeg, rad); g.applyQuaternion(new T.Quaternion().setFromUnitVectors(V3(0, 1, 0), d.normalize())); const m = a.clone().add(b).multiplyScalar(.5); g.translate(m.x, m.y, m.z); return g; };
  L.lathe = (pts, seg = 48, phi0 = 0, phiL = Math.PI * 2) => new T.LatheGeometry(pts.map(([r, y]) => new T.Vector2(r, y)), seg, phi0, phiL);
  L.rbox = (w, h, d, r = .002, seg = 3) => new D.RoundedBoxGeometry(w, h, d, seg, r);
  // 둥근 상자 (초타원체 — 인덱스 유지 · 가벼움): n이 클수록 모서리가 각진다
  L.sbox = (w, h, d, n = 6, ws = 20, hs = 14) => { const g = new T.SphereGeometry(1, ws, hs), p = g.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i), k = 1 / Math.pow(Math.abs(x) ** n + Math.abs(y) ** n + Math.abs(z) ** n, 1 / n); p.setXYZ(i, x * k * w / 2, y * k * h / 2, z * k * d / 2); } g.computeVertexNormals(); return g; };
  // 털: 타원체 표면에 가는 털 가닥(삼각 단면 · 3마디 · 끝은 뾰족)을 뭉치로 — 정점 색(뿌리는 어둡게), 노멀은 표면 쪽으로 기울여 부드럽게
  L.fur = o => {
    const R = L.rng(o.seed || 1), pos = [], nor = [], col = [], idx = [], n = o.n, c0 = V3(...o.c), rr = V3(...o.r), G = V3(...(o.down || [0, -1, 0])), flow = V3(...(o.flow || [0, 0, 0]));
    let made = 0, tries = 0; const tmpC = new T.Color();
    while (made < n && tries < n * 12) {
      tries++; const u = V3(R() * 2 - 1, R() * 2 - 1, R() * 2 - 1); if (u.lengthSq() > 1 || u.lengthSq() < 1e-4) continue; u.normalize();
      if (o.mask && !o.mask(u)) continue;
      const per = o.clump || 3;
      for (let c = 0; c < per && made < n; c++) {
        const uu = u.clone().add(V3(R() - .5, R() - .5, R() - .5).multiplyScalar(.14)).normalize();
        const base = V3(c0.x + uu.x * rr.x * (o.inset || .93), c0.y + uu.y * rr.y * (o.inset || .93), c0.z + uu.z * rr.z * (o.inset || .93));
        const nrm = V3(uu.x / rr.x, uu.y / rr.y, uu.z / rr.z).normalize();
        const flowT = flow.clone().addScaledVector(nrm, -flow.dot(nrm)), Gt = G.clone().addScaledVector(nrm, -G.dot(nrm)).multiplyScalar(.85).addScaledVector(G, .15);     // 결 · 처짐은 표면을 따라 (털이 몸속으로 파고들지 않게)
        const dir = nrm.clone().multiplyScalar(o.lift ?? 1).addScaledVector(flowT, o.flowK || 0).add(V3(R() - .5, R() - .5, R() - .5).multiplyScalar(o.jit ?? .35)).normalize();
        const len = (o.len[0] + (o.len[1] - o.len[0]) * R()) * (o.lenF ? o.lenF(uu) : 1), w = (o.w || .0026) * (.7 + R() * .6), droop = (o.droop ?? .8) * (.7 + R() * .6);
        tmpC.setHex(typeof o.color === 'function' ? o.color(uu, R) : o.color); const br = .88 + R() * .24;
        const SG = o.segs || 3, pts = Array.from({ length: SG + 1 }, (_, q) => q / SG).map(t => base.clone().addScaledVector(dir, len * t).addScaledVector(Gt, droop * len * t * t));
        const b0 = pos.length / 3;
        for (let k = 0; k < SG; k++) { const t = k / SG, a = pts[k], tg = pts[k + 1].clone().sub(a).normalize(); let sx = V3().crossVectors(tg, V3(0, 1, 0)); if (sx.lengthSq() < 1e-4) sx.set(1, 0, 0); sx.normalize(); const sz = V3().crossVectors(sx, tg).normalize(), wt = w * Math.pow(1 - t, .7);
          for (let j = 0; j < 3; j++) { const ang = j / 3 * Math.PI * 2, rd = sx.clone().multiplyScalar(Math.cos(ang)).addScaledVector(sz, Math.sin(ang)); pos.push(a.x + rd.x * wt, a.y + rd.y * wt, a.z + rd.z * wt); const nn = nrm.clone().multiplyScalar(.75).addScaledVector(rd, .35).normalize(); nor.push(nn.x, nn.y, nn.z); const sh = (.62 + .38 * t) * br; col.push(tmpC.r * sh, tmpC.g * sh, tmpC.b * sh); } }
        pos.push(pts[SG].x, pts[SG].y, pts[SG].z); nor.push(nrm.x, nrm.y, nrm.z); col.push(tmpC.r * br * 1.04, tmpC.g * br * 1.04, tmpC.b * br * 1.04);
        for (let k = 0; k < SG - 1; k++) for (let j = 0; j < 3; j++) { const a = b0 + k * 3 + j, b = b0 + k * 3 + (j + 1) % 3, c2 = a + 3, d = b + 3; idx.push(a, c2, b, b, c2, d); }
        const tb = b0 + (SG - 1) * 3; for (let j = 0; j < 3; j++) idx.push(tb + j, tb + 3, tb + (j + 1) % 3);
        made++;
      }
    }
    const g = new T.BufferGeometry(); g.setAttribute('position', new T.Float32BufferAttribute(pos, 3)); g.setAttribute('normal', new T.Float32BufferAttribute(nor, 3)); g.setAttribute('color', new T.Float32BufferAttribute(col, 3)); g.setIndex(idx); g.computeBoundingSphere(); return g;
  };
  // ---------- 리그 거울 노드 ----------
  // rigRoot 아래 userData.rig가 붙은 객체들을 같은 계층 · 같은 로컬 변환의 노드로 복제 (노드 extras.link = 리그 이름)
  L.mirror = (rigRoot, prefix, boneNames = new Set()) => {
    const map = {}, list = [];
    const make = o => {
      if (map[o.userData.rig]) return map[o.userData.rig];
      const name = o.userData.rig, isBone = boneNames.has(name), n = isBone ? new T.Bone() : new T.Object3D();
      n.name = prefix + '_' + name.replace(/[^A-Za-z0-9_]/g, '_'); n.userData = { link: name };
      n.position.copy(o.position); n.quaternion.copy(o.quaternion); n.scale.copy(o.scale);
      map[name] = n; list.push([o, n]);
      if (o !== rigRoot) { let p = o.parent; while (p && !p.userData.rig) p = p.parent; if (p) make(p).add(n); }
      return n;
    };
    rigRoot.traverse(o => { if (o.userData.rig) make(o); });
    return { root: map[rigRoot.userData.rig], map, list };
  };
  // 스킨 메시: geometry(묶음 자세의 내보내기 공간 좌표) + 뼈 목록 + 정점마다 (뼈 번호, 가중치) 함수
  L.skinned = (geo, mat, bones, weightFn) => {
    const n = geo.attributes.position.count, si = new Uint16Array(n * 4), sw = new Float32Array(n * 4), p = V3();
    for (let i = 0; i < n; i++) { p.fromBufferAttribute(geo.attributes.position, i); const ws = weightFn(p, i).filter(w => w[1] > 1e-4).sort((a, b) => b[1] - a[1]).slice(0, 4); let s = ws.reduce((a, w) => a + w[1], 0) || 1; ws.forEach((w, j) => { si[i * 4 + j] = w[0]; sw[i * 4 + j] = w[1] / s; }); }
    geo.setAttribute('skinIndex', new T.BufferAttribute(si, 4)); geo.setAttribute('skinWeight', new T.BufferAttribute(sw, 4));
    const m = new T.SkinnedMesh(geo, mat); m.frustumCulled = false;
    return { mesh: m, bind: () => { bones.forEach(b => b.updateMatrixWorld(true)); m.bind(new T.Skeleton(bones), new T.Matrix4()); } };
  };
  // ---------- 클립 녹화: 리그를 실제 애니메이션 함수로 움직이며 거울 노드의 로컬 변환을 기록 ----------
  L.record = (name, mir, frames, step, fps = 30) => {
    const data = mir.list.map(([o, n]) => ({ o, n, t: [], p: [], q: [], s: [] }));
    for (let f = 0; f < frames; f++) { step(f, f / fps); for (const d of data) { d.t.push(f / fps); d.p.push(...d.o.position.toArray()); d.q.push(...d.o.quaternion.toArray()); d.s.push(...d.o.scale.toArray()); } }
    const tracks = [], same = (arr, sz) => { for (let i = sz; i < arr.length; i++) if (Math.abs(arr[i] - arr[i % sz]) > 1e-6) return false; return true; };
    for (const d of data) {
      // 변하지 않는 값도 키 2개로 넣는다 — 클립만 재생해도(다른 클립 다음에도) 자세 전체가 정해지도록
      const tk = (Tr, prop, arr, sz) => same(arr, sz) ? new Tr(d.n.name + prop, [0, d.t[d.t.length - 1]], arr.slice(0, sz).concat(arr.slice(0, sz))) : new Tr(d.n.name + prop, d.t, arr);
      tracks.push(tk(T.VectorKeyframeTrack, '.position', d.p, 3), tk(T.QuaternionKeyframeTrack, '.quaternion', d.q, 4), tk(T.VectorKeyframeTrack, '.scale', d.s, 3));
    }
    return new T.AnimationClip(name, (frames - 1) / fps, tracks);
  };
  // 리그 로컬 변환 저장/복원 (녹화 뒤 묶음 자세로 되돌리기)
  L.snap = mir => mir.list.map(([o]) => [o, o.position.clone(), o.quaternion.clone(), o.scale.clone()]);
  L.restore = sn => sn.forEach(([o, p, q, s]) => { o.position.copy(p); o.quaternion.copy(q); o.scale.copy(s); });
  // ---------- 내보내기 ----------
  L.export = async (scene, clips) => {
    const { GLTFExporter } = await import('three/addons/exporters/GLTFExporter.js');
    scene.updateMatrixWorld(true);
    const buf = await new Promise((res, rej) => new GLTFExporter().parse(scene, res, rej, { binary: true, animations: clips, onlyVisible: false, maxTextureSize: 2048 }));
    const a = new Uint8Array(buf); let s = ''; const CH = 0x8000; for (let i = 0; i < a.length; i += CH) s += String.fromCharCode.apply(null, a.subarray(i, i + CH));
    return btoa(s);
  };
  L.stats = scene => { let meshes = 0, tris = 0, verts = 0, bones = new Set(), mats = new Set(); scene.traverse(o => { if (o.isMesh) { meshes++; const g = o.geometry; verts += g.attributes.position.count; tris += (g.index ? g.index.count : g.attributes.position.count) / 3; [].concat(o.material).forEach(m => mats.add(m)); if (o.isSkinnedMesh) o.skeleton.bones.forEach(b => bones.add(b)); } }); return { meshes, tris: Math.round(tris), verts, bones: bones.size, materials: mats.size }; };
  window.GLBA = L;
})();
