class_name PauseMenu
extends Control
## Esc while walking: the game stops and a small menu opens over the game view (same look as the floor panel).
## Continue / sound volume / text speed / fullscreen / reduce flicker / controls / quit. Up/down picks a row, left/right changes a value, interact uses
## it, cancel (X/Esc) closes. Settings are kept in user://settings.cfg (Game.save_settings).

const ROW_H := 54.0
const WIDTH := 420.0
const VOLUME_STEP := 10
const KEYS := [
	["이동", "방향키 / WASD"],
	["조사 · 결정", "Z / Space / Enter"],
	["취소 · 닫기", "X / Backspace"],
	["일시정지", "Esc"],
	["전체 화면", "F11 / Alt+Enter"],
]

signal _closed

var _panel: Panel
var _dim: ColorRect                       # darkens the stopped game behind the menu
var _rows: VBoxContainer
var _choice := 0
var _open := false
var _quit_armed := false                 # "끝내기" pressed once: the next press quits, moving away disarms
var _keys_view := false                   # the "조작법" page: what every key does (any key goes back)

var _title: Label                         # PAUSE / CONTROLS
var _menu_keys: Array[Control] = []       # footer hints that only mean something on the menu page


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	process_mode = Node.PROCESS_MODE_ALWAYS
	_dim = ColorRect.new()
	_dim.color = Color(0, 0, 0, 0.45)
	_dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_dim.visible = false
	add_child(_dim)
	var box := UiStyle.menu_box("PAUSE", [["Z", "결정"], ["◀▶", "조절"], ["X", "닫기"]])
	_panel = box["panel"]
	_rows = box["rows"]
	_title = box["title"]
	_menu_keys = [box["hints"][0], box["hints"][1]]    # mean nothing on the read-only controls page
	add_child(_panel)
	_panel.visible = false


func is_open() -> bool:
	return _open


## Opens the menu and pauses the game; returns when it is closed.
func open() -> void:
	_choice = 0
	_keys_view = false
	_quit_armed = false
	_refresh()
	_open = true
	_panel.visible = true
	_dim.visible = true
	get_tree().paused = true
	Game.sfx("page")
	await _closed
	get_tree().paused = false
	_open = false
	_panel.visible = false
	_dim.visible = false


## Row labels (and values), built fresh so they always show the current settings.
func _items() -> Array:
	var full := DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
	return [
		["resume", "계속하기", ""],
		["volume", "음량", "◀ %d%% ▶" % Game.volume],
		["text", "글자 속도", "◀ %s ▶" % Game.TEXT_SPEEDS[Game.text_speed][0]],
		["fullscreen", "전체 화면", "◀ %s ▶" % ("켜짐" if full else "꺼짐")],
		["flicker", "깜빡임 줄이기", "◀ %s ▶" % ("켜짐" if Game.reduce_flicker else "꺼짐")],
		["keys", "조작법", ""],
		["quit", "끝내기", "다시 누르면 끝" if _quit_armed else ""],
	]


func _refresh() -> void:
	for c in _rows.get_children():
		c.queue_free()
	var items: Array = KEYS.map(func(k): return ["", k[0], k[1]]) if _keys_view else _items()
	var w := WIDTH + (90.0 if _keys_view else 0.0)          # the controls page is wider (key names)
	_panel.size = UiStyle.menu_size(w, items.size(), ROW_H)
	_title.text = "CONTROLS" if _keys_view else "PAUSE"
	for k in _menu_keys:
		k.visible = not _keys_view                         # nothing to pick or adjust on the controls page
	_panel.position = ((size - _panel.size) / 2.0).round()
	for i in items.size():
		var on := i == _choice and not _keys_view
		var parts := UiStyle.list_row(on, w, ROW_H)
		var row: HBoxContainer = parts[1]
		var col := UiStyle.ACCENT_HI if on else UiStyle.TEXT_HI
		if not _keys_view:                                 # read-only rows: no cursor column, flush with the title
			row.add_child(UiStyle.cursor(on))
		var name := UiStyle.label(items[i][1], 22 if _keys_view else 24, col)
		name.custom_minimum_size.x = 140 if _keys_view else 170        # the controls page needs room for key names
		row.add_child(name)
		row.add_child(UiStyle.label(items[i][2], 19 if _keys_view else 22, col if on else UiStyle.TEXT))
		_rows.add_child(parts[0])


func _key() -> String:
	return _items()[_choice][0]


func _change(step: int) -> void:
	match _key():
		"volume":
			var v := clampi(Game.volume + step * VOLUME_STEP, 0, 100)
			if v == Game.volume:
				return
			Game.set_volume(v)
			Game.sfx("move")                             # hear the new level right away
		"text":
			Game.text_speed = wrapi(Game.text_speed + step, 0, Game.TEXT_SPEEDS.size())
			Game.sfx("move")
		"fullscreen":
			Game.toggle_fullscreen()
			Game.sfx("move")
		"flicker":
			Game.reduce_flicker = not Game.reduce_flicker
			Game.sfx("move")
		_:
			return
	Game.save_settings()
	_refresh()


func _unhandled_input(event: InputEvent) -> void:
	if not _open or event.is_echo():
		return
	if _keys_view:                                     # the controls page: interact or cancel goes back to the menu
		if event.is_action_pressed("interact", false, true) or event.is_action_pressed("cancel"):
			_keys_view = false
			Game.sfx("cancel")
			_refresh()
			get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("move_up") or event.is_action_pressed("move_down"):
		_choice = wrapi(_choice + (-1 if event.is_action_pressed("move_up") else 1), 0, _items().size())
		_quit_armed = false
		_refresh()
		Game.sfx("move")
	elif event.is_action_pressed("move_left") or event.is_action_pressed("move_right"):
		_change(-1 if event.is_action_pressed("move_left") else 1)
	elif event.is_action_pressed("interact", false, true):
		match _key():
			"resume":
				Game.sfx("cancel")
				_closed.emit()
			"volume":
				_change(1 if Game.volume < 100 else -100 / VOLUME_STEP)   # Z steps up; at 100 % it wraps to 0
			"text", "fullscreen", "flicker":
				_change(1)
			"keys":
				_keys_view = true
				Game.sfx("page")
				_refresh()
			"quit":
				if _quit_armed:
					get_tree().quit()
				else:
					_quit_armed = true                       # no quitting by a stray press
					Game.sfx("deny")
					_refresh()
	elif event.is_action_pressed("cancel"):
		Game.sfx("cancel")
		_closed.emit()
	else:
		return
	get_viewport().set_input_as_handled()
