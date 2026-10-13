# tools/glb — GLB 제작 · 확인 도구 (PROTOTYPE 전용)

> v2.9에서 이 도구로 만든 Vin · Buddy · Bully · Lounge GLB는 Three.js 도형을 조립한 것이라 **최종 아트로 인정하지 않는다** — PROTOTYPE이다 ([CLAUDE.md](../../CLAUDE.md) 2-2).
> 리뷰 후보(최종 아트 후보)는 [tools/blender/](../blender/)에서 만든다. `inspect.js` · `view.js` · `status.js`는 그대로 쓴다.

게임(`index.html`)을 헤드리스 브라우저로 열고, **게임의 실제 리그(뼈대 · 관절 이름)** 를 그대로 거울 노드로 옮겨 최종 모델을 만든 뒤 GLB로 저장한다.
그래서 GLB를 넣어도 이동 · 점프 · 충돌 · 퍼즐 코드는 바뀌지 않는다 — 게임은 리그를 움직이고, GLB는 그 리그에 붙어서 따라간다.

| 파일 | 하는 일 |
|---|---|
| `make.js` | `node make.js <게임.html> <작업.js> <출력.glb> <three 패키지 폴더>` — 게임을 열고 `lib.js` + 작업 스크립트를 실행해 GLB 저장 |
| `lib.js` | 공용: 재질 · 캔버스 텍스처 · 노멀맵 · 덩어리/튜브/털 지오메트리 · 리그 거울 노드(`extras.link`) · 스킨 메시 · 클립 녹화 · GLB 내보내기 |
| `vin.js` | Vin → `assets/characters/vin/chr_vin.glb` (LP 몸 · 홈 노멀맵 · 눈 · 장갑 · 고무호스 팔다리 스킨 · 빨간 하이탑) |
| `buddy.js` | Buddy → `assets/characters/buddy/npc_buddy.glb` (네 발 shaggy dog · 털 · 넥타이 · BUDDY 이름표) |
| `bully.js` | Bully → `assets/characters/bully/enemy_bully.glb` (150 cm 소년 · 티 · 청바지 · 팔 스킨 · 캡 · 빨간 플라잉V) |
| `lounge.js` | 거실 → `assets/environment/lounge/env_lounge.glb` (충돌 상자를 읽어 가구 윗면을 맞춘다) |
| `inspect.js` | `node inspect.js 파일.glb` — 크기 · 텍스처 · 클립 · 확장 요약 |
| `view.js` | `node view.js 파일.glb 출력.png [클립] [시간] [확대] [높이]` — GLTFLoader로 읽어 앞 · 옆 · 뒤 · 3/4 렌더 |
| `status.js` | `node status.js [측정.json] [상태.json] > ../../docs/ASSET_STATUS.md` — 저장소에 실제로 있는 GLB로 상태표 (측정 = `?visualtest=1`의 `ODD2.VT.measure()`, 상태 = 게임의 `ODD2.ASSET_STATE`; 게임이 안 쓰는 GLB는 미완성) |

필요한 것: Node 18+, `playwright`(Chromium), three.js 0.160.0 패키지 폴더(`npm pack three@0.160.0` 후 압축 해제 — `make.js`의 넷째 인자 또는 환경 변수 `THREE_PKG`).

노드 규칙: 캐릭터 GLB의 노드 `extras.link = '<게임 리그 이름>'`(예: `hip0`, `knee0`, `head`, `guitar`), 루트 `extras.oddRig = 'hero' | 'buddy' | 'bully'`.
게임은 불러올 때 이 노드들을 같은 이름의 리그 객체 밑으로 옮겨 붙이고(로컬 = 원점), 키(또는 어깨 표식)를 재서 기준과 15% 넘게 다르면 쓰지 않는다.
환경 GLB의 `extras.matRef = 'shade' | 'ember' | 'DR.shade'`는 게임이 밝기를 바꾸는 재질(램프 갓 · 잔불)로 이어 붙인다.
