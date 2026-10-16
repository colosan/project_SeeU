# 에셋 출처 기록

비영리 팬게임이지만 모든 에셋의 출처를 기록합니다. 새 에셋을 추가하면 이 표에도 추가하세요.

- **도구:** 만든 도구와 모드
- **ID:** PixelLab 에셋 ID. 같은 에셋을 다시 받거나 수정할 때 씁니다.
- **레퍼런스:** 생성 때 참고한 원본. 원본 파일은 저장소에 넣지 않습니다.
- **수정:** 생성 후 직접 손댄 내용

## 캐릭터

### 시유 (SeeU) 15주년 의상

캐릭터 권리: © SBS A&T. 의상 디자인: CHRIS (SeeU 15주년 공식 의상 설계도).

| 파일 | 도구 | ID | 레퍼런스 | 수정 |
|---|---|---|---|---|
| `assets/characters/seeu/rotations/*.png` | PixelLab create_image_pro (정면) → create_character v3 high top-down (8방향 회전) | 캐릭터 `e5b7f209-5d41-4dac-8e34-24a8d1a9e982`, 정면 이미지 작업 `5f8c3873-7f14-4f41-b3ab-8e0670ef4998` (후보 2번) | 15주년 공식 의상 설계도 (나무위키 게재본), 15주년 기념 일러스트 | 피부색을 설계도 색(`#FDE9ED` 계열)으로 교체 |
| `assets/characters/seeu/walk/<방향>/frame_*.png` | PixelLab animate_character skeleton-v3, 템플릿 `walking-8-frames` | 애니메이션 그룹 `df8b53ce-cd31-4ba6-a9ff-787ee4fa2d73` | 위 캐릭터 | 없음 (오른쪽 방향은 한 번 다시 생성) |

## 지하 시험 방 (저장소에 포함)

배경은 원본 320x240 해상도로 그리고 게임에서 3배로 표시합니다.

| 파일 | 출처 | 수정 |
|---|---|---|
| `assets/env/basement/room_floor.png` | 직접 그림 (`tools/gen_basement_floor.py`로 생성, AI 미사용) | 없음 |
| `assets/env/basement/pile_junk.png` | PixelLab create_image_pixflux, 작업 `f5c7aae0-955e-4fe4-9279-74dc5d67228f` | 회색 팔레트 재매핑 후 6색으로 축소 |
| `assets/env/basement/pile_audio.png` | PixelLab create_image_pixflux, 작업 `7f57fa79-a4a5-4a30-a7be-4e135b750a0f` | 회색 팔레트 재매핑 후 6색으로 축소. 등각 시점이라 사용 중단 |
| `assets/env/basement/pile_audio2.png` | PixelLab create_map_object (방 바닥으로 스타일 맞춤), `9c88bb90-b182-44e0-b743-5e9630ba3e08` | 회색 팔레트 재매핑 |
| `assets/env/basement/pile_junk2.png` | PixelLab create_map_object (방 바닥으로 스타일 맞춤), `2263e45f-0d31-4121-989e-b29dc4e48f0d` | 회색 팔레트 재매핑 |

### 코드로 그린 고물 (현재 방식)

| 파일 | 출처 | 비고 |
|---|---|---|
| `assets/env/basement/code/*.png` | 직접 그림: `tools/art/gen_junk.py` (그리기 키트 `tools/art/pix.py`) | AI 미사용. 재질 램프 색만 사용, 정면 3/4 시점, 외곽선은 실루엣에 한 번. `a_*.png`는 프레임을 가로로 붙인 애니메이션 |
| `assets/env/basement/code/s_worklamp.png` | 직접 그림, AI 미사용: `tools/art/gen_junk.py`(`work_lamp` 부품) | 삼각대 작업등. 지하 통로 조명의 원천 |
| `assets/env/basement/digital/dg_*.png` | 직접 그림: `tools/art/gen_digital.py` (+ `digitize.py`, `pixfont.py`), AI 미사용 | 인터넷 속 세계관 판(압축 파일 상자, 비트 버킷, 오류 창, 밈 오마주 등). 각 소품의 의미와 밈 원본은 docs/WORLD_PROPS.md |
| `assets/env/basement/organic/org_*.png` | PixelLab create_map_object로 형태만 생성 → `tools/art/import_pixellab.py`로 우리 램프 색 재매핑, 잡점 정리, 외곽선 | 원본 id는 `import_pixellab.py`의 `SOURCES`에 기록 (`e4317f37…`, `5a3c7f4b…`, `c6b111a2…`, `b4d0d864…`, `bd0a4172…`, `69afa5f4…`) |

## 엘리베이터 홀 (저장소에 포함)

지하 고물상 오른쪽 출구 밖 복도와 낡은 화물 엘리베이터. 모두 직접 그림, AI 미사용(PixelLab 호출 없음). 재질 램프 색만, 정면 3/4 시점, 외곽선은 실루엣에 한 번.

| 파일 | 출처 | 비고 |
|---|---|---|
| `assets/env/elevator/hall_floor.png` | 직접 그림, AI 미사용: `tools/gen_elevator_hall_floor.py` | 320x240 원본, 3배 표시. 바닥·벽·배관·바퀴 자국·배수구 |
| `assets/env/elevator/elevator.png` | 직접 그림, AI 미사용: `tools/art/gen_elevator.py` | 화물 엘리베이터(접이식 철창문, 반원 층 표시기, 갇힌 전구, 위로 이어지는 승강로 기둥) |
| `assets/env/elevator/a_call.png` | 직접 그림, AI 미사용: `tools/art/gen_elevator.py` | 호출 버튼 깜빡임 6프레임 |
| `assets/env/elevator/a_lamp.png`, `wall_lamp.png` | 직접 그림, AI 미사용: `tools/art/gen_elevator.py` | 벽등. `a_lamp`는 깜빡이는 8프레임 |
| `assets/env/elevator/a_drip.png`, `f_drip_puddle.png`, `drum.png` | 직접 그림, AI 미사용: `tools/art/gen_elevator.py` (드럼통은 `gen_junk.barrel` 부품) | 새는 배관 물방울 10프레임, 물웅덩이, 받침 드럼통 |
| `assets/env/elevator/notice.png`, `cart.png`, `stool.png` | 직접 그림, AI 미사용: `tools/art/gen_elevator.py` (수레 위 상자는 `gen_junk.crate` 부품) | 게시판, 평판 수레, 운전수 의자 |

복도 가장자리 고물(`c_small1/2/3`)은 지하 방의 `assets/env/basement/code/` 파일을 그대로 다시 씁니다.

## 조명용 파생 텍스처 (저장소에 포함)

그림이 아니라 조명 계산용 데이터입니다. 모두 우리 도구가 원본 그림·생성기 숫자에서 만들며 AI 미사용.

| 파일 | 출처 | 비고 |
|---|---|---|
| `assets/env/**/<이름>.emit.png` | `tools/art/gen_emission.py`가 같은 이름의 그림에서 생성 | 발광 마스크(회색조, 255 = 스스로 빛남). 발광 픽셀이 있는 그림만 |
| `assets/env/basement/room_floor.height.png` | `tools/gen_basement_floor.py` | 방 높이·표면 종류 지도(R 높이, B 종류, A 덮임) |
| `assets/env/elevator/hall_floor.height.png` | `tools/gen_elevator_hall_floor.py` | 같음 |

## 타일셋

| 파일 | 도구 | ID | 레퍼런스 | 수정 |
|---|---|---|---|---|
| `assets/tilesets/test_dirt_grass/tiles.png` | PixelLab create_topdown_tileset (standard, 32px) | `19845ea5-7931-4f71-8843-d6f88324571f` | 없음 (텍스트 프롬프트) | 없음. 테스트용 임시 타일 |

## 진행 중 (아직 저장소에 넣지 않음)

| 에셋 | 도구 | ID | 비고 |
|---|---|---|---|
| 고철 매립지 바닥 타일셋 (64px) | PixelLab create_topdown_tileset (pro) | `969a3391-9fee-4708-8c2b-5771252e419d` | 오프닝 맵 |
| 매립지 소품 16종 | PixelLab create_1_direction_object | `93904c6f-1eb3-4419-b5d4-da89a54cade9` | 오프닝 맵 |
| 착지 지점 v1 (우물 모양) | PixelLab create_1_direction_object | `ed324d2b-6e24-4c17-bee8-a15a53f28498` | 폐기: 돌벽 우물처럼 나옴 |
| 착지 지점 v2 (빛줄기 아래 CD·헤드폰 더미) | PixelLab create_1_direction_object | `8f292995-25d6-4abf-aa42-f34dc6002d5b` | 오프닝 맵 |
| 쓰레기 절벽 타일셋 v1 (64px, 3단) | PixelLab create_topdown_tileset (pro) | `1bdc57b7-bfd0-4f32-b79c-ae9a2c70a450` | 폐기: 윗면이 빈 베이지색 |
| 쓰레기 절벽 타일셋 v2 (64px, 3단) | PixelLab create_topdown_tileset (pro) | `e035088f-bdea-45b0-945c-d42ec69c051c` | 바닥 타일셋과 이어짐 |
| 거대 쓰레기 산 4종 (128px) | PixelLab create_1_direction_object | `46895dcd-acff-44ca-954c-795b8f69f4ce` | 오프닝 맵 |
| 산 아래 원경 (384x216, 측면 시점) | PixelLab create_image_pro | 작업 `0e7642ed-cd51-4323-84c3-9e492cf55358` | 오프닝 컷신·타이틀용 |

### 지하 로봇 고물상 (2026-10-15 방향 전환 후)

위의 녹슨 야외 매립지 에셋은 방향 전환으로 쓰지 않습니다.

| 에셋 | 도구 | ID | 비고 |
|---|---|---|---|
| 미래형 보컬로이드 고철 소품 16종 (64px) | PixelLab create_1_direction_object | `24d96ccd-39ed-4b8d-8db3-021e1b9c737d` | 스타일 시험 |
| 금속 바닥 + 흰 잔해 더미 타일셋 (64px) | PixelLab create_topdown_tileset (pro) | `bf38f03c-a7db-46cb-8749-0f2b5334ab66` | 스타일 시험 |
| 지하 실내 벽 타일셋 (64px, 3단) | PixelLab create_topdown_tileset (pro) | `f8a26b8b-0c83-4a2e-b1e1-1581925cc6fa` | 오프닝 맵 |
| 로봇 고물상 소품 16종 (64px) | PixelLab create_1_direction_object | `c51fb84c-ead6-44c7-bd09-be963ee2b45d` | 오프닝 맵 |
| 철 색감 거대 고물 더미 4종 (168px) | PixelLab create_1_direction_object | `ffea8c8d-c9f7-4e93-91ce-7bb9913ac2de` | 오프닝 맵 |
| 초대형 고물 산 A (256px) | PixelLab create_1_direction_object | `355bf2c7-48c8-4bc3-9492-a7dc4cd001c5` | 오프닝 맵 |
| 초대형 고물 능선 B + 슈트 (256px) | PixelLab create_1_direction_object | `c10f84cb-2cbf-4c35-9d5b-f53e9cb94994` | 오프닝 맵, 철 색감 기준 후보 |
| 콘크리트 바닥 ↔ 고철 층 타일셋 (64px) | PixelLab create_topdown_tileset (pro) | `13295079-77cf-4121-9d6f-19e2e561b3c6` | 평평하게 보여 보완 필요 |
| 고철 절벽 타일셋 (64px, 3단, 벽면이 고철) | PixelLab create_topdown_tileset (pro) | `6908381a-271a-496d-a867-65e7d773258a` | 오프닝 맵. 윗면은 평평해서 더미로 덮어 씀 |
| 랜드마크: 슈트 아래 고물 산 (512x512) | PixelLab create_image_pro, 스타일 기준 = 고물 능선 B | 작업 `e053a868-9e1c-4dad-b171-ef46dbaa838f` | 오프닝 맵 착지 지점 |
| 랜드마크: 거대 로봇 잔해 (512x384) | PixelLab create_image_pro, 스타일 기준 = 고물 능선 B | 작업 `bbcebdec-b932-479e-a649-945f775086c4` | 오프닝 맵 |
| 랜드마크: 컨베이어·분쇄기·크레인 (512x384) | PixelLab create_image_pro, 스타일 기준 = 고물 능선 B | 작업 `f2f9820d-577a-4f6d-ad2a-995741b21fe6` | 오프닝 맵 |
| 철 색감 보컬로이드 장비 더미 4종 A (168px) | PixelLab create_1_direction_object | `182a8c68-e6bf-4fbe-a8e1-dd575f9fb4ed` | 스피커, 마이크 스탠드, 홀로그램 스크린, 헤드셋 |
| 철 색감 보컬로이드 장비 더미 4종 B (168px) | PixelLab create_1_direction_object | `23c51550-e1dc-4809-9106-438422969656` | 신시사이저, 무대 트러스, 안드로이드 가수들, 우주선 조종석 |

### 평면 픽셀아트 조각 (2026-10-15, 현재 방향)

그림은 평면적으로, 입체감은 겹쳐 쌓기·그림자·앞뒤 배치로 냅니다. 모두 같은 설정(pixflux, 평면 명암, 낮은 디테일, 검정 단색 외곽선, high top-down)과 같은 17색 강제 팔레트로 생성합니다.

| 에셋 | 도구 | 작업 ID |
|---|---|---|
| 상자 더미 (128) | PixelLab create_image_pixflux | `44cad68c-a4c1-4092-892d-84f80beb5caf` |
| 둥근 머리 로봇 (128) | PixelLab create_image_pixflux | `409a7dc4-3d53-4094-aeca-d6866f9058ee` |
| 스피커 (96x128) | PixelLab create_image_pixflux | `e606b449-3de0-4d36-a0b3-b6da32d66fe3` |
| 모니터 (96) | PixelLab create_image_pixflux | `e156b511-e9a3-40ee-a78c-ba8b6f4dca4f` |
| 고철 조각 더미 (192x128) | PixelLab create_image_pixflux | `f7ff9ed3-2a12-4b7e-8b75-e51a7946c568` |
| 케이블 (96x64) | PixelLab create_image_pixflux | `c856f3f4-726a-49f7-9c6f-c3858f7c6f6b` |

### 굵은 픽셀 배경 (절반 해상도 → 2배 표시, 회색 팔레트)

캐릭터는 128px 원래 크기, 배경은 절반 해상도로 그려 2배로 표시합니다. 색은 22색 회색 팔레트로 맞춥니다(생성 후 로컬에서 팔레트 재매핑).

| 에셋 | 도구 | ID |
|---|---|---|
| 지하 바닥·벽 타일셋 (32px, 3단) | PixelLab create_topdown_tileset (standard) | `57551280-635a-40d3-99c3-5186ef0a4960` |
| 잡동사니 더미 A (112x88) | PixelLab create_image_pixflux | 작업 `f5c7aae0-955e-4fe4-9279-74dc5d67228f` |
| 음향 장비 더미 B (112x88) | PixelLab create_image_pixflux | 작업 `7f57fa79-a4a5-4a30-a7be-4e135b750a0f` |
| 로봇 더미 C (112x88) | PixelLab create_image_pixflux | 작업 `80b1974e-231f-46a4-a86e-0105032373d2` |
| 고물 산 배경 (240x148) | PixelLab create_image_pixflux | 작업 `d966aa37-9987-4965-8fb5-b4c07255e5ce` |
| 마이크 스탠드 (32x48) | PixelLab create_image_pixflux | 작업 `8359f2dd-7944-4b58-ba2f-44ef785f2c82` |
| 주저앉은 안드로이드 (48x48) | PixelLab create_image_pixflux | 작업 `8751e13a-bdd6-438b-bc82-e481ee4b2e47` |
| 모니터 (40x32) | PixelLab create_image_pixflux | 작업 `d1c8c909-3613-470f-bac3-c31bc8c21033` |

## 참고

- PixelLab 이용 약관: https://pixellab.ai/termsofservice
- 공식 일러스트와 설계도는 생성 레퍼런스로만 쓰고 저장소와 배포본에 넣지 않습니다.
