extends Node2D
## Holds the current map inside the game viewport. Game.change_map() swaps it.

@export_file("*.tscn") var initial_map := "res://scenes/world/basement_test.tscn"

var current: Node
var _scenes := {}                             # path -> PackedScene, loaded once


func _ready() -> void:
	Game.register_host(self)
	load_map(initial_map)
	# load the other maps in the background now, so walking through a door never waits on the disk
	for place in Game.PLACES.values():
		if place["scene"] != initial_map:
			ResourceLoader.load_threaded_request(place["scene"])


func load_map(path: String) -> Node:
	if current != null:
		remove_child(current)        # out of the tree now so groups (map_bounds, player) only see the new map
		current.queue_free()
	current = _scene(path).instantiate()
	add_child(current)
	return current


func _scene(path: String) -> PackedScene:
	if not _scenes.has(path):
		var status := ResourceLoader.load_threaded_get_status(path)
		if status == ResourceLoader.THREAD_LOAD_IN_PROGRESS or status == ResourceLoader.THREAD_LOAD_LOADED:
			_scenes[path] = ResourceLoader.load_threaded_get(path)
		else:
			_scenes[path] = load(path)
	return _scenes[path]
