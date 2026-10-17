extends PanelContainer
## Left panel: one tall illustration of the whole world (the Stack seen from outside, docs/WORLD.md), seen
## through the panel like a window that scrolls to where SeeU is. No boxes: the picture fills the panel, the
## place name sits on it. It is a picture of the world, not a plan of the game's rooms.

## The illustration (PixelLab art assembled by tools/art/gen_stack_map.py), shown 1:1.
## The tower is enormous next to the game's rooms: neighbouring rooms sit a few dozen px apart on it.
@export var map_texture: Texture2D
const MAP_SCALE := 1

const TOWER_CENTRE_X := 220.0            # the tower's axis on the illustration (px)
const FOLLOW := 0.62                      # the current place sits this far down the window

var _view: Control                        # clips the map
var _map: Control                         # the whole map picture, moved to scroll
var _floor_label: Label
var _place_label: Label
var _place := {}
var _tween: Tween
var _marker: Control                      # "you are here", over the map AND its fades/edge shade


func _ready() -> void:
	add_theme_stylebox_override("panel", UiStyle.panel_bg(SIDE_RIGHT))
	_view = Control.new()
	_view.clip_contents = true
	add_child(_view)
	_map = Control.new()
	_map.size = map_texture.get_size() * MAP_SCALE if map_texture != null else Vector2.ZERO
	_map.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_map.draw.connect(_draw_map)
	_view.add_child(_map)

	var top := UiStyle.fade_hold(UiStyle.BG, 0.55)          # solid behind the title and place name, then gone
	top.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	top.offset_bottom = 230
	_view.add_child(top)

	# text laid straight on the picture, all at the top: the tower's foot (where the game starts) is the
	# bottom of the picture, so the bottom of the panel stays clear
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, UiStyle.PAD)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_view.add_child(margin)
	var v := VBoxContainer.new()
	margin.add_child(v)
	v.add_theme_constant_override("separation", 6)
	v.add_child(UiStyle.header("THE STACK"))
	_floor_label = UiStyle.label("", 16, UiStyle.ACCENT_HI)
	_place_label = UiStyle.label("", 27, UiStyle.TEXT_HI)
	v.add_child(_floor_label)
	v.add_child(_place_label)

	_view.add_child(UiStyle.edge_shade(SIDE_RIGHT))       # the panel sits a step behind the game
	_marker = Control.new()
	_marker.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_marker.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_marker.draw.connect(_draw_marker)
	_view.add_child(_marker)

	Game.map_changed.connect(_on_map_changed)
	_view.resized.connect(_scroll.bind(true))
	_pick_up_current_map.call_deferred()


func _pick_up_current_map() -> void:
	if Game.current_map() != null:
		_on_map_changed(Game.current_map(), true)


func _on_map_changed(map: Node, snap := false) -> void:
	_place = Game.place_of(map)                # where every map is: Game.PLACES
	var floor_id: String = _place.get("floor", "?")
	_floor_label.text = "%s  ·  %s" % [floor_id, Game.FLOOR_NAMES.get(floor_id, "?")]
	_place_label.text = _place.get("name", String(map.name))
	_scroll(snap)
	_marker.queue_redraw()                     # the marker moves with the name, not on its next pulse


## Scroll the map so the current place sits at FOLLOW of the window (on whole art pixels).
func _scroll(snap: bool) -> void:
	# the picture is wider than the panel: keep the TOWER centred (it is not centred in the picture), the sky
	# and the far edge of the elevator lattice are what gets cropped
	_map.position.x = roundf(_view.size.x / 2.0 - TOWER_CENTRE_X * MAP_SCALE)
	if _place.is_empty():
		return
	var y := clampf(_place["at"].y * MAP_SCALE - _view.size.y * FOLLOW, 0.0, maxf(_map.size.y - _view.size.y, 0.0))
	var target := -floorf(y / 3.0) * 3.0
	if _tween != null:
		_tween.kill()
	if snap:
		_map.position.y = target
	else:
		_tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		_tween.tween_property(_map, "position:y", target, 0.6)


var _marker_state := -1
var _marker_at := Vector2.INF
var _spot := Vector2.INF                   # the marker's place on the picture: slides to a new place, not a jump


func _process(delta: float) -> void:
	# the "you are here" marker pulses in 4 steps and blinks: redraw only when that (or the scroll) changes
	var t := Time.get_ticks_msec()
	var state := int(t / 160) % 4 + (4 if fmod(t / 500.0, 2.0) < 1.4 else 0)
	var moved := false
	if not _place.is_empty():
		var goal: Vector2 = _place["at"] * MAP_SCALE
		if _spot == Vector2.INF:
			_spot = goal
		elif _spot != goal:
			_spot = _spot.move_toward(goal, maxf(1.0, _spot.distance_to(goal) * 8.0 * delta))
			if _spot.distance_to(goal) < 0.5:
				_spot = goal
			moved = true
	if state != _marker_state or _map.position != _marker_at or moved:
		_marker_state = state
		_marker_at = _map.position
		_marker.queue_redraw()


func _draw_map() -> void:
	if map_texture != null:
		_map.draw_texture_rect(map_texture, Rect2(Vector2.ZERO, _map.size), false)


## A small pulse: the tower is enormous and she is a speck in it. Every stroke sits on a dark rim so it
## reads on any part of the picture (teal lattice, lit windows), and it is drawn above the edge shade.
func _draw_marker() -> void:
	if _place.is_empty():
		return
	var p: Vector2 = (_map.position + (_spot if _spot != Vector2.INF else _place["at"] * MAP_SCALE)).round()
	var dark := Color(UiStyle.BG, 0.85)
	var r := 6.0 + 3.0 * float(_marker_state % 4)
	var ring := Rect2(p - Vector2(r, r), Vector2(r, r) * 2.0)
	_marker.draw_rect(ring.grow(1.5), dark, false, 3.0)
	_marker.draw_rect(ring, Color(UiStyle.ACCENT_HI, 0.85 - 0.15 * float(_marker_state % 4)), false, 2.0)
	_marker.draw_rect(Rect2(p - Vector2(6, 6), Vector2(12, 12)), dark)
	_marker.draw_rect(Rect2(p - Vector2(3, 3), Vector2(6, 6)), UiStyle.ACCENT_HI if _marker_state >= 4 else UiStyle.ACCENT)
