extends TileMapLayer
## Paints a corner-based (Wang) tileset from a vertex grid of terrain names.
## Temporary test map until real maps are authored in the editor.

@export_file("*.png") var sheet_path := "res://assets/tilesets/test_dirt_grass/tiles.png"
@export_file("*.json") var corners_path := "res://assets/tilesets/test_dirt_grass/corners.json"
@export var map_size := Vector2i(24, 14)

var _atlas_by_corners := {}


func _ready() -> void:
	add_to_group("map_bounds")
	var meta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(corners_path))
	var size := int(meta.tile_size)

	var source := TileSetAtlasSource.new()
	source.texture = load(sheet_path)
	source.texture_region_size = Vector2i(size, size)
	var ts := TileSet.new()
	ts.tile_size = Vector2i(size, size)
	var source_id := ts.add_source(source)
	for t in meta.tiles:
		var coords := Vector2i(int(t.x), int(t.y))
		source.create_tile(coords)
		_atlas_by_corners[_key(t.nw, t.ne, t.sw, t.se)] = coords
	tile_set = ts

	var v := _test_layout(meta.lower, meta.upper)
	for y in map_size.y:
		for x in map_size.x:
			var key := _key(v[y][x], v[y][x + 1], v[y + 1][x], v[y + 1][x + 1])
			set_cell(Vector2i(x, y), source_id, _atlas_by_corners[key])


## World-space rect covered by the painted tiles (used for camera limits).
func get_world_rect() -> Rect2:
	var size := Vector2(map_size * tile_set.tile_size) * global_scale
	return Rect2(global_position, size)


## Grass everywhere with a cross-shaped dirt road.
func _test_layout(lower: String, upper: String) -> Array:
	var v := []
	for y in map_size.y + 1:
		var row := []
		for x in map_size.x + 1:
			var road := y in [6, 7, 8] or x in [11, 12, 13]
			row.append(lower if road else upper)
		v.append(row)
	return v


static func _key(nw: String, ne: String, sw: String, se: String) -> String:
	return "%s|%s|%s|%s" % [nw, ne, sw, se]
