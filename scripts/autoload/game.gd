extends Node
## Global game flow (autoload "Game"): moving between maps, talking, the elevator.
##
## change_map() fades the game view to black, swaps the map under the MapHost,
## puts the new map's Player on the Marker2D named `spawn` (facing the marker's
## "facing" metadata), snaps the camera to the new map and fades back in.
## say() / choose() show the dialogue box over the game view; open_elevator() the elevator's floor panel.
## While any of these is open (or a map is changing) SeeU doesn't move: can_move().

signal map_changed(map: Node)

## Every map, in one place (adding a map = one line here): keyed by its scene's root node name.
##   scene - the map scene (MapHost loads them all in the background at start, so doors never hitch)
##   floor - the floor (class) it is on: the right panel's backdrop and the left panel's floor label
##   name  - its name in the left panel
##   at    - its spot on the left panel's tower illustration (px; tools/art/gen_stack_map.py PLACES).
##           Neighbouring rooms are a few dozen px apart: the tower is enormous next to a room.
const PLACES := {
	"BasementTest": {"scene": "res://scenes/world/basement_test.tscn", "floor": "L0", "name": "깨어난 방",
		"at": Vector2(367, 2102)},
	"ElevatorHall": {"scene": "res://scenes/world/elevator_hall.tscn", "floor": "L0", "name": "화물 엘리베이터 홀",
		"at": Vector2(407, 2102)},
}
## Floor (class) id -> its name in the left panel.
const FLOOR_NAMES := {"L0": "휴지통"}
## Every floor of the tower, bottom to top, labelled like the tower's signs (docs/DESIGN.md UI): the class
## sign and the view count. The elevator panel lists them top to bottom.
## "tier" = the facade material of that class on the tower picture (tools/art/gen_stack_map.py TIER_GLASS: landfill,
## rusted iron, bronze, silver, gold, platinum), shown as a chip on the elevator panel.
const FLOORS := [
	{"id": "L0", "sign": "EOL", "views": "-", "tier": Color8(52, 46, 58)},
	{"id": "L1", "sign": "DEMO", "views": "100", "tier": Color8(58, 46, 40)},
	{"id": "L2", "sign": "COVER", "views": "10K", "tier": Color8(104, 66, 36)},
	{"id": "L3", "sign": "FAN", "views": "1M", "tier": Color8(118, 126, 140)},
	{"id": "L4", "sign": "LIVE", "views": "100M", "tier": Color8(150, 116, 44)},
	{"id": "L5", "sign": "PLATINUM", "views": "1B", "tier": Color8(206, 212, 226)},
]
## Where the elevator lets her out on each floor: floor id -> [map scene, spawn marker]. Empty until the
## upper floors exist; a floor with access but no entry here can't be reached yet.
var elevator_stops := {}

## Floors SeeU may ride to (the elevator only goes where she has permission, docs/WORLD.md).
var access := {"L0": true}


## The PLACES entry of a map node ({} if it isn't listed).
static func place_of(map: Node) -> Dictionary:
	return PLACES.get(String(map.name), {}) if map != null else {}

const FADE_OUT := 0.3
const FADE_IN := 0.35
const WAKE := 1.4                               # the game opens on black and the room fades in: she wakes up
## What the narration says once she has woken up (docs/WORLD.md 6: the prologue - draft lines, change freely).
const PROLOGUE := ["……", "어딘가 높은 곳에서 떨어진 것 같다.", "소리를 내 보려 했지만, 목소리가 나오지 않는다."]

var _host: Node            # MapHost inside the game viewport
var _fade: ColorRect       # black overlay inside the same viewport
var _busy := false
var _dialogue: DialogueBox
var _elevator: ElevatorPanel
var _pause: PauseMenu
var _sfx: Array[AudioStreamPlayer] = []    # a few voices so quick sounds don't cut each other off
var _sfx_next := 0
var _sfx_cache := {}

const SFX_VOICES := 4
const SFX_DB := -10.0                        # UI sounds sit well under any future music


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS   # keep fading while the world is paused
	_ensure_input_actions()
	_load_settings()
	get_tree().root.size_changed.connect(_fit_window)
	_fit_window()


# ---------- screen scale: whole numbers only, the extra room goes to the game view ----------

const BASE := Vector2i(1920, 1080)


## The UI and the art are scaled by a whole number (1x at 1080p and 1440p, 2x at 4K), never 1.33x: the pixels stay
## even. Whatever the window has beyond BASE x that number becomes canvas, and since the side panels have fixed
## widths it all goes to the game view in the middle (more of the room around SeeU, same 3x art). A window smaller
## than BASE (under 1x) still shrinks smoothly to fit.
func _fit_window() -> void:
	var root := get_tree().root
	var win := root.size
	var k := mini(win.x / BASE.x, win.y / BASE.y)
	if k >= 1:
		root.content_scale_stretch = Window.CONTENT_SCALE_STRETCH_INTEGER
		root.content_scale_size = Vector2i(win.x / k, win.y / k)
	else:
		root.content_scale_stretch = Window.CONTENT_SCALE_STRETCH_FRACTIONAL
		root.content_scale_size = BASE


# ---------- settings (pause menu): kept in user://settings.cfg ----------

const SETTINGS := "user://settings.cfg"
var volume := 80                             # sound volume, 0..100 (master bus)
## Dialogue typing speed: name and characters per second (0 = the whole page at once).
const TEXT_SPEEDS := [["느림", 25.0], ["보통", 45.0], ["빠름", 90.0], ["즉시", 0.0]]
var text_speed := 1
var reduce_flicker := false:                 # accessibility: flickering lights hold steady (PixelLight.steady)
	set(v):
		reduce_flicker = v
		PixelLight.steady = v


func set_volume(v: int) -> void:
	volume = clampi(v, 0, 100)
	AudioServer.set_bus_volume_db(0, linear_to_db(volume / 100.0))
	AudioServer.set_bus_mute(0, volume == 0)


## F11 or Alt+Enter: fullscreen on/off. A 1920x1080 window doesn't fit a 1080p screen with its title bar, and
## windowed mode drops the odd frame to the desktop compositor; fullscreen paces frames evenly.
func toggle_fullscreen() -> void:
	var full := DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED if full else DisplayServer.WINDOW_MODE_FULLSCREEN)
	if _pause != null and _pause.is_open():
		_pause._refresh()                            # F11 while the menu is open: its row shows the new state


## Recordings and probes (--write-movie, --script) neither read nor write the player's settings.
static func _tooling() -> bool:
	return OS.has_feature("movie") or "--script" in OS.get_cmdline_args()


func save_settings() -> void:
	if _tooling():
		return
	var c := ConfigFile.new()
	c.set_value("sound", "volume", volume)
	c.set_value("text", "speed", text_speed)
	c.set_value("display", "reduce_flicker", reduce_flicker)
	c.set_value("display", "fullscreen", DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN)
	c.save(SETTINGS)


func _load_settings() -> void:
	var c := ConfigFile.new()
	if _tooling() or c.load(SETTINGS) != OK:
		set_volume(volume)
		return
	set_volume(int(c.get_value("sound", "volume", volume)))
	text_speed = clampi(int(c.get_value("text", "speed", text_speed)), 0, TEXT_SPEEDS.size() - 1)
	reduce_flicker = bool(c.get_value("display", "reduce_flicker", false))
	if bool(c.get_value("display", "fullscreen", false)) and DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)


## interact: Z / Space / Enter. cancel: X / Esc / Backspace. Registered at runtime like the move keys.
static func _ensure_input_actions() -> void:
	var bindings := {"interact": [KEY_Z, KEY_SPACE, KEY_ENTER, KEY_KP_ENTER], "cancel": [KEY_X, KEY_ESCAPE, KEY_BACKSPACE]}
	for action in bindings:
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action)
		for key in bindings[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = key
			InputMap.action_add_event(action, ev)


## The map on screen now (null before the host is up).
func current_map() -> Node:
	return _host.current if _host != null else null


## A floor's FLOORS entry by id ({} if there is none).
static func floor_info(id: String) -> Dictionary:
	for f in FLOORS:
		if f["id"] == id:
			return f
	return {}


## SeeU may walk and interact (no dialogue, no panel, no map change in progress).
func can_move() -> bool:
	return not _busy and not is_ui_open()


func is_ui_open() -> bool:
	for ui in [_dialogue, _elevator, _pause]:
		if ui != null and ui.is_open():
			return true
	return false


## Shows `pages` in the dialogue box, one at a time; returns when the last is dismissed.
func say(pages: Array, speaker := "") -> void:
	if _dialogue != null:
		await _dialogue.say(pages, speaker)


## Asks a question with options; returns the picked index (-1 = cancelled).
func choose(question: String, options: Array, speaker := "") -> int:
	if _dialogue == null:
		return -1
	return await _dialogue.choose(question, options, speaker)


## The small hint in the game view's corner (what interact would do now; "" = nothing).
func set_hint(text: String) -> void:
	if _dialogue != null:
		_dialogue.set_hint(text)


## A UI sound (assets/audio/ui_<name>.wav, synthesized by tools/audio/gen_sfx.py): move, ok, cancel, deny, page;
## or any other sound in assets/audio by its file name ("env_lift", "env_bell").
func sfx(sound: String) -> void:
	if _sfx.is_empty():
		for i in SFX_VOICES:
			var p := AudioStreamPlayer.new()
			p.volume_db = SFX_DB
			p.process_mode = Node.PROCESS_MODE_ALWAYS
			add_child(p)
			_sfx.append(p)
	if not _sfx_cache.has(sound):
		var path := "res://assets/audio/ui_%s.wav" % sound
		if not ResourceLoader.exists(path):
			path = "res://assets/audio/%s.wav" % sound   # any other sound by file name, e.g. "env_bell"
		_sfx_cache[sound] = load(path) if ResourceLoader.exists(path) else null
	if _sfx_cache[sound] == null:
		return
	var p := _sfx[_sfx_next]
	_sfx_next = (_sfx_next + 1) % SFX_VOICES
	p.stream = _sfx_cache[sound]
	p.play()


## The ride: the gate folds open, she walks into the dark car (past the threshold the car hides her), the gate
## closes behind her, and the car leaves (the usual fade to the stop's map and marker).
func _ride(stop: Array) -> void:
	var lift := get_tree().get_first_node_in_group("elevator")
	var player := _find_player(_host.current)
	if lift != null and player != null and lift.has_method("play_to"):
		_busy = true
		set_hint("")
		await lift.play_to(lift.frames - 1)
		var door: Vector2 = lift.global_position                 # the gate's threshold, centred
		await player.walk_to(Vector2(door.x, player.global_position.y))
		_in_car(player, lift, true)
		await player.walk_to(door + Vector2(0, -RIDE_STEP_IN))
		player.face("south")                                     # turns round in the car, like anyone riding one
		await get_tree().create_timer(0.3).timeout
		await lift.play_to(0)
		sfx("env_lift")                                           # the motor winds up; the fade covers the trip
		await get_tree().create_timer(0.5).timeout
		_busy = false
	if await change_map(stop[0], stop[1], true):
		await _arrive()
	elif lift != null and player != null:                         # the stop is broken: let her back out of the car
		_in_car(player, lift, false)
		await lift.play_to(lift.frames - 1)
		await player.walk_to(lift.global_position + Vector2(0, 24))
		player.scripted = false
		await lift.play_to(0)


## Arriving by elevator: the map has just faded in with her standing in its car (change_map put her there); the
## gate folds open, she walks out to the stop's marker, the gate shuts behind her.
func _arrive() -> void:
	var lift := get_tree().get_first_node_in_group("elevator")
	var player := _find_player(_host.current)
	if lift == null or player == null or not player.scripted:
		return
	_busy = true
	sfx("env_bell")                                               # ding: this floor
	await get_tree().create_timer(0.45).timeout
	await lift.play_to(lift.frames - 1)
	var door: Vector2 = lift.global_position
	await player.walk_to(Vector2(door.x, door.y + 6.0))              # out over the threshold
	_in_car(player, lift, false)
	await player.walk_to(_arrival_spot)
	player.face(_arrival_facing)
	player.scripted = false
	await lift.play_to(0)
	_busy = false


## Standing in the car or not: draw order car < SeeU < gate, and her art a step darker in the car's shadow
## (a figure behind the bars; the lighting twin is untouched).
func _in_car(player: Node, lift: Node, on: bool) -> void:
	player.z_index = 1 if on else 0
	player.sprite.self_modulate = IN_CAR if on else Color.WHITE
	lift.set_overlay_front(on)


var _arrival_spot := Vector2.ZERO
var _arrival_facing := "south"


const IN_CAR := Color(0.62, 0.62, 0.7)        # her art while standing in the car (the lighting twin is untouched)
const RIDE_STEP_IN := 45.0                     # screen px past the threshold: standing in the car, head under its roof


func _exit_tree() -> void:
	for p in _sfx:
		SoundUtil.silence(p)
	_sfx_cache.clear()


## The freight elevator: pick a floor; locked floors and the floor she is on just answer.
func open_elevator() -> void:
	var here: String = place_of(_host.current if _host != null else null).get("floor", "")
	var floors := FLOORS.duplicate()
	floors.reverse()                               # top floor first, like an elevator panel
	var picked: String = await _elevator.pick(floors, here, access)
	if picked == "":
		return
	if picked == here:
		await say(["이미 이 층이다."])
	elif not access.has(picked):
		var f := floor_info(picked)
		await say(["버튼이 붉게 깜빡인다.", "%s %s 층으로 갈 권한이 없다." % [picked, f.get("sign", "")]])
	elif not elevator_stops.has(picked):
		await say(["버튼에 불이 들어오지 않는다. 아직 갈 수 없는 층이다."])
	else:
		await _ride(elevator_stops[picked])


## Esc while walking: the pause menu (inside the UI, Esc is just cancel).
func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	if key.keycode == KEY_F11 or (key.keycode == KEY_ENTER and key.alt_pressed):
		toggle_fullscreen()
		save_settings()
		get_viewport().set_input_as_handled()
	elif key.physical_keycode == KEY_ESCAPE and can_move() and _pause != null:
		get_viewport().set_input_as_handled()        # Esc while walking: the pause menu (in UI, Esc = cancel)
		set_hint("")
		_pause.open()


## Called by MapHost: the fade overlay lives in the host's viewport so only the game view goes black.
func register_host(host: Node) -> void:
	_host = host
	var layer := CanvasLayer.new()
	layer.name = "Fade"
	layer.layer = 100
	_fade = ColorRect.new()
	_fade.color = Color(0, 0, 0, 1)                # starts black: _wake() fades the first room in
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(_fade)
	host.add_child(layer)
	# dialogue and panels: over the game view (and its lighting), under the fade
	var ui := CanvasLayer.new()
	ui.name = "GameUI"
	ui.layer = 90
	_dialogue = DialogueBox.new()
	_elevator = ElevatorPanel.new()
	_pause = PauseMenu.new()
	ui.add_child(_dialogue)
	ui.add_child(_elevator)
	ui.add_child(_pause)
	host.add_child(ui)
	_wake.call_deferred()


## The first room fades in slowly (the first map is "the room she woke up in"); she can't move until it has.
func _wake() -> void:
	_busy = true
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 0.0, WAKE).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	await tw.finished
	_busy = false
	if not PROLOGUE.is_empty():
		await say(PROLOGUE)
	_show_controls()


## Once, right after the prologue: the few keys that matter, small in the game view's top-left corner, gone after
## a few seconds (the full list is in the pause menu's controls page).
const CONTROLS_S := 7.0


func _show_controls() -> void:
	if _host == null:
		return
	var l := UiStyle.label("방향키 이동 · Z 조사 · Esc 메뉴", 18, UiStyle.TEXT_HI)
	l.position = Vector2(48, 42)
	l.modulate.a = 0.0
	_dialogue.get_parent().add_child(l)
	_dialogue.get_parent().move_child(l, 0)             # under the dialogue box and the menus' dimming
	var tw := l.create_tween()
	tw.tween_property(l, "modulate:a", 1.0, 0.4)
	tw.tween_interval(CONTROLS_S)
	tw.tween_property(l, "modulate:a", 0.0, 1.0)
	tw.tween_callback(l.queue_free)


func is_changing_map() -> bool:
	return _busy


## by_lift: she arrives in the new map's elevator car (if it has one); _arrive() then walks her out to the marker.
## Returns false (and nothing changes) when it can't go: busy, or no such scene.
func change_map(scene_path: String, spawn: StringName, by_lift := false) -> bool:
	if _busy or _host == null:
		return false
	if not ResourceLoader.exists(scene_path):      # a typo in an exit or elevator_stops: stay put, don't freeze on black
		push_error("Game.change_map: no scene at '%s'" % scene_path)
		return false
	_busy = true
	get_tree().paused = true                    # freeze the player and props during the fade
	await _fade_to(1.0, FADE_OUT)

	var map: Node = _host.load_map(scene_path)
	var player := _find_player(map)
	var marker := map.find_child(String(spawn), true, false) as Node2D
	if player != null and marker != null:
		player.global_position = marker.global_position
		if marker.has_meta("facing"):
			player.face(String(marker.get_meta("facing")))
	elif marker == null:
		push_warning("Game.change_map: no spawn '%s' in %s" % [spawn, scene_path])
	var lift: Node = get_tree().get_first_node_in_group("elevator") if by_lift else null
	if player != null and marker != null and lift != null and map.is_ancestor_of(lift):
		_arrival_spot = marker.global_position
		_arrival_facing = String(marker.get_meta("facing", "south"))
		player.scripted = true                     # standing in the car behind the shut gate: car < SeeU < gate
		player.global_position = lift.global_position + Vector2(0, -RIDE_STEP_IN)
		player.face("south")
		_in_car(player, lift, true)
	if player != null:
		player.reset_physics_interpolation()       # arrived by door: jump, don't glide from the old spot
		player.refresh_camera()
	map_changed.emit(map)

	get_tree().paused = false
	await _fade_to(0.0, FADE_IN)
	_busy = false
	return true


func _fade_to(alpha: float, time: float) -> void:
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", alpha, time)
	await tw.finished


static func _find_player(map: Node) -> Node:
	for n in map.get_tree().get_nodes_in_group("player"):
		if map.is_ancestor_of(n):
			return n
	return null
