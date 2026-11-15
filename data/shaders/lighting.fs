#version 330
// The lit shader of the game: the sun, ambient light and a haze in the distance. See lighting.sd
in vec3 fragPosition;
in vec2 fragTexCoord;
in vec3 fragNormal;

uniform sampler2D texture0;
uniform vec4 colDiffuse;
uniform vec3 viewPos;
uniform vec3 sunDirection;
uniform vec3 sunColor;
uniform vec3 ambientColor;
uniform vec3 hazeColor;

out vec4 finalColor;

void main() {
    vec4 base = texture(texture0, fragTexCoord) * colDiffuse;

    vec3 normal  = normalize(fragNormal);
    vec3 toLight = normalize(-sunDirection);
    vec3 toEye   = normalize(viewPos - fragPosition);

    float diffuse  = max(dot(normal, toLight), 0.0);
    float specular = pow(max(dot(normal, normalize(toLight + toEye)), 0.0), 24.0) * 0.18;

    vec3 color = base.rgb * (ambientColor + sunColor * diffuse) + sunColor * specular * diffuse;

    float haze = clamp((length(viewPos - fragPosition) - 140.0) / 260.0, 0.0, 0.75);
    finalColor = vec4(mix(color, hazeColor, haze), base.a);
}
