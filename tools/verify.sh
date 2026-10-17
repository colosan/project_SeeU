#!/usr/bin/env bash
# The whole check routine in one go (docs/WORKFLOW.md "검증 루틴"), from the repository root in Git Bash:
#   GODOT=/path/to/godot_console.exe bash tools/verify.sh            # everything
#   GODOT=... bash tools/verify.sh --no-record                         # skip the 2-3 minute recording
# Rebuilds the emission masks and both rooms' scenes, imports, catches script errors with a short headless run,
# checks how the maps connect (tools/check_project.gd), mashes random input at it (tools/monkey_test.gd), records the autoplay run (build/autoplay/f*.png + f.wav)
# and prints every error or warning it saw. Ends by putting back .import files a different Godot version rewrote.
set -u
cd "$(dirname "$0")/.."
: "${GODOT:?set GODOT to the console Godot of this PC, see docs/WORKFLOW.md}"
RECORD=1
[ "${1:-}" = "--no-record" ] && RECORD=0
FAIL=0
START=$(date +%s)
step() { echo; echo "== $*"; }

step "emission masks";   python tools/art/gen_emission.py | grep -iE "wrote|warn|error" || true
step "basement scene";   python tools/layout_basement.py | tail -1 | tee /tmp/verify_layout.txt
grep -q " 0 problems" /tmp/verify_layout.txt || FAIL=1
step "hall scene";       python tools/layout_elevator_hall.py | tail -1 | tee /tmp/verify_layout.txt
grep -q " 0 problems" /tmp/verify_layout.txt || FAIL=1
step "import";           "$GODOT" --headless --path . --import > /dev/null 2>&1
step "script errors (short headless run)"
if "$GODOT" --headless --path . --quit-after 30 2>&1 | grep -E "SCRIPT ERROR|Parse Error"; then
	echo "script errors: stopping before the recording (it would only wait out every step)"
	FAIL=1
	RECORD=0
else
	echo "none"
fi
step "project check"
"$GODOT" --headless --path . --script res://tools/check_project.gd 2>&1 | grep -E "PROBLEM|check_project"
"$GODOT" --headless --path . --script res://tools/check_project.gd > /dev/null 2>&1 || FAIL=1
step "reach check (everything examinable can be walked up to)"
"$GODOT" --headless --path . --script res://tools/reach_check.gd 2>&1 | grep -E "PROBLEM|reach_check|things in reach"
"$GODOT" --headless --path . --script res://tools/reach_check.gd > /dev/null 2>&1 || FAIL=1
step "leak check (200 map swaps)"
"$GODOT" --headless --fixed-fps 60 --path . --script res://tools/leak_check.gd 2>&1 | grep -E "leak_check|PROBLEM"
"$GODOT" --headless --fixed-fps 60 --path . --script res://tools/leak_check.gd > /dev/null 2>&1 || FAIL=1
step "monkey test (random input, 4 seeds x 20000 frames, headless)"
for seed in 1 2 3 4; do
	"$GODOT" --headless --fixed-fps 60 --path . --script res://tools/monkey_test.gd -- 20000 $seed > /tmp/verify_monkey.txt 2>&1 || FAIL=1
	grep -E "^monkey: [0-9]+ frames|PROBLEM|SCRIPT ERROR" /tmp/verify_monkey.txt
	grep -q "SCRIPT ERROR" /tmp/verify_monkey.txt && FAIL=1
done
if [ "$RECORD" = 1 ]; then
	step "recording (build/autoplay)"
	rm -rf build/autoplay
	timeout 900 cmd //c "tools\\record_autoplay.cmd" > build/rec.log 2>&1
	echo "$(ls build/autoplay | grep -c png) frames"
	# the Camera2D note and the movie writer's exit-time leak report are expected
	grep -E "ERROR|WARNING|SCRIPT" build/rec.log | grep -vE "Camera2D overridden|resources still in use at exit|ObjectDB instances leaked" \
		| sort | uniq -c | tee /tmp/verify_rec.txt
	[ -s /tmp/verify_rec.txt ] && FAIL=1
fi
step "put back .import files rewritten by another Godot version"
git diff --name-only | grep '\.import$' | xargs -r git checkout --
echo
[ "$FAIL" = 0 ] && echo "VERIFY: OK ($(( $(date +%s) - START ))s)" || echo "VERIFY: PROBLEMS (see above, $(( $(date +%s) - START ))s)"
exit "$FAIL"
