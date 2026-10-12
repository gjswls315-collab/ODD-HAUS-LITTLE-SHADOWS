// 자산 상태표 만들기: node tools/glb/status.js [측정.json] [상태.json] > docs/ASSET_STATUS.md
// 저장소에 실제로 있는 GLB 파일만 '완료'로 쓴다. 없으면 '미완성 (PLACEHOLDER)'.
// 측정.json = ?visualtest=1의 ODD2.VT.measure() 결과, 상태.json = 게임의 ODD2.ASSET_STATE (둘 다 선택).
// 파일이 있어도 게임이 쓰지 않으면(비율 탈락 rejected · 불러오기 오류 error) '완료'가 아니다.
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const measure = process.argv[2] && fs.existsSync(process.argv[2]) ? JSON.parse(fs.readFileSync(process.argv[2], 'utf8')) : [];
const M = Object.fromEntries(measure.map(m => [m.id, m]));
const ST = process.argv[3] && fs.existsSync(process.argv[3]) ? JSON.parse(fs.readFileSync(process.argv[3], 'utf8')) : {};
const state = (ok, I, used) => !ok ? null : I.bad ? '파일 불량 (' + I.bad + ')' : used && used !== 'glb' ? '파일 있음 · 게임 미사용 (' + used + ')' : null;
const chars = [['vin', 'Vin', 'assets/characters/vin/chr_vin.glb', '24 cm'], ['picker', 'Picker', 'assets/characters/picker/chr_picker.glb', '23 cm'], ['aa', 'A.A.', 'assets/characters/aa/chr_aa.glb', '28 cm'], ['locke', 'Locke', 'assets/characters/locke/chr_locke.glb', '30 cm'], ['rex', 'Rex', 'assets/characters/rex/chr_rex.glb', '35 cm'], ['buddy', 'Buddy', 'assets/characters/buddy/npc_buddy.glb', '어깨 33 cm'], ['bully', 'Bully', 'assets/characters/bully/enemy_bully.glb', '150 cm'], ['mrOdd', 'Mr. ODD', 'assets/characters/mr-odd/boss_mr_odd.glb', '180 cm']];
const envs = [['lounge', '01 LOUNGE (거실 방)', 'assets/environment/lounge/env_lounge.glb'], ['lp-library', '02 LP LIBRARY', 'assets/environment/lp-library/env_lp_library.glb'], ['studio', '03 STUDIO', 'assets/environment/studio/env_studio.glb'], ['dj-booth', '04 DJ BOOTH', 'assets/environment/dj-booth/env_dj_booth.glb'], ['terrace', '05 TERRACE', 'assets/environment/terrace/env_terrace.glb'], ['locked-room', '06 LOCKED ROOM', 'assets/environment/locked-room/env_locked_room.glb']];
function glbInfo(f) {
  const b = fs.readFileSync(f); if (b.readUInt32LE(0) !== 0x46546c67) return { bad: 'glTF 머리글 아님' };
  const jl = b.readUInt32LE(12), J = JSON.parse(b.slice(20, 20 + jl).toString()), acc = J.accessors || [];
  let verts = 0, tris = 0; for (const m of J.meshes || []) for (const p of m.primitives) { verts += acc[p.attributes.POSITION].count; tris += (p.indices !== undefined ? acc[p.indices].count : acc[p.attributes.POSITION].count) / 3; }
  return { bytes: b.length, verts, tris: Math.round(tris), clips: (J.animations || []).map(a => a.name), skins: (J.skins || []).length, images: (J.images || []).length };
}
const kb = n => (n / 1024 / 1024).toFixed(2) + ' MB';
const out = [];
out.push('# 자산 상태 (저장소의 실제 파일 기준)', '', '> 이 표는 `node tools/glb/status.js`가 저장소에 **실제로 있는 GLB 파일**을 읽어 만든다. 손으로 "완료"를 적지 않는다.', '> 파일이 없으면 미완성이다 — 게임은 코드로 만든 PLACEHOLDER를 쓰고, PLACEHOLDER는 완성품으로 세지 않는다.', '');
out.push('## 캐릭터', '', '| 캐릭터 | 상태 | 파일 | 크기 | 정점 · 삼각형 | 클립 | 기준 키 | 게임 실측 |', '|---|---|---|---|---|---|---|---|');
for (const [id, name, rel, tgt] of chars) {
  const f = path.join(ROOT, rel), ok = fs.existsSync(f), I = ok ? glbInfo(f) : null, m = M[id];
  const meas = m ? (m.file != null ? `파일 ${(m.file * 100).toFixed(1)} cm · 화면 ${(m.measured * 100).toFixed(1)} cm (±${(m.dev * 100).toFixed(1)}%)` : `PLACEHOLDER ${(m.measured * 100).toFixed(1)} cm`) : '—';
  const used = (m && m.state) || ST['chr:' + id], bad = state(ok, I, used);
  out.push(`| ${name} | ${!ok ? '미완성 (PLACEHOLDER)' : bad ? '미완성 — ' + bad : '**완료 (GLB)**' + (used === 'glb' ? ' · 게임 사용 확인' : '')} | \`${rel}\`${ok ? '' : ' — 없음'} | ${ok ? kb(I.bytes) : '—'} | ${ok ? I.verts.toLocaleString() + ' · ' + I.tris.toLocaleString() : '—'} | ${ok && I.clips.length ? I.clips.join(', ') : '—'} | ${tgt} | ${meas} |`);
}
out.push('', '## 환경', '', '| 스테이지 | 상태 | 파일 | 크기 | 정점 · 삼각형 |', '|---|---|---|---|---|');
for (const [id, name, rel] of envs) { const f = path.join(ROOT, rel), ok = fs.existsSync(f), I = ok ? glbInfo(f) : null, used = ST['env:' + id], bad = state(ok, I, used); out.push(`| ${name} | ${!ok ? '미완성 (코드 그레이박스 · PLACEHOLDER)' : bad ? '미완성 — ' + bad : '**완료 (GLB)**' + (used === 'glb' ? ' · 게임 사용 확인' : '')} | \`${rel}\`${ok ? '' : ' — 없음'} | ${ok ? kb(I.bytes) : '—'} | ${ok ? I.verts.toLocaleString() + ' · ' + I.tris.toLocaleString() : '—'} |`); }
out.push('', `만든 날: ${new Date().toISOString().slice(0, 10)}`);
console.log(out.join('\n'));
