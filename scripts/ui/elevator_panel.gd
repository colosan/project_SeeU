class_name ElevatorPanel
extends Control
## The freight elevator's floor panel ("the bus", docs/WORLD.md): every floor of the tower, top to bottom,
## labelled the way the tower's signs label them (the class sign and its view count). Floors without access
## show LOCKED - the elevator only goes where SeeU has permission. Up/down + interact picks, cancel closes.

const ROW_H := 54.0
const WIDTH := 460.0

signal _picked(floor_id: String)

var _panel: Panel
var _rows: VBoxContainer
var _floors: Array = []
var _current := ""
var _access := {}
var _choice := 0
var _open := false
var _flash := -1                          # row blinking red right now (a locked floor was pressed)
var _busy := false


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	process_mode = Node.PROCESS_MODE_ALWAYS
	var box := UiStyle.menu_box("FLOOR", [["Z", "선택"], ["X", "닫기"]])
	_panel = box["panel"]
	_rows = box["rows"]
	add_child(_panel)
	_panel.visible = false


func is_open() -> bool:
	return _open


## Shows the panel; returns the picked floor id, or "" if closed without picking.
func pick(floors: Array, current: String, access: Dictionary) -> String:
	_floors = floors
	_current = current
	_access = access
	_choice = maxi(0, floors.find_custom(func(f): return f["id"] == current))
	_panel.size = UiStyle.menu_size(WIDTH, floors.size(), ROW_H)
	_panel.position = ((size - _panel.size) / 2.0).round()
	_refresh()
	Game.sfx("page")
	_open = true
	_panel.visible = true
	var picked: String = await _picked
	_open = false
	_panel.visible = false
	return picked


func _refresh() -> void:
	for c in _rows.get_children():
		c.queue_free()
	for i in _floors.size():
		var f: Dictionary = _floors[i]
		var on := i == _choice
		var here: bool = f["id"] == _current
		var open: bool = _access.has(f["id"])
		var parts := UiStyle.list_row(on, WIDTH, ROW_H)
		var row: HBoxContainer = parts[1]
		var bg: StyleBoxFlat = parts[2]
		# the cursor row is teal only where she could go; on a locked floor it stays grey (it is not available)
		var col := (UiStyle.ACCENT_HI if open else UiStyle.TEXT) if on else (UiStyle.TEXT_HI if open else UiStyle.TEXT_DIM)
		if i == _flash:
			col = UiStyle.DENY
			bg.bg_color = Color(UiStyle.DENY, 0.22)
		row.add_child(UiStyle.cursor(on, UiStyle.DENY if i == _flash else UiStyle.ACCENT_HI))
		row.add_child(_chip(f.get("tier", UiStyle.LINE), open or here))
		row.add_child(UiStyle.label(f["id"], 24, col))
		var sign := UiStyle.label(f["sign"], 24, col)
		sign.custom_minimum_size.x = 130
		row.add_child(sign)
		var views := UiStyle.label(f["views"], 20, col)
		views.custom_minimum_size.x = 64
		row.add_child(views)
		row.add_child(UiStyle.label("HERE" if here else ("" if open else "LOCKED"), 16,
			UiStyle.ACCENT if here else (UiStyle.TEXT if on else UiStyle.TEXT_DIM)))
		_rows.add_child(parts[0])


## A locked floor: its button blinks red three times, then the pick goes through (Game says why it didn't move).
func _deny() -> void:
	_busy = true
	var row := _choice
	for k in 3:
		_flash = row
		_refresh()
		Game.sfx("deny")
		await get_tree().create_timer(0.12).timeout
		_flash = -1
		_refresh()
		await get_tree().create_timer(0.09).timeout
	_busy = false
	_picked.emit(String(_floors[row]["id"]))


## The floor's facade colour from the tower picture (rust, bronze, silver, gold, platinum), a dark-rimmed
## square: the panel and the left panel's tower speak the same colours. Dim on floors she can't go to.
func _chip(c: Color, lit: bool) -> Control:
	var box := CenterContainer.new()
	var chip := Panel.new()
	var face := c.lightened(0.25)                          # the facade as lit glass, readable on the dark panel
	# a floor she can't go to: just the outline in its colour (a dimmed fill vanished into the panel)
	var sb := UiStyle.panel_box_all(face, UiStyle.LINE_HI) if lit else UiStyle.panel_box_all(UiStyle.BG, face)
	chip.add_theme_stylebox_override("panel", sb)
	chip.custom_minimum_size = Vector2(18, 18)
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(chip)
	return box


func _unhandled_input(event: InputEvent) -> void:
	if not _open or event.is_echo():
		return
	if _busy:
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("move_up") or event.is_action_pressed("move_down"):
		_choice = wrapi(_choice + (-1 if event.is_action_pressed("move_up") else 1), 0, _floors.size())
		_refresh()
		Game.sfx("move")
	elif event.is_action_pressed("interact", false, true):
		var id := String(_floors[_choice]["id"])
		if id != _current and not _access.has(id):
			_deny()                                    # the button blinks red first, then the panel closes
		else:
			Game.sfx("ok")
			_picked.emit(id)
	elif event.is_action_pressed("cancel"):
		Game.sfx("cancel")
		_picked.emit("")
	else:
		return
	get_viewport().set_input_as_handled()
