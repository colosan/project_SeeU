extends SceneTree
## Deterministic autoplay: loads the main scene, presses movement keys on a
## fixed frame schedule, then quits. Pair with --write-movie to get frames.
## Run via tools/record_autoplay.cmd. Not part of release builds.

const ACTIONS: Array[String] = ["move_up", "move_down", "move_left", "move_right"]

## frame -> action to hold from that frame on ("" = release everything)
const SCHEDULE := {
	15: "move_right", 45: "move_down", 75: "move_left",
	165: "move_up", 225: "",
}
const LAST_FRAME := 240

var _frame := 0


func _initialize() -> void:
	root.add_child(load("res://scenes/main/main.tscn").instantiate())


func _process(_delta: float) -> bool:
	_frame += 1
	if SCHEDULE.has(_frame):
		for a in ACTIONS:
			Input.action_release(a)
		if SCHEDULE[_frame] != "":
			Input.action_press(SCHEDULE[_frame])
	return _frame >= LAST_FRAME
