class_name CharacterFrames
extends RefCounted
## Builds SpriteFrames from a PixelLab character export folder:
##   <dir>/rotations/<direction>.png        -> "idle_<direction>"
##   <dir>/walk/<direction>/frame_NNN.png  -> "walk_<direction>"

const DIRECTIONS: Array[String] = ["south", "east", "north", "west"]
const WALK_FPS := 10.0


static func build(dir: String) -> SpriteFrames:
	var frames := SpriteFrames.new()
	frames.remove_animation("default")
	for d in DIRECTIONS:
		var idle: String = "idle_" + d
		frames.add_animation(idle)
		frames.set_animation_loop(idle, true)
		frames.add_frame(idle, load("%s/rotations/%s.png" % [dir, d]))

		var walk: String = "walk_" + d
		frames.add_animation(walk)
		frames.set_animation_loop(walk, true)
		frames.set_animation_speed(walk, WALK_FPS)
		var i := 0
		while ResourceLoader.exists("%s/walk/%s/frame_%03d.png" % [dir, d, i]):
			frames.add_frame(walk, load("%s/walk/%s/frame_%03d.png" % [dir, d, i]))
			i += 1
	return frames
