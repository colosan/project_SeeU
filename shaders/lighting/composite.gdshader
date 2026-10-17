shader_type canvas_item;
render_mode unshaded;

// Final pass of the pixel lighting (scripts/world/pixel_lighting.gd): drawn over the world as one
// sprite showing the LEFT half of the light viewport (region), scaled 3x with nearest filtering.
//   final = albedo x light + glow, light in 0..2
// The light map stores light / 2 so pools can brighten the (dark) art; above 1 the extra light lifts dark
// pixels more than bright ones, so pale plates and dials keep their shading instead of clipping to white.
// The glow map (right half of the same texture) holds the additive beam haze, dust and halos.
// Everything outside the map's rectangle (clip_rect, in SCREEN_UV) is the void, even where props hang over
// the room's edge: the unrendered space between maps (docs/WORLD.md, rendering law) drawn as a dim dot grid
// on the art's native grid, anchored to the room's corner. No frame around the room's rectangle: only what is
// rendered stands out of the pattern.
// Inside the room, wall tops and empty cells are unrendered too: the light pass gives them exactly zero light
// (light.gdshader), and they get the same pattern - only the room itself is rendered. Because the front
// layer's wall tops are drawn over the props, whatever stands behind a wall is hidden by that pattern.

uniform sampler2D screen_tex : hint_screen_texture, filter_nearest;
uniform vec4 clip_rect = vec4(0.0, 0.0, 1.0, 1.0);   // xy = top-left, zw = bottom-right
uniform vec3 void_color : source_color = vec3(0.059, 0.063, 0.067);   // rubber 0f1011
uniform vec3 void_dot : source_color = vec3(0.106, 0.110, 0.122);     // plastic 1b1c1f
const float NATIVE = 3.0;         // screen px per art px (PixelLighting.SCALE)
const float DOT_STEP = 8.0;       // art px between grid dots

vec3 void_at(vec2 screen_uv, vec2 px_size) {
	vec2 a = floor((screen_uv - clip_rect.xy) / px_size / NATIVE);   // art px from the room's top-left
	vec2 b = floor((clip_rect.zw - screen_uv) / px_size / NATIVE);   // art px from its bottom-right
	vec2 m = mod(a, DOT_STEP);
	return (m.x == 0.0 && m.y == 0.0) ? void_dot : void_color;
}

void fragment() {
	vec3 albedo = texture(screen_tex, SCREEN_UV).rgb;
	vec3 light = texture(TEXTURE, UV).rgb * 2.0;
	vec3 glow = texture(TEXTURE, UV + vec2(0.5, 0.0)).rgb;
	vec3 over = max(light - 1.0, vec3(0.0));
	vec3 lit = albedo * min(light, vec3(1.0)) + over * albedo * (1.0 - 0.75 * albedo);
	bool inside = all(greaterThanEqual(SCREEN_UV, clip_rect.xy)) && all(lessThan(SCREEN_UV, clip_rect.zw));
	bool unrendered = max(light.r, max(light.g, light.b)) < 0.004;
	COLOR = inside && !unrendered ? vec4(min(lit + glow, vec3(1.0)), 1.0) : vec4(void_at(SCREEN_UV, SCREEN_PIXEL_SIZE), 1.0);
}
