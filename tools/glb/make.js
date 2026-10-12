// ODD HAUS GLB 제작 실행기: node make.js <게임 build.html> <작업 스크립트.js> <출력.glb> [three 패키지 폴더]
// 게임을 헤드리스 브라우저로 열고(리그 · 재질을 그대로 쓰려고), lib.js + 작업 스크립트를 넣어 모델을 만든 뒤 GLB로 저장한다.
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
(async () => {
  const [game, job, out, pkgArg] = process.argv.slice(2);
  const pkg = pkgArg || process.env.THREE_PKG || path.join(__dirname, '..', 'npmtmp', 'package');
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await (await browser.newContext({ viewport: { width: 960, height: 540 } })).newPage();
  const errs = []; page.on('pageerror', e => errs.push(e.message)); page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
  await page.route('https://cdn.jsdelivr.net/**', r => { const u = new URL(r.request().url()); const f = path.join(pkg, u.pathname.replace('/npm/three@0.160.0/', '')); if (!fs.existsSync(f)) return r.abort(); r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(f) }); });
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.fulfill({ status: 200, contentType: 'text/css', body: '' }));
  await page.goto('file://' + path.resolve(game), { waitUntil: 'commit' });
  await page.waitForFunction(() => window.ODD2 && ODD2.RT.state === 'title', null, { timeout: 240000, polling: 500 });
  await page.evaluate(() => { ODD2.RT.noLoop = true; });
  await page.addScriptTag({ content: fs.readFileSync(path.join(__dirname, 'lib.js'), 'utf8') });
  await page.addScriptTag({ content: fs.readFileSync(path.resolve(job), 'utf8') });
  if (errs.length) console.log('PAGE MESSAGES (before job)', errs.slice(0, 8).join('\n'));
  const r = await page.evaluate(async () => { const res = await window.GLBA_JOB(); return res; });
  fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
  fs.writeFileSync(out, Buffer.from(r.b64, 'base64'));
  const info = Object.assign({}, r.info, { file: out, bytes: fs.statSync(out).size });
  console.log(JSON.stringify(info, null, 1));
  if (errs.length) console.log('PAGE MESSAGES', errs.length, errs.slice(0, 12).join('\n'));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
