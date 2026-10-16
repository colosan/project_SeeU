# project_SeeU — 작업 안내 (새 세션은 이 파일부터)

시유(SeeU)를 비롯한 보컬로이드들이 나오는 **비영리 무료 팬게임**. Godot 4 + GDScript, 탑다운 쯔꾸르풍.
자세한 내용: [docs/WORLD.md](docs/WORLD.md)(세계관 설정서 — 인터넷 속 가상 세계, 맵 컨셉의 기준), [docs/DESIGN.md](docs/DESIGN.md)(결정 사항), [docs/ART_PIPELINE.md](docs/ART_PIPELINE.md)(그림 만드는 법),
[docs/WORKFLOW.md](docs/WORKFLOW.md)(실행·검증·커밋), [docs/ASSETS.md](docs/ASSETS.md)(에셋 출처 기록).

## 사용자와 일하는 방식
- 사용자는 한국어로 대화한다. 답도 한국어로.
- **다음 단계나 무료 작업은 묻지 말고 바로 진행**하고 결과를 보고한다. 선택지 메뉴를 내밀지 않는다.
- **PixelLab 생성은 전략적으로**: 방향이 정해지기 전에 시험 생성을 남발하지 않는다. 무료 목업/코드로 먼저 확인하고,
  큰 묶음은 비용을 말하고 진행한다. 이미 생성한 그림을 확대·축소해서 크기를 속이지 않는다.
- 결과는 **Godot에서 실제로 배치해서** 보여 준다(PIL 합성 목업 금지). 자동 녹화로 프레임/GIF를 만들어 확인한다.
- 큰 작업은 하위 에이전트에게 맡겨도 된다(사용자가 선호함).

## 반드시 지킬 그림 규칙 (어긴 시안은 모두 반려됐다)
1. 시점: **정면 3/4(쯔꾸르식)** — 바닥은 위에서, 서 있는 물체는 **윗면 + 앞면만**. 등각(대각선) 금지.
2. 픽셀 밀도 통일: 배경은 원본 **320x240**을 정확히 **3배**로 표시. 캐릭터 시유는 128px 스프라이트를 1배로(예외, 사용자 결정).
3. 각진 물체(상자·기계·벽·엘리베이터 등)는 **코드로 그린다**(`tools/art/pix.py`). PixelLab은 둥근/유기적 형태만,
   그것도 `tools/art/import_pixellab.py`로 색·잡점·외곽선을 우리 규칙으로 바꾼 뒤 쓴다.
4. 색은 재질 램프(`tools/art/pix.py`의 RAMPS)만. 지하는 칙칙한 회색, 강조색은 청록(glow) 하나. 외곽선은 실루엣에 한 번(sel-out).
5. 어둠·빛은 그림에 굽지 않고 2.5D 픽셀 조명(`scripts/world/pixel_lighting.gd` + `PixelLight`, docs/ART_PIPELINE.md 8절)으로.
   빛은 레이아웃의 LIGHTS 표에 이유와 함께, 반드시 보이는 원천(전구·화면·스파크·슈트) 위에. 그림을 고치면 발광 마스크(`gen_emission.py`)를 다시 만든다.
6. 디테일은 뿌리지 말고 놓는다(무작위 잡점 금지). 쉴 곳(빈 바닥)을 남긴다. 같은 크기를 줄 세우지 말고 크기 위계·겹침·쌓임·비대칭.
7. **모든 배치에는 이유가 있다**: 방마다 `tools/layout_*.py`의 PLAN에 위치와 이유를 적고, 스크립트가 씬을 만든다.
8. **길은 절대 막히지 않고, 화살표 없이 직관적으로**(빛·대비·밀린 고물의 테두리·바퀴 자국). 레이아웃 스크립트가 막힘/가림을 검사한다.

## 자주 쓰는 명령 (Git Bash 기준, 저장소 루트에서)
- 코드 그림 생성: `python tools/art/gen_junk.py` (없는 파일만 씀, 덮어쓰기는 `--force 파일명`), 미리보기는 `--out=build/art_preview`
- 발광 마스크(조명): `python tools/art/gen_emission.py` (그림을 만들거나 고친 뒤 항상, `--check`는 보고만)
- PixelLab 형태 가져오기: `python tools/art/import_pixellab.py`
- 지하 방 바닥(+ 조명 높이 지도): `python tools/gen_basement_floor.py` / 지하 방 씬: `python tools/layout_basement.py`
- 엘리베이터 홀: 그림 `python tools/art/gen_elevator.py`, 바닥 `python tools/gen_elevator_hall_floor.py`, 씬 `python tools/layout_elevator_hall.py`
- 임포트: `/d/MIDAS/godot/bin/godot.windows.editor.dev.x86_64.console.exe --headless --path . --import`
- 자동 녹화(검증): `cmd /c tools\record_autoplay.cmd` → `build/autoplay/f*.png`
- 게임 실행: `/d/MIDAS/godot/bin/godot.windows.editor.dev.x86_64.exe --path .`

## Git
- 저장소 로컬 신원은 `colosan <mljs0912@gmail.com>`(PC 전역은 회사 계정이라 바꾸지 말 것). 원격: github.com/colosan/project_SeeU, 브랜치 main.
- 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. 사용자가 요청하면 커밋·푸시.
- 공식 일러스트·설계도 원본은 저장소에 넣지 않는다(저작권). 새 에셋은 docs/ASSETS.md에 출처 한 줄.
