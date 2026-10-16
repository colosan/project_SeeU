extends PointLight2D
## Light whose energy follows a frame pattern, in step with an animated prop
## (same fps, same number of frames) such as a flickering bulb.

@export var pattern: PackedFloat32Array = PackedFloat32Array([1.0])
@export var fps := 8.0

var _base := 1.0
var _t := 0.0


func _ready() -> void:
	_base = energy


func _process(delta: float) -> void:
	_t += delta
	energy = _base * pattern[int(_t * fps) % pattern.size()]
