"""UI sound effects, synthesized here (no samples, no AI): short soft square/triangle blips in the spirit of
the pixel art - few voices, hard edges smoothed by a tiny envelope so they don't click. Writes
assets/audio/ui_<name>.wav (mono 16-bit 22050 Hz), played by Game.sfx(name); the room sounds env_<name>.wav,
played by props on animation frames (pixel_prop.gd `sound`) or by Game (the elevator ride); and the seamless room-tone
loops tone_<name>.wav (scripts/world/room_tone.gd)."""
import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/audio"
RATE = 22050


def tone(freq, ms, wave_kind="square", vol=0.5, duty=0.5, slide_to=None, attack=3, release=None):
    """One note: freq (Hz) optionally sliding to slide_to; attack/release in ms (release defaults to ~60%)."""
    n = int(RATE * ms / 1000)
    rel = int(RATE * (release if release is not None else ms * 0.6) / 1000)
    att = max(1, int(RATE * attack / 1000))
    out, phase = [], 0.0
    for i in range(n):
        f = freq if slide_to is None else freq + (slide_to - freq) * i / n
        phase = (phase + f / RATE) % 1.0
        if wave_kind == "square":
            s = 1.0 if phase < duty else -1.0
        elif wave_kind == "triangle":
            s = 4.0 * abs(phase - 0.5) - 1.0
        else:
            s = math.sin(2 * math.pi * phase)
        env = min(1.0, i / att) * (min(1.0, (n - i) / rel) if rel > 0 else 1.0)
        out.append(s * env * vol)
    return out


def crackle(ms, vol=0.5, density=0.25, seed=1, lowpass=0.35):
    """Electric crackle: sparse random clicks with a fast decay, smoothed by a one-pole low-pass."""
    r = random.Random(seed)
    n = int(RATE * ms / 1000)
    out, y, hold = [], 0.0, 0.0
    for i in range(n):
        if r.random() < density * (1.0 - i / n):
            hold = r.uniform(-1.0, 1.0)
        hold *= 0.92
        y += (hold - y) * lowpass
        out.append(y * vol * (1.0 - i / n) ** 0.5)
    return out


def mix(*parts):
    n = max(len(p) for p in parts)
    return [sum(p[i] for p in parts if i < len(p)) for i in range(n)]


def rest(ms):
    return [0.0] * int(RATE * ms / 1000)


UI = {
    # cursor moves one row (floor panel, choices)
    "move": lambda: tone(1320, 28, "square", 0.22, duty=0.25),
    # confirm: two quick notes up
    "ok": lambda: tone(988, 40, "square", 0.25, duty=0.25) + tone(1480, 70, "square", 0.22, duty=0.25),
    # cancel / close: two notes down
    "cancel": lambda: tone(988, 40, "square", 0.22, duty=0.25) + tone(660, 70, "square", 0.2, duty=0.25),
    # a locked floor: one low buzz per red blink of the button (3 blinks: played 3 times)
    "deny": lambda: tone(130, 110, "square", 0.28, duty=0.5, slide_to=110, release=30),
    # dialogue page turns / box opens: a soft triangle tick
    "page": lambda: tone(740, 45, "triangle", 0.35, release=35),
}
# Room sounds, played by props on animation frames (pixel_prop.gd `sound`, positional). Written as env_<name>.wav.
ENV = {
    # a drop landing in the half-full drum: a short falling sine "plink" and a softer echo off the steel
    "drip": lambda: tone(1500, 70, "sine", 0.55, slide_to=900, attack=1, release=60)
    + rest(25) + tone(1100, 50, "sine", 0.18, slide_to=800, attack=1, release=45),
    # a soft shoe on concrete: a muffled scuff (low-passed noise) over a short low thump; played on walk frames
    "step": lambda: mix(crackle(55, 0.45, 0.9, seed=3, lowpass=0.12), tone(95, 45, "sine", 0.35, slide_to=70, attack=1, release=35)),
    # something the chute dropped landing on the heap: a dull thump with a papery rustle
    "thud": lambda: mix(tone(80, 70, "sine", 0.45, slide_to=55, attack=1, release=55),
                        crackle(120, 0.35, 0.6, seed=41, lowpass=0.25)),
    # an old bulb catching again after it flickered out: a short mains buzz with a tick
    "buzz": lambda: mix(tone(120, 110, "square", 0.22, duty=0.3, attack=2, release=40), crackle(30, 0.4, 0.8, seed=51, lowpass=0.6)),
    # the folding scissor gate: a dry metal rattle with a ring of steel bars in it (played every other gate frame)
    "gate": lambda: mix(crackle(90, 0.45, 0.5, seed=21, lowpass=0.7),
                        tone(1340, 90, "sine", 0.12, attack=1, release=80), tone(2110, 70, "sine", 0.08, attack=1, release=60)),
    # the severed power line arcing: a crackle with a faint mains buzz under it
    "spark": lambda: mix(crackle(140, 0.7, 0.3, seed=7), tone(100, 140, "square", 0.06, release=80)),
}


def periodic(seconds, partials, seed):
    """A seamless loop: every partial (freq Hz, amplitude) is rounded to a whole number of cycles over the loop,
    with a random phase, so the end joins the start without a click. Slow wobble partials (< 1 Hz) also loop."""
    import numpy as np
    rng = np.random.default_rng(seed)
    n = int(RATE * seconds)
    t = np.arange(n) / RATE
    out = np.zeros(n)
    for f, a in partials:
        k = max(1, round(f * seconds))                    # whole cycles in the loop
        out += a * np.sin(2 * np.pi * k / seconds * t + rng.uniform(0, 2 * np.pi))
    return out


def chute_tone():
    """Basement: air pulled down the deletion chute - a soft rumble (many low partials, falling 1/f) that
    swells slowly twice per loop."""
    import numpy as np
    sec = 8.0
    partials = [(f, 1.0 / f ** 0.9) for f in np.arange(35, 420, 1.7)]
    x = periodic(sec, partials, seed=11)
    x /= np.abs(x).max()
    swell = 0.8 + 0.2 * periodic(sec, [(0.25, 1.0)], seed=2)
    return list(x * swell * 0.5)


def hum_tone():
    """Elevator hall: the mains hum of old fittings (100 Hz and harmonics, a little uneven) over faint air."""
    import numpy as np
    sec = 4.0
    x = periodic(sec, [(100, 1.0), (200, 0.45), (300, 0.3), (400, 0.12), (500, 0.08), (101, 0.25)], seed=5)
    air = periodic(sec, [(f, 1.0 / f) for f in np.arange(60, 300, 2.3)], seed=6)
    x = x / np.abs(x).max() * 0.35 + air / np.abs(air).max() * 0.25
    return list(x / np.abs(x).max() * 0.5)


def lift_motor():
    """The car moving: an old motor winding up and settling (low buzz with harmonics, pitch rising then easing),
    a cable rattle under it, louder in the middle. ~1.6 s, covers the fade between floors."""
    import numpy as np
    n = int(RATE * 1.6)
    t = np.arange(n) / RATE
    f = 55 + 25 * np.sin(np.pi * np.clip(t / 1.6, 0, 1)) ** 0.7
    ph = 2 * np.pi * np.cumsum(f) / RATE
    x = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph) + 0.15 * np.sign(np.sin(4 * ph))
    rattle = np.array(crackle(1600, 1.0, 0.08, seed=33, lowpass=0.5))[:n]
    env = np.sin(np.pi * np.clip(t / 1.6, 0, 1)) ** 0.8
    y = (x / np.abs(x).max() * 0.6 + rattle * 0.3) * env
    return list(y / np.abs(y).max() * 0.32)


def bell():
    """Arrival: one soft ding of an old elevator bell (a struck bar: a few inharmonic partials, long decay)."""
    import numpy as np
    n = int(RATE * 1.1)
    t = np.arange(n) / RATE
    y = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in
            ((1318, 1.0, 3.5), (2637, 0.35, 6.0), (3620, 0.18, 9.0), (659, 0.2, 4.0)))
    y *= np.minimum(1.0, t / 0.003)
    return list(y / np.abs(y).max() * 0.3)


# Room tones: seamless loops for each map's background (scripts/world/room_tone.gd), written as tone_<name>.wav.
TONES = {"chute": chute_tone, "hum": hum_tone}
# One-off sounds played by Game (the elevator ride): written as env_<name>.wav like the prop sounds.
ENV.update({"lift": lift_motor, "bell": bell})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for prefix, table in (("ui", UI), ("env", ENV), ("tone", TONES)):
        for name, make in table.items():
            write(OUT / f"{prefix}_{name}.wav", make())


def write(path, data):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in data))
    print("wrote", path.relative_to(ROOT), f"{len(data) / RATE * 1000:.0f} ms")


if __name__ == "__main__":
    main()
