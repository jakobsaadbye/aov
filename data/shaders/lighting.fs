#version 330
// The lit shader of the game, see lighting.sd: a warm sun with a soft edge to its shade, light from the sky above and
// warmer light bounced off the ground below, a rim of light round the edges of heroes and cars, a little shine, and a
// haze in the distance. The colors come out a bit richer than they are, like paint
in vec3 fragPosition;
in vec2 fragTexCoord;
in vec3 fragNormal;

uniform sampler2D texture0;
uniform vec4 colDiffuse;
uniform vec3 viewPos;
uniform vec3 sunDirection;
uniform vec3 sunColor;
uniform vec3 skyColor;
uniform vec3 groundColor;
uniform vec3 rimColor;
uniform vec3 hazeColor;

out vec4 finalColor;

void main() {
    vec4 base = texture(texture0, fragTexCoord) * colDiffuse;

    vec3 normal  = normalize(fragNormal);
    vec3 toLight = normalize(-sunDirection);
    vec3 toEye   = normalize(viewPos - fragPosition);

    // The sun wraps a little round to the dark side, so shade is soft and never flat
    float diffuse = smoothstep(0.0, 1.0, clamp((dot(normal, toLight) + 0.3) / 1.3, 0.0, 1.0));
    vec3 ambient  = mix(groundColor, skyColor, normal.y * 0.5 + 0.5);
    float specular = pow(max(dot(normal, normalize(toLight + toEye)), 0.0), 28.0) * 0.16;

    // A rim on what stands up, strongest on the side of the sun
    float rim = pow(1.0 - max(dot(normal, toEye), 0.0), 3.0) * (1.0 - abs(normal.y)) * (0.35 + 0.65 * diffuse);

    vec3 color = base.rgb * (ambient + sunColor * diffuse) + sunColor * specular * diffuse + rimColor * rim * 0.45;

    float grey = dot(color, vec3(0.299, 0.587, 0.114));
    color = mix(vec3(grey), color, 1.15);

    float haze = clamp((length(viewPos - fragPosition) - 160.0) / 280.0, 0.0, 0.7);
    finalColor = vec4(mix(color, hazeColor, haze), base.a);
}
