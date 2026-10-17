extends SceneTree
## Project check (not part of the game): loads every map in Game.PLACES and checks what ties the maps together,
## the things a typo breaks silently. Run it after adding or changing a map:
##   $GODOT --headless --path . --script res://tools/check_project.gd
## Prints every problem and exits with code 1 if there is any (0 = all good).
##
## Checks: each place's scene loads and its root is named like its PLACES key (Game.place_of matches by name),
## floor ids exist in FLOORS and have a name, map coordinates lie on the left panel's picture; every exit's
## target scene exists and has the target spawn marker; every elevator stop's scene and marker exist and the floor
## is in FLOORS; a map has a player, a Lighting node and at most PixelLighting.MAX_LIGHTS lights; every
## Interactable has something to do; textures of props exist; a map with an elevator (group "elevator") has the
## FromElevator marker a ride arrives at; each floor's right-panel backdrop (BACKDROPS) exists (a floor without one
## is only noted).

var _problems: Array[String] = []


func _initialize() -> void:
	var game_script: GDScript = load("res://scripts/autoload/game.gd")
	var places: Dictionary = game_script.get_script_constant_map()["PLACES"]
	var floors: Array = game_script.get_script_constant_map()["FLOORS"]
	var floor_names: Dictionary = game_script.get_script_constant_map()["FLOOR_NAMES"]
	var floor_ids := floors.map(func(f): return f["id"])
	var map_tex: Texture2D = load("res://assets/ui/stack_map.png")

	for key in places:
		var p: Dictionary = places[key]
		var path: String = p["scene"]
		if not ResourceLoader.exists(path):
			_bad("place %s: no scene %s" % [key, path])
			continue
		if not p["floor"] in floor_ids:
			_bad("place %s: floor %s is not in FLOORS" % [key, p["floor"]])
		if not floor_names.has(p["floor"]):
			_bad("place %s: floor %s has no FLOOR_NAMES entry (left panel)" % [key, p["floor"]])
		var at: Vector2 = p["at"]
		if map_tex != null and not Rect2(Vector2.ZERO, map_tex.get_size()).has_point(at):
			_bad("place %s: map point %s is off the left panel's picture" % [key, at])
		var map: Node = (load(path) as PackedScene).instantiate()
		if map.name != key:
			_bad("place %s: the scene's root is called %s (Game.place_of matches by name)" % [key, map.name])
		_check_map(key, map)
		map.free()

	# elevator stops are filled at runtime (empty until the upper floors exist), so check the Game instance's table
	var game: Node = game_script.new()
	for floor_id in game.elevator_stops:
		var stop: Array = game.elevator_stops[floor_id]
		if not floor_id in floor_ids:
			_bad("elevator stop %s: not a floor in FLOORS" % floor_id)
		_check_target("elevator stop %s" % floor_id, stop[0], stop[1])
	game.free()

	# a floor with maps but no right-panel backdrop just shows the panel's plain colour: worth a note, not a failure
	var backdrops: Dictionary = (load("res://scripts/ui/info_panel.gd") as GDScript).get_script_constant_map()["BACKDROPS"]
	for key in places:
		var fl: String = places[key]["floor"]
		if not backdrops.has(fl):
			print("note: floor %s (%s) has no backdrop in info_panel.gd BACKDROPS" % [fl, key])
		elif not ResourceLoader.exists(backdrops[fl]):
			_bad("floor %s: backdrop %s does not exist" % [fl, backdrops[fl]])

	for line in _problems:
		printerr("PROBLEM: ", line)
	print("check_project: %d map(s), %d problem(s)" % [places.size(), _problems.size()])
	quit(1 if not _problems.is_empty() else 0)


func _check_map(key: String, map: Node) -> void:
	var players := map.find_children("*", "", true, false).filter(func(n): return n.is_in_group("player") \
		or (n.scene_file_path == "res://scenes/characters/player.tscn"))
	if players.is_empty():
		_bad("%s: no player in the map" % key)
	var lights := 0
	var has_lighting := false
	var has_lift := false
	for n in map.find_children("*", "", true, false):
		var script: Script = n.get_script()
		var sp := script.resource_path if script != null else ""
		if sp == "res://scripts/world/pixel_light.gd":
			lights += 1
		elif sp == "res://scripts/world/pixel_lighting.gd":
			has_lighting = true
		elif sp == "res://scripts/world/exit_zone.gd":
			_check_target("%s exit %s" % [key, n.name], n.target_map, n.target_spawn)
		elif sp == "res://scripts/world/interactable.gd":
			if n.action == &"" and n.lines.is_empty():
				_bad("%s: %s does nothing (no lines, no action)" % [key, n.get_path()])
		elif sp == "res://scripts/world/pixel_prop.gd":
			if n.texture == null:
				_bad("%s: prop %s has no texture" % [key, n.name])
			if n.is_in_group("elevator"):
				has_lift = true
	if not has_lighting:
		_bad("%s: no Lighting (PixelLighting) node" % key)
	if lights > PixelLighting.MAX_LIGHTS:
		_bad("%s: %d lights, the lighting pass takes %d" % [key, lights, PixelLighting.MAX_LIGHTS])
	if has_lift and map.find_child("FromElevator", true, false) == null:
		_bad("%s: has an elevator but no FromElevator marker (where a ride lets her out)" % key)


func _check_target(what: String, scene: String, spawn: StringName) -> void:
	if not ResourceLoader.exists(scene):
		_bad("%s: target scene %s does not exist" % [what, scene])
		return
	var m: Node = (load(scene) as PackedScene).instantiate()
	if m.find_child(String(spawn), true, false) == null:
		_bad("%s: %s has no spawn marker %s" % [what, scene.get_file(), spawn])
	m.free()


func _bad(line: String) -> void:
	_problems.append(line)
