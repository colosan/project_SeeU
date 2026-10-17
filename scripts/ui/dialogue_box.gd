class_name DialogueBox
extends Control
## The dialogue box: shown over the bottom of the game view only while someone talks (never a fixed panel,
## docs/DESIGN.md UI), same look as the frame around the game (steel border, teal corner brackets).
## Pages type out; interact finishes the page or turns to the next; choices are picked with up/down + interact.
## A portrait slot sits above the box's left end (hidden until portraits exist - DESIGN.md A안).
## Also shows the small "Z  조사" hint when SeeU faces something she can use.

const MARGIN := 48.0                       # clear of the game frame's own corner marks
const HEIGHT := 180.0                     # name + three lines

signal _advance
signal _picked(index: int)

var _box: Panel
var _name: Label
var _text: Label
var _more: Label
var _choices: VBoxContainer
var _hint: HBoxContainer                 # [Z] 조사 - a keycap and what it does
var _hint_text: Label
var portrait: TextureRect                # for later: the speaker's half-body portrait above the box

var _open := false
var _box_tween: Tween
var _hint_tween: Tween
var _hint_shown := false
var _typing := false
var _shown := 0.0
var _choice := -1
var _options: Array = []


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	process_mode = Node.PROCESS_MODE_ALWAYS

	_box = Panel.new()
	var sb := UiStyle.panel_box_all(UiStyle.BG, UiStyle.LINE_HI)
	_box.add_theme_stylebox_override("panel", sb)
	_box.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	_box.offset_left = MARGIN
	_box.offset_right = -MARGIN
	_box.offset_bottom = -MARGIN
	_box.offset_top = -MARGIN - HEIGHT
	_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_box.draw.connect(_draw_brackets)
	add_child(_box)

	_name = UiStyle.label("", 20, UiStyle.ACCENT_HI)
	_name.position = Vector2(24, 16)
	_box.add_child(_name)
	_text = UiStyle.label("", 26, UiStyle.TEXT_HI)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.position = Vector2(24, 50)
	_box.add_child(_text)
	_box.resized.connect(func() -> void: _text.size = Vector2(_box.size.x - 48, HEIGHT - 70))
	_more = UiStyle.label("▼", 18, UiStyle.ACCENT)
	_box.add_child(_more)
	_box.resized.connect(func() -> void: _more.position = Vector2(_box.size.x - 40, HEIGHT - 40))
	_choices = VBoxContainer.new()
	_choices.position = Vector2(48, 50)
	_choices.add_theme_constant_override("separation", 6)
	_box.add_child(_choices)

	portrait = TextureRect.new()
	portrait.visible = false
	add_child(portrait)

	_hint = UiStyle.key_hint("Z", "")
	_hint_text = _hint.get_child(1)
	add_child(_hint)
	_hint.resized.connect(_place_hint)
	resized.connect(_place_hint)

	_box.visible = false
	_hint.visible = false
	_hint.modulate.a = 0.0


func is_open() -> bool:
	return _open


## The "Z  조사" hint in the game view's corner ("" hides it). Hidden while the box is open.
func set_hint(text: String) -> void:
	if text != "" and _hint_text.text != text:      # going away it keeps its last words while it fades
		_hint_text.text = text
		_hint.reset_size()
	var show := text != "" and not _open
	if show == _hint_shown:
		return
	_hint_shown = show
	if _hint_tween != null:
		_hint_tween.kill()
	_hint_tween = create_tween()
	if show:                                         # fades in and out rather than popping
		_hint.visible = true
		_hint_tween.tween_property(_hint, "modulate:a", 1.0, 0.12)
	else:
		_hint_tween.tween_property(_hint, "modulate:a", 0.0, 0.12)
		_hint_tween.tween_callback(_hint.hide)


func _place_hint() -> void:
	_hint.position = (size - _hint.size - Vector2(MARGIN + 36, MARGIN + 24)).round()   # clear of the frame's corner marks


## Shows the pages one after another; returns when the last one is dismissed.
func say(pages: Array, speaker := "") -> void:
	_show(speaker)
	for page in pages:
		_choices.visible = false
		_text.visible = true
		_text.text = String(page)
		Game.sfx("page")
		_type()
		await _advance
	_close()


## Asks `question` (may be "") with `options`; returns the picked index, or -1 if cancelled.
func choose(question: String, options: Array, speaker := "") -> int:
	if options.is_empty():                           # nothing to pick: the box could never close
		push_error("DialogueBox.choose: no options")
		return -1
	_show(speaker)
	_text.text = question
	_text.visible = question != ""
	_text.visible_characters = -1
	_typing = false
	_options = options
	_choice = 0
	_choices.visible = true
	_choices.position.y = 50.0 + (36.0 if question != "" else 0.0)
	_refresh_choices()
	Game.sfx("page")
	_more.visible = false
	var picked: int = await _picked
	_close()
	return picked


func _show(speaker: String) -> void:
	_open = true
	if _hint_tween != null:
		_hint_tween.kill()
	_hint.visible = false                            # the box takes over: the hint goes at once
	_hint_shown = false
	if not _box.visible:                             # opens with a short rise and fade, not a pop
		var rest := size.y - MARGIN - HEIGHT           # where the anchors put it (not wherever a last tween left it)
		if _box_tween != null:
			_box_tween.kill()
		_box.position.y = rest + 9.0
		_box.modulate.a = 0.0
		_box_tween = create_tween().set_parallel()
		_box_tween.tween_property(_box, "position:y", rest, 0.1).set_ease(Tween.EASE_OUT)
		_box_tween.tween_property(_box, "modulate:a", 1.0, 0.1)
	_box.visible = true
	_name.text = speaker
	_name.visible = speaker != ""
	_text.position.y = 50.0 if speaker != "" else 30.0


func _close() -> void:
	_open = false
	_box.visible = false
	_options = []
	_choice = -1
	for c in _choices.get_children():
		c.queue_free()


func _type() -> void:
	_typing = true
	_shown = 0.0
	_text.visible_characters = 0
	_more.visible = false
	if float(Game.TEXT_SPEEDS[Game.text_speed][1]) <= 0.0:   # text speed "instant": the whole page at once
		_finish_typing()


func _process(delta: float) -> void:
	if not _open:
		return
	if _typing:
		_shown += float(Game.TEXT_SPEEDS[Game.text_speed][1]) * delta
		_text.visible_characters = int(_shown)
		if _text.visible_characters >= _text.get_total_character_count():
			_finish_typing()
	elif _options.is_empty():
		_more.visible = fmod(Time.get_ticks_msec() / 400.0, 2.0) < 1.3      # blink: there is more


func _finish_typing() -> void:
	_typing = false
	_text.visible_characters = -1


func _refresh_choices() -> void:
	for c in _choices.get_children():
		c.queue_free()
	for i in _options.size():
		var on := i == _choice
		var row := HBoxContainer.new()
		row.add_child(UiStyle.cursor(on, UiStyle.ACCENT_HI, 24))
		row.add_child(UiStyle.label(String(_options[i]), 24, UiStyle.ACCENT_HI if on else UiStyle.TEXT))
		_choices.add_child(row)


func _unhandled_input(event: InputEvent) -> void:
	if not _open or event.is_echo():
		return
	if not _options.is_empty():
		if event.is_action_pressed("move_up") or event.is_action_pressed("move_down"):
			var step := -1 if event.is_action_pressed("move_up") else 1
			_choice = wrapi(_choice + step, 0, _options.size())
			_refresh_choices()
			Game.sfx("move")
		elif event.is_action_pressed("interact", false, true):
			Game.sfx("ok")
			_picked.emit(_choice)
		elif event.is_action_pressed("cancel"):
			Game.sfx("cancel")
			_picked.emit(-1)
		else:
			return
	elif event.is_action_pressed("interact", false, true) or event.is_action_pressed("cancel"):
		if _typing:
			_finish_typing()
		else:
			_advance.emit()
	else:
		return
	get_viewport().set_input_as_handled()


func _draw_brackets() -> void:
	UiStyle.draw_brackets(_box, _box.size)
