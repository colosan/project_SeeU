extends CharacterBody2D
## 4-direction (RPG Maker style) free movement. No diagonals: the most
## recently pressed axis wins, so turning feels responsive.

@export var speed := 240.0
@export_dir var sprite_dir := "res://assets/characters/seeu"

var facing := "south"
var _last_axis := Vector2.ZERO
var _twin: AnimatedSprite2D           # same frames on the lighting height layer (see PixelLighting)

@onready var sprite: AnimatedSprite2D = $Sprite
@onready var camera: Camera2D = $Camera


func _ready() -> void:
	add_to_group("player")
	_ensure_input_actions()
	sprite.sprite_frames = CharacterFrames.build(sprite_dir)
	sprite.play("idle_" + facing)
	if PixelLighting.active_for(self):
		_add_light_twin()
	_apply_camera_limits.call_deferred()


## Her sprite is 1:1 screen px, so heights are (feet line - y) / 3 native px.
func _add_light_twin() -> void:
	_twin = AnimatedSprite2D.new()
	_twin.name = "LightTwin"
	_twin.sprite_frames = sprite.sprite_frames
	_twin.offset = sprite.offset
	_twin.centered = sprite.centered
	_twin.material = PixelLighting.height_material({
		"base_y": 0.0, "units_per_native": float(PixelLighting.SCALE), "kind": PixelLighting.KIND_CHARACTER})
	PixelLighting.add_twin(self, _twin)
	# Sync in _process AFTER the sprite advanced its frame (higher priority value = later): a sprite's
	# redraw is deferred, so a change made any later (e.g. right before drawing) would show a frame late.
	process_priority = 100
	_process(0.0)


func _process(_delta: float) -> void:
	if _twin == null:
		return
	if _twin.animation != sprite.animation:
		_twin.animation = sprite.animation
	_twin.frame = sprite.frame
	_twin.flip_h = sprite.flip_h


## Turn to "north" / "south" / "east" / "west" without moving (e.g. after arriving through a door).
func face(dir: String) -> void:
	facing = dir
	sprite.play("idle_" + facing)


## Re-read the map bounds and jump the camera to the player (after a map change or teleport).
func refresh_camera() -> void:
	_apply_camera_limits()
	camera.force_update_scroll()
	camera.reset_smoothing()


## Keep the camera inside the current map so the void past its edge never shows.
## Safe to call again whenever the map changes.
func _apply_camera_limits() -> void:
	var map := get_tree().get_first_node_in_group("map_bounds")
	if map == null:
		return
	var r: Rect2 = map.get_world_rect()
	camera.limit_left = int(r.position.x)
	camera.limit_top = int(r.position.y)
	camera.limit_right = int(r.end.x)
	camera.limit_bottom = int(r.end.y)
	camera.reset_smoothing()


func _physics_process(_delta: float) -> void:
	var dir := _read_direction()
	velocity = dir * speed
	move_and_slide()

	if dir != Vector2.ZERO:
		facing = _direction_name(dir)
		sprite.play("walk_" + facing)
	else:
		sprite.play("idle_" + facing)


func _read_direction() -> Vector2:
	var x := Input.get_axis("move_left", "move_right")
	var y := Input.get_axis("move_up", "move_down")
	if Input.is_action_just_pressed("move_left") or Input.is_action_just_pressed("move_right"):
		_last_axis = Vector2.RIGHT
	elif Input.is_action_just_pressed("move_up") or Input.is_action_just_pressed("move_down"):
		_last_axis = Vector2.DOWN

	if x != 0.0 and y != 0.0:
		return Vector2(signf(x), 0) if _last_axis == Vector2.RIGHT else Vector2(0, signf(y))
	if x != 0.0:
		return Vector2(signf(x), 0)
	if y != 0.0:
		return Vector2(0, signf(y))
	return Vector2.ZERO


static func _direction_name(dir: Vector2) -> String:
	if dir.x > 0: return "east"
	if dir.x < 0: return "west"
	if dir.y < 0: return "north"
	return "south"


## Arrow keys + WASD, registered at runtime so project.godot stays readable.
static func _ensure_input_actions() -> void:
	var bindings := {
		"move_up": [KEY_UP, KEY_W],
		"move_down": [KEY_DOWN, KEY_S],
		"move_left": [KEY_LEFT, KEY_A],
		"move_right": [KEY_RIGHT, KEY_D],
	}
	for action in bindings:
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action)
		for key in bindings[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = key
			InputMap.action_add_event(action, ev)
