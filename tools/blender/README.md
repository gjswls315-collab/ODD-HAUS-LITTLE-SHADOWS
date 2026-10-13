# tools/blender — 리뷰 후보 모델 제작 (Blender 4.5 · bpy)

결과물은 모두 **PROTOTYPE · 리뷰 후보**다. 사용자가 [디자인 리뷰 페이지](../../review/index.html)에서 눈으로 승인하기 전에는 게임에 넣지 않는다 ([CLAUDE.md](../../CLAUDE.md) 2-2 · 3).

기준 그림: [docs/concept/](../../docs/concept/) — 사용자가 준 콘셉트 시트(라인업 · Vin · Buddy · Bully · Lounge). 리뷰 페이지의 '콘셉트 시트' 버튼으로 모델 옆에 띄워 비교한다.

## 하는 일

v2.9의 `tools/glb`(Three.js 도형 조립)와 달리, 조형 과정을 거쳐 메시를 만든다.

| 단계 | 방법 |
|---|---|
| 큰 형태 | **SDF 스컬프트** — 둥근 원뿔 · 타원체 · 2D 윤곽 돌출을 부드러운 합 · 빼기로 녹여 붙인 하나의 표면(머리 · 손 · 몸 · 신발 라스트 · 소파 · 가구). 레코드처럼 원래 회전체인 물건은 실제 단면(비드 · 홈 영역 · 라벨 단)을 설계해 돌린다 |
| 토폴로지 | **Quadriflow 리토폴로지** → 서브디비전 → 원래 표면에 다시 붙임 (고른 사각면) |
| 디테일 조형 | 스컬프트 브러시: 잡아당기기 · 부풀리기 · 주름(crease) · 꼬집기 · 납작하게 · 매끈하게 — 위치 · 반경 · 깊이를 정해 표면을 직접 민다. 털은 흐름 방향을 따라 겹치는 다발(shingle)로 표면 자체를 변형 — UV는 변형 **전** 매끈한 몸에서 펴고(변형 뒤에 펴면 조각 수천 개), 다발 끝이 다음 다발 위로 접힌 면은 변위를 이웃 평균으로 풀고, 셰이딩 법선에 변형 전 법선을 섞는다(다발 아래 턱 면이 검은 줄로 보이지 않게) |
| 천 | 천 시뮬레이션(커튼 · 넥타이), 또는 몸 껍질 + 처짐 · 주름 조형(티셔츠) |
| 재질 | UV 텍셀마다 3D 위치 · 법선을 구워(`tex.Surf`) 그 위에 홈 · 긁힘 · 결 · 박음질 · 때 · 프린트를 그린다 → 색 · 거칠기 · 노멀(탄젠트 공간, 3D 미분) → glTF (클리어코트 · 쉰 · 이방성). 구운 텍셀은 값을 옮겨 구워(위치 +100 m) 골라내고, 섬 바깥은 가장 가까운 섬 텍셀로 채운다 — 알파로 고르면 굽기 전 지우기가 알파까지 채워서 섬 테두리에 밝은 줄이 생긴다 |
| 면 예산 | 조형 뒤 큰 메시는 형태를 지키며 줄인다 (잔디테일은 노멀맵) |
| 내보내기 | glTF(WebP). 노멀맵은 원본에서 **무손실 WebP**로 다시 넣는다 — 손실 압축은 고운 홈 · 박음질을 16×16 블록으로 깨뜨린다. 레코드처럼 이방성 반사를 쓰는 메시는 **접선(MikkTSpace)을 함께** 넣는다 — 없으면 three.js가 삼각형마다 접선을 계산해 반사가 면마다 계단처럼 끊긴다. 흰 `COLOR_0` 옆에 진짜 정점 색이 `COLOR_1`로 나가면 바로잡는다 (털 카드 색) |

## 파일

| 파일 | 내용 |
|---|---|
| `odd.py` | 공용: 장면 · 스킨 골격 · SDF(둥근 원뿔 · 타원체 · 상자 · 부드러운 합/빼기) → 마칭 큐브 · Quadriflow 리토폴로지 · 스컬프트 브러시 · 곡선 관 · 띠 · 천 시뮬레이션 · UV · glTF 재질 · 내보내기 · 확인 렌더 |
| `tex.py` | 텍스처: 위치 · 법선 굽기, 값 노이즈 · fbm, 섬 경계 없는 3D 미분 노멀(`bump`), 박음질 · 꺾은선 거리 |
| `shoe.py` | 빨간 하이탑 (Vin · Bully 공용): 밑창 · 토캡 · 갑피 · 혀 · 아일릿 · 끈 · 나비 매듭 + 재질 |
| `vin.py` | Vin → `assets/review/chr_vin_review.glb` |
| `buddy.py` | Buddy → `assets/review/npc_buddy_review.glb` |
| `bully.py` | Bully → `assets/review/enemy_bully_review.glb` |
| `lounge_section.py` | Lounge 구역 → `assets/review/env_lounge_section_review.glb` |

## 실행

```
python3 -m venv bl && bl/bin/pip install bpy==4.5.14 scikit-image scipy pillow
node tools/glb/make.js index.html <rigdump_job.js> rigs.json <three 패키지>   # 게임 리그 관절 위치 (rigs.json)
ODD_OUT=out ODD_RIGS=out/rigs.json bl/bin/python tools/blender/vin.py        # (buddy.py · bully.py · lounge_section.py 같은 방식)
```

게임 리그 관절 위치(`rigs.json`)는 형태를 그 관절에 맞추는 데만 쓴다 — 게임 크기를 바꾸지 않기 위해서다.
