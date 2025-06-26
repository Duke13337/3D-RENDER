#pragma once

#ifdef __cplusplus
extern "C" {
#endif

// Макрос для экспорта функций из DLL на Windows
#ifdef _WIN32
    #ifdef RENDERER3D_EXPORTS
        #define RENDERER3D_API __declspec(dllexport)
    #else
        #define RENDERER3D_API __declspec(dllimport)
    #endif
#else
    #define RENDERER3D_API
#endif

	// Инициализация рендерера
	RENDERER3D_API void InitRenderer3D(int width, int height);

	// Рендеринг одного кадра
	RENDERER3D_API void RenderFrame();

	// Закрытие и очистка
	RENDERER3D_API void CloseRenderer3D();

	// Жив ли рендерер
	RENDERER3D_API bool IsRunning();

	// Добавить куб в сцену
	RENDERER3D_API void AddCube(float x, float y, float z, float size);

	// Управление камерой (можно вызывать из Python)
	RENDERER3D_API void RotateCamera(float dx, float dy);
	RENDERER3D_API void MoveCamera(float dx, float dy);
	RENDERER3D_API void ZoomCamera(float delta);

	// === НОВЫЕ ФУНКЦИИ ===
	// Очистить всю сцену от объектов
	RENDERER3D_API void ClearScene();

	// Сбросить камеру к начальным настройкам
	RENDERER3D_API void ResetCamera();

	// Получить количество объектов в сцене
	RENDERER3D_API int GetObjectCount();

	// Установить цвет фона
	RENDERER3D_API void SetBackgroundColor(float r, float g, float b);

#ifdef __cplusplus
}
#endif
