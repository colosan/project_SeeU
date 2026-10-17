class_name TvScreen
extends Control
## The floor's broadcast TV in the right panel. Until the YouTube embed exists (on hold, docs/DESIGN.md UI) it
## shows a dead channel: dim colour bars, scanlines, a little static that crawls a few times a second, and
## NO SIGNAL. Drawn in 3 px blocks so it sits with the pixel art.

const PX := 3.0                           # one art pixel
const FPS := 8.0                          # static updates per second (redraws only then)
const BARS := [Color("7c838b"), Color("c4a24a"), Color("3aa3a8"), Color("4a8a50"), Color("8e5080"), Color("a8665e"),
	Color("32465e")]

var _frame := -1
## The on-screen channel label, top left like a real TV's OSD: the floor's channel (docs/WORLD.md 7: each floor
## has its own broadcast). Set by the info panel when the floor changes.
var channel := "":
	set(v):
		if channel != "" and v != channel:
			_burst_until = Time.get_ticks_msec() + BURST_MS   # changing channel: a burst of snow first
		channel = v
		queue_redraw()

const BURST_MS := 450
var _burst_until := 0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true


func _process(_delta: float) -> void:
	var f := int(Time.get_ticks_msec() / 1000.0 * FPS)
	if f != _frame:
		_frame = f
		queue_redraw()


func _draw() -> void:
	var w := size.x
	var h := size.y
	draw_rect(Rect2(Vector2.ZERO, size), Color("08090a"))
	# colour bars, dim, on the upper two thirds
	var bh := floorf(h * 0.62 / PX) * PX
	var bw := w / BARS.size()
	for i in BARS.size():
		draw_rect(Rect2(i * bw, 0, bw + 1, bh), Color(BARS[i], 0.28))
	# a darker strip under them, like a test card's lower band
	draw_rect(Rect2(0, bh, w, PX * 4), Color(0.0, 0.0, 0.0, 0.5))
	# static: a few hundred dim blocks, a new pattern each update
	var rng := RandomNumberGenerator.new()
	rng.seed = _frame
	for i in 220:
		var x := floorf(rng.randf() * w / PX) * PX
		var y := floorf(rng.randf() * h / PX) * PX
		draw_rect(Rect2(x, y, PX * rng.randi_range(1, 3), PX), Color(1, 1, 1, rng.randf_range(0.04, 0.14)))
	# switching channel: thick snow over everything for a moment
	if Time.get_ticks_msec() < _burst_until:
		for i in 900:
			var x := floorf(rng.randf() * w / PX) * PX
			var y := floorf(rng.randf() * h / PX) * PX
			draw_rect(Rect2(x, y, PX * rng.randi_range(1, 2), PX), Color(1, 1, 1, rng.randf_range(0.15, 0.5)))
	# a brighter roll line drifting down
	var roll := fmod(_frame * PX * 2.0, h)
	draw_rect(Rect2(0, roll, w, PX), Color(1, 1, 1, 0.06))
	# scanlines
	for y in range(0, int(h), int(PX * 2)):
		draw_rect(Rect2(0, y, w, 1), Color(0, 0, 0, 0.35))
	# NO SIGNAL
	var font := get_theme_default_font()
	var fs := 28
	var text := "NO SIGNAL"
	var tw := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var pos := Vector2(roundf((w - tw) / 2.0), roundf(h * 0.5 + fs * 0.35))
	draw_string_outline(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 6, Color(0, 0, 0, 0.85))
	draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, UiStyle.TEXT_HI)
	if channel != "":
		var cpos := Vector2(PX * 4, PX * 4 + 16)
		draw_string_outline(font, cpos, channel, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, 6, Color(0, 0, 0, 0.85))
		draw_string(font, cpos, channel, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, UiStyle.ACCENT_HI)
