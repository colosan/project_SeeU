# 작업 흐름 (실행·검증·커밋)

## 환경
- Windows, 저장소 `D:\MIDAS\project_SeeU`. Git Bash와 PowerShell 둘 다 사용 가능. Python 3 + Pillow.
- Godot: `D:\MIDAS\godot\bin\godot.windows.editor.dev.x86_64(.console).exe` (직접 빌드 4.8 dev). 공식 안정판 설치 후 경로를 이 문서에 갱신할 것.
- PixelLab MCP(사용자 범위로 등록됨). 잔량 확인 `get_balance`. 생성 비용은 도구마다 다름: pixflux/map_object 1, create_image_pro 10~25, 타일셋 pro 25, 캐릭터 v3 2, skeleton-v3 걷기 방향당 3.

## 검증 루틴 (그림·배치를 바꿨으면 항상)
1. 생성: `python tools/art/gen_junk.py`, `python tools/art/gen_elevator.py`(필요 시 `--force`), 바닥 `python tools/gen_basement_floor.py`, `python tools/gen_elevator_hall_floor.py`
   (바닥 그림과 함께 조명용 `.height.png`도 씀), 발광 마스크 `python tools/art/gen_emission.py`(그림을 바꿨으면 항상),
   배치 `python tools/layout_basement.py`, `python tools/layout_elevator_hall.py`(둘 다 문제 0개여야 함. 빛의 원천 검사 포함).
2. 임포트: `godot --headless --path . --import`
3. 빠른 실행: `godot --headless --path . --quit-after 30` — 오류가 없어야 함.
4. 녹화: `cmd /c tools\record_autoplay.cmd` → `build/autoplay/f*.png`(30fps). 시나리오는 `tools/autoplay_record.gd`의 STEPS
   (키를 누른 채 위치·맵 조건까지 진행: 양탄자 → 통로 → 출구 → 페이드 → 엘리베이터 앞 → 다시 지하로).
5. 프레임을 직접 보고 확인: 떠 있는 물건, 길 막힘/가림, 시점 어긋남, 반복 패턴. 사용자에게는 실제 화면 PNG와 GIF를 보낸다.
   조명: 그림자가 빛 반대쪽으로 지는지, 원천(전구·화면·스파크)이 밝게 살아 있는지, 허공이 밝아지지 않는지, 빛 픽셀이 3배 격자에 맞는지, 통로가 가장 밝은 띠인지.
   조명 버퍼를 직접 보려면 HeightVP/LightVP(`Lighting` 노드 밑)의 텍스처를 `get_image()`로 저장한다.

## Git
- 로컬 신원 `colosan <mljs0912@gmail.com>`(저장소 설정). 전역(회사 계정)은 건드리지 않는다.
- 커밋 메시지 끝: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- `build/`, `.godot/`은 무시됨. `.gitattributes`로 LF 고정.
- 기록을 다시 쓰는 강제 푸시는 사용자 허락이 있을 때만.

## 현재 상태 (2026-10-16)
- 끝남: 시유 스프라이트·걷기, Godot 골격, 지하 고물상 시험 방(코드 그림, 조명, 애니메이션, 양탄자, 통로, 배치 규칙),
  맵 이동 시스템(`Game.change_map`, 페이드), 엘리베이터 홀(코드 그림, 배치 규칙, 지하와 양방향 이동),
  2.5D 픽셀 조명(원본 해상도 높이 버퍼 + 화면 공간 그림자 + 디더 양자화, 발광 마스크, 슈트 광선, 작업등. docs/ART_PIPELINE.md 8절).
- 다음: 엘리베이터 탑승·층 선택(아직 작동하지 않음).
- 남은 일: 소품 다듬기(앉은 안드로이드 과노출, 누운 안드로이드/다리 각도), 대화창 A안 + 반신 초상화, 공식 안정판 Godot 이전과 웹 내보내기, 컷신, 유튜브 TV 패널(보류), 위층 스테이지들.
