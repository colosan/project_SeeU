class_name PixelLighting
extends Node
## Per-map 2.5D deferred pixel lighting. Put one in every lit map (the layout scripts do);
## it replaces CanvasModulate + PointLight2D.
##
## Passes, all at NATIVE resolution (1 px = one 3x3 art pixel, aligned to the art's grid):
##   1. HeightVP  - shares the game viewport's World2D but culls to visibility layer 2, where every lit
##                  visual has a "twin" drawn with shaders/lighting/height.gdshader: R height above the
##                  floor, G emission, B surface kind, A coverage. Same nodes, same Y-sort, 1/3 scale.
##   2. LightVP   - one rect with shaders/lighting/light.gdshader reads the height buffer and up to 16
##                  PixelLights: falloff, lambert, spot cones, beams, screen-space shadows, contact AO,
##                  quantized + Bayer-dithered steps; right half = additive glow (haze, dust, halos).
##   3. Composite - a CanvasLayer over the world (under the fade/UI): one 3x nearest-filtered sprite whose
##                  shader (shaders/lighting/composite.gdshader) reads the drawn scene and writes
##                  albedo x light + glow, light 0..2 (stored as light / 2, so pools may brighten the dark art;
##                  above 1 dark pixels are lifted more than bright ones so pale parts don't clip).
## The camera may sit on any screen pixel: the buffers follow the world's native grid and the composite is
## shifted by the remainder, so light pixels always sit on the art's pixels.

const SCALE := 3
const LAYER_ALBEDO := 1
const LAYER_HEIGHT := 2
const MAX_LIGHTS := 16
const GROUP := &"pixel_lighting"
const KIND_FLOOR := 0
const KIND_FACE := 1
const KIND_CHARACTER := 2
const COMPOSITE_LAYER := 50                     # above the world, below Game's fade (100) and any UI
const HEIGHT_SHADER := preload("res://shaders/lighting/height.gdshader")
const LIGHT_SHADER := preload("res://shaders/lighting/light.gdshader")
const COMPOSITE_SHADER := preload("res://shaders/lighting/composite.gdshader")

## Dim cool base light of the map (the floor never goes pure black; void does).
@export var ambient := Color(0.30, 0.32, 0.40)
## Light (x art colour) of the brightest pools; 1 = the art as painted, up to 2.
@export_range(1.0, 2.0, 0.05) var peak := 1.6
## Light steps between ambient and the peak (ordered-dithered in between).
@export_range(2, 16) var levels := 8
@export_range(0.0, 1.0, 0.01) var ao_strength := 0.35
## Extra light on the player's own pixels so she stays readable in shadow.
@export_range(0.0, 0.5, 0.01) var player_fill := 0.16

var _game_vp: Viewport
var _height_vp: SubViewport
var _light_vp: SubViewport
var _light_rect: ColorRect
var _light_mat: ShaderMaterial
var _comp: Sprite2D
var _warmup: ColorRect                  # black until the light buffers have been drawn once
var _syncs := 0
var _size := Vector2i.ZERO
var _flip_y := false


# ---------- helpers used by the lit visuals (pixel_room, pixel_prop, player) ----------

## True when the scene the node belongs to is lit by a PixelLighting (and we are not in the editor).
static func active_for(node: Node) -> bool:
	return not Engine.is_editor_hint() and node.is_inside_tree() \
		and node.get_tree().get_first_node_in_group(GROUP) != null


## Adds `twin` under `parent` on the height layer. Every CanvasItem above it must share that layer
## (a viewport only draws an item if it and all its parents match its cull mask); those ancestors are
## containers that draw nothing themselves, so giving them both layers is harmless.
static func add_twin(parent: Node, twin: CanvasItem) -> void:
	twin.visibility_layer = LAYER_HEIGHT
	twin.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	parent.add_child(twin)
	var n: Node = parent
	while n is CanvasItem:
		(n as CanvasItem).visibility_layer |= LAYER_HEIGHT
		n = n.get_parent()


## Height-buffer material for one twin. Keys: base_y, units_per_native, height_offset, kind, lies_flat,
## use_data, emit (Texture2D or null).
static func height_material(params: Dictionary) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = HEIGHT_SHADER
	for k in params:
		if k == "emit":
			if params[k] != null:
				m.set_shader_parameter("emit_tex", params[k])
		else:
			m.set_shader_parameter(k, params[k])
	return m


## The emission mask that tools/art/gen_emission.py wrote next to `tex` (null = nothing glows).
static func emission_for(tex: Texture2D) -> Texture2D:
	if tex == null or tex.resource_path.is_empty():
		return null
	var p := tex.resource_path.get_basename() + ".emit.png"
	return load(p) if ResourceLoader.exists(p) else null


# ---------- the passes ----------

func _enter_tree() -> void:
	add_to_group(GROUP)


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_game_vp = get_viewport()
	_game_vp.canvas_cull_mask = LAYER_ALBEDO
	# texelFetch row 0 is the top row of a viewport texture on the Compatibility renderer (checked
	# with buffer dumps); keep the switch for backends that store render targets bottom-up.
	_flip_y = false

	_light_vp = SubViewport.new()
	_light_vp.name = "LightVP"
	_light_vp.disable_3d = true
	_light_vp.transparent_bg = false
	_light_vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	_light_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_light_mat = ShaderMaterial.new()
	_light_mat.shader = LIGHT_SHADER
	_light_rect = ColorRect.new()
	_light_rect.material = _light_mat
	_light_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_light_vp.add_child(_light_rect)

	# Child of LightVP so it renders first (child viewports draw before their parents).
	_height_vp = SubViewport.new()
	_height_vp.name = "HeightVP"
	_height_vp.disable_3d = true
	_height_vp.transparent_bg = true
	_height_vp.world_2d = _game_vp.world_2d
	_height_vp.canvas_cull_mask = LAYER_HEIGHT
	_height_vp.snap_2d_transforms_to_pixel = true
	_height_vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	_height_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_light_vp.add_child(_height_vp)
	add_child(_light_vp)
	_light_mat.set_shader_parameter("height_buf", _height_vp.get_texture())

	var layer := CanvasLayer.new()
	layer.name = "LightComposite"
	layer.layer = COMPOSITE_LAYER
	add_child(layer)
	_comp = Sprite2D.new()
	_comp.name = "Composite"
	_comp.texture = _light_vp.get_texture()
	_comp.centered = false
	_comp.region_enabled = true
	_comp.scale = Vector2(SCALE, SCALE)
	_comp.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var cm := ShaderMaterial.new()
	cm.shader = COMPOSITE_SHADER
	_comp.material = cm
	layer.add_child(_comp)
	# The very first frame has no light texture yet; show black instead of the unlit art.
	_warmup = ColorRect.new()
	_warmup.color = Color.BLACK
	_warmup.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_warmup.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(_warmup)

	_sync()
	RenderingServer.frame_pre_draw.connect(_sync)


func _exit_tree() -> void:
	if RenderingServer.frame_pre_draw.is_connected(_sync):
		RenderingServer.frame_pre_draw.disconnect(_sync)
	if _game_vp != null:
		_game_vp.canvas_cull_mask = 0xFFFFFFFF


func _resize(size: Vector2i) -> void:
	_size = size
	_height_vp.size = size
	_light_vp.size = Vector2i(size.x * 2, size.y)
	_light_rect.size = Vector2(size.x * 2, size.y)
	_comp.region_rect = Rect2(0, 0, size.x, size.y)
	_light_mat.set_shader_parameter("buf_size", size)


## Runs right before every frame is drawn (after all game logic and the camera have moved).
func _sync() -> void:
	if not is_inside_tree():
		return
	var view := Vector2i((_game_vp.get_visible_rect().size / SCALE).ceil()) + Vector2i.ONE
	if view != _size:
		_resize(view)
	# Buffer pixel (0, 0) sits on a world native pixel; the composite takes the sub-native remainder.
	var o := _game_vp.canvas_transform.origin.round()
	var on := Vector2i(ceili(o.x / SCALE), ceili(o.y / SCALE))
	_height_vp.canvas_transform = Transform2D(0.0, Vector2.ONE / SCALE, 0.0, Vector2(on))
	var rem := o - Vector2(on * SCALE)
	_comp.position = rem
	_feed_clip()
	_feed_lights(on)
	_syncs += 1
	if _warmup != null and _syncs > 2:
		_warmup.hide()
		_warmup.queue_free()
		_warmup = null


## The map's rectangle on screen: the composite paints everything outside it black (the void).
func _feed_clip() -> void:
	var clip := Vector4(0.0, 0.0, 1.0, 1.0)
	var map := get_tree().get_first_node_in_group("map_bounds")
	if map != null and map.has_method("get_world_rect"):
		var r: Rect2 = map.get_world_rect()
		var view := _game_vp.get_visible_rect().size
		var a := (_game_vp.canvas_transform * r.position) / view
		var b := (_game_vp.canvas_transform * r.end) / view
		clip = Vector4(a.x, a.y, b.x, b.y)
	(_comp.material as ShaderMaterial).set_shader_parameter("clip_rect", clip)


func _feed_lights(on: Vector2i) -> void:
	var map := get_parent()
	var pos: Array[Vector4] = []
	var col: Array[Vector4] = []
	var dir: Array[Vector4] = []
	var fx: Array[Vector4] = []
	var view := Rect2(Vector2.ZERO, Vector2(_size))
	for n in get_tree().get_nodes_in_group(PixelLight.GROUP):
		var l := n as PixelLight
		if l == null or not map.is_ancestor_of(l) or not l.is_visible_in_tree():
			continue
		var e := l.current_energy()
		if e <= 0.0:
			continue
		var p := l.global_position / SCALE + Vector2(on)
		var reach := maxf(l.radius, l.pool_radius) + l.height
		if not view.grow(reach).has_point(p):
			continue
		pos.append(Vector4(p.x, p.y, l.height, l.radius))
		col.append(Vector4(l.color.r * e, l.color.g * e, l.color.b * e, float(l.type)))
		if l.type == PixelLight.Type.BEAM:
			dir.append(Vector4(l.mouth_radius, 0.0, 0.0, l.pool_radius))
		else:
			var axis := l.direction.normalized() if l.direction != Vector3.ZERO else Vector3(0, 0, -1)
			dir.append(Vector4(axis.x, axis.y, axis.z, cos(deg_to_rad(l.angle) * 0.5)))
		fx.append(Vector4(1.0 if l.casts_shadows else 0.0, l.halo, l.haze, l.halo_radius))
		if pos.size() >= MAX_LIGHTS:
			break
	var count := pos.size()
	while pos.size() < MAX_LIGHTS:
		pos.append(Vector4.ZERO)
		col.append(Vector4.ZERO)
		dir.append(Vector4.ZERO)
		fx.append(Vector4.ZERO)
	var m := _light_mat
	m.set_shader_parameter("light_count", count)
	m.set_shader_parameter("l_pos", pos)
	m.set_shader_parameter("l_col", col)
	m.set_shader_parameter("l_dir", dir)
	m.set_shader_parameter("l_fx", fx)
	m.set_shader_parameter("world_offset", on)
	m.set_shader_parameter("flip_y", _flip_y)
	m.set_shader_parameter("ambient", Vector3(ambient.r, ambient.g, ambient.b))
	m.set_shader_parameter("levels", float(levels))
	m.set_shader_parameter("peak", peak)
	m.set_shader_parameter("ao_strength", ao_strength)
	m.set_shader_parameter("player_fill", player_fill)
