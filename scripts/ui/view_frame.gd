extends Control
## A frame around the game view, drawn over it: a thin steel bezel and teal HUD brackets in the corners, so
## the eye settles on the game between the two panels. Draws only lines; clicks pass through.
## Follows the game view's rectangle (it grows with wider windows, the panels keep their size).

@export var target: NodePath

const BEZEL := 3.0                       # one art pixel at the 3x world scale
const BRACKET := 30.0                    # length of each corner bracket arm
const INSET := 9.0                       # brackets sit this far inside the bezel


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(queue_redraw)
	var t := get_node_or_null(target) as Control
	if t != null:
		t.resized.connect(_follow.bind(t))
		_follow.call_deferred(t)


func _follow(t: Control) -> void:
	position = t.position + (t.get_parent() as Control).position
	size = t.size


func _draw() -> void:
	var r := Rect2(Vector2.ZERO, size)
	# bezel: steel, with a dark inner line so the game's own edge stays crisp
	draw_rect(r, UiStyle.LINE_HI, false, BEZEL * 2.0)
	draw_rect(r.grow(-BEZEL), Color(UiStyle.BG, 0.9), false, 2.0)
	# HUD brackets in the four corners
	var a := INSET + BEZEL
	for corner in [Vector2(a, a), Vector2(size.x - a, a), Vector2(a, size.y - a), Vector2(size.x - a, size.y - a)]:
		var sx := 1.0 if corner.x < size.x / 2.0 else -1.0
		var sy := 1.0 if corner.y < size.y / 2.0 else -1.0
		draw_rect(Rect2(corner, Vector2(BRACKET * sx, BEZEL * sy)).abs(), UiStyle.ACCENT)
		draw_rect(Rect2(corner, Vector2(BEZEL * sx, BRACKET * sy)).abs(), UiStyle.ACCENT)
