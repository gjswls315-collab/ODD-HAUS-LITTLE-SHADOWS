# ODD HAUS: LITTLE SHADOWS — Visual Lock 점검 · 적용 기록

기준: 사용자가 준 Visual Reference 3장(IMAGE 01 캐릭터 3D · IMAGE 02 환경/레벨 · IMAGE 03 인게임 카메라 · 조명)과
"VISUAL LOCK / 3D IMPLEMENTATION MASTER PROMPT". 세 장은 하나의 Art Bible로 본다.

이 문서는 v2.6 작업 **전에** 현재 코드(v2.5)를 분석한 결과(A–F)와, v2.6에서 실제로 바꾼 것을 함께 적는다.
코드 위치는 빌드 전 소스 조각 기준이며, 배포 파일(`index.html`)은 이 조각들을 이어 붙인 단일 HTML이다.

---

## A. 현재 3D로 구현된 부분 (v2.5 기준)

전부 Three.js(r160) 실제 3D 메시다. 2D 일러스트 게임 요소는 없다.

| 영역 | 구현 | 소스 |
|---|---|---|
| 플레이어 5인 (Vin · Picker · A.A. · Rex · Locke) | 절차 모델(구 · 캡슐 · 라테 · 튜브 · RoundedBox), 리그(엉덩이 · 어깨 · 손 · 발) + 절차 애니메이션 | `03_heroes.js` `buildHero(id)` |
| Buddy | 사족보행 개, 털 인스턴싱(InstancedMesh), 넥타이 · 이름표 | `05c_buddy.js` `buildBuddy()` |
| Mr. ODD | 180 cm 집주인, 체크 로브 · 콧수염 · 곱슬머리 · 머그 · 손전등 | `05_odd.js` `buildOdd()` |
| Bully | 150 cm, 캡 · 티셔츠 · 카고 반바지 · 일렉 기타 | `05b_bully.js` `buildBully()` |
| 튜토리얼 포치 · 00 ENTRANCE · 01 LOUNGE | 실측 가구(소파 · 커피 테이블 · 책장 · 레코드 캐비닛 · 전화 탁자 · 문), 충돌 박스 · 숨는 곳 · 잡을 모서리 | `04d_tutorial.js` · `04_world.js` |
| 복도 · 02 LP LIBRARY · 추격 복도 | 5단 LP 큐브 선반(LP 약 1만 장 인스턴싱), 사다리 · 크레이트 · 헤드폰 케이블 · 게이트 | `04b_library.js` |
| 03 STUDIO | 방음 폼 · 믹싱 데스크 · 모니터 · ON AIR · 드럼 라이저 · 앰프 · 로드 케이스 · 환풍구 | `04c_studio.js` |
| 살림살이 | 책 · LP 더미, 상자, 탁자 램프, 선반, 알전구, 나방, 거미줄, 전경 실루엣 | `04e_dress.js` |
| 물리 | 고정 60 Hz, AABB 충돌, 모서리 매달리기 · 오르기 · 밀기 · 손잡이 · 사다리/로프 | `06_game.js` · `06c_hero.js` |

게임플레이 충돌은 화면에 보이는 메시와 분리된 상자(`W.colliders`)라서, 나중에 GLB로 겉모습만 바꿔도 동선은 그대로 유지된다.

## B. 현재 2D(평면) placeholder인 부분

| 위치 | 무엇 | 판단 |
|---|---|---|
| `04_world.js` 거실 창밖 | 밤하늘과 먼 창 불빛을 캔버스로 그려 붙인 평면 | **교체 대상** (배경 이미지 평면 금지) |
| `04b_library.js` 서고 창밖 하늘 | 같은 방식의 평면 | **교체 대상** |
| `04d_tutorial.js` 마당 너머 | 이웃집 지붕 · 불 켜진 창을 그려 붙인 큰 평면 | **교체 대상** |
| `04d_tutorial.js` 창 너머 Mr. ODD 실루엣 | 실루엣 텍스처 평면 | **교체 대상** (실제 3D 모델로) |
| `04d_tutorial.js` 창 안쪽 불빛 | 단색 발광 평면 | 교체 대상 (얕은 3D 방으로) |
| 빛 번짐 스프라이트 · 빛줄기 카드 · 바닥 빛 웅덩이 · 접촉 그림자 | 가산 합성 효과용 평면 | 유지 (조명 효과이며 오브젝트 대용이 아님) |
| 액자 그림 · 포스터 · 라벨 · 모니터 화면 · 사인 | 3D 물체 표면의 텍스처 | 유지 (실제 집에서도 평면인 것) |

캐릭터 중 2D 스프라이트로 된 것은 없다.

## C. 교체해야 할 캐릭터 에셋 (최종 GLB 경로)

| 캐릭터 | 최종 파일 | 현재 placeholder | v2.5 기준 시트와 다른 점 |
|---|---|---|---|
| Vin | `assets/models/chr_vin.glb` | `PlaceholderVin3D` | LP 몸통이 얇다(두께 필요), 팔다리가 너무 가늘다 |
| Picker | `assets/models/chr_picker.glb` | `PlaceholderPicker3D` | 대체로 맞음. 반창고 위치 · 피크 두께 |
| A.A. | `assets/models/chr_aa.glb` | `PlaceholderAA3D` | 신발이 밝은 회색(→ 어둡고 낡은 운동화), 찌그러짐 없음 |
| Locke | `assets/models/chr_locke.glb` | `PlaceholderLocke3D` | 주황 갈색(→ 황동 · 바랜 금), 열쇠 이빨이 안 보임, 가방이 정면에서 안 보임 |
| Rex | `assets/models/chr_rex.glb` | `PlaceholderRex3D` | 밝은 주황 나무(→ 광택 나는 짙은 나무), 왕관 띠가 검정(→ 바랜 금) |
| Buddy | `assets/models/npc_buddy.glb` | `PlaceholderBuddy3D` | 털이 한 가지 베이지(→ 갈색 · 회색 · 크림 섞임), 눈이 작다(→ 크고 촉촉한 갈색), 어깨 약 40 cm(→ 30–35 cm), **역할이 추격자**(→ 길잡이 NPC) |
| Mr. ODD | `assets/models/boss_mr_odd.glb` | `PlaceholderMrOdd3D` | 어깨가 각지다(→ 둥글고 넓게), 회색 섞인 곱슬머리 · 굵은 눈썹 부족, 로프 벨트가 가는 선, 머그가 손에 없음 |
| Bully | `assets/models/enemy_bully.glb` | `PlaceholderBully3D` | 이를 다 드러낸 섬뜩한 웃음(→ 얄미운 장난꾸러기 웃음), 머리가 작다, 캡이 검정(→ 뒤로 쓴 빨간 캡) |

스케일(Visual Lock 2): Vin 24 · Picker 23 · A.A. 28 · Locke 30 · Rex 35 · Bully 150 · Mr. ODD 180 cm는 이미 맞다. Buddy만 어깨 높이를 줄여야 한다.

## D. 교체해야 할 환경 에셋

| 스테이지 | 최종 파일 | 현재 | 상태 |
|---|---|---|---|
| 01 LOUNGE | `assets/models/env_lounge.glb` | `04_world.js` (현관 · 거실) | 있음. 소파 팔걸이 오르기 · 쿠션 발판이 없다 |
| 02 LP LIBRARY | `assets/models/env_lp_library.glb` | `04b_library.js` (복도 · 서고 · 추격 복도) | 있음. 중간 선반 · 숨은 틈이 없다 |
| 03 STUDIO | `assets/models/env_studio.glb` | `04c_studio.js` | 있음. 키보드 · 녹음 부스 유리 · 큰 모니터 스피커 없음, 데스크 · 믹서가 발판이 아니다 |
| 04 DJ BOOTH | `assets/models/env_dj_booth.glb` | 없음 | 미제작 (사운드 룸에서 소리만) |
| 05 TERRACE | `assets/models/env_terrace.glb` | 없음 | 미제작 |
| 06 LOCKED ROOM | `assets/models/env_locked_room.glb` | 없음 | 미제작 |

## E. 현재 카메라 구조 (`06_game.js` 카메라 갱신부)

- PerspectiveCamera **FOV 30°** (Visual Lock 35–45보다 좁다).
- 사이드뷰 + 옆으로 약 4°(0.075 rad) 비튼 각도. 3/4 느낌이 약하다.
- 구간마다 "피사체 평면에서 보이는 높이"(1.6–2.6 m)를 정하고 거리를 계산 → 캐릭터는 화면 높이의 약 9–15%.
- 진행 방향으로 앞 여백(lead), 스프링 추적, 핸드헬드 흔들림, 피사계 심도 초점 = 플레이어.
- 추격 2.6 m로 물러남. 위협 방향 쪽 여백 · 보스 부분 프레이밍은 없다.

## F. 현재 조명 구조 (`04b_library.js` 조명 구역 · `06_game.js` 렌더러)

- 광원 수 고정: 구역마다 점광 10개 풀 + 그림자 키 램프 1 + 달(방향광, 그림자) + 복도 스폿 + 반구광 + 림 방향광. 방을 옮기면 같은 광원을 재배치(구역 T · A · B · C · D).
- 실용 광원(램프 · 전구 · REC · LED)은 발광 재질 + 가산 스프라이트 + 빛 웅덩이.
- ACES 톤매핑 노출 1.16, 지수 안개 0.07.
- 후처리: 피사계 심도 → 블룸 → 출력 → 색 보정(어두운 곳 파랑 · 밝은 곳 호박색 · 비네트 0.52 · 그레인 · 색수차).
- 캐릭터 전용 림 라이트가 없다(어두운 곳에서 실루엣이 묻힌다). 화면 명암 비율을 측정한 적이 없다.

---

## v2.6에서 적용한 것

| Visual Lock 항목 | 적용 | 위치 |
|---|---|---|
| 1 캐릭터 8인 · 실루엣 | A.A. 찌그러진 자국 · 낡은 어두운 운동화 / Locke 황동 · 열쇠 이빨 · 배낭 / Rex 짙은 나무 · 바랜 금 왕관 / Buddy 갈색 · 회색 · 크림 털 · 큰 갈색 눈 / Mr. ODD 둥근 몸 · 회색 섞인 곱슬머리 · 굵은 눈썹 · 로프 벨트 / Bully 큰 머리 · 빨간 캡 · 얄미운 웃음 · 주근깨 / Vin · Picker 팔다리 굵기 | `03_heroes.js` · `05c_buddy.js` · `05_odd.js` · `05b_bully.js` |
| 1 역할 | Buddy = 길잡이 NPC(인사 → 안내 → 위험 감지 → 한 번 물기 → 환풍구 지키기). 스튜디오 추격은 Bully | `05c_buddy.js` · `05b_bully.js` |
| 2 스케일 | 24 · 23 · 28 · 30 · 35 · 150 · 180 cm 유지, Buddy 어깨 약 33 cm로 축소 | `03_heroes.js` · `05c_buddy.js` |
| 3 환경 = 실제 3D | 창밖 · 마당 · 실루엣 · 창 안쪽 방의 평면 그림을 3D로 교체 | `04e_dress.js`(nightView) · `04d_tutorial.js` |
| 3 스테이지 소품 | 거실 책 더미 · 소파 팔걸이 · 쿠션 / 서고 독서등 · 숨은 틈 / 스튜디오 키보드 · 녹음 부스 유리 · 보컬 마이크 · 전원 콘센트 · 텅스텐 램프 | `04_world.js` · `04b_library.js` · `04c_studio.js` · `04e_dress.js` |
| 4 카메라 | FOV 38°, 3/4(약 7°), 위협 쪽 여백, 추격 때 물러남, Mr. ODD 가까이에서는 다리 · 손만 | `06_game.js` 카메라 갱신부 |
| 5 조명 | 방마다 노출, 푸른 숯색 그림자 바닥(완전한 검정 금지), 푸른 검정 안개, 캐릭터 림 라이트, 실용 광원 추가 | `06_game.js` · `04b_library.js`(applyZone) · `04c_studio.js` |
| 7 가구 = 게임플레이 | 소파(밑 숨기 · 팔걸이 오르기 · 쿠션 발판), 책(발판), 케이블(걸려 넘어짐), 키보드(밟으면 소리), 콘센트(A.A.), 상자 · 케이스(오르기) | 위와 같음 |
| 9 · 10 에셋 이름 · placeholder | `assets/models/manifest.json` 에 적힌 GLB를 불러와 `Placeholder…3D` 를 바꿔 낀다. 클립 이름이 맞으면 애니메이션 자동 재생 | `04f_assets.js` · `assets/README.md` |

### 화면 명암 측정 (sRGB 루마, 1280×720 렌더)

깊은 그림자 = L < 0.10, 읽히는 영역 = L ≥ 0.16, 뭉개진 검정 = L < 0.025.

| 장면 | 깊은 그림자 | 읽히는 영역 | 메모 |
|---|---|---|---|
| 00 현관 | 0.71 | 0.19 | 거울 아래 램프 · 천장 알전구 |
| 01 거실 (램프 켬) | 0.63 | 0.23 | 램프 주변만 밝다 |
| 01 거실 창가 | 0.88 | 0.06 | 달빛 · 사이드 테이블 램프 — 가장 어두운 구간 |
| 복도 | 0.58 | 0.31 | 콘솔 램프 · 알전구 (좁은 공간이라 밝은 편) |
| 02 서고 | 0.69–0.73 | 0.13–0.17 | 독서등 · 달빛 창 |
| 추격 복도 | 0.75 | 0.13 | 흔들리는 백열전구 |
| 03 스튜디오 | 0.76 | 0.11 | REC 빨강 · 텅스텐 · 모니터 파랑 |

뭉개진 검정은 그레인을 빼면 거의 없다. 가장 어두운 곳도 푸른 숯색(약 RGB 9·10·16)으로 남는다.

### 아직 남은 것

- 04 DJ BOOTH · 05 TERRACE · 06 LOCKED ROOM 스테이지 자체(현재는 에셋 슬롯 · 사운드 룸만).
- 스튜디오 동선을 Visual Lock의 "케이블 → 앰프 → 데스크 → 믹서 → 유리 부스 → 컨트롤 룸" 순서로 다시 짜기(지금은 케이블 → 라이저 → 케이스 → 환풍구 + 키보드 · 부스 · 콘센트).
- 서고 "중간 선반" 정지 지점.
- 최종 GLB 모델 (받으면 `assets/models/` 에 넣기만 하면 된다).

## v2.7 갱신

- **에셋 경로가 바뀌었다** — `assets/models/` + `manifest.json` 대신 `assets/characters/<캐릭터>/` · `assets/environment/<스테이지>/` 에 정해진 이름으로 넣기만 하면 된다(목록 파일 없음). 위 표의 `assets/models/chr_vin.glb` → `assets/characters/vin/chr_vin.glb`, `env_lounge.glb` → `assets/environment/lounge/env_lounge.glb` … 전체 표는 [assets/README.md](../assets/README.md).
- 위 "아직 남은 것" 중 **04 · 05 · 06 스테이지**와 **스튜디오 동선(케이블 → 앰프 → 데스크 → 믹서 → 유리 부스 → 컨트롤 룸)** 은 v2.7에서 만들었다 — [STAGES_v2.7.md](STAGES_v2.7.md).
- 화면 명암 비율(같은 측정): 03 스튜디오 0.79 · 컨트롤 룸 0.64 · 04 DJ BOOTH 0.86–0.89(거의 검은 방 — LED 튜브 · 벽 번짐 · 주황 계단 엣지로 발판을 읽게) · 05 테라스 0.78–0.79 · 06 잠긴 방 0.64–0.84.
