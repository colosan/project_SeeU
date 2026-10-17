extends Sprite2D
## Room background drawn at native resolution (see tools/gen_basement_floor.py),
## shown at an integer scale, plus invisible wall colliders.

const ENV_SCALE := 3

## Wall rectangles in native room pixels: x, y, w, h.
@export var walls: Array[Rect2] = [
	Rect2(0, 0, 320, 64),     # back wall
	Rect2(0, 0, 14, 240),     # left wall
	Rect2(306, 0, 14, 120),   # right wall above the exit
	Rect2(306, 176, 14, 64),  # right wall below the exit
]


## The front (south) wall drawn over everything in the room: same size as the room, transparent except the
## wall's top. A wall has depth, so whatever stands close behind it (props, SeeU) is partly hidden by it.
## Its lighting companion is <name>.height.png next to it, like the room's.
@export var front: Texture2D

## Above every Y-sorted prop and the player (they are all z 0).
const FRONT_Z := 10

var _size := Vector2.ZERO


func _ready() -> void:
	add_to_group("map_bounds")
	centered = false
	scale = Vector2(ENV_SCALE, ENV_SCALE)
	_size = texture.get_size()
	if PixelLighting.active_for(self):
		_split_for_lighting()
	if front != null:
		_add_front()
	var body := StaticBody2D.new()
	add_child(body)
	for r in walls:
		var shape := RectangleShape2D.new()
		shape.size = r.size
		var col := CollisionShape2D.new()
		col.shape = shape
		col.position = r.position + r.size / 2.0
		body.add_child(col)


## Lit maps: the room becomes a container holding the art (layer 1) and its height twin (layer 2),
## which shows the baked <name>.height.png companion written by the floor generator.
func _split_for_lighting() -> void:
	var art := texture
	var data_path := art.resource_path.get_basename() + ".height.png"
	if not ResourceLoader.exists(data_path):
		push_warning("pixel_room: no height map %s, the room stays unlit" % data_path)
		return
	texture = null
	var albedo := Sprite2D.new()
	albedo.name = "Art"
	albedo.texture = art
	albedo.centered = false
	add_child(albedo)
	var twin := Sprite2D.new()
	twin.name = "LightTwin"
	twin.texture = load(data_path)
	twin.centered = false
	twin.material = PixelLighting.height_material({"use_data": true, "emit": PixelLighting.emission_for(art)})
	PixelLighting.add_twin(self, twin)


func _add_front() -> void:
	var art := Sprite2D.new()
	art.name = "Front"
	art.texture = front
	art.centered = false
	art.z_as_relative = false
	art.z_index = FRONT_Z
	add_child(art)
	if not PixelLighting.active_for(self):
		return
	var data_path := front.resource_path.get_basename() + ".height.png"
	if not ResourceLoader.exists(data_path):
		push_warning("pixel_room: no height map %s, the front wall stays out of the lighting" % data_path)
		return
	var twin := Sprite2D.new()
	twin.name = "FrontTwin"
	twin.texture = load(data_path)
	twin.centered = false
	twin.z_as_relative = false
	twin.z_index = FRONT_Z
	twin.material = PixelLighting.height_material({"use_data": true, "emit": null})
	PixelLighting.add_twin(self, twin)


func get_world_rect() -> Rect2:
	return Rect2(global_position, _size * ENV_SCALE)
