extends Area2D
## Invisible doorway: when the player walks in, Game moves her to `target_spawn` in `target_map`.
## The trigger rectangle is `size` (screen px), centred on the node.

@export_file("*.tscn") var target_map := ""
@export var target_spawn: StringName = &""
@export var size := Vector2(42, 165)


func _ready() -> void:
	var shape := RectangleShape2D.new()
	shape.size = size
	var col := CollisionShape2D.new()
	col.shape = shape
	add_child(col)
	monitorable = false
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node) -> void:
	if body.is_in_group("player") and target_map != "":
		Game.change_map.call_deferred(target_map, target_spawn)
