#define RENDERER3D_EXPORTS
#include "renderer3d.h"
#include <Windows.h>
#include <GL/gl.h>
#include <GL/glu.h>
#include <SDL.h>
#include <SDL_opengl.h>
#include <vector>
#include <iostream>
#include <cmath>

// ОРБИТАЛЬНАЯ КАМЕРА - координаты в сферической системе
float cameraDistance = 15.0f;  // Расстояние от центра сцены
float cameraAngleX = 0.0f;     // Угол по вертикали
float cameraAngleY = 0.0f;     // Угол по горизонтали
float panX = 0.0f, panY = 0.0f; // Панорамирование центра сцены

// Цвет фона
float bgR = 0.2f, bgG = 0.3f, bgB = 0.3f;

bool leftMouseDown = false;
bool middleMouseDown = false;
int lastMouseX = 0, lastMouseY = 0;

struct Cube {
    float x, y, z, size;
};
std::vector<Cube> cubes;

SDL_Window* window = nullptr;
SDL_GLContext glContext = nullptr;
bool isRunning = true;

// Функция для вычисления позиции камеры из сферических координат
void updateCameraPosition() {
    float x = cameraDistance * cos(cameraAngleX) * sin(cameraAngleY);
    float y = cameraDistance * sin(cameraAngleX);
    float z = cameraDistance * cos(cameraAngleX) * cos(cameraAngleY);
    
    glLoadIdentity();
    gluLookAt(
        x + panX, y + panY, z,     // Позиция камеры
        panX, panY, 0.0f,          // Точка, на которую смотрим (центр + панорамирование)
        0.0f, 1.0f, 0.0f           // Вектор "вверх"
    );
}

void drawCube(float x, float y, float z, float size) {
    glPushMatrix();
    glTranslatef(x, y, z);
    glScalef(size, size, size);

    float vertices[8][3] = {
        {-0.5f, -0.5f, -0.5f}, {0.5f, -0.5f, -0.5f},
        {0.5f,  0.5f, -0.5f}, {-0.5f,  0.5f, -0.5f},
        {-0.5f, -0.5f,  0.5f}, {0.5f, -0.5f,  0.5f},
        {0.5f,  0.5f,  0.5f}, {-0.5f,  0.5f,  0.5f}
    };

    int faces[6][4] = {
        {0,1,2,3}, {1,5,6,2},
        {5,4,7,6}, {4,0,3,7},
        {3,2,6,7}, {4,5,1,0}
    };

    float colors[6][3] = {
        {1,0,0}, {0,1,0},
        {0,0,1}, {1,1,0},
        {1,0,1}, {0,1,1}
    };

    glBegin(GL_QUADS);
    for (int i = 0; i < 6; ++i) {
        glColor3fv(colors[i]);
        for (int j = 0; j < 4; ++j) {
            glVertex3fv(vertices[faces[i][j]]);
        }
    }
    glEnd();

    glPopMatrix();
}

void handleCameraInput(const SDL_Event& event) {
    if (event.type == SDL_MOUSEBUTTONDOWN) {
        if (event.button.button == SDL_BUTTON_LEFT) leftMouseDown = true;
        else if (event.button.button == SDL_BUTTON_MIDDLE) middleMouseDown = true;
    }
    else if (event.type == SDL_MOUSEBUTTONUP) {
        if (event.button.button == SDL_BUTTON_LEFT) leftMouseDown = false;
        else if (event.button.button == SDL_BUTTON_MIDDLE) middleMouseDown = false;
    }
    else if (event.type == SDL_MOUSEMOTION) {
        int dx = event.motion.x - lastMouseX;
        int dy = event.motion.y - lastMouseY;

        if (leftMouseDown) {
            // Орбитальное вращение
            cameraAngleY += dx * 0.01f;
            cameraAngleX += dy * 0.01f;
            
            // Ограничиваем вертикальный угол
            if (cameraAngleX > 1.5f) cameraAngleX = 1.5f;
            if (cameraAngleX < -1.5f) cameraAngleX = -1.5f;
        }
        else if (middleMouseDown) {
            // Панорамирование
            panX += dx * 0.05f;
            panY -= dy * 0.05f;
        }

        lastMouseX = event.motion.x;
        lastMouseY = event.motion.y;
    }
    else if (event.type == SDL_MOUSEWHEEL) {
        // Зум изменяет расстояние от центра
        cameraDistance -= event.wheel.y * 1.0f;
        if (cameraDistance < 2.0f) cameraDistance = 2.0f;
        if (cameraDistance > 50.0f) cameraDistance = 50.0f;
    }
}

extern "C" {

    void InitRenderer3D(int width, int height) {
        if (SDL_Init(SDL_INIT_VIDEO) < 0) {
            std::cerr << "SDL initialization failed: " << SDL_GetError() << std::endl;
            return;
        }

        window = SDL_CreateWindow("3D Renderer",
            SDL_WINDOWPOS_CENTERED,
            SDL_WINDOWPOS_CENTERED,
            width, height,
            SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE);

        if (!window) {
            std::cerr << "Window creation failed: " << SDL_GetError() << std::endl;
            SDL_Quit();
            return;
        }

        glContext = SDL_GL_CreateContext(window);
        if (!glContext) {
            std::cerr << "OpenGL context creation failed: " << SDL_GetError() << std::endl;
            SDL_DestroyWindow(window);
            SDL_Quit();
            return;
        }

        glEnable(GL_DEPTH_TEST);
        glMatrixMode(GL_PROJECTION);
        gluPerspective(45.0, (double)width / height, 0.1, 100.0);
        glMatrixMode(GL_MODELVIEW);

        lastMouseX = width / 2;
        lastMouseY = height / 2;
    }

    void RenderFrame() {
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) {
                isRunning = false;
            }
            handleCameraInput(event);
        }

        if (!isRunning) return;

        glClearColor(bgR, bgG, bgB, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        // НОВАЯ ЛОГИКА КАМЕРЫ - орбитальное вращение
        updateCameraPosition();

        for (const auto& cube : cubes) {
            drawCube(cube.x, cube.y, cube.z, cube.size);
        }

        SDL_GL_SwapWindow(window);
    }

    void CloseRenderer3D() {
        if (glContext) {
            SDL_GL_DeleteContext(glContext);
            glContext = nullptr;
        }
        if (window) {
            SDL_DestroyWindow(window);
            window = nullptr;
        }
        SDL_Quit();
    }

    bool IsRunning() {
        return isRunning;
    }

    void AddCube(float x, float y, float z, float size) {
        cubes.push_back({ x, y, z, size });
    }

    void RotateCamera(float dx, float dy) {
        // ОРБИТАЛЬНОЕ ВРАЩЕНИЕ вместо поворота сцены
        cameraAngleY += dx * 0.01f;
        cameraAngleX += dy * 0.01f;
        
        // Ограничиваем вертикальный угол
        if (cameraAngleX > 1.5f) cameraAngleX = 1.5f;
        if (cameraAngleX < -1.5f) cameraAngleX = -1.5f;
    }

    void MoveCamera(float dx, float dy) {
        // Панорамирование центра обзора
        panX += dx;
        panY += dy;
    }

    void ZoomCamera(float delta) {
        // Изменяем расстояние от центра сцены
        cameraDistance += delta;
        if (cameraDistance < 2.0f) cameraDistance = 2.0f;
        if (cameraDistance > 50.0f) cameraDistance = 50.0f;
    }

    // === НОВЫЕ ФУНКЦИИ ===
    void ClearScene() {
        cubes.clear();
    }

    void ResetCamera() {
        cameraDistance = 15.0f;
        cameraAngleX = 0.0f;
        cameraAngleY = 0.0f;
        panX = 0.0f;
        panY = 0.0f;
    }

    int GetObjectCount() {
        return static_cast<int>(cubes.size());
    }

    void SetBackgroundColor(float r, float g, float b) {
        bgR = r;
        bgG = g;
        bgB = b;
    }

} // extern "C"
