# 자산 상태 (저장소의 실제 파일 기준)

> `node tools/glb/status.js`가 저장소에 **실제로 있는 GLB 파일**, 게임 사용 여부, 사용자 승인 기록(`assets/APPROVED.json`)으로 만든다. 손으로 "완료"를 적지 않는다.
> **FINAL = 실루엣 · 조형된 메시 · 의도된 토폴로지 · 재질 디테일 · 믿을 만한 천/금속/나무/털 · 도형 조립이 안 보임 + 사용자 승인.** 승인 전은 모두 PROTOTYPE.
> 파일이 없으면 미완성 — 게임은 코드로 만든 PLACEHOLDER를 쓰고, PLACEHOLDER는 완성품으로 세지 않는다.

## 캐릭터

| 캐릭터 | 지금 게임 (게임 경로) | 크기 · 삼각형 | 리뷰 후보 (assets/review) | 크기 · 삼각형 | 기준 | 게임 실측 |
|---|---|---|---|---|---|---|
| Vin | **FINAL** (승인 2026-10-14)<br>`assets/characters/vin/chr_vin.glb` | 4.77 MB · 123,320 | 리뷰 후보 · 승인 2026-10-14 → 게임 파일 `assets/characters/vin/chr_vin.glb`<br>`assets/review/chr_vin_review.glb` | 4.62 MB · 123,320 | 24 cm | 파일 25.5 · 화면 25.5 cm |
| Picker | 미완성 (PLACEHOLDER)<br>`assets/characters/picker/chr_picker.glb` — 없음 | — | — | — | 23 cm | PLACEHOLDER 25.7 cm |
| A.A. | 미완성 (PLACEHOLDER)<br>`assets/characters/aa/chr_aa.glb` — 없음 | — | — | — | 28 cm | PLACEHOLDER 35.1 cm |
| Locke | 미완성 (PLACEHOLDER)<br>`assets/characters/locke/chr_locke.glb` — 없음 | — | — | — | 30 cm | PLACEHOLDER 33.1 cm |
| Rex | 미완성 (PLACEHOLDER)<br>`assets/characters/rex/chr_rex.glb` — 없음 | — | — | — | 35 cm | PLACEHOLDER 38.1 cm |
| Buddy | **FINAL** (승인 2026-10-14)<br>`assets/characters/buddy/npc_buddy.glb` | 5.08 MB · 118,804 | 리뷰 후보 · 승인 2026-10-14 → 게임 파일 `assets/characters/buddy/npc_buddy.glb`<br>`assets/review/npc_buddy_review.glb` | 4.19 MB · 118,804 | 어깨 33 cm | 파일 30.1 · 화면 29.2 cm |
| Bully | **FINAL** (승인 2026-10-14)<br>`assets/characters/bully/enemy_bully.glb` | 11.12 MB · 252,452 | 리뷰 후보 · 승인 2026-10-14 → 게임 파일 `assets/characters/bully/enemy_bully.glb`<br>`assets/review/enemy_bully_review.glb` | 10.12 MB · 252,452 | 150 cm | 파일 152.1 · 화면 152.7 cm |
| Mr. ODD | 미완성 (PLACEHOLDER)<br>`assets/characters/mr-odd/boss_mr_odd.glb` — 없음 | — | — | — | 180 cm | PLACEHOLDER 201.1 cm |

## 환경

| 스테이지 | 지금 게임 (게임 경로) | 크기 · 삼각형 | 리뷰 후보 (assets/review) | 크기 · 삼각형 |
|---|---|---|---|---|
| 01 LOUNGE (거실 방) | PROTOTYPE + **부분 승인** (2026-10-14: 승인된 리뷰 구역의 조형 · 재질로 게임 충돌 상자 크기에 맞춰 다시 만든 소파 · 사이드 테이블 · 램프 · 커튼 · 금박 액자 3점 · 러그 · 담요 (tools/blender/lounge_game.py — 게임 크기로 만든 것은 아직 사용자가 따로 보지 않음). 벽 · 마루 · 책장 · 벽난로 · 시계 · 안락의자 · LP 캐비닛 · 스피커 등 나머지는 v2.9 PROTOTYPE)<br>`assets/environment/lounge/env_lounge.glb` | 13.14 MB · 244,269 | 리뷰 후보 · 승인 2026-10-14 → 게임 파일 `assets/environment/lounge/env_lounge.glb`<br>`assets/review/env_lounge_section_review.glb` | 11.57 MB · 287,706 |
| 02 LP LIBRARY | 미완성 (코드 그레이박스 · PLACEHOLDER)<br>`assets/environment/lp-library/env_lp_library.glb` — 없음 | — | — | — |
| 03 STUDIO | 미완성 (코드 그레이박스 · PLACEHOLDER)<br>`assets/environment/studio/env_studio.glb` — 없음 | — | — | — |
| 04 DJ BOOTH | 미완성 (코드 그레이박스 · PLACEHOLDER)<br>`assets/environment/dj-booth/env_dj_booth.glb` — 없음 | — | — | — |
| 05 TERRACE | 미완성 (코드 그레이박스 · PLACEHOLDER)<br>`assets/environment/terrace/env_terrace.glb` — 없음 | — | — | — |
| 06 LOCKED ROOM | 미완성 (코드 그레이박스 · PLACEHOLDER)<br>`assets/environment/locked-room/env_locked_room.glb` — 없음 | — | — | — |

리뷰 페이지: [review/index.html](../review/index.html) (GitHub Pages: `…/review/`)

만든 날: 2026-10-14
