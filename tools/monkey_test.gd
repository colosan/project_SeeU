extends SceneTree
## Monkey test (not part of the game): presses random keys for a while and watches for states the
## game must never get stuck in. Headless and fast:
##   $GODOT --headless --fixed-fps 60 --path . --script res://tools/monkey_test.gd -- 9000 3
## (args after --: frames to run, random seed). Prints what it saw and exits 1 on any problem.
## Watches: a UI (dialogue, floor panel, pause menu) or Game._busy staying on for over STUCK_S seconds; the tree
## paused with no pause menu open for over STUCK_S; SeeU outside her map's rectangle; SeeU left `scripted` after
## a ride. Script errors show up in the log itself (grep SCRIPT ERROR).
## Test hook: opens L1 with its stop in the elevator hall (like tools/autoplay_record.gd) so rides happen too.

const STUCK_S := 25.0
const PRESSES := ["move_up", "move_down", "move_left", "move_right", "interact", "cancel"]

var _frames := 9000
var _rng := RandomNumberGenerator.new()
var _f := 0
var _held := ""
var _hold_left := 0
var _ui_since := -1.0
var _pause_since := -1.0
var _t := 0.0
var _problems: Array[String] = []
var _stats := {"rides": 0, "maps": {}, "dialogues": 0, "pauses": 0}
var _last_map := ""
var _last_map_id := 0
var _was_dialogue := false
var _was_pause := false


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		_frames = int(args[0])
	_rng.seed = int(args[1]) if args.size() > 1 else 1
	root.add_child(load("res://scenes/main/main.tscn").instantiate())


func _process(delta: float) -> bool:
	_f += 1
	var game := root.get_node_or_null("Game")
	if _f == 2 and game != null:
		game.access["L1"] = true
		game.elevator_stops["L1"] = ["res://scenes/world/elevator_hall.tscn", &"FromElevator"]
	if game == null:
		return _f >= _frames
	_t += delta
	if _f % 900 == 450 and game.can_move():
		_shuffle(game)
	_act(game)
	_watch(game)
	if _f >= _frames:
		_report()
		return true
	return false


func _act(game: Node) -> void:
	if game._pause != null and game._pause.is_open():     # in the pause menu: change things, never pick "끝내기"
		if _hold_left <= 0:
			InputTap.tap(["move_left", "move_right", "cancel"][_rng.randi_range(0, 2)])
			_hold_left = _rng.randi_range(5, 25)
		_hold_left -= 1
		return
	if _hold_left > 0:
		_hold_left -= 1
		if _hold_left == 0 and _held != "":
			Input.action_release(_held)
			_held = ""
		return
	var r := _rng.randf()
	if r < 0.55:                                   # walk somewhere for a moment (the most common thing)
		_held = PRESSES[_rng.randi_range(0, 3)]
		Input.action_press(_held)
		_hold_left = _rng.randi_range(10, 70)
	elif r < 0.68:                                 # a single step as an input event (lists and panels need events)
		InputTap.tap(PRESSES[_rng.randi_range(0, 3)])
		_hold_left = _rng.randi_range(3, 12)
	elif r < 0.85:
		InputTap.tap(PRESSES[4])
		_hold_left = _rng.randi_range(3, 20)
	elif r < 0.95:
		InputTap.tap(PRESSES[5])
		_hold_left = _rng.randi_range(3, 20)
	else:
		InputTap.tap_key(KEY_ESCAPE)
		_hold_left = _rng.randi_range(5, 30)


## Random walking rarely finds the doors: now and then go to the other map like a door would, and in the hall
## stand at the elevator gate facing it, so the next random interact may ride it.
func _shuffle(game: Node) -> void:
	var host := root.find_child("MapHost", true, false)
	if host == null or host.current == null:
		return
	if String(host.current.name) == "BasementTest":
		game.change_map("res://scenes/world/elevator_hall.tscn", &"FromBasement")
	elif _rng.randf() < 0.5:
		game.change_map("res://scenes/world/basement_test.tscn", &"FromElevator")
	else:
		var p: Node2D = get_first_node_in_group("player")
		var m := host.current.find_child("FromElevator", true, false) as Node2D
		if p != null and m != null:
			p.global_position = m.global_position
			p.face("north")
			_hold_left = 0
			await physics_frame                       # let her reach box see the gate, then use it: the floor panel
			await physics_frame
			InputTap.tap("interact")




func _watch(game: Node) -> void:
	var t := _t
	var ui_or_busy: bool = game.is_ui_open() or game.is_changing_map()
	if ui_or_busy:
		if _ui_since < 0.0:
			_ui_since = t
		elif t - _ui_since > STUCK_S:
			_bad("UI or busy for over %ds (frame %d)" % [STUCK_S, _f])
			_ui_since = t
	else:
		_ui_since = -1.0
	var pause_open: bool = game._pause != null and game._pause.is_open()
	if paused and not pause_open:
		if _pause_since < 0.0:
			_pause_since = t
		elif t - _pause_since > STUCK_S:
			_bad("tree paused without the pause menu for over %ds (frame %d)" % [STUCK_S, _f])
			_pause_since = t
	else:
		_pause_since = -1.0
	var host := root.find_child("MapHost", true, false)
	if host != null and host.current != null:
		var name := String(host.current.name)
		if host.current.get_instance_id() != _last_map_id:  # a new map instance (a ride to the hall keeps the name)
			_stats["maps"][name] = int(_stats["maps"].get(name, 0)) + 1
			if _last_map == "ElevatorHall" and name == "ElevatorHall":
				_stats["rides"] += 1
			_last_map = name
			_last_map_id = host.current.get_instance_id()
		var bounds := get_first_node_in_group("map_bounds")
		var players := get_nodes_in_group("player")
		if bounds != null and not players.is_empty() and not ui_or_busy:
			var p: Node2D = players[0]
			if not bounds.get_world_rect().grow(4.0).has_point(p.global_position):
				_bad("SeeU outside the map at %s in %s (frame %d)" % [p.global_position, name, _f])
			if p.scripted:
				_bad("SeeU still scripted while free to move (frame %d)" % _f)
	var dlg: bool = game._dialogue != null and game._dialogue.is_open()
	if dlg and not _was_dialogue:
		_stats["dialogues"] += 1
	_was_dialogue = dlg
	if pause_open and not _was_pause:
		_stats["pauses"] += 1
	_was_pause = pause_open


func _bad(line: String) -> void:
	if _problems.size() < 30:
		_problems.append(line)


func _report() -> void:
	print("monkey: %d frames, maps entered %s, elevator rides %d, dialogues %d, pause menus %d" % [_frames,
		_stats["maps"], _stats["rides"], _stats["dialogues"], _stats["pauses"]])
	for line in _problems:
		printerr("PROBLEM: ", line)
	print("monkey: %d problem(s)" % _problems.size())
	if not _problems.is_empty():
		quit(1)
