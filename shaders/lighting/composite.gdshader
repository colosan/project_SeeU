shader_type canvas_item;
render_mode unshaded;

// Final pass of the pixel lighting (scripts/world/pixel_lighting.gd): drawn over the world as one
// sprite showing the LEFT half of the light viewport (region), scaled 3x with nearest filtering.
//   final = albedo x light + glow, light in 0..2
// The light map stores light / 2 so pools can brighten the (dark) art; above 1 the extra light lifts dark
// pixels more than bright ones, so pale plates and dials keep their shading instead of clipping to white.
// The glow map (right half of the same texture) holds the additive beam haze, dust and halos.

uniform sampler2D screen_tex : hint_screen_texture, filter_nearest;

void fragment() {
	vec3 albedo = texture(screen_tex, SCREEN_UV).rgb;
	vec3 light = texture(TEXTURE, UV).rgb * 2.0;
	vec3 glow = texture(TEXTURE, UV + vec2(0.5, 0.0)).rgb;
	vec3 over = max(light - 1.0, vec3(0.0));
	vec3 lit = albedo * min(light, vec3(1.0)) + over * albedo * (1.0 - 0.75 * albedo);
	COLOR = vec4(min(lit + glow, vec3(1.0)), 1.0);
}
