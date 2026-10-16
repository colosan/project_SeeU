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


func _ready() -> void:
	add_to_group("map_bounds")
	centered = false
	scale = Vector2(ENV_SCALE, ENV_SCALE)
	var body := StaticBody2D.new()
	add_child(body)
	for r in walls:
		var shape := RectangleShape2D.new()
		shape.size = r.size
		var col := CollisionShape2D.new()
		col.shape = shape
		col.position = r.position + r.size / 2.0
		body.add_child(col)


func get_world_rect() -> Rect2:
	return Rect2(global_position, texture.get_size() * ENV_SCALE)
