shader_type canvas_item;
render_mode unshaded;

// "Twin" of a lit visual. Twins live on visibility layer 2 and are drawn only into the
// native-res height buffer (HeightVP, see scripts/world/pixel_lighting.gd), never on screen.
// Output per pixel:
//   R = height above the floor in native px / 255   (props: distance above the sprite's base line)
//   G = emission (0..1, from the <name>.emit.png mask; 1 = shows its true art colour)
//   B = surface kind * 64 / 255: 0 floor/top, 1 vertical face, 2 character, 3 wall cap (ambient only)
//   A = coverage (transparent pixels are discarded, so the buffer keeps whatever is behind)

uniform sampler2D emit_tex : filter_nearest, hint_default_black;
uniform bool use_data = false;          // room backgrounds: TEXTURE is the baked .height.png companion
uniform float base_y = 0.0;             // local y of the floor contact line
uniform float units_per_native = 1.0;   // local units per native px (props: 1, the 1:1 player sprite: 3)
uniform float height_offset = 0.0;      // native px between the base line and the floor (wall-hung props)
uniform int kind = 1;
uniform bool lies_flat = false;         // floor decals: height 0, floor normal

varying float local_y;

void vertex() {
	local_y = VERTEX.y;
}

void fragment() {
	vec4 src = texture(TEXTURE, UV);
	if (src.a < 0.5) {
		discard;
	}
	float e = texture(emit_tex, UV).r;
	if (use_data) {
		COLOR = vec4(src.r, e, src.b, 1.0);
	} else {
		float h = lies_flat ? 0.0 : floor(max(base_y - local_y, 0.0) / units_per_native) + height_offset;
		float k = lies_flat ? 0.0 : float(kind);
		COLOR = vec4(min(h, 255.0) / 255.0, e, k * 64.0 / 255.0, 1.0);
	}
}
