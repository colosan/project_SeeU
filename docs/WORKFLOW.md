# 작업 흐름 (실행·검증·커밋)

## 환경
- Windows, 여러 PC에서 작업한다. Git Bash와 PowerShell 둘 다 사용 가능. Python 3 + Pillow(+ numpy: `cut_standing.py`).
  - 회사 PC: 저장소 `D:\MIDAS\project_SeeU`, Godot `D:\MIDAS\godot\bin\godot.windows.editor.dev.x86_64(.console).exe`(직접 빌드 4.8 dev).
  - 개인 PC: 저장소 `D:\dev\project_SeeU`, Godot `%USERPROFILE%\Downloads\Godot_v4.6.3-stable_win64.exe\Godot_v4.6.3-stable_win64(_console).exe`.
  - `tools\record_autoplay.cmd`는 인자 → `GODOT` 환경 변수 → 위 두 경로 순으로 Godot를 찾는다.
  - **4.6.3으로 임포트하면 `.import` 파일 수백 개가 바뀐다**(4.8의 `compress/high_quality_mode` 줄이 빠짐). 버전 차이일 뿐이라 커밋하지 않고
    `git diff --name-only | grep '\.import$' | xargs git checkout --`로 되돌린다.
  - 공식 안정판으로 옮기면 이 절을 갱신할 것.
- PixelLab MCP(사용자 범위로 등록됨). 잔량 확인 `get_balance`. 생성 비용은 도구마다 다름: pixflux/map_object 1, create_image_pro 10~25, 타일셋 pro 25, 캐릭터 v3 2, skeleton-v3 걷기 방향당 3.

## 검증 루틴 (그림·배치를 바꿨으면 항상)
아래 1~4를 한 번에: `GODOT=<콘솔 Godot> bash tools/verify.sh` (`--no-record`면 녹화 빼고 1분 반 정도, 녹화까지 5분 정도). 끝에 `VERIFY: OK`여야 한다.
그다음 5(프레임 직접 보기)는 사람이/에이전트가 한다.
1. 생성: `python tools/art/gen_junk.py`, `python tools/art/gen_digital.py`(인터넷 세계판, 지하는 이쪽을 씀), `python tools/art/gen_elevator.py`(필요 시 `--force`), 바닥 `python tools/gen_basement_floor.py`, `python tools/gen_elevator_hall_floor.py`
   (바닥 그림과 함께 조명용 `.height.png`도 씀), 발광 마스크 `python tools/art/gen_emission.py`(그림을 바꿨으면 항상),
   배치 `python tools/layout_basement.py`, `python tools/layout_elevator_hall.py`(둘 다 문제 0개여야 함. 빛의 원천 검사 포함).
2. 임포트: `godot --headless --path . --import`
3. 빠른 실행: `godot --headless --path . --quit-after 30` — 오류가 없어야 함(스크립트 문법 오류는 여기서 잡는다. 녹화부터 돌리면
   오토로드가 죽은 채 모든 단계가 시간 초과까지 기다려 10분 가까이 걸린다).
   프로젝트 검사: `godot --headless --path . --script res://tools/check_project.gd` — 맵끼리의 연결(출구 → 도착 지점, 엘리베이터 정류장,
   PLACES 좌표·층)과 맵마다 플레이어·조명·빛 16개 이하를 본다. 문제 0개여야 함.
   닿는지 검사: `godot --headless --path . --script res://tools/reach_check.gd` — 실제 물리로 설 수 있는 칸을 시작점에서 채워 나가
   조사·사용할 것마다 손이 닿는 자리가 있는지 본다(`-- --dump`면 칸 목록을 build/reach_<맵>.txt로: 바닥 그림 밖으로 새는지 확인용).
   누수 검사: `godot --headless --fixed-fps 60 --path . --script res://tools/leak_check.gd` — 맵을 200번 바꿔 객체가 쌓이는지 본다.
   몽키 테스트: `godot --headless --fixed-fps 60 --path . --script res://tools/monkey_test.gd -- 20000 <시드>` — 무작위 키 입력을
   퍼붓고(맵 이동·엘리베이터 탑승 포함) UI가 영영 안 닫히거나, 멈춘 채 일시정지되거나, 시유가 맵 밖으로 나가면 문제로 센다. 2만 프레임에 몇 초.
4. 녹화: `cmd /c tools\record_autoplay.cmd` → `build/autoplay/f*.png`(30fps). 시나리오는 `tools/autoplay_record.gd`의 STEPS
   (키를 누른 채 위치·맵 조건까지 진행: 양탄자 → 매트 조사 → 통로 → 출구 → 페이드 → 엘리베이터 앞 → 층 선택판(잠긴 층) → 시험용 정류장으로 타고 같은 홀에 도착 → 걸어서 지하로 → 일시정지 메뉴).
   소리도 `build/autoplay/f.wav`로 같이 녹음된다(효과음이 제때 나는지 파형으로 확인 가능).
5. 프레임을 직접 보고 확인: 떠 있는 물건, 길 막힘/가림, 시점 어긋남, 반복 패턴. 사용자에게는 실제 화면 PNG와 GIF를 보낸다.
   조명: 그림자가 빛 반대쪽으로 지는지, 원천(전구·화면·스파크)이 밝게 살아 있는지, 허공이 밝아지지 않는지, 빛 픽셀이 3배 격자에 맞는지, 통로가 가장 밝은 띠인지.
   조명 버퍼를 직접 보려면 HeightVP/LightVP(`Lighting` 노드 밑)의 텍스처를 `get_image()`로 저장한다.

## 새 맵·새 층 추가 순서 (체크리스트)
1. **기획**: docs/WORLD.md 4절의 층 개념 → 방의 이야기 한 줄과 길(PATH). 그림 규칙은 CLAUDE.md(정면 3/4, 가로 320 세로로 길게, 재질 램프, 벽은 두꺼운 물체).
2. **바닥·벽 그림**: `tools/gen_<방>_floor.py`(지하·홀 것을 본보기로): 바닥 + 조명 높이 지도(`.height.png`) + 앞벽 층(`*_front.png`).
3. **소품**: 각진 것은 코드(`tools/art/gen_*.py`), 둥근 것만 PixelLab → `import_pixellab.py`. 새 그림마다 `gen_emission.py`, 출처는 docs/ASSETS.md.
4. **배치 스크립트** `tools/layout_<방>.py`: PLAN(이유 필수, 옵션은 ART_PIPELINE 6절 — 씬 줄은 `tools/scene_parts.py`), LIGHTS(보이는 원천 위),
   EXAMINE/INTERACT, ROOM_TONE, SPAWNS(엘리베이터가 있으면 문 앞 `FromElevator`), EXITS. 검사 문제 0개.
5. **이어 붙이기** (`scripts/autoload/game.gd`): `PLACES`에 한 줄(씬·층·이름·왼쪽 지도 좌표 `at` — 탑 그림에서 잰다),
   새 층이면 `FLOOR_NAMES`에 이름, 엘리베이터로 가는 층이면 `elevator_stops[층] = [씬, &"FromElevator"]`(+ 권한 `access`는 이야기에서 준다).
   오른쪽 패널 층 배경은 `scripts/ui/info_panel.gd`의 BACKDROPS(ART_PIPELINE 11절).
6. **검증**: `bash tools/verify.sh`(프로젝트 검사가 출구·도착 지점·정류장·좌표를, 몽키 테스트가 막힘을 잡는다) → 녹화 시나리오
   (`tools/autoplay_record.gd`)에 새 방을 지나가는 단계 추가 → 프레임을 직접 본다.

## Git
- 로컬 신원 `colosan <mljs0912@gmail.com>`(저장소 설정). 전역(회사 계정)은 건드리지 않는다.
- 커밋 메시지 끝: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- `build/`, `.godot/`은 무시됨. `.gitattributes`로 LF 고정.
- 기록을 다시 쓰는 강제 푸시는 사용자 허락이 있을 때만.

## 현재 상태 (2026-10-17)
- 화면: 1920x1080, [지도 패널 420 | 게임 1080 | 정보 패널 420], 넓은 창·큰 화면에선 게임 칸만 넓어짐. 배율은 정수만(1440p = 1배, 패널 그대로, 게임 칸 1720x1440)(docs/DESIGN.md 화면·UI).
  왼쪽 = 세상에서 가장 큰 탑(보컬로이드들의 탑) 일러스트, 오른쪽 = 층별 배경 + 시유 스탠딩(이 PC의 reference/에만) + TV·상태·인벤토리.
- 방: 실제 방만 렌더링(벽 윗면·빈 칸·방 밖은 점 무늬), 벽은 앞에 그려지는 두꺼운 물체(앞벽 층). 엘리베이터 홀은 세로형 320x480.
- 맵·층·지도 좌표는 `Game.PLACES` 한 곳에 적는다(새 맵 = 한 줄).
- 조사·대사창·엘리베이터 층 선택판·탑승/도착 연출이 동작한다(docs/DESIGN.md UI). 녹화 시나리오가 프롤로그, 매트 조사, 잠긴 층,
  시험용 정류장 탑승·도착, 일시정지 메뉴(조작법 쪽 포함)까지 시험한다.
- 검증 도구(`tools/verify.sh` 하나로): 프로젝트 연결 검사, 손 닿는지 검사(실제 물리), 맵 교체 누수 검사(슈트 낙하물 누수를 이것으로 찾아 고침),
  몽키 테스트(10시드 × 3만 프레임 문제 0), 녹화. 2026-10-17 밤 작업 묶음의 커밋 나누기 초안은 `build/COMMIT_DRAFT.md`(git 제외).
- 맵을 더하거나 고치면 `tools/check_project.gd`(맵끼리의 연결 검사)를 돌린다. 배치 스크립트의 소품 줄은 `tools/scene_parts.py` 하나가 쓴다.
- 시작: 검은 화면에서 첫 방이 밝아지고(깨어남) 프롤로그 서술 세 쪽 → 기본 조작 한 줄이 잠깐. Esc = 일시정지 메뉴
  (음량·글자 속도·전체 화면·깜빡임 줄이기·조작법·끝내기, `user://settings.cfg`에 저장 — 녹화·검사 도구는 읽지도 쓰지도 않음).
- 소리: 전부 코드 합성(`tools/audio/gen_sfx.py`) — UI 효과음, 소품 소리(물방울·스파크, 애니메이션 프레임에 맞춤), 발소리, 맵 바탕 소리.
- 성능: 두 맵 모두 144fps 고정(평균 6.94ms), 맵 전환은 화면이 완전히 검을 때 한 프레임 ~21ms(`tools/perf_probe.gd`).
  접촉 그림자는 텍스처별로 한 번만 만들어 재사용(`pixel_prop.gd`). 창 모드의 드문 끊김은 OS 합성기 몫 → F11 전체 화면.
- 다음: 위층 맵(L1 DEMO부터)과 엘리베이터 도착 지점(위층 맵에 엘리베이터와 `FromElevator` 마커를 두면 탑승·도착 연출이 그대로 쓰임), 권한을 얻는 이야기.
- 미결: 맵 가로 360 표준화 여부(게임 칸 1080 = 원본 360), 한글 픽셀 글꼴(갈무리) 도입, 다른 층 배경 일러스트.

## 이전 상태 (2026-10-16)
- 끝남: 시유 스프라이트·걷기, Godot 골격, 지하 고물상 시험 방(코드 그림, 조명, 애니메이션, 양탄자, 통로, 배치 규칙),
  맵 이동 시스템(`Game.change_map`, 페이드), 엘리베이터 홀(코드 그림, 배치 규칙, 지하와 양방향 이동),
  2.5D 픽셀 조명(원본 해상도 높이 버퍼 + 화면 공간 그림자 + 디더 양자화, 발광 마스크, 슈트 광선, 작업등. docs/ART_PIPELINE.md 8절).
  지하 정리(조용한 빛 = 이야기 광원만, 단품 절반으로, 더미는 크고 적게, 전부 기울고·눕고·묻힘: RotSprite 회전 `tools/art/rot.py`. ART_PIPELINE.md 9~10절).
- 다음: 엘리베이터 탑승·층 선택(아직 작동하지 않음).
- 남은 일: 소품 다듬기(앉은 안드로이드 과노출, 누운 안드로이드/다리 각도), 대화창 A안 + 반신 초상화, 공식 안정판 Godot 이전과 웹 내보내기, 컷신, 유튜브 TV 패널(보류), 위층 스테이지들.
