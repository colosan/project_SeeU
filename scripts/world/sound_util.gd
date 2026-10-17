class_name SoundUtil
## Small shared pieces for the game's sounds (all synthesized by tools/audio/gen_sfx.py).

const HEAR_PX := 1100.0                 # positional sounds fade out about one game view away
const FALLOFF := 1.6


## A positional player for a room sound at `path` (null if the file is missing). Add it under the thing that
## makes the sound.
static func positional(path: String, db: float) -> AudioStreamPlayer2D:
	if not ResourceLoader.exists(path):
		return null
	var p := AudioStreamPlayer2D.new()
	p.stream = load(path)
	p.volume_db = db
	p.max_distance = HEAR_PX
	p.attenuation = FALLOFF
	return p


## Stops a sound player and lets go of its stream: a sound still playing at quit is reported as leaked.
static func silence(p: Node) -> void:
	if p != null and is_instance_valid(p):
		p.stop()
		p.stream = null
