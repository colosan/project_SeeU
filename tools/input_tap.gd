class_name InputTap
## Test input for the tool scripts (tools/autoplay_record.gd, tools/monkey_test.gd): real input events, so the
## dialogue box and panels (which listen to events, not to held actions) see them.


static func action(name: String, pressed: bool) -> void:
	var ev := InputEventAction.new()
	ev.action = name
	ev.pressed = pressed
	Input.parse_input_event(ev)


## Press and release an action in one go.
static func tap(name: String) -> void:
	action(name, true)
	action(name, false)


## Press and release a raw key (for keys that are not actions, e.g. Esc = pause menu).
static func tap_key(k: Key) -> void:
	for down in [true, false]:
		var ev := InputEventKey.new()
		ev.keycode = k
		ev.physical_keycode = k
		ev.pressed = down
		Input.parse_input_event(ev)
