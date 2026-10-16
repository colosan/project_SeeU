# 캐릭터 스프라이트 만드는 법 (시유 사례)

2026-10-14에 시유 맵 스프라이트를 만들면서 겪은 시행착오와, 결국 통한 방법을 정리했다.
다른 보컬로이드나 NPC를 만들 때도 이 순서를 따른다. 배경·소품은 [ART_PIPELINE.md](ART_PIPELINE.md), 출처 기록은 [ASSETS.md](ASSETS.md).

## 1. 요약: 통한 방법
1. **먼저 세 가지를 정한다**: 디자인 기준(공식 설계도), 크기(**128px**), 시점(**high top-down**). 이 셋 중 하나가 바뀔 때마다 처음부터 다시 했다.
2. **정면 한 장을 `create_image_pro`로 뽑는다**: 128x128, 배경 없음, 설계도를 레퍼런스로 넣는다. 한 번에 후보 4개(10 generations).
3. **고른 정면을 손본다**: 피부색을 설계도 색으로 바꾸고(매번 필요), 거슬리는 픽셀 몇 개만 고친다. 얼굴을 AI로 다시 그리지 않는다.
4. **정면을 high top-down 시점으로 다시 뽑는다**: 눈높이 정면을 레퍼런스로 넣고 "위에서 내려다본 시점"으로 `create_image_pro`. 피부색을 다시 바꾼다.
5. **`create_character` v3로 8방향을 돌린다**: `reference_image_url` = 손본 정면, `view` = `high top-down`(정면 그림의 시점과 같아야 한다). 2 generations.
6. **걷기는 `animate_character` skeleton-v3**: 템플릿 `walking-8-frames`, 상하좌우 4방향, 방향당 3 generations. 템플릿 모드는 쓰지 않는다.
7. **GIF로 확인하고, 나쁜 방향만 지우고 다시 뽑는다**: `delete_animation(group, direction)` → 같은 그룹에 `animate_character`.
8. **zip으로 받아 `assets/characters/<이름>/`에 넣는다** (6절).

얼굴 디테일(별 모양 안광, V자 턱)은 맵 스프라이트에서 포기했다. 대화창 반신 초상화에서 살린다(아직 안 만듦).

## 2. 시행착오 순서
| # | 시도 | 결과 | 배운 것 |
|---|---|---|---|
| 1 | `create_character` **pro 모드**, 2011 원작 일러스트를 `concept_image_url`로, 32·48px, low top-down | 원작 디자인이 오래돼서 사용자 반려 | 디자인 기준부터 확정할 것 |
| 2 | 같은 pro 모드, 15주년 기념 일러스트로 64px | 정면이 좌우로 늘어나고 얼굴이 가로로 긴 타원, 대각선 방향의 입체감이 이상함 | pro 모드는 일러스트에서 바로 8방향을 지어내서 형태가 무너진다. 정면부터 따로 뽑는다 |
| 3 | `create_image_pro` 64px 정면(후보 16개) | 16개 모두 턱이 일직선 | 64px에서는 얼굴 폭 약 16px, 턱 2~3줄, 눈 4x3px라 V자 턱과 별 안광을 그릴 자리가 없다 |
| 4 | 64px 턱을 손으로 깎기 | 더 어색해서 버림 | 해상도 한계는 손질로 못 넘는다 |
| 5 | **128px**로 올리면서 프롬프트에 "V자 턱, 별 안광" 명시 | 사용자가 결과 전에 중단("명시하면 더 이상해질 것") | 얼굴 형태는 프롬프트에 쓰지 않는다 |
| 6 | 128px, 턱 묘사 없이 안광만 묘사 | 턱선이 저절로 좁아지고 등신도 일러스트에 가까워짐. 안광은 여전히 흰 점 | 해상도가 답이었다 |
| 7 | 15주년 **공식 설계도**를 기준으로 정면·뒷모습을 새로 뽑음(각 후보 4개) | 설계도 요소가 거의 다 들어감. 정면 1번 채택 | 일러스트보다 설계도(앞·뒤 전신)가 레퍼런스로 낫다 |
| 8 | 정면 얼굴만 `inpaint_image_pro_flash`로 다시 그리기(2안), 눈에 별 안광을 손으로 찍기 | 사용자: "기본이 제일 낫다" | AI 얼굴 재작업과 손 안광은 원본보다 못하다 |
| 9 | 피부를 밝게 톤업 | 사용자: 설계도 같은 연분홍을 원함 | 피부색은 설계도에서 직접 뽑는다(5절) |
| 10 | 입의 "이빨" 픽셀을 진한 선 3개로 덮음 | 너무 진해서 반려 | 원래 여러 톤이던 입은 2픽셀만 고친다(5절) |
| 11 | 정면+뒷모습 두 장을 v3에 넣는 안 | 뒷모습 머리 볼륨이 정면보다 좁아 불일치 → 정면 한 장만 사용 | 따로 뽑은 뒷모습은 정면과 안 맞는다. 정면 한 장이 기준 |
| 12 | v3 8방향, `view: low top-down` | 맵 위에서 입간판처럼 보임("이거 탑다운 맞아?") | v3는 레퍼런스 그림의 카메라 각도를 따라간다. 눈높이 정면을 넣으면 눈높이 8방향이 나온다 |
| 13 | 정면을 high top-down으로 다시 뽑음(후보 4개) → 1번(A, 팔 내림)·2번(B, 가방끈을 잡음) 둘 다 v3 `high top-down` | 둘 다 맵에 잘 붙음. 뒷모습도 머리가 갈라지며 후드가 보임. **B 채택**(로제트·마스코트가 잘 보임) | 시점은 정면 그림에서 해결하고, v3 `view`를 같게 맞춘다 |
| 14 | B의 팔만 inpaint(2안, 약 12 generations) | 반려. 사용자: 문제는 팔 모양이 아니라 자세, 애니메이션을 보고 판단 | 정지 화면으로 자세를 판단하지 말고 걷기 GIF로 본다 |
| 15 | 걷기 **템플릿 모드**(4방향) | 매 프레임 새로 그려서 가방끈·15 로제트·마스코트가 사라지고, 웨이브 머리가 직모가 되고, 뒤에서 모자가 사라지고, 오른쪽은 다리가 회색이 됨 | 템플릿 모드는 디자인을 지킨다는 보장이 없다 |
| 16 | 걷기 **skeleton-v3**(정면 먼저, GIF 비교 후 나머지 3방향) | 모자·웨이브 머리·가방끈·로제트·줄무늬 니삭스가 8프레임 내내 유지됨. 가방끈을 잡은 팔 자세도 그대로 남음(가방끈을 잡고 걷는 느낌, 사용자 승인) | skeleton-v3는 지금 스프라이트를 뼈대로 움직인다. 정면 자세가 곧 걷는 자세다 |
| 17 | 오른쪽 걷기 3프레임에서 홀로그램 리본이 막대처럼 뻗음 → 다시 뽑기 | 같은 방향으로 `animate_character`를 부르면 "already complete"만 돌아옴. `delete_animation(direction="east")` 후 다시 생성하니 정상 | PixelLab은 이미 있는 방향을 다시 만들지 않는다. 먼저 지운다 |

## 3. 레퍼런스 구하기
- 위키 이미지는 외부에서 바로 못 가져온다. Fandom은 PixelLab이 URL로 가져가면 403을 내고, `curl` 원본 주소는 Cloudflare 확인 페이지(HTML)를 준다.
  - Fandom: `.../revision/latest/scale-to-width-down/640?cb=...` 주소를 브라우저 User-Agent와 `Referer: https://vocaloid.fandom.com/`로 `curl` → WebP → PIL로 PNG.
  - 나무위키 이미지(`i.namu.wiki`): 브라우저 User-Agent와 `Referer: https://namu.wiki/`로 `curl`.
  - 받은 파일에 `file`을 돌려 HTML이 아닌지 꼭 확인한다.
- 설계도는 앞모습과 뒷모습을 잘라서 각각 올렸다(시유 설계도에서는 x 105~525가 앞, 580~930이 뒤).
- 올리기: `get_upload_url`(15분 유효, 여러 번 사용 가능) → `curl -F "file=@그림.png" <url>` → 응답의 `upload:<id>`를 레퍼런스로 쓴다(3일 유지).
- **공식 그림과 설계도는 저장소에 넣지 않는다.** 작업 폴더(스크래치패드)에만 둔다.

## 4. 실제로 쓴 값
### 4-1. 눈높이 정면 (설계도 기준, 7번)
`create_image_pro`, `width/height` 128, `no_background` true, 레퍼런스 = 설계도 앞모습(`usage`: "official front design sheet: copy the face, hair, outfit, accessories and colors exactly").
```
Full-body pixel art game sprite of SeeU in her 15th anniversary outfit, standing straight, facing directly toward the viewer
(front view), symmetrical neutral pose, arms relaxed at her sides, eyes open. Big blue eyes with a white star-shaped highlight
in each eye, small smile. Long wavy pale blonde hair in two twin tails. Orange pilot cap with black cat ears, white fluffy
cloud-like fur trim and ear flaps. Orange parka with fluffy white cloud fur collar, worn off the shoulders, long sleeves with
cream cuffs. Black collared shirt, orange necktie, light grey V-neck vest. Holographic iridescent shoulder strap across the
chest with an orange "15" rosette brooch and a big holographic ribbon, small white cat mascot plush bag at her hip. Fluffy
white tutu skirt with brown checkered lace frill hem. White knee socks with two orange stripes. Orange, black and white
high-top sneakers. Soft anime cel shading, high quality detailed pixel art.
```
- 의상을 하나하나 영어로 적었다. 설계도만 넣고 설명을 줄이면 작은 장식이 빠진다.
- 후보를 고를 때: 눈을 뜨고, 팔을 내리고, 다리를 모은 것. 손을 흔들거나 윙크·눈 감은 후보는 회전 기준으로 못 쓴다.

### 4-2. high top-down 정면 (13번)
`create_image_pro` 128, 레퍼런스 = 4-1을 손본 정면(`usage`: "character base: copy this exact character design, outfit, colors, face and pixel art style").
```
Top-down RPG game character sprite of the same girl, viewed from above at a high top-down 3/4 angle (camera looking down
about 35-45 degrees, like a classic top-down RPG): the top of her head and cap is visible, head appears slightly larger,
shoulders seen from above, legs foreshortened and shorter, feet seen from above. Facing south toward the camera, standing
straight, arms relaxed at her sides, symmetrical neutral pose. Keep exactly the same outfit, colors, hair and face as the
reference sprite.
```
- 결과는 4등신과 치비 사이 비율이 됐다. 쯔꾸르 느낌에 가까우면서 디자인은 유지된다.
- "arms relaxed"라고 적어도 후보마다 자세가 다르다(2번은 가방끈을 잡음, 3·4번은 손을 허리에). 채택한 B가 바로 그 2번이다.

### 4-3. 8방향 회전
`create_character`: `mode` "v3", `reference_image_url` = 피부색을 바꾼 high top-down 정면, `n_directions` 8, `view` "high top-down".
`description`에는 의상을 짧게 다시 적었다(뒤에서 보이는 날개·가방 포함):
`SeeU in her 15th anniversary outfit, high top-down RPG view: long voluminous wavy pale blonde hair in two twin tails, orange pilot cap with black cat ears and white fluffy fur trim, orange parka with white cloud fur collar and small white wings on the back, black shirt with orange tie, grey vest, holographic shoulder strap with a white cat mascot plush bag, white tutu skirt with brown plaid frill, white knee socks with orange stripes, orange high-top sneakers`

### 4-4. 걷기
`animate_character`: `template_animation_id` "walking-8-frames", `mode` "skeleton-v3", `directions` ["south"]부터.
정면을 GIF로 확인한 뒤 같은 `animation_group_id`로 ["east", "north", "west"]를 추가했다.
대각선 4방향은 아직 없다(이동이 상하좌우뿐이라서).

## 5. 생성 뒤 손질 (Python + PIL, 정확한 색 치환만)
- **피부색**: 생성기는 매번 살구색·누런 피부로 돌려놓는다. 레퍼런스에 분홍 피부를 넣어도 마찬가지였다. 생성할 때마다 다시 바꾼다.
  - 기준색: 설계도 허벅지에서 가장 많이 쓰인 색 `#FDE9ED`(253, 233, 237).
  - 바꿀 색 찾는 법: 피부처럼 보이는 색 후보를 하나씩 빨갛게 칠한 확인 이미지를 만들어, 실제로 얼굴·손·다리에만 있는 색을 고른다(머리카락·퍼 장식과 겹치는 색은 빼기).
  - 눈높이 정면: (252,224,215)→(253,233,237), (237,200,183)→(244,212,220), (216,155,154)→(228,180,192)
  - high top-down 정면(최종): (253,235,222)→(253,233,237), (250,223,205)→(244,212,220)
- **입**: 오른쪽 끝 노란 픽셀 1개(`#F5DAB6`)가 이빨처럼 보였다. 그 픽셀을 옆과 같은 (244,212,220)로, 가운데 1픽셀을 (232,190,200)으로 바꿨다. 사용자는 원본과 차이를 못 느꼈다.
- 얼굴은 그 밖에 손대지 않았다. 별 안광은 흰 점 그대로다.

## 6. 받기와 Godot 연결
- zip 받기: `https://api.pixellab.ai/mcp/characters/<캐릭터 id>/download`
  - `Idle/rotations/<방향>.png`(8방향, 128x128) → `assets/characters/seeu/rotations/`
  - `Idle/animations/walk_skv3/<방향>/frame_000~007.png` → `assets/characters/seeu/walk/<방향>/`
  - **주의**: 같은 zip에 템플릿 모드로 만든 `Idle/animations/walk/`(디자인이 망가진 것)도 들어 있다. 쓰지 않는다.
- skeleton-v3 프레임은 **176x176**(위아래좌우로 24px 여백)이고 정지 그림은 128x128이다. 둘 다 중앙 정렬이라 Godot에서 발 위치가 맞는다.
- `scripts/characters/character_frames.gd`: 폴더에서 `idle_<방향>`, `walk_<방향>`(10fps) 애니메이션을 만든다. 상하좌우만 쓴다.
- `scenes/characters/player.tscn`: Sprite `offset = (0, -59)` → 노드 원점이 발(128px 그림의 y≈123)에 온다. 충돌 상자는 발 36x16.
- 표시 배율은 **1배**(128px 그대로). 배경은 320x240을 3배로 보여 주므로 시유가 배경보다 픽셀이 가늘다. 사용자가 정한 예외다.

## 7. ID와 비용
| 이름 | ID | 상태 |
|---|---|---|
| **최종 캐릭터** "SeeU 15th HTD B" | `e5b7f209-5d41-4dac-8e34-24a8d1a9e982` | 사용 중 |
| 최종 걷기 그룹 `walk_skv3`(skeleton-v3, 4방향) | `df8b53ce-cd31-4ba6-a9ff-787ee4fa2d73` | 사용 중 |
| high top-down 정면 작업(후보 4개, index 1 = B) | `5f8c3873-7f14-4f41-b3ab-8e0670ef4998` | B의 원본 |
| 템플릿 모드 걷기 그룹 `walk` | `84c55aef-54f7-4779-9ec8-f50670da6d5d` | 안 씀(같은 캐릭터에 남아 있음) |
| "SeeU 15th HTD A"(팔 내린 안) | `7a425a16-f686-41b3-bd4f-d286d6a8c3c8` | 안 씀 |
| "SeeU 15th 128"(v3, 눈높이) | `1065c74a-1798-4974-b496-b3e00b7dd2e6` | 반려 |
| "SeeU 64 (15th)"(pro 모드) | `f6822048-7d42-436e-8ce1-04f9c9dc4a9b` | 반려 |
| "SeeU 48" / "SeeU 32"(pro 모드, 원작) | `1f6023d0-f89b-40d1-9d41-35a82c137afb` / `4b7e82f5-c4c9-40e3-8778-4e797680fa9e` | 반려 |

| 도구 | 비용(generations) |
|---|---|
| `create_character` pro 모드 | 10 / 캐릭터 |
| `create_image_pro` | 10 / 호출 (64px 이하는 후보 16개, 86~170px는 4개) |
| `create_character` v3 | 2 / 캐릭터 |
| `inpaint_image_pro_flash` 128px | 약 6 / 호출 |
| `animate_character` 템플릿 128px | 최대 2 / 방향 |
| `animate_character` skeleton-v3 | 3 / 방향 |

시유 한 명에 시행착오까지 약 130~150 generations가 들었다. 아래 순서대로만 하면 약 30이면 된다
(설계도 정면 10 + high top-down 정면 10 + v3 2 + 걷기 4방향 12).

## 8. 다음 캐릭터 체크리스트
- [ ] 디자인 기준 그림(가능하면 앞·뒤 전신 설계도)을 정하고 스크래치패드에 받는다. 저장소에는 넣지 않는다.
- [ ] 크기 128px, high top-down으로 시유와 맞춘다(바꾸려면 사용자 결정).
- [ ] 정면을 `create_image_pro`로: 의상을 전부 영어로 적고, 얼굴 형태(턱 등)는 적지 않는다.
- [ ] 정면 자세를 고를 때 **이 자세 그대로 걷는다**는 걸 기억한다(skeleton-v3).
- [ ] 피부색 등 기준색을 설계도에서 뽑아 정확히 치환한다. 생성할 때마다 다시 한다.
- [ ] high top-down 정면 → v3 `view: high top-down` → 맵 위(Godot)에서 크기와 시점을 확인한다.
- [ ] 걷기 skeleton-v3를 정면 한 방향만 먼저 뽑아 GIF로 보고, 괜찮으면 나머지 방향.
- [ ] 이상한 방향은 `delete_animation(direction=...)` 후 다시 뽑는다. 장식이 팔·무기처럼 뻗는 프레임이 없는지 본다.
- [ ] zip에서 skeleton-v3 폴더만 가져온다. [ASSETS.md](ASSETS.md)에 도구·ID·레퍼런스·손질 내용을 적는다.
- [ ] 얼굴 디테일이 중요하면 대화창 반신 초상화로 따로 만든다(맵 스프라이트에서 해결하려 하지 않는다).

## 9. 아직 없는 것
- 대각선 걷기, 대기(숨쉬기) 애니메이션, 달리기.
- 대화창 반신 초상화(UI A안, [DESIGN.md](DESIGN.md) UI 절). 별 안광과 V자 턱은 여기서 살린다.
- 다른 보컬로이드 캐릭터.
