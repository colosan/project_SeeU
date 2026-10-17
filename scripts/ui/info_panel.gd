extends PanelContainer
## Right panel: SeeU's standing illustration in front of a backdrop of the floor she is on (it changes with
## the floor); the floor's broadcast TV (YouTube embed, on hold — docs/DESIGN.md UI) hangs at the top and a
## short status line with the inventory sits on her lower part over a fade. No boxes around the parts.
## Until the illustration exists, a plain silhouette is drawn in code where she will stand.

## SeeU's standing illustration. Null = the local cut-out of the official design sheet if it exists
## (LOCAL_STANDING, made by tools/art/cut_standing.py, never committed), else a drawn stand-in.
@export var standing_texture: Texture2D
## Scale of the illustration and where its top sits in a 1080-tall panel: her head under the TV (never behind it),
## low enough that her shoes (from row ~735 of the cut-out) run off the panel's bottom; the fade covers her shins.
## A taller panel (a taller window, see Game._fit_window) keeps her pinned to the bottom, so the shoes stay hidden.
@export var standing_scale := 1.0
@export var standing_top := 360.0
const DESIGN_H := 1080.0                  # the panel height standing_top is measured in
## Dimmed so the painted illustration sits behind the game instead of pulling the eye off the dark,
## muted pixel world next to it.
@export var standing_tint := Color(0.72, 0.72, 0.76)

const LOCAL_STANDING := "res://reference/seeu_standing.png"

## The backdrop behind her on each floor (pixel art, shown at BACKDROP_SCALE, centred, dimmed by backdrop_tint so
## she and the text stay in front). Which floor a map is on: Game.PLACES.
const BACKDROPS := {"L0": "res://assets/ui/backdrop_l0.png"}
const BACKDROP_SCALE := 2
@export var backdrop_tint := Color(0.62, 0.62, 0.68)

const TV_SIZE := Vector2(384, 216)       # 16:9, the panel width minus padding
const SLOTS := 6
const SLOT := 59                          # 6 slots + 5 gaps of 6 = the panel's inner width (420 - 2 x 18), as wide as the TV

var _stage: Control
var _backdrop: TextureRect
var _floor := ""
var _tv: TvScreen


func _ready() -> void:
	add_theme_stylebox_override("panel", UiStyle.panel_bg(SIDE_LEFT))
	var root := Control.new()
	root.clip_contents = true
	add_child(root)

	# layer 0: the backdrop of the floor she is on (set by _on_map_changed)
	_backdrop = TextureRect.new()
	_backdrop.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_backdrop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_backdrop.modulate = backdrop_tint
	root.add_child(_backdrop)
	root.resized.connect(func() -> void: _place_backdrop(root))

	# layer 1: the standing illustration, the whole panel
	var tex := standing_texture
	if tex == null and ResourceLoader.exists(LOCAL_STANDING):
		tex = load(LOCAL_STANDING)
	if tex != null:
		var art := TextureRect.new()
		art.texture = tex
		art.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		art.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR     # a painted illustration, not pixel art
		art.mouse_filter = Control.MOUSE_FILTER_IGNORE
		art.size = tex.get_size() * standing_scale
		art.modulate = standing_tint
		root.add_child(art)
		root.resized.connect(func() -> void:
			art.position = Vector2(roundf((root.size.x - art.size.x) / 2.0), standing_top + root.size.y - DESIGN_H))
	else:
		_stage = Control.new()
		_stage.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		_stage.draw.connect(_draw_stand_in)
		root.add_child(_stage)

	# layer 2: fade at the bottom so the status reads on top of her
	var fade := UiStyle.fade_hold(UiStyle.BG, 0.55, false)   # solid behind the status block, then gone upward
	fade.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	fade.offset_top = -380
	root.add_child(fade)

	# layer 3: TV at the top, status + inventory at the bottom
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, UiStyle.PAD)
	root.add_child(margin)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 9)
	margin.add_child(v)

	v.add_child(UiStyle.header("ON AIR"))
	# the TV: a bezel around a dead channel until the YouTube embed exists (scripts/ui/tv_screen.gd)
	var tv := PanelContainer.new()
	tv.custom_minimum_size = TV_SIZE
	var bezel := UiStyle.panel_box_all(Color("08090a"), UiStyle.LINE_HI)
	bezel.set_content_margin_all(UiStyle.BORDER)
	tv.add_theme_stylebox_override("panel", bezel)
	_tv = TvScreen.new()
	tv.add_child(_tv)
	v.add_child(tv)

	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(spacer)

	v.add_child(UiStyle.header("STATUS"))
	v.add_child(UiStyle.label("시유", 27, UiStyle.TEXT_HI))
	v.add_child(UiStyle.label("목소리  404 Voice Not Found     음소  0", 16, UiStyle.ACCENT_HI))
	var slots := HBoxContainer.new()
	slots.add_theme_constant_override("separation", 6)
	for i in SLOTS:
		var s := Panel.new()
		s.custom_minimum_size = Vector2(SLOT, SLOT)
		var box := StyleBoxFlat.new()
		box.bg_color = Color(UiStyle.BG, 0.7)
		box.border_color = UiStyle.LINE_HI
		box.set_border_width_all(UiStyle.BORDER)
		s.add_theme_stylebox_override("panel", box)
		slots.add_child(s)
	v.add_child(slots)
	root.add_child(UiStyle.edge_shade(SIDE_LEFT))           # the panel sits a step behind the game

	Game.map_changed.connect(_on_map_changed)
	(func() -> void:
		if Game.current_map() != null:
			_on_map_changed(Game.current_map())).call_deferred()


func _on_map_changed(map: Node) -> void:
	var floor_id: String = Game.place_of(map).get("floor", "")
	if floor_id == _floor:
		return
	_floor = floor_id
	_tv.channel = "CH %s  %s" % [floor_id, Game.floor_info(floor_id).get("sign", "")] if floor_id != "" else ""   # this floor's channel
	var path: String = BACKDROPS.get(floor_id, "")
	var tex: Texture2D = load(path) if path != "" and ResourceLoader.exists(path) else null
	if _backdrop.texture != null and tex != _backdrop.texture:   # a new floor: the old backdrop fades out over it
		var old := _backdrop.duplicate() as TextureRect
		_backdrop.add_sibling(old)
		var tw := old.create_tween()
		tw.tween_property(old, "modulate:a", 0.0, 0.6)
		tw.tween_callback(old.queue_free)
	_backdrop.texture = tex
	_place_backdrop(_backdrop.get_parent() as Control)


func _place_backdrop(root: Control) -> void:
	if _backdrop.texture == null:
		return
	_backdrop.size = _backdrop.texture.get_size() * BACKDROP_SCALE
	_backdrop.position = Vector2(roundf((root.size.x - _backdrop.size.x) / 2.0), 0.0)


## Stand-in for the illustration: a flat silhouette (head, long twin tails, shoulders, body) where she will
## stand, cropped at the knees by the panel's bottom edge.
func _draw_stand_in() -> void:
	var c := _stage
	var w := c.size.x
	var h := DESIGN_H
	c.draw_set_transform(Vector2(0, c.size.y - DESIGN_H))      # pinned to the bottom like the illustration
	var cx := w * 0.55
	var body := UiStyle.BOX.lerp(UiStyle.LINE, 0.5)
	var hair := UiStyle.BOX
	c.draw_rect(Rect2(cx - 132, 390, 54, h - 420), hair)       # twin tails behind
	c.draw_rect(Rect2(cx + 78, 390, 54, h - 420), hair)
	c.draw_circle(Vector2(cx, 405), 75.0, body)                 # head
	c.draw_rect(Rect2(cx - 24, 465, 48, 45), body)              # neck
	c.draw_colored_polygon(PackedVector2Array([                 # shoulders down to the knees
		Vector2(cx - 105, 507), Vector2(cx + 105, 507), Vector2(cx + 135, h), Vector2(cx - 135, h)]), body)
	var font := c.get_theme_default_font()
	c.draw_string(font, Vector2(0, 660), "시유 스탠딩 일러스트 자리", HORIZONTAL_ALIGNMENT_CENTER, w, 15, UiStyle.TEXT_DIM)
