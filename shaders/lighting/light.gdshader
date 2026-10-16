shader_type canvas_item;
render_mode unshaded, blend_disabled;

// Native-res deferred pixel lighting (scripts/world/pixel_lighting.gd draws this on a 2W x H rect).
//   left half  (x <  W): light map, stored as light / 2 -> final = albedo x light x 2 (composite.gdshader)
//   right half (x >= W): glow map, added over the scene  (beam haze, dust motes, halos)
// Space: buffer px. A floor point (x, y) at height z is drawn at (x, y - z). The height buffer
// holds, per drawn pixel, its height above the floor, so the 3D point is P = (x, y + h, h).

const int MAX_LIGHTS = 16;
const int SHADOW_STEPS = 24;
const int KIND_FLOOR = 0;
const int KIND_FACE = 1;
const int KIND_CHAR = 2;
const int KIND_CAP = 3;
const int TYPE_POINT = 0;
const int TYPE_SPOT = 1;
const int TYPE_BEAM = 2;

uniform sampler2D height_buf : filter_nearest, repeat_disable;
uniform ivec2 buf_size = ivec2(321, 241);
uniform ivec2 world_offset = ivec2(0, 0);   // buffer px = world native px + world_offset
uniform bool flip_y = false;                // height buffer stored bottom-up (backend dependent)
uniform vec3 ambient = vec3(0.30, 0.32, 0.40);
uniform float ao_strength = 0.35;
uniform float peak = 1.6;                   // light of the brightest pools (1 = art as painted, max 2)
uniform float levels = 8.0;                 // light steps between ambient and the peak
uniform float glow_step = 0.04;             // quantum of the additive glow map
uniform float player_fill = 0.16;
uniform int light_count = 0;
uniform vec4 l_pos[16];   // floor point x, y (buffer px), height z, radius
uniform vec4 l_col[16];   // colour * energy, type
uniform vec4 l_dir[16];   // spot: axis xyz (unit, z up), cos(half angle) | beam: mouth radius, -, -, pool radius
uniform vec4 l_fx[16];    // casts shadows (0/1), halo strength, haze density, halo radius

varying vec2 px;

void vertex() {
	px = VERTEX;
}

vec4 gbuf(ivec2 p) {
	if (p.x < 0 || p.y < 0 || p.x >= buf_size.x || p.y >= buf_size.y) {
		return vec4(0.0);
	}
	if (flip_y) {
		p.y = buf_size.y - 1 - p.y;
	}
	return texelFetch(height_buf, p, 0);
}

int kind_of(vec4 g) {
	return int(g.b * 255.0 / 64.0 + 0.5);
}

float height_of(vec4 g) {
	return floor(g.r * 255.0 + 0.5);
}

// 4x4 ordered dither threshold in (0, 1), fixed to the world's native pixel grid.
float bayer(ivec2 p) {
	int m[16] = {0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5};
	return (float(m[(p.y & 3) * 4 + (p.x & 3)]) + 0.5) / 16.0;
}

// Screen-space shadow: march from P toward the light; a sample is blocked when the buffer there
// holds something taller than the ray whose floor line is close to the ray's floor point.
// `layer` > 0: ignore occluders standing within that many px of P's own floor line (a pile's parts and
// the junk leaning on it are one clump; they must not speckle each other).
float shadow(vec3 P, vec3 L, float jitter, float layer) {
	vec3 d = L - P;
	float len = length(d);
	float thick = max(3.0, length(d.xy) / float(SHADOW_STEPS) * 1.6);
	float vis = 1.0;
	for (int k = 0; k < SHADOW_STEPS; k++) {
		float t = (float(k) + jitter) / float(SHADOW_STEPS);
		if ((1.0 - t) * len < 3.0) {
			break;                                      // don't let the source's own fixture shadow it
		}
		vec3 q = P + d * t;
		ivec2 s = ivec2(floor(vec2(q.x, q.y - q.z)));
		vec4 g = gbuf(s);
		int ok = kind_of(g);
		if (g.a < 0.5 || ok == KIND_CAP) {
			continue;
		}
		float oh = height_of(g);
		float ofy = float(s.y) + 0.5 + oh;
		if (oh > q.z + 1.5 && abs(ofy - q.y) < thick && abs(ofy - P.y) >= layer) {
			if (ok != KIND_CHAR) {
				return 0.0;
			}
			vis = 0.45;                                 // her own shadow: a flat billboard, keep it light
		}
	}
	return vis;
}

// Contact darkening: floor right in front of something standing, and the lowest rows of faces.
float occlusion(ivec2 b, vec3 P, int kd, float h) {
	if (kd == KIND_FLOOR) {
		float ao = 0.0;
		for (int k = 1; k <= 3; k++) {
			for (int dx = -1; dx <= 1; dx++) {
				ivec2 s = b + ivec2(dx, -k);
				vec4 g = gbuf(s);
				int ok = kind_of(g);
				if (g.a < 0.5 || ok == KIND_FLOOR || ok == KIND_CAP) {
					continue;
				}
				float oh = height_of(g);
				float gap = P.y - (float(s.y) + 0.5 + oh);
				if (gap > -0.5 && gap < 4.0 && oh >= float(k) - 0.5) {
					ao = max(ao, 1.0 - max(gap, 0.0) / 4.0);
				}
			}
		}
		return ao;
	}
	return h < 3.0 ? (3.0 - h) / 3.0 * 0.7 : 0.0;
}

vec3 light_at(ivec2 b, float dither, vec4 g) {
	if (g.a < 0.5) {
		return vec3(0.0);                               // void stays black
	}
	int kd = kind_of(g);
	if (kd == KIND_CAP) {
		return ambient * 0.85;                          // wall tops: never lit directly
	}
	float h = height_of(g);
	vec3 P = vec3(float(b.x) + 0.5, float(b.y) + 0.5 + h, h);
	vec3 N = kd == KIND_FLOOR ? vec3(0.0, 0.0, 1.0) : normalize(vec3(0.0, 1.0, 0.45));
	float wrap = kd == KIND_CHAR ? 0.35 : 0.15;

	vec3 sum_rgb = vec3(0.0);
	vec3 sum_hue2 = vec3(0.0);
	float sum_i = 0.0;
	float sum_i2 = 0.0;
	for (int i = 0; i < MAX_LIGHTS; i++) {
		if (i >= light_count) {
			break;
		}
		vec4 lp = l_pos[i];
		vec4 lc = l_col[i];
		vec4 ld = l_dir[i];
		int type = int(lc.w + 0.5);
		vec3 L = lp.xyz;
		vec3 d = L - P;
		float dist = max(length(d), 0.001);
		float att;
		if (type == TYPE_BEAM) {
			if (P.z >= L.z) {
				continue;
			}
			float r = mix(ld.w, ld.x, P.z / L.z);       // cone: pool radius on the floor, mouth radius at the source
			float rad = length(P.xy - L.xy) / max(r, 1.0);
			if (rad >= 1.0) {
				continue;
			}
			att = (1.0 - smoothstep(0.55, 1.0, rad)) * (1.0 - 0.3 * rad * rad);
		} else {
			if (dist >= lp.w) {
				continue;
			}
			float x = dist / lp.w;                      // smooth inverse-square-ish, exactly 0 at the radius
			float x2 = x * x;
			float win = 1.0 - x2 * x2;
			att = win * win / (1.0 + 2.5 * x2);
			if (type == TYPE_SPOT) {
				att *= smoothstep(ld.w, ld.w + 0.3, dot(-d / dist, ld.xyz));
			}
		}
		float ndl = (dot(N, d / dist) + wrap) / (1.0 + wrap);
		float lum = max(lc.r, max(lc.g, lc.b));
		float inten = att * ndl * lum;
		if (inten < 0.008) {
			continue;
		}
		if (l_fx[i].x > 0.5) {
			inten *= kd == KIND_FLOOR ? shadow(P, L, dither, 0.0) : shadow(P, L, 0.5, 3.0);
			if (inten <= 0.0) {
				continue;
			}
		}
		vec3 hue = lc.rgb / lum;
		sum_rgb += hue * inten;
		sum_hue2 += hue * inten * inten;
		sum_i += inten;
		sum_i2 += inten * inten;
	}
	// colour: lean toward the dominant light instead of averaging every overlapping hue into mud
	vec3 direct = vec3(0.0);
	if (sum_i > 0.0) {
		direct = mix(sum_rgb, sum_hue2 / sum_i2 * sum_i, 0.6);
	}
	// pixel-art steps: quantize the direct light, ordered-dither between neighbouring steps. Floors get
	// the full dither ramp; on busy prop art a full ramp reads as noise, so faces mostly snap to a step.
	float dl = max(direct.r, max(direct.g, direct.b));
	if (dl > 0.0) {
		float step_size = (peak - max(ambient.r, max(ambient.g, ambient.b))) / levels;
		float t = kd == KIND_FLOOR ? dither : 0.5 + (dither - 0.5) * 0.4;
		float q = floor(dl / step_size + t) * step_size;
		direct = direct / dl * q;
	}
	float ao = floor(occlusion(b, P, kd, h) * 3.0 + dither) / 3.0;
	vec3 total = ambient * (1.0 - ao_strength * ao) + direct * (1.0 - 0.25 * ao);
	if (kd == KIND_CHAR) {
		total += vec3(player_fill);                    // readability: she never sinks fully into shadow
	}
	total = max(total, vec3(g.g));                     // emitters show (at least) their true art colour
	float m = max(total.r, max(total.g, total.b));
	return m > 2.0 ? total / m * 2.0 : total;
}

vec3 glow_at(ivec2 b, ivec2 wp, float dither, vec4 g) {
	if (g.a < 0.5) {
		return vec3(0.0);
	}
	vec2 sp = vec2(b) + 0.5;
	float drawn_floor_y = sp.y + height_of(g);          // floor line of whatever is drawn here
	vec3 add = vec3(0.0);
	for (int i = 0; i < MAX_LIGHTS; i++) {
		if (i >= light_count) {
			break;
		}
		vec4 lp = l_pos[i];
		vec4 lc = l_col[i];
		vec4 fx = l_fx[i];
		vec2 src = vec2(lp.x, lp.y - lp.z);              // where the source is drawn
		if (fx.y > 0.0) {                                // tiny halo around the source, hidden by things in front
			float d = length(sp - src);
			if (d < fx.w && drawn_floor_y <= lp.y + 3.0) {
				float k = 1.0 - d / fx.w;
				add += lc.rgb * fx.y * k * k;
			}
		}
		if (int(lc.w + 0.5) == TYPE_BEAM && fx.z > 0.0 && sp.y > src.y && sp.y < lp.y + 4.0) {
			vec4 ld = l_dir[i];
			float z = clamp(lp.y - sp.y, 0.0, lp.z);      // height of the beam slice drawn on this row
			float r = mix(ld.w, ld.x, z / lp.z);
			float dx = abs(sp.x - lp.x) / max(r, 1.0);
			if (dx < 1.0 && drawn_floor_y <= lp.y + r) {   // nothing standing in front of the beam
				float body = (1.0 - dx * dx) * smoothstep(0.0, 18.0, z);
				float shimmer = 0.85 + 0.15 * sin(TIME * 0.7 + float(wp.y) * 0.21);
				add += lc.rgb / max(lc.r, max(lc.g, lc.b)) * fx.z * body * shimmer;
				for (int k = 0; k < 7; k++) {               // dust drifting down through the light
					float seed = float(k) * 7.31 + float(i) * 3.7;
					float fall = fract(seed * 0.618 + TIME * (0.025 + 0.012 * float(k % 3)));
					float mz = lp.z * (1.0 - fall);
					float mr = mix(ld.w, ld.x, mz / lp.z);
					vec2 mote = floor(vec2(lp.x + sin(TIME * 0.5 + seed) * mr * 0.7, lp.y - mz));
					if (all(equal(ivec2(mote), b))) {
						add += vec3(0.34) * (0.6 + 0.4 * sin(TIME * 3.0 + seed));
					}
				}
			}
		}
	}
	// stepped, dithered glow (no smooth airbrush)
	float gl = max(add.r, max(add.g, add.b));
	if (gl <= 0.0) {
		return vec3(0.0);
	}
	float q = floor(gl / glow_step + dither) * glow_step;
	return min(add / gl * q, vec3(1.0));
}

void fragment() {
	ivec2 ip = ivec2(floor(px));
	bool glow_half = ip.x >= buf_size.x;
	ivec2 b = ivec2(glow_half ? ip.x - buf_size.x : ip.x, ip.y);
	ivec2 wp = b - world_offset;
	float dither = bayer(wp + ivec2(1024));
	vec4 g = gbuf(b);
	COLOR = vec4(glow_half ? glow_at(b, wp, dither, g) : light_at(b, dither, g) * 0.5, 1.0);
}
