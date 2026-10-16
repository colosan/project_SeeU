extends Node2D
## Holds the current map inside the game viewport. Game.change_map() swaps it.

@export_file("*.tscn") var initial_map := "res://scenes/world/basement_test.tscn"

var current: Node


func _ready() -> void:
	Game.register_host(self)
	load_map(initial_map)


func load_map(path: String) -> Node:
	if current != null:
		remove_child(current)        # out of the tree now so groups (map_bounds, player) only see the new map
		current.queue_free()
	current = load(path).instantiate()
	add_child(current)
	return current
