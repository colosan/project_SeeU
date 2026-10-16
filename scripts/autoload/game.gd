extends Node
## Global game flow (autoload "Game"). For now: moving between maps.
##
## change_map() fades the game view to black, swaps the map under the MapHost,
## puts the new map's Player on the Marker2D named `spawn` (facing the marker's
## "facing" metadata), snaps the camera to the new map and fades back in.

signal map_changed(map: Node)

const FADE_OUT := 0.3
const FADE_IN := 0.35

var _host: Node            # MapHost inside the game viewport
var _fade: ColorRect       # black overlay inside the same viewport
var _busy := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS   # keep fading while the world is paused


## Called by MapHost: the fade overlay lives in the host's viewport so only the game view goes black.
func register_host(host: Node) -> void:
	_host = host
	var layer := CanvasLayer.new()
	layer.name = "Fade"
	layer.layer = 100
	_fade = ColorRect.new()
	_fade.color = Color(0, 0, 0, 0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(_fade)
	host.add_child(layer)


func is_changing_map() -> bool:
	return _busy


func change_map(scene_path: String, spawn: StringName) -> void:
	if _busy or _host == null:
		return
	_busy = true
	get_tree().paused = true                    # freeze the player and props during the fade
	await _fade_to(1.0, FADE_OUT)

	var map: Node = _host.load_map(scene_path)
	var player := _find_player(map)
	var marker := map.find_child(String(spawn), true, false) as Node2D
	if player != null and marker != null:
		player.global_position = marker.global_position
		if marker.has_meta("facing"):
			player.face(String(marker.get_meta("facing")))
	elif marker == null:
		push_warning("Game.change_map: no spawn '%s' in %s" % [spawn, scene_path])
	if player != null:
		player.refresh_camera()
	map_changed.emit(map)

	get_tree().paused = false
	await _fade_to(0.0, FADE_IN)
	_busy = false


func _fade_to(alpha: float, time: float) -> void:
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", alpha, time)
	await tw.finished


static func _find_player(map: Node) -> Node:
	for n in map.get_tree().get_nodes_in_group("player"):
		if map.is_ancestor_of(n):
			return n
	return null
