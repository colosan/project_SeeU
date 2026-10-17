extends CharacterBody2D
## 4-direction (RPG Maker style) free movement. No diagonals: the most
## recently pressed axis wins, so turning feels responsive.

@export var speed := 240.0
@export_dir var sprite_dir := "res://assets/characters/seeu"

var facing := "south"
var _last_axis := Vector2.ZERO
var _twin: AnimatedSprite2D           # same frames on the lighting height layer (see PixelLighting)
var _reach: Area2D                    # a box just in front of her: what she could examine or use
var _target: Interactable

## Where the reach box sits for each facing (screen px from her feet), and its size.
const REACH := {"south": Vector2(0, 16), "north": Vector2(0, -34), "east": Vector2(30, -8), "west": Vector2(-30, -8)}
const REACH_SIZE := Vector2(40, 30)

@onready var sprite: AnimatedSprite2D = $Sprite
@onready var camera: Camera2D = $Camera


func _ready() -> void:
	add_to_group("player")
	_ensure_input_actions()
	sprite.sprite_frames = CharacterFrames.build(sprite_dir)
	sprite.play("idle_" + facing)
	if PixelLighting.active_for(self):
		_add_light_twin()
	_add_reach()
	_add_steps()
	_add_shadow()
	_apply_camera_limits.call_deferred()
	get_viewport().size_changed.connect(_apply_camera_limits)   # wider/taller window: re-centre small rooms


## Footsteps: a soft scuff (assets/audio/env_step.wav, tools/audio/gen_sfx.py) whenever a walk frame puts a
## foot down, slightly varied in pitch so a long walk doesn't tick like a clock.
const STEP_FRAMES := [2, 6]                    # widest stride of the 8-frame walk cycles
const STEP_DB := -23.0
var _steps: AudioStreamPlayer


## A small contact shadow under her feet, drawn like the props' (3x pixels, the same colour), so she stands on
## the floor instead of floating over it. Under the sprite, above the floor.
const SHADOW_ROWS := ["....xxxxxx....", "..xxxxxxxxxx..", "..xxxxxxxxxx..", "....xxxxxx...."]


func _add_shadow() -> void:
	var w: int = SHADOW_ROWS[0].length()
	var img := Image.create(w, SHADOW_ROWS.size(), false, Image.FORMAT_RGBA8)
	for y in SHADOW_ROWS.size():
		for x in w:
			if SHADOW_ROWS[y][x] == "x":
				img.set_pixel(x, y, Color(0.06, 0.06, 0.06, 0.6))   # pixel_prop.gd SHADOW_COLOR
	var s := Sprite2D.new()
	s.name = "Shadow"
	s.texture = ImageTexture.create_from_image(img)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	s.scale = Vector2(3, 3)
	s.position = Vector2(0, -3)                     # centred on the soles: peeks out evenly around both shoes
	add_child(s)
	move_child(s, 0)                               # drawn before (under) the sprite


func _add_steps() -> void:
	if not ResourceLoader.exists("res://assets/audio/env_step.wav"):
		return
	_steps = AudioStreamPlayer.new()
	_steps.stream = load("res://assets/audio/env_step.wav")
	_steps.volume_db = STEP_DB
	add_child(_steps)
	sprite.frame_changed.connect(_on_frame)


func _on_frame() -> void:
	if sprite.animation.begins_with("walk_") and sprite.frame in STEP_FRAMES:
		_steps.pitch_scale = randf_range(0.88, 1.12)
		_steps.play()


func _exit_tree() -> void:
	SoundUtil.silence(_steps)


func _add_reach() -> void:
	_reach = Area2D.new()
	_reach.name = "Reach"
	_reach.collision_layer = 0
	_reach.collision_mask = Interactable.LAYER
	_reach.monitorable = false
	var shape := RectangleShape2D.new()
	shape.size = REACH_SIZE
	var col := CollisionShape2D.new()
	col.shape = shape
	_reach.add_child(col)
	add_child(_reach)


## The nearest interactable in front of her, or null.
func _find_target() -> Interactable:
	_reach.position = REACH[facing]
	var best: Interactable = null
	var best_d := INF
	for a in _reach.get_overlapping_areas():
		var it := a as Interactable
		if it == null:
			continue
		var d := it.global_position.distance_squared_to(_reach.global_position)
		if it.action != &"":                     # something to use (the call box) beats something to look at
			d -= 1e9                             # (the stool under it) when both are in reach
		if d < best_d:
			best = it
			best_d = d
	return best


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact", false, true) and not event.is_echo() and Game.can_move() \
			and _target != null and not scripted:
		get_viewport().set_input_as_handled()
		sprite.play("idle_" + facing)
		Game.set_hint("")
		_target.interact()


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
## A map smaller than the view is centred in it instead (void shows evenly around it).
## Safe to call again whenever the map changes.
func _apply_camera_limits() -> void:
	var map := get_tree().get_first_node_in_group("map_bounds")
	if map == null:
		return
	var r: Rect2 = map.get_world_rect()
	var view := get_viewport_rect().size
	# Grow by whole native pixels on each side so the art stays on the screen's 3 px grid.
	var step := float(PixelLighting.SCALE)
	var pad := ((view - r.size).max(Vector2.ZERO) / (2.0 * step)).floor() * step
	r = r.grow_individual(pad.x, pad.y, view.x - r.size.x - pad.x if pad.x > 0 else 0.0,
		view.y - r.size.y - pad.y if pad.y > 0 else 0.0)
	camera.limit_left = int(r.position.x)
	camera.limit_top = int(r.position.y)
	camera.limit_right = int(r.end.x)
	camera.limit_bottom = int(r.end.y)
	camera.reset_smoothing()


## A scripted walk (cutscenes, the elevator ride): straight to `to` at walking speed, ignoring walls and input.
## Returns when she is there; she stays scripted (frozen in place) until `scripted` is set false again.
var scripted := false


func walk_to(to: Vector2) -> void:
	scripted = true
	var d := to - global_position
	if d.length() < 1.0:
		return
	facing = _direction_name(d)
	sprite.play("walk_" + facing)
	var tw := create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)   # physics ticks: interpolation stays smooth
	tw.tween_property(self, "global_position", to, d.length() / speed)
	await tw.finished
	sprite.play("idle_" + facing)


func _physics_process(_delta: float) -> void:
	if scripted:
		return
	if not Game.can_move():                    # talking, a panel open, or a map changing
		velocity = Vector2.ZERO
		sprite.play("idle_" + facing)
		return
	_target = _find_target()
	Game.set_hint(_target.prompt if _target != null else "")
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
