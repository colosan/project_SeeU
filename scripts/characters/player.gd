extends CharacterBody2D
## 4-direction (RPG Maker style) free movement. No diagonals: the most
## recently pressed axis wins, so turning feels responsive.

@export var speed := 240.0
@export_dir var sprite_dir := "res://assets/characters/seeu"

var facing := "south"
var _last_axis := Vector2.ZERO

@onready var sprite: AnimatedSprite2D = $Sprite
@onready var camera: Camera2D = $Camera


func _ready() -> void:
	add_to_group("player")
	_ensure_input_actions()
	sprite.sprite_frames = CharacterFrames.build(sprite_dir)
	sprite.play("idle_" + facing)
	_apply_camera_limits.call_deferred()


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
