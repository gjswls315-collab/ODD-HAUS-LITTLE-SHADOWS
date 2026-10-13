# ODD HAUS: LITTLE SHADOWS — 작업 규칙

이 저장소에서 일하는 사람(그리고 Claude)이 지키는 규칙이다.

## 1. 버전 파일

- 게임을 수정할 때마다 **새 HTML 버전 파일**을 만든다: `versions/ODD_HAUS_LITTLE_SHADOWS_vX.Y.html`.
- `index.html`은 항상 최신 버전과 같은 내용이다 (GitHub Pages가 여는 파일).
- 예전 버전 파일은 고치지 않는다.

## 2. "완성했다"고 거짓으로 말하지 않는다

### 2-1. GLB 파일 규칙
- **GLB 파일이 저장소에 실제로 있어야** 그 캐릭터 · 맵을 다음 단계로 셀 수 있다. 파일이 없으면 **미완성**.
- **코드로 만든 PLACEHOLDER(그레이박스 · 코드 3D 모델)는 완성품으로 세지 않는다.** "PLACEHOLDER 다듬기"라고 쓴다.
- 작업 보고에는 **실제 파일 경로**(과 크기)를 반드시 적는다. 경로를 적을 수 없으면 완료가 아니다.
- 파일이 있어도 게임에 쓰이지 않으면(비율 검사 탈락 `rejected`, 불러오기 오류) 완료가 아니다.

### 2-2. FINAL 기준 — "GLB가 있다"로는 부족하다
FINAL은 다음을 **모두** 갖춰야 하고, **사용자가 디자인 리뷰에서 눈으로 승인**해야 한다. 하나라도 빠지면 **PROTOTYPE**이라고 쓴다.
- 실루엣이 컨셉(캐릭터 시트)과 맞는다
- 조형된 메시(authored mesh) · 의도된 토폴로지
- 재질 디테일 · 표면 변화
- 믿을 만한 천 · 금속 · 나무 · 털
- **도형 조립이 드러나지 않는다**

FINAL 아트에 쓰지 않는 방식 (PLACEHOLDER에는 써도 된다):
- `SphereGeometry` · `BoxGeometry` · `CylinderGeometry` · `CapsuleGeometry` · `TorusGeometry` · `LatheGeometry` 등 단순 도형 조합으로 최종 캐릭터 만들기
- 코드로 만든 가구를 최종 환경으로 내보내기
- 지오메트리 생성기를 복잡하게 만들어 놓고 "최종 모델링"이라고 부르기

현재: 저장소의 모든 GLB는 **PROTOTYPE**이다 — `assets/characters/…` · `assets/environment/…`(v2.9, 게임이 쓰는 것)와 `assets/review/…`(리뷰 후보, 게임이 안 쓰는 것) 모두.
승인 기록: `assets/APPROVED.json` (사용자가 승인한 파일만 적는다 — Claude가 스스로 적지 않는다).
상태표: [docs/ASSET_STATUS.md](docs/ASSET_STATUS.md) — `node tools/glb/status.js`가 실제 파일 · 게임 사용 여부 · 승인 기록으로 만든다.

## 3. 디자인 리뷰 → 승인 → 게임 반영

1. 새 모델은 먼저 `assets/review/`에 넣고 **디자인 리뷰 페이지** [review/index.html](review/index.html)에서 확인한다
   (중립 스튜디오 조명 / 게임 조명, 앞 · 옆 · 뒤 · 3/4 · 클로즈업, 안개 · 시네마틱 어둠 · 후처리 없음, v2.9와 나란히 비교, 점토 · 와이어 보기).
2. 사용자가 눈으로 승인한 것만 게임 경로(`assets/characters/…` · `assets/environment/…`)로 옮긴다.
3. 승인 전에는 게임 파일(`index.html` · 게임 경로 GLB)을 바꾸지 않는다.

## 4. 모델을 바꿀 때 게임플레이는 건드리지 않는다

- 바꾸지 않는 것: 이동 · 점프 · 충돌 · 퍼즐 · AI · 스테이지 배치. 겉모습(VisualModel)만 바뀐다.
- 게임 내 크기도 바꾸지 않는다 (기준 키: Picker 23 · Vin 24 · A.A. 28 · Locke 30 · Rex 35 cm · Buddy 어깨 33 cm · Bully 150 cm · Mr. ODD 180 cm).
- 환경 모델 교체: **"동선은 안 바꾸고 보이는 모양만 바꾼다."** 충돌 상자 · 트리거 · 매달리기 손잡이 · 오르기 지점 · 숨는 곳 · 밀 수 있는 물건은 게임 코드가 그대로 갖는다.
  가구의 윗면 · 옆면은 충돌 상자(`W.colliders`)에 맞춘다 — 검사: 플레이어 길 위에서 위→아래로 쏜 광선의 GLB 윗면과 충돌 윗면 차이가 2.5 cm 이하.
- 비율이 기준과 15% 넘게 다르면 그 GLB는 본편에 쓰지 않는다 (불러올 때 자동으로 거른다 — `measureModel`).

## 5. 도구 · 확인

- 리뷰 후보 제작: [tools/blender/](tools/blender/) — Blender(bpy 4.5) 스크립트. 조형 과정(스킨 · SDF 스컬프트 → 쿼드 리토폴로지 → 스컬프트 브러시 · 천 시뮬레이션 → 텍스처)을 기록한 것이다.
- v2.9 PROTOTYPE 제작 도구: [tools/glb/](tools/glb/) — Three.js 도형 조립 방식이라 **PLACEHOLDER/PROTOTYPE 전용**.
- `?visualtest=1` (또는 주소 끝 `#visualtest`): 게임 시작 전, 모든 캐릭터를 같은 바닥에 세워 앞 · 옆 · 뒤를 돌려 본다.

## 6. 브랜치 · 커밋

- 작업 브랜치에서 커밋하고 푸시한다. 요청이 없으면 PR을 만들지 않는다.
- 커밋 메시지 · 문서에 모델 식별자를 적지 않는다.
