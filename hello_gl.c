#include <stdio.h>
#include <math.h>
#include <emscripten.h>
#include <emscripten/html5.h>
#include <GLES2/gl2.h>

static int canvas_width = 800;
static int canvas_height = 600;
static float angle = 0.0f;
static GLuint program;
static GLuint vbo;
static GLint u_angle;

const char *vert_src =
    "attribute vec2 a_pos;\n"
    "attribute vec3 a_color;\n"
    "varying vec3 v_color;\n"
    "uniform float u_angle;\n"
    "void main() {\n"
    "  float c = cos(u_angle);\n"
    "  float s = sin(u_angle);\n"
    "  vec2 p = vec2(a_pos.x * c - a_pos.y * s,\n"
    "               a_pos.x * s + a_pos.y * c);\n"
    "  gl_Position = vec4(p, 0.0, 1.0);\n"
    "  v_color = a_color;\n"
    "}\n";

const char *frag_src =
    "precision mediump float;\n"
    "varying vec3 v_color;\n"
    "void main() {\n"
    "  gl_FragColor = vec4(v_color, 1.0);\n"
    "}\n";

GLuint compile_shader(GLenum type, const char *src) {
    GLuint s = glCreateShader(type);
    glShaderSource(s, 1, &src, NULL);
    glCompileShader(s);
    GLint ok;
    glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[512];
        glGetShaderInfoLog(s, 512, NULL, log);
        printf("Shader error: %s\n", log);
    }
    return s;
}

void frame(void) {
    angle += 0.02f;

    glViewport(0, 0, canvas_width, canvas_height);
    glClearColor(0.1f, 0.1f, 0.15f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);

    glUseProgram(program);
    glUniform1f(u_angle, angle);

    glBindBuffer(GL_ARRAY_BUFFER, vbo);

    GLint a_pos = glGetAttribLocation(program, "a_pos");
    GLint a_color = glGetAttribLocation(program, "a_color");
    glEnableVertexAttribArray(a_pos);
    glEnableVertexAttribArray(a_color);
    glVertexAttribPointer(a_pos, 2, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void*)0);
    glVertexAttribPointer(a_color, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void*)(2 * sizeof(float)));

    glDrawArrays(GL_TRIANGLES, 0, 3);
}

int main() {
    printf("Initializing WebGL...\n");

    emscripten_set_canvas_element_size("#canvas", canvas_width, canvas_height);

    EmscriptenWebGLContextAttributes attrs;
    emscripten_webgl_init_context_attributes(&attrs);
    attrs.majorVersion = 1;
    attrs.minorVersion = 0;

    EMSCRIPTEN_WEBGL_CONTEXT_HANDLE ctx = emscripten_webgl_create_context("#canvas", &attrs);
    if (ctx <= 0) {
        printf("Failed to create WebGL context: %d\n", ctx);
        return 1;
    }
    emscripten_webgl_make_context_current(ctx);
    printf("WebGL context created.\n");

    // Compile shaders and link program
    GLuint vs = compile_shader(GL_VERTEX_SHADER, vert_src);
    GLuint fs = compile_shader(GL_FRAGMENT_SHADER, frag_src);
    program = glCreateProgram();
    glAttachShader(program, vs);
    glAttachShader(program, fs);
    glLinkProgram(program);
    u_angle = glGetUniformLocation(program, "u_angle");

    // Triangle: x, y, r, g, b
    float verts[] = {
         0.0f,  0.6f,  1.0f, 0.2f, 0.2f,  // top - red
        -0.6f, -0.4f,  0.2f, 1.0f, 0.2f,  // bottom left - green
         0.6f, -0.4f,  0.2f, 0.2f, 1.0f,  // bottom right - blue
    };
    glGenBuffers(1, &vbo);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(verts), verts, GL_STATIC_DRAW);

    printf("Rendering started. Triangle should be spinning.\n");
    emscripten_set_main_loop(frame, 0, 1);
    return 0;
}
