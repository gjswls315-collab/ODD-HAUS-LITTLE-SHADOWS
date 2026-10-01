# assets/ — 최종 3D 모델 넣는 곳

게임은 지금 모든 캐릭터와 공간을 **코드로 만든 3D 모델(placeholder)** 로 그린다.
최종 GLB가 준비되면 `assets/models/` 에 아래 이름 그대로 넣고, `assets/models/manifest.json` 에서 그 이름의 값을 파일명으로 바꾸면 된다.
그러면 다음 실행부터 placeholder 대신 그 모델이 나온다. 코드는 고칠 필요가 없다.

```json
"models": {
  "chr_vin": "chr_vin.glb",
  "npc_buddy": { "file": "npc_buddy.glb", "scale": 1.0, "yaw": 0, "y": 0 }
}
```

`null` 이면 아직 없다는 뜻이고, 그 슬롯은 placeholder를 쓴다.
웹(GitHub Pages)이나 로컬 서버로 열 때만 불러온다. `index.html`을 더블클릭해서 `file://` 로 열면 브라우저 보안 때문에 placeholder만 쓴다.

## 슬롯 (Visual Lock 9)

| 파일 | 대상 | 지금 쓰는 placeholder | 기준 키 |
|---|---|---|---|
| `chr_vin.glb` | Vin | `PlaceholderVin3D` | 24 cm |
| `chr_picker.glb` | Picker | `PlaceholderPicker3D` | 23 cm |
| `chr_aa.glb` | A.A. | `PlaceholderAA3D` | 28 cm |
| `chr_locke.glb` | Locke | `PlaceholderLocke3D` | 30 cm |
| `chr_rex.glb` | Rex | `PlaceholderRex3D` | 35 cm |
| `npc_buddy.glb` | Buddy (길잡이 NPC) | `PlaceholderBuddy3D` | 어깨 33 cm |
| `boss_mr_odd.glb` | Mr. ODD | `PlaceholderMrOdd3D` | 180 cm |
| `enemy_bully.glb` | Bully | `PlaceholderBully3D` | 150 cm |
| `env_lounge.glb` | 00 ENTRANCE + 01 LOUNGE (x −7.3 … 14.1) | `PlaceholderLounge3D` | — |
| `env_lp_library.glb` | 복도 + 02 LP LIBRARY + 추격 복도 (x 14.1 … 50.6) | `PlaceholderLPLibrary3D` | — |
| `env_studio.glb` | 03 STUDIO (x 50.6 … 66.5) | `PlaceholderStudio3D` | — |
| `env_dj_booth.glb` | 04 DJ BOOTH | 아직 스테이지 없음 | — |
| `env_terrace.glb` | 05 TERRACE | 아직 스테이지 없음 | — |
| `env_locked_room.glb` | 06 LOCKED ROOM | 아직 스테이지 없음 | — |

코드에서 이 목록은 `ASSET_SLOTS`(소스 `04f_assets.js`, 배포 파일 `index.html` 안)에 있다.

## 모델 규칙

- glTF 2.0 바이너리(`.glb`), **1 unit = 1 m**(실제 크기), **+Y 위**, **정면 = +Z**(카메라 쪽), 발바닥(또는 바닥면) = 원점.
- 캐릭터는 위 표의 키로 만든다. 다르면 manifest의 `scale`로 맞춘다.
- 캐릭터 애니메이션 클립 이름이 아래와 같으면 상태에 맞춰 자동으로 재생한다(없는 클립은 `idle`로 대체):
  `idle` · `walk` · `run` · `jump` · `crouch` · `crawl` · `hang` · `climb` · `push`
  NPC는 `idle` · `walk` · `run`.
- 클립이 없어도 된다. 그때는 게임의 절차 애니메이션(몸 기울기 · 웅크림 · 방향 전환)만 적용된다.
- 환경 GLB는 **게임 좌표 그대로**(x = 왼쪽→오른쪽 진행 방향, z = 안쪽이 −, 바닥 y = 0) 배치한다. 넣으면 그 구간의 고정 장식 메시만 숨기고, 문 · 펫도어 · 밀 수 있는 물건 · 레코드 조각 · 빛 효과는 그대로 남긴다.
- 충돌 · 숨는 곳 · 잡을 모서리는 겉모습과 분리된 상자라서, 모델을 바꿔도 동선과 난이도는 그대로다. 모델의 가구 위치가 다르면 동선과 어긋나므로, 지금 placeholder의 위치에 맞춰 만든다.
