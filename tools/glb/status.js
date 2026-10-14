// 자산 상태표 만들기: node tools/glb/status.js [측정.json] [상태.json] > docs/ASSET_STATUS.md
// 저장소에 실제로 있는 GLB 파일 · 게임 사용 여부 · 사용자 승인 기록(assets/APPROVED.json)으로 상태를 쓴다. 손으로 "완료"를 적지 않는다.
//   파일 없음                 → 미완성 (PLACEHOLDER)
//   파일 있음 · 승인 기록 없음 → PROTOTYPE   (게임이 쓰는지 · 리뷰 후보인지 함께 적는다)
//   파일 있음 · 승인 기록 있음 → FINAL (승인 날짜) — 기록에 partial이 있으면 'PROTOTYPE + 부분 승인' (한 파일 안 일부만 승인된 디자인)
// 측정.json = ?visualtest=1의 ODD2.VT.measure() 결과, 상태.json = 게임의 ODD2.ASSET_STATE (둘 다 선택).
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const measure = process.argv[2] && fs.existsSync(process.argv[2]) ? JSON.parse(fs.readFileSync(process.argv[2], 'utf8')) : [];
const M = Object.fromEntries(measure.map(m => [m.id, m]));
const ST = process.argv[3] && fs.existsSync(process.argv[3]) ? JSON.parse(fs.readFileSync(process.argv[3], 'utf8')) : {};
const APPROVED = (() => { const f = path.join(ROOT, 'assets', 'APPROVED.json'); try { return JSON.parse(fs.readFileSync(f, 'utf8')).approved || {}; } catch (e) { return {}; } })();
const chars = [['vin', 'Vin', 'assets/characters/vin/chr_vin.glb', '24 cm', 'assets/review/chr_vin_review.glb'], ['picker', 'Picker', 'assets/characters/picker/chr_picker.glb', '23 cm'], ['aa', 'A.A.', 'assets/characters/aa/chr_aa.glb', '28 cm'], ['locke', 'Locke', 'assets/characters/locke/chr_locke.glb', '30 cm'], ['rex', 'Rex', 'assets/characters/rex/chr_rex.glb', '35 cm'], ['buddy', 'Buddy', 'assets/characters/buddy/npc_buddy.glb', '어깨 33 cm', 'assets/review/npc_buddy_review.glb'], ['bully', 'Bully', 'assets/characters/bully/enemy_bully.glb', '150 cm', 'assets/review/enemy_bully_review.glb'], ['mrOdd', 'Mr. ODD', 'assets/characters/mr-odd/boss_mr_odd.glb', '180 cm']];
const envs = [['lounge', '01 LOUNGE (거실 방)', 'assets/environment/lounge/env_lounge.glb', 'assets/review/env_lounge_section_review.glb'], ['lp-library', '02 LP LIBRARY', 'assets/environment/lp-library/env_lp_library.glb'], ['studio', '03 STUDIO', 'assets/environment/studio/env_studio.glb'], ['dj-booth', '04 DJ BOOTH', 'assets/environment/dj-booth/env_dj_booth.glb'], ['terrace', '05 TERRACE', 'assets/environment/terrace/env_terrace.glb'], ['locked-room', '06 LOCKED ROOM', 'assets/environment/locked-room/env_locked_room.glb']];
function glbInfo(f) {
  const b = fs.readFileSync(f); if (b.readUInt32LE(0) !== 0x46546c67) return { bad: 'glTF 머리글 아님' };
  const jl = b.readUInt32LE(12), J = JSON.parse(b.slice(20, 20 + jl).toString()), acc = J.accessors || [];
  let verts = 0, tris = 0; for (const m of J.meshes || []) for (const p of m.primitives) { verts += acc[p.attributes.POSITION].count; tris += (p.indices !== undefined ? acc[p.indices].count : acc[p.attributes.POSITION].count) / 3; }
  return { bytes: b.length, verts, tris: Math.round(tris), clips: (J.animations || []).map(a => a.name), images: (J.images || []).length };
}
const kb = n => (n / 1024 / 1024).toFixed(2) + ' MB';
function status(rel, used) {
  const f = path.join(ROOT, rel); if (!fs.existsSync(f)) return { ok: false, text: '미완성 (PLACEHOLDER)' };
  const I = glbInfo(f); if (I.bad) return { ok: true, I, text: '불량 — ' + I.bad };
  if (APPROVED[rel] && APPROVED[rel].partial) return { ok: true, I, text: `PROTOTYPE + **부분 승인** (${APPROVED[rel].date || ''}: ${APPROVED[rel].partial})` };   // v3.0: 한 파일 안에서 일부만 승인된 디자인 (거실)
  if (APPROVED[rel]) return { ok: true, I, text: `**FINAL** (승인 ${APPROVED[rel].date || ''})` };
  const into = Object.keys(APPROVED).find(k => APPROVED[k].from === rel);      // v3.0: 승인돼 게임 파일로 반영된 리뷰 후보
  if (into) return { ok: true, I, text: `리뷰 후보 · 승인 ${APPROVED[into].date || ''} → 게임 파일 \`${into}\`` };
  const where = rel.startsWith('assets/review/') ? '리뷰 후보 · 게임 미사용' : used === 'glb' ? '게임 사용 중' : used ? '게임 미사용 (' + used + ')' : '게임 경로';
  return { ok: true, I, text: `PROTOTYPE (${where} · 승인 전)` };
}
const out = [];
out.push('# 자산 상태 (저장소의 실제 파일 기준)', '',
  '> `node tools/glb/status.js`가 저장소에 **실제로 있는 GLB 파일**, 게임 사용 여부, 사용자 승인 기록(`assets/APPROVED.json`)으로 만든다. 손으로 "완료"를 적지 않는다.',
  '> **FINAL = 실루엣 · 조형된 메시 · 의도된 토폴로지 · 재질 디테일 · 믿을 만한 천/금속/나무/털 · 도형 조립이 안 보임 + 사용자 승인.** 승인 전은 모두 PROTOTYPE.',
  '> 파일이 없으면 미완성 — 게임은 코드로 만든 PLACEHOLDER를 쓰고, PLACEHOLDER는 완성품으로 세지 않는다.', '');
out.push('## 캐릭터', '', '| 캐릭터 | 지금 게임 (게임 경로) | 크기 · 삼각형 | 리뷰 후보 (assets/review) | 크기 · 삼각형 | 기준 | 게임 실측 |', '|---|---|---|---|---|---|---|');
for (const [id, name, rel, tgt, rv] of chars) {
  const m = M[id], used = (m && m.state) || ST['chr:' + id];
  const a = status(rel, used), b = rv ? status(rv) : null;
  const meas = m ? (m.file != null ? `파일 ${(m.file * 100).toFixed(1)} · 화면 ${(m.measured * 100).toFixed(1)} cm` : `PLACEHOLDER ${(m.measured * 100).toFixed(1)} cm`) : '—';
  out.push(`| ${name} | ${a.text}<br>\`${rel}\`${a.ok ? '' : ' — 없음'} | ${a.ok ? kb(a.I.bytes) + ' · ' + a.I.tris.toLocaleString() : '—'} | ${b ? b.text + '<br>`' + rv + '`' + (b.ok ? '' : ' — 없음') : '—'} | ${b && b.ok ? kb(b.I.bytes) + ' · ' + b.I.tris.toLocaleString() : '—'} | ${tgt} | ${meas} |`);
}
out.push('', '## 환경', '', '| 스테이지 | 지금 게임 (게임 경로) | 크기 · 삼각형 | 리뷰 후보 (assets/review) | 크기 · 삼각형 |', '|---|---|---|---|---|');
for (const [id, name, rel, rv] of envs) {
  const a = status(rel, ST['env:' + id]), b = rv ? status(rv) : null;
  out.push(`| ${name} | ${a.ok ? a.text : '미완성 (코드 그레이박스 · PLACEHOLDER)'}<br>\`${rel}\`${a.ok ? '' : ' — 없음'} | ${a.ok ? kb(a.I.bytes) + ' · ' + a.I.tris.toLocaleString() : '—'} | ${b ? b.text + '<br>`' + rv + '`' + (b.ok ? '' : ' — 없음') : '—'} | ${b && b.ok ? kb(b.I.bytes) + ' · ' + b.I.tris.toLocaleString() : '—'} |`);
}
out.push('', '리뷰 페이지: [review/index.html](../review/index.html) (GitHub Pages: `…/review/`)', '', `만든 날: ${new Date().toISOString().slice(0, 10)}`);
console.log(out.join('\n'));
