class_name UiStyle
## Shared look of the side panels: colours from the art ramps (tools/art/pix.py RAMPS) so the frame
## around the game view belongs to the same world. Sizes are multiples of 3 (one art pixel).
## No boxes inside the panels: each panel is one picture with text and a few items laid over it.

const BG := Color("101113")          # plastic 0: panel background
const BOX := Color("1b1c1f")         # plastic 1
const LINE := Color("2a2c31")        # steel 1: the edge against the game view
const LINE_HI := Color("3f434a")     # steel 2
const TEXT := Color("9a9ea3")        # shell 3
const TEXT_HI := Color("c3c6c9")     # shell 4
const TEXT_DIM := Color("4c4f55")    # shell 1
const ACCENT := Color("3aa3a8")      # glow 2: the single accent
const ACCENT_HI := Color("7fdad8")   # glow 3
const DENY := Color("a8665e")        # redp 4: "no" (a locked floor's button blinking), nowhere else

const PAD := 18
const BORDER := 3


## Plain panel background with one edge line on the side that touches the game view.
static func panel_bg(edge_side: Side) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = BG
	s.border_color = LINE
	s.set_border_width(edge_side, BORDER)
	return s


## A box with a border on every side (dialogue box, elevator panel).
static func panel_box_all(bg: Color, line: Color) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = line
	s.set_border_width_all(BORDER)
	return s


## Teal corner brackets just outside a box's border (the frame around the game view wears the same):
## call from the box's draw signal.
static func draw_brackets(ci: CanvasItem, s: Vector2, arm: float = 22.0) -> void:
	var t := float(BORDER)
	for c in [Vector2(-1.5, -1.5), Vector2(s.x + 1.5, -1.5), Vector2(-1.5, s.y + 1.5), Vector2(s.x + 1.5, s.y + 1.5)]:
		var sx := 1.0 if c.x < s.x / 2.0 else -1.0
		var sy := 1.0 if c.y < s.y / 2.0 else -1.0
		ci.draw_rect(Rect2(c, Vector2(arm * sx, t * sy)).abs(), ACCENT)
		ci.draw_rect(Rect2(c, Vector2(t * sx, arm * sy)).abs(), ACCENT)


## One "[key] what it does" pair, the key drawn as a small keycap (dialogue hint, elevator panel footer).
static func key_hint(key: String, what: String, size: int = 18) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 9)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var cap := PanelContainer.new()
	var box := panel_box_all(Color(BG, 0.9), ACCENT)
	box.content_margin_left = 9
	box.content_margin_right = 9
	box.content_margin_top = 1
	box.content_margin_bottom = 1
	cap.add_theme_stylebox_override("panel", box)
	cap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cap.add_child(label(key, size, ACCENT_HI))
	h.add_child(cap)
	h.add_child(label(what, size, TEXT_HI))
	return h


## A menu box (floor panel, pause menu): opaque box with the teal corner marks, a header, a list and a footer of
## key hints ([key, what] pairs). Returns {panel, rows, title (the header's Label), hints (the footer's items)}.
## Add `panel` to the menu; size it with menu_size().
static func menu_box(title: String, hints: Array) -> Dictionary:
	var panel := Panel.new()
	panel.add_theme_stylebox_override("panel", panel_box_all(BG, LINE_HI))
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.draw.connect(func() -> void: draw_brackets(panel, panel.size))
	var v := VBoxContainer.new()
	v.position = Vector2(24, 18)
	v.add_theme_constant_override("separation", 10)
	panel.add_child(v)
	var head := header(title)
	v.add_child(head)
	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 0)
	v.add_child(rows)
	var footer := HBoxContainer.new()                    # what the keys do, small, under the list
	footer.add_theme_constant_override("separation", 24)
	var items: Array[Control] = []
	for h in hints:
		var k := key_hint(h[0], h[1], 16)
		footer.add_child(k)
		items.append(k)
	v.add_child(footer)
	return {"panel": panel, "rows": rows, "title": head.get_child(0), "hints": items}


## The size of a menu_box with `count` rows of `row_h`: header, list, footer and even padding above and below.
static func menu_size(width: float, count: int, row_h: float) -> Vector2:
	return Vector2(width, 18.0 + 34.0 + count * row_h + 10.0 + 30.0 + 28.0)


## One list row: [strip, row, bg]. The picked row sits on a faint teal strip (bg can be recoloured, e.g. a red
## blink); fill `row` with the cursor cell and labels.
static func list_row(on: bool, width: float, row_h: float) -> Array:
	var strip := PanelContainer.new()
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(ACCENT, 0.14) if on else Color(0, 0, 0, 0)
	strip.add_theme_stylebox_override("panel", bg)
	var row := HBoxContainer.new()
	row.custom_minimum_size = Vector2(width - 48, row_h)
	row.add_theme_constant_override("separation", 14)
	strip.add_child(row)
	return [strip, row, bg]


## The ▶ cursor cell of a list row, always the same width so the row's text never shifts when it is picked.
static func cursor(on: bool, color: Color = ACCENT_HI, size: int = 22) -> Label:
	var l := label("▶" if on else "", size, color)
	l.custom_minimum_size.x = 24
	return l


static func label(text: String, size: int = 18, color: Color = TEXT) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	# text sits on pictures, so give it a dark edge instead of a box
	l.add_theme_color_override("font_shadow_color", Color(BG, 0.9))
	l.add_theme_constant_override("shadow_offset_x", 0)
	l.add_theme_constant_override("shadow_offset_y", 0)
	l.add_theme_constant_override("shadow_outline_size", 6)
	return l


## A section header, the same everywhere: small teal capitals over a short steel underline.
static func header(text: String) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 3)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(label(text, 16, ACCENT))
	var line := ColorRect.new()
	line.color = LINE_HI
	line.custom_minimum_size = Vector2(96, BORDER)
	line.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(line)
	return v


## A shadow along a panel's inner edge (the side touching the game view), so the panel sits a step behind
## the game. Add it last, anchored to that edge.
static func edge_shade(edge_side: Side, width: float = 36.0) -> TextureRect:
	var g := Gradient.new()
	g.set_color(0, Color(0, 0, 0, 0.55))
	g.set_color(1, Color(0, 0, 0, 0.0))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.width = 64
	t.height = 4
	t.fill_from = Vector2(1, 0) if edge_side == SIDE_RIGHT else Vector2(0, 0)
	t.fill_to = Vector2(0, 0) if edge_side == SIDE_RIGHT else Vector2(1, 0)
	var r := TextureRect.new()
	r.texture = t
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_SCALE
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.set_anchors_and_offsets_preset(Control.PRESET_RIGHT_WIDE if edge_side == SIDE_RIGHT else Control.PRESET_LEFT_WIDE)
	if edge_side == SIDE_RIGHT:
		r.offset_left = -width
	else:
		r.offset_right = width
	return r


## A fade that stays almost opaque over the first `hold` (0..1) of its height, then fades out: text sits on the
## solid part, the picture shows again below it. `up` = solid at the top.
static func fade_hold(c: Color, hold: float, up: bool = true) -> TextureRect:
	var r := fade(c, up)
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, hold if up else 1.0 - hold, 1.0])
	var solid := [Color(c, 0.94), Color(c, 0.82), Color(c, 0.0)]
	if not up:
		solid.reverse()
	g.colors = PackedColorArray(solid)
	(r.texture as GradientTexture2D).gradient = g
	return r


## Vertical fade from transparent to `c` (top to bottom unless `up`), to seat overlays on a picture.
static func fade(c: Color, up: bool = false) -> TextureRect:
	var g := Gradient.new()
	g.set_color(0, Color(c, 0.0) if not up else c)
	g.set_color(1, c if not up else Color(c, 0.0))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill_from = Vector2(0, 0)
	t.fill_to = Vector2(0, 1)
	t.width = 4
	t.height = 64
	var r := TextureRect.new()
	r.texture = t
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_SCALE
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r
