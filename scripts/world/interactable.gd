class_name Interactable
extends Area2D
## Something SeeU can examine or use: she faces it, presses interact (Z / Space / Enter) and it answers.
## Put on a prop by the layout scripts (PLAN extra "examine" or "use"), never by hand.
##   lines  - what is said when she examines it (pages, shown one at a time in the dialogue box)
##   action - "" = just say the lines; "elevator" = open the elevator's floor panel
## The trigger is `size` (screen px) centred on `position`; the player's reach box finds it.

const LAYER := 1 << 7                    # physics layer 8: only the player's reach looks at it

@export var lines: PackedStringArray = []
@export var speaker := ""
@export var action: StringName = &""
@export var prompt := "조사"
@export var size := Vector2(60, 60)


func _ready() -> void:
	add_to_group("interactable")
	collision_layer = LAYER
	collision_mask = 0
	monitoring = false
	monitorable = true
	var shape := RectangleShape2D.new()
	shape.size = size
	var col := CollisionShape2D.new()
	col.shape = shape
	add_child(col)


## Starts the reaction and returns at once (not awaited: a ride on the elevator frees this map, us included,
## before the coroutine would resume).
func interact() -> void:
	_flash()
	if action == &"elevator":
		Game.open_elevator()
	elif not lines.is_empty():
		Game.say(Array(lines), speaker)


## The thing she examines brightens for a blink, so it is clear which one answered.
func _flash() -> void:
	if get_parent().has_method("flash"):
		get_parent().flash()
