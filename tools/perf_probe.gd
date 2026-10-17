extends SceneTree
## Performance probe (not part of the game): real frame times, per-viewport CPU/GPU render time, draw calls and
## objects, first in the basement, then in the elevator hall; frames over 12 ms are listed as spikes.
##   $GODOT --path . --script res://tools/perf_probe.gd
## Reference (2026-10-17 morning, personal PC, 144 Hz, RTX 4070): both maps avg 6.94 ms / max ~7.4 ms, GPU total ~1 ms,
## draw calls 158 (basement) / 114 (hall), nodes 324 / 247, VRAM ~66 MB.
## The map change in between (frames 311-400) is measured on its own: its worst frame is printed (reference ~21 ms,
## one frame while the screen is fully black: instancing the map + new lighting viewports; contact shadows are cached).
## Spikes listed right after the change are often a measuring artifact: viewport_set_measure_render_time (GPU timer
## queries) sometimes halves the frame rate (~15.6 ms frames) until it is set again. Without measuring, a map change
## costs exactly one slow frame (checked 2026-10-17, 4 runs x 2 changes).
## Godot's TIME_PROCESS monitor is printed too but does not match real frame times here - trust "real frame".
var _f := 0
var _vps: Array = []
var _acc := {}
var _n := 0

func _initialize() -> void:
	root.add_child(load("res://scenes/main/main.tscn").instantiate())

func _collect_vps() -> void:
	_vps = [root]
	for v in root.find_children("*", "SubViewport", true, false):
		_vps.append(v)
	for v in _vps:
		RenderingServer.viewport_set_measure_render_time(v.get_viewport_rid(), true)

var _dsum := 0.0
var _dmax := 0.0
var _dn := 0
var _tmax := 0.0
func _process(_d: float) -> bool:
	_f += 1
	if _f > 310 and _f <= 400:                   # the map change (fade + instancing the hall)
		_tmax = max(_tmax, _d)
		if _d > 0.012:
			print("  transition spike f=", _f, " ms=", snappedf(_d * 1000.0, 0.1))
	if _f == 400:
		print("=== map change: worst frame %.2f ms" % (_tmax * 1000.0))
	if (_f > 60 and _f <= 300) or (_f > 420 and _f <= 660):
		_dsum += _d
		_dmax = max(_dmax, _d)
		if _d > 0.012:
			print("  spike f=", _f, " ms=", snappedf(_d * 1000.0, 0.1))
		_dn += 1
	if _f == 30 or _f == 400:
		_collect_vps()
		_acc = {}
		_n = 0
	if (_f > 60 and _f <= 300) or (_f > 420 and _f <= 660):
		_n += 1
		for v in _vps:
			var rid: RID = v.get_viewport_rid()
			var key := String(v.name)
			var a: Array = _acc.get(key, [0.0, 0.0])
			a[0] += RenderingServer.viewport_get_measured_render_time_cpu(rid)
			a[1] += RenderingServer.viewport_get_measured_render_time_gpu(rid)
			_acc[key] = a
		var m: Array = _acc.get("_frame", [0.0, 0.0, 0.0, 0.0])
		m[0] += Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
		m[1] += Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0
		m[2] += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		m[3] += Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)
		_acc["_frame"] = m
	if _f == 300 or _f == 660:
		print("=== ", "basement" if _f == 300 else "hall", " (avg of ", _n, " frames)")
		for k in _acc:
			var a: Array = _acc[k]
			if k == "_frame":
				print("  process_ms=%.2f physics_ms=%.2f draw_calls=%.0f objects=%.0f" % [a[0] / _n, a[1] / _n, a[2] / _n, a[3] / _n])
			else:
				print("  vp %-14s cpu_ms=%.3f gpu_ms=%.3f" % [k, a[0] / _n, a[1] / _n])
		print("  real frame: avg_ms=%.2f max_ms=%.2f fps=%d" % [_dsum / _dn * 1000.0, _dmax * 1000.0, Engine.get_frames_per_second()])
		_dsum = 0.0
		_dmax = 0.0
		_dn = 0
		print("  nodes=", Performance.get_monitor(Performance.OBJECT_NODE_COUNT), " vram_mb=%.1f" % (Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0))
	if _f == 310:
		root.get_node("Game").change_map("res://scenes/world/elevator_hall.tscn", &"FromBasement")
	return _f >= 670
