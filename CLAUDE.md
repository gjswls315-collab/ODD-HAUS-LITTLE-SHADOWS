# ODD HAUS: LITTLE SHADOWS — 작업 규칙

이 저장소에서 일하는 사람(그리고 Claude)이 지키는 규칙이다.

## 1. 버전 파일

- 수정할 때마다 **새 HTML 버전 파일**을 만든다: `versions/ODD_HAUS_LITTLE_SHADOWS_vX.Y.html`.
- `index.html`은 항상 최신 버전과 같은 내용이다 (GitHub Pages가 여는 파일).
- 예전 버전 파일은 고치지 않는다.

## 2. "완성했다"고 거짓으로 말하지 않는다 (GLB 정직 규칙)

- **GLB 파일이 저장소에 실제로 있어야** 그 캐릭터 · 맵을 완료로 표시할 수 있다.
  - 예: `assets/characters/vin/chr_vin.glb`가 없으면 Vin은 **미완성**.
  - 예: `assets/environment/lounge/env_lounge.glb`가 없으면 Lounge는 **미완성**.
- **코드로 만든 PLACEHOLDER(그레이박스 · 코드 3D 모델)는 완성품으로 세지 않는다.** 아무리 다듬어도 "리모델 완료"라고 쓰지 않는다 — "PLACEHOLDER 다듬기"라고 쓴다.
- 작업 완료 보고에는 **실제 파일 경로**(과 크기)를 반드시 적는다. 경로를 적을 수 없으면 완료가 아니다.
- 파일이 있어도 게임에 쓰이지 않으면(비율 검사 탈락 `rejected`, 불러오기 오류) 완료가 아니다. `?visualtest=1`에서 `GLB` 표시와 실측 키를 확인한다.
- 현재 상태표: [docs/ASSET_STATUS.md](docs/ASSET_STATUS.md) — 저장소의 실제 파일로 만든다 (손으로 "완료"를 적지 않는다).

## 3. 모델을 바꿀 때 게임플레이는 건드리지 않는다

- 캐릭터 모델 교체: 이동 · 점프 · 충돌 · 퍼즐 · AI 코드는 그대로. 겉모습(VisualModel)만 바뀐다.
  게임 내 크기도 바꾸지 않는다 (기준 키: Picker 23 · Vin 24 · A.A. 28 · Locke 30 · Rex 35 cm · Buddy 어깨 33 cm · Bully 150 cm · Mr. ODD 180 cm).
- 환경 모델 교체: **"동선은 안 바꾸고 보이는 모양만 바꾼다."** 충돌 상자 · 트리거 · 매달리기 손잡이 · 오르기 지점 · 숨는 곳 · 밀 수 있는 물건은 게임 코드가 그대로 갖는다.
  가구의 윗면 · 옆면은 충돌 상자(`W.colliders`)에 맞춘다 — 검사: 플레이어 길 위에서 위→아래로 쏜 광선의 GLB 윗면과 충돌 윗면 차이가 2.5 cm 이하.
- 비율이 기준과 15% 넘게 다르면 그 GLB는 본편에 쓰지 않는다 (불러올 때 자동으로 거른다 — `measureModel`).

## 4. 확인

- `?visualtest=1` (또는 주소 끝 `#visualtest`): 게임 시작 전, 모든 캐릭터를 같은 바닥에 세워 앞 · 옆 · 뒤를 돌려 본다.
- GLB 제작 도구: [tools/glb/](tools/glb/) — 게임 리그에서 GLB를 다시 만들고(make.js), 단독으로 확인한다(view.js · inspect.js).

## 5. 브랜치 · 커밋

- 작업 브랜치에서 커밋하고 푸시한다. 요청이 없으면 PR을 만들지 않는다.
- 커밋 메시지 · 문서에 모델 식별자를 적지 않는다.
