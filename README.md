# project_SeeU

시유(SeeU)를 비롯한 보컬로이드 캐릭터들이 나오는 탑다운 쯔꾸르풍 팬게임입니다. Godot 4로 만드는 연습용 프로젝트예요.

> 비공식 팬게임이며 SBS A&T 및 각 캐릭터 권리사와 무관합니다. 비영리·무료로만 배포합니다.

## 현재 상태

- 엔진: Godot 4.8 (GDScript)
- 배포 예정: itch.io 웹 빌드 (Chrome 기준)
- 에셋: PixelLab 등 AI 도구로 직접 생성. 공식 일러스트와 설계도 원본은 저장소에 넣지 않습니다.

## 에셋

`assets/characters/seeu/`

- `rotations/`: 8방향 정지 스프라이트 (128x128, high top-down)
- `walk/<방향>/`: 4방향 걷기 애니메이션 8프레임 (PixelLab skeleton-v3)

시유 15주년 의상 디자인을 기준으로 했어요.

## 문서

- [CLAUDE.md](CLAUDE.md): 작업 규칙 요약 (AI 작업 세션이 가장 먼저 읽는 파일)
- [docs/WORLD.md](docs/WORLD.md): 세계관 설정서
- [docs/DESIGN.md](docs/DESIGN.md): 세계관, 화면 구성, 결정 사항
- [docs/ART_PIPELINE.md](docs/ART_PIPELINE.md): 배경·소품 그리는 법 (코드 그리기, PixelLab 가져오기, 배치 규칙)
- [docs/WORKFLOW.md](docs/WORKFLOW.md): 실행, 검증, 커밋 방법과 현재 진행 상황
- [docs/ASSETS.md](docs/ASSETS.md): 모든 에셋의 출처
