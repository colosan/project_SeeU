@tool
extends StaticBody2D
## A static environment prop drawn at the environment's native resolution and
## shown at ENV_SCALE (integer) so its pixels match the floor. The origin is the
## prop's base (feet line) so Y-sorting against characters works.

const ENV_SCALE := 3

@export var texture: Texture2D:
	set(v):
		texture = v
		_rebuild()
@export var flip_h := false:
	set(v):
		flip_h = v
		_rebuild()
## >1 for animated strips (frames side by side in one PNG).
@export var frames := 1:
	set(v):
		frames = maxi(1, v)
		_rebuild()
@export var fps := 8.0
## A second strip drawn over the art, frame for frame (the elevator's gate over its car): set_overlay_front()
## lifts it one z step so a character can stand between the two (riding the car behind the gate).
@export var overlay: Texture2D:
	set(v):
		overlay = v
		_rebuild()
## A flashing animation (a flickering bulb, a TV, sparks): held on frame 0 while "reduce flicker" is on
## (PixelLight.steady, the pause menu).
@export var flashes := false
## false = the frames are not looped: they are stepped on command (play_to), e.g. the elevator gate opening.
@export var autoplay := true
## Native px between the sprite's bottom row and the floor, for props hung on a wall face
## (lighting heights). 0 = stands on the floor at its base line.
@export var height_offset := 0

## A room sound (assets/audio/env_<sound>.wav, tools/audio/gen_sfx.py) played, positioned at the prop, whenever
## the animation reaches one of `sound_frames` (the drop lands, the line sparks). "" = silent.
@export var sound := ""
@export var sound_frames := PackedInt32Array()
@export var sound_db := -12.0

## Frame shown right now (PixelLight.sync_prop reads it to flicker in step).
var current_frame := 0

var _twin: Sprite2D
var _sound: AudioStreamPlayer2D
var _overlay: Sprite2D
var _sprite: Sprite2D
var _anim_t := 0.0

## Off for walkable floor litter: no collider, no shadow, drawn under everything.
@export var solid := true:
	set(v):
		solid = v
		_rebuild()
## Fraction of the sprite height (from the bottom) that blocks movement.
@export_range(0.05, 1.0) var solid_fraction := 0.35:
	set(v):
		solid_fraction = v
		_rebuild()


func _ready() -> void:
	_rebuild()


func _rebuild() -> void:
	if not is_inside_tree():
		return
	for c in get_children():
		if c.owner == null:                      # only the parts this script made; children from the scene
			c.queue_free()                       # (e.g. an Interactable the layout put under the prop) stay
	if texture == null:
		return
	var size := texture.get_size()
	size.x /= frames
	z_index = 0 if solid else -5

	if solid:
		# Contact shadow that hugs the art's real bottom contour (native pixels, scaled like the art).
		var shadow := Sprite2D.new()
		shadow.texture = _shadow_for(texture, frames, flip_h)
		shadow.centered = false
		shadow.scale = Vector2(ENV_SCALE, ENV_SCALE)
		shadow.position = Vector2(-(size.x + 2 * SHADOW_PAD) * ENV_SCALE / 2.0, -size.y * ENV_SCALE)
		add_child(shadow)

	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.hframes = frames
	sprite.flip_h = flip_h
	sprite.centered = false
	sprite.scale = Vector2(ENV_SCALE, ENV_SCALE)
	sprite.position = Vector2(-size.x * ENV_SCALE / 2.0, -size.y * ENV_SCALE)
	add_child(sprite)
	_sprite = sprite
	_overlay = null
	if overlay != null:
		_overlay = _strip_like(sprite, overlay)
		add_child(_overlay)
	_twin = null
	if not Engine.is_editor_hint() and PixelLighting.active_for(self):
		_add_light_twin(sprite)
	_sound = null
	if sound != "" and not Engine.is_editor_hint():
		_add_sound()

	if not solid:
		return
	var shape := RectangleShape2D.new()
	shape.size = Vector2(size.x * 0.8, size.y * solid_fraction) * ENV_SCALE
	var col := CollisionShape2D.new()
	col.shape = shape
	col.position = Vector2(0, -shape.size.y / 2.0)
	add_child(col)


const SHADOW_PAD := 2        # native px the shadow may spread past the art on each side
const SHADOW_DEPTH := 3      # native px of shadow under the lowest pixel of each column
const SHADOW_COLOR := Color(0.06, 0.06, 0.06, 0.6)


static var _shadows := {}    # [texture, frames, flip] -> contact shadow: built once, reused on every map visit


static func _shadow_for(tex: Texture2D, n_frames: int, flipped: bool) -> ImageTexture:
	var key := [tex, n_frames, flipped]
	if not _shadows.has(key):
		var img := tex.get_image()
		if n_frames > 1:
			img = img.get_region(Rect2i(0, 0, img.get_width() / n_frames, img.get_height()))
		_shadows[key] = _contact_shadow(img, flipped)
	return _shadows[key]


## For every column, find the lowest opaque pixel and lay a short shadow right under
## (and slightly overlapping) it, then spread it sideways so edges also touch the floor.
static func _contact_shadow(src: Image, flipped: bool) -> ImageTexture:
	if src.is_compressed():
		src.decompress()
	var w := src.get_width()
	var h := src.get_height()
	var out := Image.create(w + 2 * SHADOW_PAD, h + SHADOW_DEPTH, false, Image.FORMAT_RGBA8)
	var bottoms := PackedInt32Array()
	bottoms.resize(w)
	for x in w:
		bottoms[x] = -1
		for y in range(h - 1, -1, -1):
			if src.get_pixel(x, y).a > 0.5:
				bottoms[x] = y
				break
	for x in w:
		var b := bottoms[x]
		if b < 0:
			continue
		var ox := (w - 1 - x) if flipped else x
		for dx in range(-SHADOW_PAD, SHADOW_PAD + 1):
			for y in range(b - 1, b + SHADOW_DEPTH):
				out.set_pixel(ox + dx + SHADOW_PAD, y, SHADOW_COLOR)
	return ImageTexture.create_from_image(out)


## Same sprite on the lighting height layer: standing props are vertical faces whose height grows
## from the base line; floor decals (not solid, not wall-hung) lie flat.
func _add_light_twin(sprite: Sprite2D) -> void:
	_twin = _strip_like(sprite, sprite.texture)
	_twin.name = "LightTwin"
	_twin.material = PixelLighting.height_material({
		"base_y": sprite.texture.get_height(), "units_per_native": 1.0, "height_offset": float(height_offset),
		"kind": PixelLighting.KIND_FACE, "lies_flat": not solid and height_offset == 0,
		"emit": PixelLighting.emission_for(texture)})
	PixelLighting.add_twin(self, _twin)


## A sprite laid exactly over `src` (same frames, flip, scale, place) showing `tex`: the overlay and the light twin.
static func _strip_like(src: Sprite2D, tex: Texture2D) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = tex
	s.hframes = src.hframes
	s.flip_h = src.flip_h
	s.centered = false
	s.scale = src.scale
	s.position = src.position
	return s


func _add_sound() -> void:
	_sound = SoundUtil.positional("res://assets/audio/env_%s.wav" % sound, sound_db)
	if _sound == null:
		return
	_sound.position = Vector2(0, -texture.get_height() * ENV_SCALE / 2.0)
	add_child(_sound)


func _exit_tree() -> void:
	SoundUtil.silence(_sound)


## Steps the frames one by one at `fps` until `target` is shown (autoplay = false props). Returns when there.
func play_to(target: int) -> void:
	target = clampi(target, 0, frames - 1)
	while current_frame != target and is_inside_tree():
		await get_tree().create_timer(1.0 / fps, false).timeout
		_show_frame(current_frame + signi(target - current_frame))


func _process(delta: float) -> void:
	if frames <= 1 or not is_instance_valid(_sprite) or not autoplay:
		return
	_anim_t += delta
	var f := int(_anim_t * fps) % frames
	if flashes and PixelLight.steady:
		f = 0
	if f == current_frame:
		return                                   # nothing to update this frame
	_show_frame(f)


## A blink of light on the art only (not its lighting twin, whose colours are heights): "this one answered".
func flash() -> void:
	if _sprite == null:
		return
	var tw := create_tween()
	tw.tween_property(_sprite, "self_modulate", Color(1.35, 1.35, 1.35), 0.07)
	tw.tween_property(_sprite, "self_modulate", Color.WHITE, 0.2)


## true: the overlay draws above everything y-sorted at z 0 (a rider at z 1 then sits between car and gate).
func set_overlay_front(on: bool) -> void:
	if _overlay != null:
		_overlay.z_index = 1 if on else 0


func _show_frame(f: int) -> void:
	current_frame = f
	_sprite.frame = current_frame
	if _overlay != null:
		_overlay.frame = current_frame
	if _twin != null and is_instance_valid(_twin):
		_twin.frame = current_frame
	if _sound != null and current_frame in sound_frames:
		_sound.play()
