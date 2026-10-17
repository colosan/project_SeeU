@tool
class_name PixelLight
extends Node2D
## A light for the native-res pixel-lighting pass (scripts/world/pixel_lighting.gd).
##
## The node's position is the FLOOR point under the light (screen px, like every other node);
## the visible source (bulb, screen, spark, chute mouth) is `height` native px above it, i.e. drawn
## at position + (0, -height * 3). Every light must sit on a visible source - the layout scripts check it.
##
## Flicker: `flicker` holds one energy multiplier per frame. With `sync_prop` pointing at an animated
## pixel_prop the multiplier follows that prop's current frame (bulb, sparks, TV, call button), so light
## and art never drift apart; without it the pattern runs at `flicker_fps`.

const GROUP := &"pixel_lights"
const SCALE := 3

enum Type { POINT, SPOT, BEAM }

@export var type := Type.POINT:
	set(v):
		type = v
		queue_redraw()
@export var color := Color(1.0, 0.86, 0.62)
@export_range(0.0, 8.0, 0.01) var energy := 1.0
## Native px above the floor point: where the visible source is.
@export var height := 30.0:
	set(v):
		height = v
		queue_redraw()
## Native px reach (point / spot). Beams use pool_radius instead.
@export var radius := 80.0:
	set(v):
		radius = v
		queue_redraw()
@export var casts_shadows := true

@export_group("Spot")
## Aim of the cone in native 3D: x east, y south (toward the viewer), z up.
@export var direction := Vector3(0, 1, -1)
## Full cone angle in degrees.
@export_range(1.0, 180.0) var angle := 120.0

@export_group("Beam")
## Radius of the pool on the floor (native px).
@export var pool_radius := 26.0
## Radius of the opening the beam falls from (native px).
@export var mouth_radius := 8.0
## Density of the visible light shaft (additive haze + drifting dust).
@export_range(0.0, 0.5, 0.005) var haze := 0.0

@export_group("Glow")
## Strength of the tiny dithered halo drawn around the source.
@export_range(0.0, 1.0, 0.01) var halo := 0.0
@export var halo_radius := 4.0

@export_group("Flicker")
## Energy multiplier per frame (empty = steady).
@export var flicker := PackedFloat32Array()
@export var flicker_fps := 8.0
## Animated pixel_prop whose current frame indexes `flicker`.
@export var sync_prop: NodePath

var _t := 0.0
var _prop: Node


func _enter_tree() -> void:
	add_to_group(GROUP)


func _ready() -> void:
	if not sync_prop.is_empty():
		_prop = get_node_or_null(sync_prop)


func _process(delta: float) -> void:
	_t += delta


## Energy this frame (flicker applied).
## "Reduce flicker" (pause menu, Game.reduce_flicker): every flickering light holds its average brightness.
static var steady := false


func current_energy() -> float:
	if flicker.is_empty():
		return energy
	if steady:
		var sum := 0.0
		for v in flicker:
			sum += v
		return energy * sum / flicker.size()
	var f := int(_t * flicker_fps)
	if _prop != null and is_instance_valid(_prop) and "current_frame" in _prop:
		f = _prop.current_frame
	return energy * flicker[f % flicker.size()]


## Where the source is drawn, in screen px relative to this node (editor gizmo, checks).
func source_offset() -> Vector2:
	return Vector2(0, -height * SCALE)


func _draw() -> void:
	if not Engine.is_editor_hint():
		return
	var c := Color(color, 0.9)
	draw_line(Vector2.ZERO, source_offset(), c, 1.0)
	draw_circle(source_offset(), 4.0, c)
	draw_line(Vector2(-6, 0), Vector2(6, 0), c, 1.0)
	var r := (pool_radius if type == Type.BEAM else radius) * SCALE
	draw_arc(Vector2.ZERO, r, 0.0, TAU, 48, Color(c, 0.35), 1.0)
