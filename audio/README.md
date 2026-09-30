# audio/ — ODD HAUS 사운드 에셋 (v2.4)

> **THE HOUSE IS THE SOUNDTRACK.** 음악은 가장 낮은 우선순위입니다. 집 자체(문 · 마루 · 파이프 · 시계 · 바람 · 기계)가 소리를 냅니다.

게임은 **`audio/manifest.json`에 적힌 파일만** 불러옵니다. 목록에 없는 슬롯은 코드가 절차 합성으로 대신 만들기 때문에, 파일이 하나도 없어도 모든 소리가 납니다. 파일을 넣으면 그 슬롯만 실제 음원으로 바뀝니다. 깨진 URL은 요청하지 않습니다.

## 폴더 구조

```
index.html                  ← 최신 빌드 (audio/ 를 찾는다)
versions/ODD_HAUS_LITTLE_SHADOWS_v2.4.html   ← ../audio/ 를 찾는다
audio/
├─ manifest.json            ← 어떤 슬롯에 어떤 파일을 쓸지 (여기 적은 것만 로드)
├─ README.md                ← 이 문서
├─ music/                   ← 음악 (스트리밍 재생, 길이 제한 없음)
│   ├─ title_odd_haus.mp3
│   ├─ stage01_lounge.mp3
│   ├─ stage02_lp_library.mp3
│   ├─ stage03_studio.mp3
│   ├─ stage04_dj_booth.mp3
│   ├─ (stage05_terrace.mp3)      ← 아직 없음 → 절차 패드로 대체
│   └─ stage06_locked_room.mp3
├─ amb/                     ← 방 룸톤 루프 (지금은 비어 있음 → 절차 합성)
└─ sfx/                     ← 효과음 (지금은 비어 있음 → 절차 합성)
```

## 파일을 넣는 방법

1. 파일을 `audio/sfx/`, `audio/amb/`, `audio/music/` 중 알맞은 곳에 넣습니다.
2. `audio/manifest.json`의 해당 그룹에 **슬롯 이름: 경로**를 적습니다. 효과음은 변형 여러 개를 배열로 적으면 매번 무작위로 고르고(같은 파일이 연속되지 않게) 피치 · 볼륨도 조금씩 흔듭니다.
3. 커밋 · 푸시하면 GitHub Pages에 1–2분 뒤 반영됩니다. 타이틀의 **사운드 룸**에서 어떤 슬롯이 실제 파일(●)로, 어떤 슬롯이 절차 합성(○)으로 재생되는지, 로드에 실패한 파일(×)이 있는지 볼 수 있습니다.

```json
{
  "version": "2.4",
  "music": {
    "title": "music/title_odd_haus.mp3",
    "lounge": "music/stage01_lounge.mp3",
    "terrace": "music/stage05_terrace.mp3"
  },
  "amb": {
    "bed_lounge": "amb/lounge_roomtone.mp3"
  },
  "sfx": {
    "floorCreak": ["sfx/floor_creak_01.mp3", "sfx/floor_creak_02.mp3", "sfx/floor_creak_03.mp3"],
    "step_wood": ["sfx/step_wood_01.mp3", "sfx/step_wood_02.mp3", "sfx/step_wood_03.mp3", "sfx/step_wood_04.mp3"],
    "door_shut": ["sfx/door_shut_01.mp3", "sfx/door_shut_02.mp3"]
  }
}
```

- **형식**: `.mp3`(모든 브라우저 · iOS 호환) 권장. 효과음은 모노 44.1/48 kHz, 음악은 스테레오 128–192 kbps.
- **레벨**: 효과음 · 룸톤은 **피크 −1 dBFS로 정규화**해서 넣으세요. 게임 안의 크기는 코드의 `AUDIO_SAMPLE_GAIN`이 맞춥니다(아래 "볼륨 조절").
- **길이**: 효과음 0.05–5초(앞 무음 없이 바로 시작), 룸톤 루프 20–60초(끝과 처음이 이어지게), 음악은 자유.
- **로컬 실행 주의**: `index.html`을 더블클릭(file://)으로 열면 브라우저가 manifest.json을 읽지 못합니다. 이때는 코드에 내장된 목록(`AUDIO_LOCAL_MANIFEST`)으로 **음악만** 재생하고, 효과음 · 룸톤 파일은 불러오지 않습니다(절차 합성). 파일까지 확인하려면 GitHub Pages나 `python -m http.server`로 여세요.

## 슬롯 목록 · 권장 파일명 · 사용 스테이지

### 음악 (`music`) — 모두 "조각"으로 흐른다. 게임 중엔 아주 작게, 위험이 오면 사라진다

| 슬롯 | 권장 파일명 | 쓰이는 곳 · 방식 | 상태 |
|---|---|---|---|
| `title` | `music/title_odd_haus.mp3` | 타이틀 · 캐릭터 선택 · **엔딩**(메뉴 음악, 루프) | ● 있음 |
| `lounge` | `music/stage01_lounge.mp3` | 01 LOUNGE — 레코드 캐비닛의 턴테이블에서 나는 먼 LP. 바늘 올림 → 40–80초 → 바늘 들림/페이드 → 25–55초 정적. Mr. ODD가 오면 멈춘다 | ● 있음 |
| `library` | `music/stage02_lp_library.mp3` | 01 복도 — 서고에서 새어 나오는 낡은 레코드(피치가 흔들리고 가끔 튄다). **서고에 들어서는 순간 바이닐 스톱 → 정적** → 그 뒤로는 Bully의 기타만 | ● 있음 |
| `studio` | `music/stage03_studio.mp3` | 03 STUDIO — 모니터 스피커의 테이프. 좌/우/뒤로 소리 위치가 바뀌어 헷갈린다. Buddy의 상자가 깨어나면 테이프 스톱 → 정적 | ● 있음 |
| `djbooth` | `music/stage04_dj_booth.mp3` | 04 DJ BOOTH(사운드 룸 미리듣기) — 3–7초씩 끊기는 조각 + 클릭 · 팝 · 스크래치 · 스피커 펄스가 만드는 우연한 리듬 | ● 있음 |
| `terrace` | `music/stage05_terrace.mp3` | 05 TERRACE(미리듣기) — 아주 옅은 패드 | ○ 없음 → 절차 패드 |
| `locked` | `music/stage06_locked_room.mp3` | 06 LOCKED ROOM(미리듣기) — 10–18초 스웰, 25–50초 무음 | ● 있음 |

추격 음악 · 위험 음악 · 스팅어는 **없습니다**(의도). 추격 때는 위험층(저음 럼블 · 불규칙한 펄스 · 나무 충격 · 일그러진 환경음 · 가쁜 숨)이 대신합니다.

### 방 룸톤 (`amb`) — 슬롯 이름 `bed_<방>`

넣으면 그 방에 있을 때 루프로 깔리고, 합성 룸톤은 받침(40%)으로만 남습니다. 권장 파일명 `amb/<방>_roomtone.mp3`.

| 슬롯 | 방 | 들어가면 좋은 소리 |
|---|---|---|
| `bed_entrance` | 00 ENTRANCE | 비 · 현관문 틈 바람 · 낮은 룸톤 |
| `bed_lounge` | 01 LOUNGE | 조용한 거실 룸톤 · 창밖 비 |
| `bed_hall` | 01 복도 | 좁은 복도의 룸톤 |
| `bed_library` | 02 LP LIBRARY | 넓고 먹먹한 서고 · 먼지 · 아주 옅은 크래클 |
| `bed_corridor` | 02 추격 복도 | 긴 복도 · 외풍 · 전구 험 |
| `bed_studio` | 03 STUDIO | 방음된 방 · 험 · 테이프 히스 |
| `bed_djbooth` | 04 DJ BOOTH | 전자 장비 험 |
| `bed_terrace` | 05 TERRACE | 밤바람 · 먼 도시 · 차량 |
| `bed_locked` | 06 LOCKED ROOM | 거의 무음에 가까운 룸톤 |

### 발소리 (`sfx`) — 슬롯 이름 `step_<재질>`

바닥 재질 층만 대신합니다(캐릭터 몸의 재질음 · 걷기/달리기/숙이기의 크기 차이는 그대로). 변형 4–8개 권장. 권장 파일명 `sfx/step_<재질>_01.mp3` …

| 슬롯 | 재질 | 게임 안의 자리 | 적이 듣는 소음 |
|---|---|---|---|
| `step_wood` | 나무 마루 | 대부분의 바닥 · 가구 위 | ×1.0 |
| `step_carpet` | 카펫 · 러그 | 거실 러그 · 복도 러너 · 스튜디오 카펫 · 현관 매트 · 드럼 라이저 | ×0.55 |
| `step_fabric` | 천 | 소파 · 안락의자 · 신발 | ×0.5 |
| `step_paper` | 종이 | 책 더미 · LP 더미 | ×0.85 |
| `step_stone` | 타일 | 현관 앞 바닥 | ×1.05 |
| `step_metal` | 금속 | 앰프 · 펫 게이트 · 환풍구 덕트 · 로드 케이스 | ×1.2 |

### 문 (`sfx`) — 슬롯 이름 `door_<사건>`

경첩 삐걱임은 문이 도는 **속도**에서 실시간으로 만들어지므로(빠르면 높고 짧게, 느리면 낮고 길게) 파일 슬롯이 없습니다. 아래 사건음만 바꿀 수 있습니다.

| 슬롯 | 권장 파일명 | 쓰이는 곳 |
|---|---|---|
| `door_handle` | `sfx/door_handle_01.mp3` | 문고리가 돌아간다(거실 문, Mr. ODD 등장 전) |
| `door_unlatch` | `sfx/door_unlatch_01.mp3` | 걸쇠가 풀림 + 나무가 눌리는 소리(문이 열리기 시작) |
| `door_shut` | `sfx/door_shut_01.mp3` | 문이 닫히며 걸쇠가 걸림 + 방 울림 |
| `door_burst` | `sfx/door_burst_01.mp3` | Bully가 복도 옆문을 박차고 나온다 |

### 환경 효과음 (`sfx`) — 랜덤 앰비언트 이벤트 · 대본 이벤트

슬롯 이름은 코드의 레시피 이름과 같습니다. 권장 파일명 `sfx/<슬롯>_01.mp3`, `_02` … (변형 3개 이상이면 반복감이 사라집니다.)

| 슬롯 | 소리 | 주로 쓰이는 방 |
|---|---|---|
| `settle` | 집이 식으며 나는 작은 '딱' | 전체 |
| `floorCreak` | 마루 한 장이 삐걱 | 전체 (복도 · 서고 · 추격 복도에선 발밑에서도 가끔) |
| `woodGroan` | 나무가 길게 신음 | 전체 · 06 |
| `woodPressure` | 벽 속 나무가 눌리는 긴 소리 | 06 |
| `thudFar` | 멀리서 '쿵' (다이내믹 사일런스의 끝) | 전체 |
| `doorFar` | 먼 곳에서 문이 닫힌다 | 00 · 01 · 02 · 추격 복도 (위층 · 옆방) |
| `stepsAbove` | 위층 발소리 3–6걸음 | 00 · 01 · 02 · 추격 복도 |
| `furniture` | 가구가 밀리는 소리 | 00 · 01 · 추격 복도 |
| `smallFall` | 작은 물건이 떨어져 튀는 소리 | 01 · 추격 복도 · 거인의 발걸음 · Rex 일격 |
| `scratch` | 벽을 긁는 소리 | 추격 복도(옆문 뒤, 매복 전) · 06 |
| `pipeKnock` | 파이프 · 라디에이터 두드림 | 00 · 01 · 복도 · 추격 복도 |
| `pipeGurgle` | 파이프 속 물 흐름 | 00 · 01 · 복도 · 추격 복도 |
| `elec` | 전기 지직 (전구 · 램프) | 01 스탠드 · 복도 콘솔 램프 · 추격 복도 전구 · 04 |
| `machine` | 멀리 냉장고 컴프레서 | 01 복도 |
| `windowRattle` | 바람에 유리창이 떨림 | 01 창문 · 02 아치 창 |
| `gust` | 바람 한 줄기 | 00 · 01 · 02 · 추격 복도(마루 구멍) · 05 |
| `doorHandleWind` | 현관문 손잡이가 바람에 달그락 | 00 |
| `metalRes` | 금속의 낮은 울림 | 추격 복도(마루 구멍) · 06 |
| `firePop` | 벽난로 잔불이 탁 | 01 |
| `leather` | 가죽 소파가 삐걱 | 01 |
| `pianoNote` | 조율이 어긋난 피아노 한 음(아주 가끔, 멀리서) | 01 |
| `chime` | 괘종시계 종 한 번 | 01 |
| `shelfCreak` | 선반이 삐걱 | 02 |
| `bookFall` | 책 한 권이 떨어진다 | 02 |
| `pages` | 페이지가 넘어간다 | 02 |
| `dust` | 먼지가 흩어진다 | 02 |
| `ladderCreak` | 롤링 사다리가 삐걱 | 02 |
| `lpCrackle` | 바이닐 크래클 한 줄기 | 02 |
| `needle` | 바늘이 판에 닿는다 | 01 턴테이블 · 02 |
| `needleLift` | 바늘이 들린다 | 01 · 02 (바이닐 스톱 끝) |
| `rpmMotor` | 턴테이블 모터가 돈다 | 02 |
| `reel` | 릴 테이프 모터 | 03 |
| `tapeHiss` | 테이프 히스 스웰 | 03 |
| `recClick` | REC 릴레이 딸깍 | 03 |
| `micBump` | 마이크 스탠드를 건드림 | 03 |
| `feedback` | 옅은 피드백 | 03 |
| `speakerHum` | 스피커 험이 올라왔다 '퍽' | 03 · 04 |
| `cableBuzz` | 헐거운 케이블 지직 | 03 · 04 |
| `djClick` · `djPop` · `djScratch` · `speakerPulse` · `switchClick` | DJ 장비의 클릭 · 팝 · 스크래치 · 스피커 펄스 · 스위치 | 04 (우연한 리듬의 재료) |
| `city` | 먼 도시 · 차량 | 05 |
| `rooftopMetal` | 옥상 금속판 | 05 |
| `plants` | 화분 잎 바스락 | 05 |
| `breathAir` | 숨 같은 공기의 흐름 | 06 |
| `tinyMove` | 아주 작은 움직임 | 06 |
| `woodImpact` | 추격 중 사방에서 나무가 부딪친다 | 추격(위험층) |
| `vent` | 환풍구 공기 | 03 |

적 · 캐릭터의 목소리(Bully · Buddy · Mr. ODD 발걸음)와 캐릭터 능력음은 이번 버전에서 절차 합성 전용입니다(실제 몸 위치에서 3D로 들린다).

## 볼륨 조절

1. **게임 안** — 일시정지 메뉴 · 타이틀의 사운드 룸에 **전체 · 효과음 · 환경음 · 음악** 슬라이더. 브라우저에 저장됩니다(`oddhaus_audio_v24`).
2. **믹스 전체(코드)** — `index.html`(또는 빌드 소스 `01b_audio.js`) 맨 위 `2-0` 섹션의 `AUDIO_MIX`:

   | 키 | 기본값 | 의미 |
   |---|---|---|
   | `master` | 0.9 | 전체 |
   | `fx` | 1.0 | 1순위 · 플레이어 효과음 |
   | `enemy` | 0.9 | 2순위 · 적 |
   | `env` | 0.78 | 3순위 · 환경 효과음 |
   | `amb` | 0.36 | 4순위 · 룸톤 · 바람 · 험 |
   | `music` | 0.3 | 5순위 · 게임 중 음악 |
   | `menuMusic` | 0.72 | 타이틀 · 엔딩 · 사운드 룸 음악 |
   | `reverb` | 0.6 | 방 잔향 |
   | `danger` | 0.85 | 적 근접 위험층 |
   | `ambientRate` | 1 | 랜덤 앰비언트 이벤트 빈도 배율 |
   | `maxAmbient` | 3 | 동시에 울리는 랜덤 이벤트 수 |
   | `maxVoices` | 48 | 동시 원샷 수 |

3. **실제 파일의 기본 크기** — 같은 섹션의 `AUDIO_SAMPLE_GAIN` (`step` 0.12 · `door` 0.35 · `bed` 0.3 · 나머지 0.14). 피크 −1 dBFS 파일 기준.
4. **방마다의 룸톤 · 잔향** — `01c_soundscape.js`의 `ROOMS`(각 방의 `bed` 레벨, 잔향 길이 `ir.t`, 젖은 정도 `wet`).
5. **개별 랜덤 이벤트** — `buildSoundZones()`의 각 존: `min`/`max` 간격(초), `vol`, `prob` 확률, `pv`/`vv` 피치 · 볼륨 흔들림, `maxDist`.
6. **스테이지 음악의 흐름** — `STAGE_MUSIC`(재생 `on` · 쉼 `off` 구간(초), `gain`, 필터, 와우/플러터).
