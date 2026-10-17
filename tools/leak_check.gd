extends SceneTree
## Leak check (not part of the game): swaps the maps of Game.PLACES in turn many times, as fast as they load,
## and fails if objects keep piling up (something in a map outliving it: a coroutine waiting on a timer or tween
## of a freed node, a cache keyed per instance, ...). Headless, a few seconds:
##   $GODOT --headless --fixed-fps 60 --path . --script res://tools/leak_check.gd
## Counts objects after a warm-up and again after SWAPS more swaps; allows a little noise (timers in flight).

const SWAPS := 200
const ALLOWED := 25

var _f := 0
var _n := 0
var _paths: Array = []
var _host: Node
var _start := -1


func _initialize() -> void:
	var places: Dictionary = (load("res://scripts/autoload/game.gd") as GDScript).get_script_constant_map()["PLACES"]
	for key in places:
		_paths.append(places[key]["scene"])
	root.add_child(load("res://scenes/main/main.tscn").instantiate())


func _process(_d: float) -> bool:
	_f += 1
	if _f == 200:
		_host = root.find_child("MapHost", true, false)
	if _host == null or _f % 20 != 0:
		return false
	_host.load_map(_paths[_n % _paths.size()])        # straight swap: no fade, nothing but the maps themselves
	_n += 1
	if _n == 20:
		_start = int(Performance.get_monitor(Performance.OBJECT_COUNT))
	if _n == 20 + SWAPS:
		var grown := int(Performance.get_monitor(Performance.OBJECT_COUNT)) - _start
		print("leak_check: %d swaps, objects %+d (allowed %d)" % [SWAPS, grown, ALLOWED])
		if grown > ALLOWED:
			printerr("PROBLEM: objects keep piling up when maps are swapped (+%d)" % grown)
			quit(1)
		else:
			quit(0)
	return false
