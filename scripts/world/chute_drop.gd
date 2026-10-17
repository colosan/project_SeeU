extends Node2D
## Now and then the deletion chute drops something onto the heap (docs/WORLD.md: the recycle bin): a small
## folder, file or archive tumbles down the chute's light shaft, thumps onto the heap and sinks into it.
## The node sits just in front of the heap's base (so it draws over the heap); the item falls from `mouth_y`
## (the chute's mouth, px above this node) to a spot on the heap's slope. Seeded, so recordings repeat.

@export var texture: Texture2D            # one item per frame (assets/env/basement/digital/dg_drop.png)
@export var frames := 3
@export var mouth_y := -249.0             # the chute's mouth (game y 102), screen px above this node
@export var land_y := Vector2(-171.0, -123.0)   # landing height range on the heap's face, screen px above this node
@export var land_x := Vector2(-24.0, 24.0)
@export var interval := Vector2(6.0, 11.0)      # seconds between drops
@export var seed := 7

const SCALE := 3
const FALL_S := 0.5
var _rng := RandomNumberGenerator.new()
var _thud: AudioStreamPlayer2D
var _timer: Timer


# No awaits here: a coroutine waiting on a timer or tween when the map is freed (walking out mid-drop) is never
# resumed and leaks. A Timer child and tween callbacks go away with the node.
func _ready() -> void:
	_rng.seed = seed
	_thud = SoundUtil.positional("res://assets/audio/env_thud.wav", -14.0)
	if _thud != null:
		add_child(_thud)
	_timer = Timer.new()
	_timer.one_shot = true
	_timer.timeout.connect(_drop)
	add_child(_timer)
	if texture != null:
		_timer.start(_rng.randf_range(2.5, 4.0))         # the first one soon after waking


func _drop() -> void:
	var s := Sprite2D.new()
	s.texture = texture
	s.hframes = frames
	s.frame = _rng.randi_range(0, frames - 1)
	s.scale = Vector2(SCALE, SCALE)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var x := roundf(_rng.randf_range(land_x.x, land_x.y) / SCALE) * SCALE
	var ground := roundf(_rng.randf_range(land_y.x, land_y.y) / SCALE) * SCALE
	var landed_turn := 90.0 * _rng.randi_range(0, 3)        # lands any way up
	s.position = Vector2(x, mouth_y)
	add_child(s)
	# fall, tumbling in quarter turns (stays on the pixel grid), then thump, a small bounce, sink into the heap
	var spin := create_tween().set_loops(4)
	spin.tween_interval(0.12)
	spin.tween_callback(func() -> void: s.rotation_degrees = fmod(s.rotation_degrees + 90.0, 360.0))
	var tw := create_tween()
	tw.tween_property(s, "position:y", ground, FALL_S).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_callback(func() -> void:
		spin.kill()
		s.rotation_degrees = landed_turn
		if _thud != null:
			_thud.position = s.position
			_thud.play())
	tw.tween_property(s, "position:y", ground - SCALE * 2, 0.08).set_ease(Tween.EASE_OUT)
	tw.tween_property(s, "position:y", ground, 0.1).set_ease(Tween.EASE_IN)
	tw.tween_interval(0.8)
	tw.tween_property(s, "position:y", ground + SCALE * 3, 0.7)
	tw.parallel().tween_property(s, "modulate:a", 0.0, 0.7)
	tw.tween_callback(s.queue_free)
	_timer.start(FALL_S + 1.7 + _rng.randf_range(interval.x, interval.y))


func _exit_tree() -> void:
	SoundUtil.silence(_thud)
