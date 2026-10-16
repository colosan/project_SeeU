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
## Native px between the sprite's bottom row and the floor, for props hung on a wall face
## (lighting heights). 0 = stands on the floor at its base line.
@export var height_offset := 0

## Frame shown right now (PixelLight.sync_prop reads it to flicker in step).
var current_frame := 0

var _anim_sprite: Sprite2D
var _twin: Sprite2D
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
		c.queue_free()
	if texture == null:
		return
	var size := texture.get_size()
	size.x /= frames
	z_index = 0 if solid else -5

	if solid:
		# Contact shadow that hugs the art's real bottom contour (native pixels, scaled like the art).
		var shadow := Sprite2D.new()
		var img := texture.get_image()
		if frames > 1:
			img = img.get_region(Rect2i(0, 0, int(size.x), int(size.y)))
		shadow.texture = _contact_shadow(img, flip_h)
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
	_anim_sprite = sprite if frames > 1 else null
	_twin = null
	if not Engine.is_editor_hint() and PixelLighting.active_for(self):
		_add_light_twin(sprite)

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
	_twin = Sprite2D.new()
	_twin.name = "LightTwin"
	_twin.texture = sprite.texture
	_twin.hframes = sprite.hframes
	_twin.flip_h = sprite.flip_h
	_twin.centered = false
	_twin.scale = sprite.scale
	_twin.position = sprite.position
	_twin.material = PixelLighting.height_material({
		"base_y": sprite.texture.get_height(), "units_per_native": 1.0, "height_offset": float(height_offset),
		"kind": PixelLighting.KIND_FACE, "lies_flat": not solid and height_offset == 0,
		"emit": PixelLighting.emission_for(texture)})
	PixelLighting.add_twin(self, _twin)


func _process(delta: float) -> void:
	if _anim_sprite == null or not is_instance_valid(_anim_sprite):
		return
	_anim_t += delta
	current_frame = int(_anim_t * fps) % frames
	_anim_sprite.frame = current_frame
	if _twin != null and is_instance_valid(_twin):
		_twin.frame = current_frame
