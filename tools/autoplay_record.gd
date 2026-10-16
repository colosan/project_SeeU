extends SceneTree
## Deterministic autoplay: loads the main scene and holds movement keys step by step,
## then quits. Pair with --write-movie to get frames (tools/record_autoplay.cmd).
## Not part of release builds.
##
## Scenario: SeeU walks from the rug along the basement walkway out of the right-hand exit,
## through the fade into the elevator hall, up to the elevator gate, then back to the basement.

const ACTIONS: Array[String] = ["move_up", "move_down", "move_left", "move_right"]
const STEP_LIMIT := 240              # safety: no step holds longer than this many frames

## Each step holds `key` ("" = nothing) until its condition is met:
##   frames: n        - for n frames
##   x_ge / x_le / y_ge / y_le: v - until the player's position passes v (screen px)
##   map: "Name"      - until that map is loaded and the fade has finished
const STEPS := [
	{"key": "", "frames": 15},
	{"key": "move_down", "y_ge": 512},
	{"key": "move_right", "x_ge": 700},
	{"key": "move_up", "y_le": 448},
	{"key": "move_right", "map": "ElevatorHall"},      # out of the exit, keep walking through the fade
	{"key": "move_right", "x_ge": 756},
	{"key": "move_up", "frames": 22},                    # up to the gate
	{"key": "", "frames": 30},                           # look at the elevator
	{"key": "move_down", "y_ge": 444},
	{"key": "move_left", "map": "BasementTest"},         # back out of the entrance
	{"key": "move_left", "frames": 24},
	{"key": "", "frames": 15},
]

var _step := -1
var _step_frames := 0


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
	_step_frames += 1
	return false


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
