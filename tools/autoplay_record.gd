extends SceneTree
## Deterministic autoplay: loads the main scene and holds movement keys step by step,
## then quits. Pair with --write-movie to get frames (tools/record_autoplay.cmd).
## Not part of release builds.
##
## Scenario: the room fades in and the prologue is read, SeeU steps off the rug and examines the doormat, walks along the basement walkway out of the right-hand exit,
## through the fade into the elevator hall, right to the corner and up the long corridor to the elevator gate,
## uses the elevator (floor panel, picks the locked floor above, reads the answer), then - with a test stop in this
## same hall - rides it (gate opens, she steps in, gate shuts, fade) and arrives (gate opens, she steps out), walks
## back to the basement and opens the pause menu.

const ACTIONS: Array[String] = ["move_up", "move_down", "move_left", "move_right"]
const STEP_LIMIT := 240              # safety: no step holds longer than this many frames

## Each step holds `key` ("" = nothing) until its condition is met:
##   frames: n        - for n frames
##   x_ge / x_le / y_ge / y_le: v - until the player's position passes v (screen px)
##   map: "Name"      - until that map is loaded and the fade has finished
##   tap: "action"    - also taps that action once when the step starts (a real input event, so the dialogue
##                      box and panels see it), e.g. {"key": "", "tap": "interact", "frames": 20}
##   tap_key: KEY_x     - taps a raw key instead (for keys that are not actions, e.g. Esc = pause menu)
##   call: "name"       - runs a test hook first (see _hook): e.g. "test_stop" opens L1 with its stop in this hall
##                        so the elevator ride can be recorded before the upper floors exist
const STEPS := [
	{"key": "", "frames": 75},                           # the room fades in, the prologue's first page types out
	{"key": "", "tap": "interact", "frames": 40},        # prologue page 2
	{"key": "", "tap": "interact", "frames": 50},        # page 3
	{"key": "", "tap": "interact", "frames": 15},        # close: she can move
	{"key": "move_down", "y_ge": 470},                   # to the rug's edge, the mat (and its address) right below
	{"key": "", "tap": "interact", "frames": 40},        # examine the 127.0.0.1 doormat at her feet
	{"key": "", "tap": "interact", "frames": 30},        # second page
	{"key": "", "tap": "interact", "frames": 10},        # close
	{"key": "move_down", "y_ge": 512},                   # onto the walkway, below the work lamp
	{"key": "move_right", "x_ge": 700},
	{"key": "move_up", "y_le": 448},
	{"key": "move_right", "map": "ElevatorHall"},      # out of the exit, keep walking through the fade
	{"key": "move_right", "x_ge": 699},                  # along the passage to the corner
	{"key": "move_up", "y_le": 300},                     # straight up the long corridor to the gate
	{"key": "", "frames": 30},                           # look at the elevator
	{"key": "", "tap": "interact", "frames": 20},        # use it: the floor panel opens
	{"key": "", "tap": "move_up", "frames": 15},         # one floor up: L1, locked
	{"key": "", "tap": "interact", "frames": 45},        # pick it: "the button blinks red..."
	{"key": "", "tap": "interact", "frames": 45},        # next page: "no permission"
	{"key": "", "tap": "interact", "frames": 15},        # close the dialogue
	{"key": "", "call": "test_stop", "tap": "interact", "frames": 20},   # (test: L1 opened, its stop = this hall)
	{"key": "", "tap": "move_up", "frames": 15},         # L1 again, now open
	{"key": "", "tap": "interact", "frames": 210},       # ride: gate opens, in, gate shuts, fade - and arrive:
	                                                     # (the test stop is this hall) gate opens, out, gate shuts
	{"key": "move_down", "y_ge": 1188},                  # back down the corridor
	{"key": "move_left", "map": "BasementTest"},         # back out of the entrance
	{"key": "move_left", "frames": 24},
	{"key": "", "frames": 15},
	{"key": "", "tap_key": KEY_ESCAPE, "frames": 20},    # pause menu
	{"key": "", "tap": "move_down", "frames": 12},       # to the volume row
	{"key": "", "tap": "move_right", "frames": 12},      # 80 -> 90 %
	{"key": "", "tap": "move_left", "frames": 12},       # back to 80 %
	{"key": "", "tap": "move_down", "frames": 8},        # text speed
	{"key": "", "tap": "move_down", "frames": 8},        # fullscreen
	{"key": "", "tap": "move_down", "frames": 8},        # reduce flicker
	{"key": "", "tap": "move_down", "frames": 8},        # controls
	{"key": "", "tap": "interact", "frames": 30},        # the controls page
	{"key": "", "tap": "cancel", "frames": 12},          # back to the menu
	{"key": "", "tap": "cancel", "frames": 20},          # close: the game goes on
]

var _step := -1
var _step_frames := 0
var _tapped := ""                       # action tapped this step, released on the next frame


func _initialize() -> void:
	root.add_child(load("res://scenes/main/main.tscn").instantiate())


func _process(_delta: float) -> bool:
	if _step < 0 or _done(STEPS[_step]):
		_step += 1
		_step_frames = 0
		if _step >= STEPS.size():
			_hold("")
			return true
		_hold(STEPS[_step]["key"])
		if STEPS[_step].has("call"):
			_hook(STEPS[_step]["call"])
		if STEPS[_step].has("tap"):
			_tapped = STEPS[_step]["tap"]
			InputTap.action(_tapped, true)
		if STEPS[_step].has("tap_key"):
			InputTap.tap_key(STEPS[_step]["tap_key"])
	else:
		if _tapped != "":
			InputTap.action(_tapped, false)
			_tapped = ""
		# Godot releases every held action when the window loses focus (someone using the PC while it
		# records): press the step's key again each frame so the run never depends on window focus.
		var key: String = STEPS[_step]["key"]
		if key != "" and not Input.is_action_pressed(key):
			Input.action_press(key)
	_step_frames += 1
	return false


func _hook(name: String) -> void:
	var game := root.get_node("Game")
	match name:
		"test_stop":
			game.access["L1"] = true
			game.elevator_stops["L1"] = ["res://scenes/world/elevator_hall.tscn", &"FromElevator"]


func _hold(key: String) -> void:
	for a in ACTIONS:
		Input.action_release(a)
	if key != "":
		Input.action_press(key)


func _done(s: Dictionary) -> bool:
	if _step_frames >= STEP_LIMIT:
		push_warning("autoplay: step %d timed out" % _step)
		return true
	if s.has("frames"):
		return _step_frames >= s["frames"]
	if s.has("map"):
		var game := root.get_node("Game")
		var host := root.find_child("MapHost", true, false)
		return host != null and host.current != null and String(host.current.name) == s["map"] \
			and not game.is_changing_map()
	var players := get_nodes_in_group("player")
	if players.is_empty():
		return false
	var p: Vector2 = players[0].global_position
	if s.has("x_ge"): return p.x >= s["x_ge"]
	if s.has("x_le"): return p.x <= s["x_le"]
	if s.has("y_ge"): return p.y >= s["y_ge"]
	if s.has("y_le"): return p.y <= s["y_le"]
	return true
