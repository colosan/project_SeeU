# project_SeeU — 작업 안내 (새 세션은 이 파일부터)

시유(SeeU)를 비롯한 보컬로이드들이 나오는 **비영리 무료 팬게임**. Godot 4 + GDScript, 탑다운 쯔꾸르풍.
자세한 내용: [docs/WORLD.md](docs/WORLD.md)(세계관 설정서 — 인터넷 속 가상 세계, 맵 컨셉의 기준), [docs/DESIGN.md](docs/DESIGN.md)(결정 사항), [docs/ART_PIPELINE.md](docs/ART_PIPELINE.md)(그림 만드는 법), [docs/CHARACTER_PIPELINE.md](docs/CHARACTER_PIPELINE.md)(캐릭터 스프라이트 만드는 법·시행착오),
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
2. 픽셀 밀도 통일: 배경은 원본 픽셀을 정확히 **3배**로 표시(창 1920x1080 = 원본 640x360, 게임 칸은 원본 320x360).
   **맵은 가로 320, 세로로 길게**(360 이상, 카메라가 위아래로 따라감). 지하 시작 방만 320x240(예외, 그대로 둠).
   캐릭터 시유는 128px 스프라이트를 1배로(예외, 사용자 결정).
3. 각진 물체(상자·기계·벽·엘리베이터 등)는 **코드로 그린다**(`tools/art/pix.py`). PixelLab은 둥근/유기적 형태만,
   그것도 `tools/art/import_pixellab.py`로 색·잡점·외곽선을 우리 규칙으로 바꾼 뒤 쓴다.
4. 색은 재질 램프(`tools/art/pix.py`의 RAMPS)만. 지하는 칙칙한 회색, 강조색은 청록(glow) 하나. 외곽선은 실루엣에 한 번(sel-out).
5. 어둠·빛은 그림에 굽지 않고 2.5D 픽셀 조명(`scripts/world/pixel_lighting.gd` + `PixelLight`, docs/ART_PIPELINE.md 8절)으로.
   빛은 레이아웃의 LIGHTS 표에 이유와 함께, 반드시 보이는 원천(전구·화면·스파크·슈트) 위에. 그림을 고치면 발광 마스크(`gen_emission.py`)를 다시 만든다.
6. 디테일은 뿌리지 말고 놓는다(무작위 잡점 금지). 쉴 곳(빈 바닥)을 남긴다. 같은 크기를 줄 세우지 말고 크기 위계·겹침·쌓임·비대칭.
   **빛은 이야기가 필요한 곳에만**(작업등·슈트·스파크·켜진 화면 2~3개 등, `gen_emission.py`의 STORY_EMITTERS): 더미 속 화면·LED는 꺼진 검은 유리.
   글자·체크무늬·디레즈는 방 전체에 몇 개만. **버려진 물건은 똑바로 서 있지 않다**: 기울고·눕고·뒤집히고·더미에 파묻힌다
   (`tools/art/rot.py` RotSprite 회전 + 눕힌 그림, docs/ART_PIPELINE.md 9~10절). 서 있는 것은 일부러 세운 도구(작업등)뿐.
7. **모든 배치에는 이유가 있다**: 방마다 `tools/layout_*.py`의 PLAN에 위치와 이유를 적고, 스크립트가 씬을 만든다.
8. **길은 절대 막히지 않고, 화살표 없이 직관적으로**(빛·대비·밀린 고물의 테두리·바퀴 자국). 레이아웃 스크립트가 막힘/가림을 검사한다.
9. **벽은 실제로 있는 두꺼운 물체**: 옆벽·아래쪽(앞) 벽·막힌 덩어리의 윗면은 별도 층(`*_front.png`, `pixel_room.gd`의 `front`)으로
   소품과 캐릭터 위에 그린다. 소품의 바닥(충돌 영역)은 절대 벽에 들어가지 않고(벽에 민 더미의 가장자리만 살짝 숨음),
   앞벽 바로 뒤에 선 것은 아랫부분이 벽에 가려진다. 레이아웃 스크립트가 검사한다.

## 자주 쓰는 명령 (Git Bash 기준, 저장소 루트에서)
- 코드 그림 생성: `python tools/art/gen_junk.py` (없는 파일만 씀, 덮어쓰기는 `--force 파일명`), 미리보기는 `--out=build/art_preview`
- 발광 마스크(조명): `python tools/art/gen_emission.py` (그림을 만들거나 고친 뒤 항상, `--check`는 보고만)
- 인터넷 세계판 소품(지하에서 사용): `python tools/art/gen_digital.py` — 소품 의미 사전 [docs/WORLD_PROPS.md](docs/WORLD_PROPS.md)
- PixelLab 형태 가져오기: `python tools/art/import_pixellab.py`
- 지하 방 바닥(+ 조명 높이 지도): `python tools/gen_basement_floor.py` / 지하 방 씬: `python tools/layout_basement.py`
- 엘리베이터 홀: 그림 `python tools/art/gen_elevator.py`, 바닥 `python tools/gen_elevator_hall_floor.py`, 씬 `python tools/layout_elevator_hall.py`
- Godot 위치는 PC마다 다르다(docs/WORKFLOW.md 환경). 아래 `$GODOT` = 그 PC의 콘솔용 Godot.
- 임포트: `$GODOT --headless --path . --import` (4.6.3으로 하면 `.import` 잡음이 생김 → 되돌린다, docs/WORKFLOW.md)
- **한 번에 전부 검증**: `GODOT=... bash tools/verify.sh` (발광 마스크·두 방 씬·임포트·스크립트 오류·프로젝트 검사·손 닿는지 검사·맵 교체 누수 검사·무작위 입력 몽키 테스트·녹화·`.import` 되돌리기, 끝에 VERIFY: OK).
  녹화를 빼려면 `--no-record`
- 자동 녹화(검증): `cmd /c tools\record_autoplay.cmd` → `build/autoplay/f*.png` (창 포커스를 잃어도 키를 다시 누르므로 녹화 중 PC를 써도 됨)
- 오른쪽 패널 스탠딩: `python tools/art/cut_standing.py` — `reference/`(git 제외)의 15주년 설계도에서 앞모습을 잘라 `reference/seeu_standing.png`로
- 게임 실행: `$GODOT --path .` (F11 또는 Alt+Enter = 전체화면)
- 효과음 합성: `python tools/audio/gen_sfx.py` → `assets/audio/*.wav` (샘플·AI 없이 코드로), 재생은 `Game.sfx(이름)`
- 프로젝트 검사: `$GODOT --headless --path . --script res://tools/check_project.gd` (맵 연결·출구·도착 지점·엘리베이터 정류장·빛 개수, 문제 있으면 종료 코드 1). 맵을 추가·수정하면 항상
- 성능 측정: `$GODOT --path . --script res://tools/perf_probe.gd` (두 맵의 실제 프레임 시간·GPU·드로우 콜 + 맵 전환 최악 프레임, 기준값은 파일 머리말)
- 맵·층 추가: docs/WORKFLOW.md의 "새 맵·새 층 추가 순서" 체크리스트(바닥 → 소품 → 배치 스크립트 → `Game.PLACES`·`elevator_stops` → BACKDROPS → verify.sh)
- 조사 대사·사용: 배치 스크립트의 EXAMINE / INTERACT 표(소품 이름 → 대사 쪽들 또는 `"use": "elevator"`) → 스크립트를 다시 돌리면 소품 밑에 들어감.
  대사창·선택지는 코드에서 `await Game.say([...])`, `await Game.choose(질문, [보기...])`
- 왼쪽 패널 세계 일러스트: `python tools/art/gen_stack_map.py --guide`(PixelLab 구도 가이드) → PixelLab 두 조각 →
  `python tools/art/widen_stack_top.py` → `python tools/art/gen_stack_map.py --finish ...` (docs/ART_PIPELINE.md 11절)

## Git
- 저장소 로컬 신원은 `colosan <mljs0912@gmail.com>`(여러 PC에서 작업하므로 `git config --local`로 저장소에만 설정하고 PC 전역 설정은 건드리지 말 것). 원격: github.com/colosan/project_SeeU, 브랜치 main.
- 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. 사용자가 요청하면 커밋·푸시.
- 공식 일러스트·설계도 원본은 저장소에 넣지 않는다(저작권). 새 에셋은 docs/ASSETS.md에 출처 한 줄.
