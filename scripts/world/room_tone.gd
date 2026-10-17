extends AudioStreamPlayer
## A map's quiet background sound (assets/audio/tone_<tone>.wav, a seamless loop from tools/audio/gen_sfx.py):
## the chute's air in the basement, the hum of old fittings in the elevator hall. Fades in when the map loads so
## walking through a door never starts it with a pop. The layout scripts add one per map (ROOM_TONE).

@export var tone := ""
@export var level_db := -26.0

const FADE_IN := 1.2


func _ready() -> void:
	var path := "res://assets/audio/tone_%s.wav" % tone
	if tone == "" or not ResourceLoader.exists(path):
		return
	var wav := load(path) as AudioStreamWAV
	if wav == null:
		return
	wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
	wav.loop_begin = 0
	wav.loop_end = int(round(wav.get_length() * wav.mix_rate))   # in samples, whatever the import compressed to
	stream = wav
	volume_db = -60.0
	play()
	create_tween().tween_property(self, "volume_db", level_db, FADE_IN).set_trans(Tween.TRANS_SINE)


func _exit_tree() -> void:
	SoundUtil.silence(self)
