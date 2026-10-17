extends SceneTree
## Reach check (not part of the game): can SeeU actually walk up to every examinable / usable thing?
##   $GODOT --headless --path . --script res://tools/reach_check.gd
## For each map in Game.PLACES: lays a grid over the map, keeps the cells where her feet box fits (real physics
## against the walls and props), flood-fills from where she enters, and from every reachable cell tries her
## reach box in all four facings (the same offsets as scripts/characters/player.gd). An Interactable no reachable
## cell touches is reported. Exit code 1 if any.

const STEP := 6.0                                     # grid spacing, screen px

var _problems: Array[String] = []
var _maps: Array = []
var _i := -1
var _wait := 0
var _map: Node


func _initialize() -> void:
	var places: Dictionary = (load("res://scripts/autoload/game.gd") as GDScript).get_script_constant_map()["PLACES"]
	for key in places:
		_maps.append(places[key]["scene"])


func _process(_d: float) -> bool:
	if _wait > 0:
		_wait -= 1
		if _wait == 0:
			_check(_map)
			_map.queue_free()
			_map = null
		return false
	_i += 1
	if _i >= _maps.size():
		for p in _problems:
			printerr("PROBLEM: ", p)
		print("reach_check: %d map(s), %d problem(s)" % [_maps.size(), _problems.size()])
		quit(1 if not _problems.is_empty() else 0)
		return false
	_map = (load(_maps[_i]) as PackedScene).instantiate()
	root.add_child(_map)
	_wait = 3                                         # let the props build their colliders and areas
	return false


func _check(map: Node) -> void:
	var space := (map as Node2D).get_world_2d().direct_space_state
	var player: CharacterBody2D = map.find_children("*", "CharacterBody2D", true, false).filter(
		func(n): return n.is_in_group("player"))[0]
	var feet := (player.get_node("Collision") as CollisionShape2D)
	var feet_q := PhysicsShapeQueryParameters2D.new()
	feet_q.shape = feet.shape
	feet_q.collision_mask = player.collision_mask
	feet_q.exclude = [player.get_rid()]
	var rect: Rect2 = map.get_tree().get_first_node_in_group("map_bounds").get_world_rect()

	var fits := func(p: Vector2) -> bool:
		feet_q.transform = Transform2D(0.0, p + feet.position)
		return space.intersect_shape(feet_q, 1).is_empty()

	# flood fill from every entry point: the player's start and each spawn marker
	var starts: Array[Vector2] = [player.global_position]
	for m in map.find_children("*", "Marker2D", true, false):
		starts.append((m as Node2D).global_position)
	var seen := {}
	var queue: Array[Vector2i] = []
	for s in starts:
		var c := Vector2i(roundi((s.x - rect.position.x) / STEP), roundi((s.y - rect.position.y) / STEP))
		if not seen.has(c):
			seen[c] = true
			queue.append(c)
	var reachable: Array[Vector2] = []
	while not queue.is_empty():
		var c: Vector2i = queue.pop_back()
		var p := rect.position + Vector2(c) * STEP
		if not rect.has_point(p) or not fits.call(p):
			continue
		reachable.append(p)
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = c + d
			if not seen.has(n):
				seen[n] = true
				queue.append(n)

	if OS.get_cmdline_user_args().has("--dump"):       # for checking against the floor art: build/reach_<map>.txt
		var f := FileAccess.open("res://build/reach_%s.txt" % map.name, FileAccess.WRITE)
		for p in reachable:
			f.store_line("%d %d" % [p.x, p.y])
		f.close()

	# which interactables a reach box touches from some reachable cell
	var reach_q := PhysicsShapeQueryParameters2D.new()
	var box := RectangleShape2D.new()
	box.size = player.REACH_SIZE
	reach_q.shape = box
	reach_q.collision_mask = 1 << 7                  # Interactable.LAYER (naming the class here would pull in Game too early)
	reach_q.collide_with_areas = true
	reach_q.collide_with_bodies = false
	var touched := {}
	for p in reachable:
		for off in player.REACH.values():
			reach_q.transform = Transform2D(0.0, p + off)
			for hit in space.intersect_shape(reach_q, 8):
				touched[hit["collider"]] = true
	for it in map.get_tree().get_nodes_in_group("interactable"):
		if not map.is_ancestor_of(it):
			continue
		if not touched.has(it):
			_problems.append("%s: %s can't be reached (nowhere she can stand puts it in reach)" % [map.name, it.get_parent().name])
	print("%s: %d cells reachable, %d/%d things in reach" % [map.name, reachable.size(),
		touched.size(), map.get_tree().get_nodes_in_group("interactable").filter(func(n): return map.is_ancestor_of(n)).size()])
