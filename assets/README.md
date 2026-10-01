# assets/ — 최종 3D 모델(GLB) 넣는 곳

지금 게임은 모든 캐릭터와 공간을 **코드로 만든 실제 3D 모델(PLACEHOLDER)** 로 그린다.
최종 GLB가 준비되면 **아래 경로에 그 이름 그대로 넣기만 하면** 다음 실행부터 PLACEHOLDER 대신 그 모델이 나온다.
코드도, 목록 파일도 고칠 필요가 없다. 파일이 없거나 불러오지 못하면 PLACEHOLDER를 그대로 쓴다(게임은 멈추지 않는다).

웹(GitHub Pages)이나 로컬 서버로 열 때만 불러온다. `index.html`을 더블클릭해 `file://`로 열면 브라우저 보안 때문에 PLACEHOLDER만 쓴다.
브라우저 콘솔의 `404 (… .glb)` 줄은 "아직 없는 GLB를 확인했다"는 뜻이다(정상). 콘솔에는 `[ODD HAUS] Missing GLB Asset List` 로 아직 없는 파일 목록이 나온다.

## 캐릭터 (CHARACTER_ASSETS)

| 경로 | 대상 | 지금 쓰는 PLACEHOLDER | 기준 키 |
|---|---|---|---|
| `assets/characters/vin/chr_vin.glb` | Vin | `PlaceholderVin3D` | 24 cm |
| `assets/characters/picker/chr_picker.glb` | Picker | `PlaceholderPicker3D` | 23 cm |
| `assets/characters/aa/chr_aa.glb` | A.A. | `PlaceholderAA3D` | 28 cm |
| `assets/characters/locke/chr_locke.glb` | Locke | `PlaceholderLocke3D` | 30 cm |
| `assets/characters/rex/chr_rex.glb` | Rex | `PlaceholderRex3D` | 35 cm |
| `assets/characters/buddy/npc_buddy.glb` | Buddy (동행 NPC) | `PlaceholderBuddy3D` | 어깨 33 cm |
| `assets/characters/mr-odd/boss_mr_odd.glb` | Mr. ODD | `PlaceholderMrOdd3D` | 180 cm |
| `assets/characters/bully/enemy_bully.glb` | Bully | `PlaceholderBully3D` | 150 cm |

## 환경 (STAGES)

| 경로 | 스테이지 | 지금 쓰는 것 | 게임 좌표(x) |
|---|---|---|---|
| `assets/environment/lounge/env_lounge.glb` | 00 ENTRANCE + 01 LOUNGE | 코드로 지은 집 | −99 … 14.1 |
| `assets/environment/lp-library/env_lp_library.glb` | 복도 + 02 LP LIBRARY + 추격 복도 | 코드로 지은 집 | 14.1 … 50.6 |
| `assets/environment/studio/env_studio.glb` | 03 STUDIO + 컨트롤 룸 | 코드로 지은 집 | 50.6 … 70.2 |
| `assets/environment/dj-booth/env_dj_booth.glb` | 04 DJ BOOTH | `buildDJBoothGraybox()` | 194.4 … 205.4 |
| `assets/environment/terrace/env_terrace.glb` | 05 TERRACE | `buildTerraceGraybox()` | 294.0 … 306.2 |
| `assets/environment/locked-room/env_locked_room.glb` | 06 LOCKED ROOM | `buildLockedRoomGraybox()` | 394.6 … 404.2 |

코드에서 이 목록은 `CHARACTER_ASSETS`(소스 `04f_assets.js`)와 `STAGES`(소스 `04g_stages.js`)에 있다 — 배포 파일 `index.html` 안.

## 겉모습과 게임플레이는 따로다

```
PlayerRoot                 BuddyRoot
├ VisualModel   ← 여기만 바뀐다 (PLACEHOLDER ↔ GLB)      ├ VisualModel   ← 여기만 바뀐다
├ CollisionCapsule (캐릭터 정의의 키 · 반폭)              ├ Collision
├ GroundRay                                               ├ GroundRay
├ InteractionOrigin                                       ├ GuideTarget (다음 길잡이 지점)
├ AbilityOrigin                                           └ AudioOrigin
└ AudioOrigin
```

이동 · 점프 · 충돌 · 숨기 · 오르기 · 밀기/당기기 · 상호작용 · AI는 전부 이 원점들과 충돌 상자로 계산하고, 메시를 보지 않는다.
그래서 모델을 바꿔도 동선 · 난이도 · 판정은 그대로다.

환경 GLB를 넣으면 그 스테이지의 **고정 그레이박스 메시만** 숨기고 그 자리에 GLB를 놓는다. 그대로 남는 것:
충돌 · 숨는 곳 · 잡을 모서리 · 손잡이 · 트리거(보이지 않는 상자), 움직이는 장치(턴테이블 플래터 · 믹서 페이더/노브 · 스피커 우퍼 · 문 · 레버 · 트렁크 · 옷장 · 기계 모듈 · 식물/천/종이처럼 바람에 움직이는 것), 빛 번짐 · LED 발광.
모델의 가구 위치가 다르면 동선과 어긋나므로, 지금 그레이박스의 위치와 높이에 맞춰 만든다(높이 표: [docs/STAGES_v2.7.md](../docs/STAGES_v2.7.md)).

## 모델 규칙

- glTF 2.0 바이너리(`.glb`), **1 unit = 1 m**(실제 크기), **+Y 위**, **정면 = +Z**(카메라 쪽), 발바닥(또는 바닥면) = 원점.
- 캐릭터는 위 표의 키로 만든다.
- 환경 GLB는 **게임 좌표 그대로**(x = 왼쪽→오른쪽 진행 방향, z = 안쪽이 −, 바닥 y = 0) 배치한다.
- 캐릭터 애니메이션 클립 이름이 아래와 같으면 상태에 맞춰 자동으로 재생한다(없는 클립은 `idle`로 대체, 클립이 아예 없어도 된다):
  `idle` · `walk` · `run` · `jump` · `crouch` · `crawl` · `hang` · `climb` · `push` — NPC는 `idle` · `walk` · `run`.
  (권장 애니메이션 목록 전체 — Jump Start · Fall · Land · Pull · Ledge Hang · Hide와 캐릭터별 Listen · Dash · Charge · Unlock · Royal Pose · Sniff · Bark · Guide · Search 등 — 은 다음 단계에서 클립 이름으로 연결한다.)
