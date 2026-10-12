// GLB 단독 확인: node view.js file.glb out.png [clip] [time] [zoom] — GLTFLoader로 읽어 정면 · 측면 · 뒷면 · 3/4 (+ 클립 한 프레임)
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
(async () => {
  const [file, out, clip = '', time = '0', zoom = '1', yoff = '0'] = process.argv.slice(2);
  const pkg = process.env.THREE_PKG || path.join(__dirname, '..', 'npmtmp', 'package');
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1600, height: 560 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.route('https://cdn.jsdelivr.net/**', r => { const u = new URL(r.request().url()); r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(pkg, u.pathname.replace('/npm/three@0.160.0/', ''))) }); });
  await p.route('http://glb.local/model.glb', r => r.fulfill({ status: 200, contentType: 'model/gltf-binary', body: fs.readFileSync(file) }));
  await p.route('http://glb.local/', r => r.fulfill({ status: 200, contentType: 'text/html', body: `<!doctype html><body style="margin:0;background:#1d1c1a"><script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
  <script type="module">
  import * as THREE from 'three'; import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'; import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
  const R = new THREE.WebGLRenderer({ antialias: true }); R.setSize(1600, 560); R.toneMapping = THREE.ACESFilmicToneMapping; R.outputColorSpace = THREE.SRGBColorSpace; document.body.appendChild(R.domElement);
  const S = new THREE.Scene(); S.background = new THREE.Color(0x24221f); const pm = new THREE.PMREMGenerator(R); S.environment = pm.fromScene(new RoomEnvironment(), .04).texture;
  S.add(new THREE.HemisphereLight(0xfff0dc, 0x2a2018, .7)); const k = new THREE.DirectionalLight(0xffe2c0, 2.6); k.position.set(-2, 3, 4); S.add(k); const rim = new THREE.DirectionalLight(0x9fb4ff, 2.2); rim.position.set(3, 2.5, -4); S.add(rim); const f = new THREE.DirectionalLight(0xffc890, .8); f.position.set(3, 1, 3); S.add(f);
  const g = await new GLTFLoader().loadAsync('http://glb.local/model.glb'); const M = g.scene; S.add(M);
  window.INFO = { clips: g.animations.map(a => a.name + '(' + a.duration.toFixed(2) + 's)') };
  const want = ${JSON.stringify(clip)}; if (want) { const c = g.animations.find(a => a.name === want); if (c) { const mx = new THREE.AnimationMixer(M); mx.clipAction(c).play(); mx.update(${+time}); } }
  M.updateMatrixWorld(true); const bb = new THREE.Box3(); M.traverse(o => { if (o.isMesh) { o.geometry.computeBoundingBox(); bb.union(o.geometry.boundingBox.clone().applyMatrix4(o.isSkinnedMesh ? new THREE.Matrix4() : o.matrixWorld)); } });
  const h = bb.max.y - bb.min.y, cy = (bb.max.y + bb.min.y) / 2 + ${+yoff}, sz = Math.max(h, Math.max(bb.max.x - bb.min.x, bb.max.z - bb.min.z) * 1.3) / ${+zoom}, d = sz * 1.15 / 2 / Math.tan(13 * Math.PI / 180);
  window.INFO.h = +h.toFixed(4); window.INFO.box = [bb.min.toArray().map(v => +v.toFixed(3)), bb.max.toArray().map(v => +v.toFixed(3))];
  const cam = new THREE.PerspectiveCamera(26, 400 / 560, .005, 50); R.setScissorTest(true); R.autoClear = false; R.clear();
  [0, Math.PI / 2, Math.PI, .6].forEach((a, i) => { R.setViewport(i * 400, 0, 400, 560); R.setScissor(i * 400, 0, 400, 560); cam.position.set(Math.sin(a) * d, cy + h * .04, Math.cos(a) * d); cam.lookAt(0, cy, 0); R.clear(); R.render(S, cam); });
  window.DONE = true;
  </script></body>` }));
  await p.goto('http://glb.local/'); await p.waitForFunction(() => window.DONE || window.onerror, null, { timeout: 120000 });
  console.log(JSON.stringify(await p.evaluate(() => window.INFO)), errs.length ? 'ERR ' + errs.slice(0, 3).join(' | ') : '');
  await p.screenshot({ path: out }); await b.close();
})().catch(e => { console.error(e); process.exit(1); });
