import sys
import ctypes
import random
import math
from PyQt6 import QtWidgets, QtCore, QtGui

# Загрузка DLL
renderer3d = ctypes.CDLL("./renderer3d.dll")

# Определение типов функций (только те, что доступны в текущей DLL)
renderer3d.InitRenderer3D.argtypes = [ctypes.c_int, ctypes.c_int]
renderer3d.RenderFrame.restype = None
renderer3d.AddCube.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]

# Проверяем доступные функции
available_functions = []
functions_to_check = [
    "CloseRenderer3D", "IsRunning", "RotateCamera", "MoveCamera", "ZoomCamera",
    "ClearScene", "ResetCamera", "GetObjectCount", "SetBackgroundColor"
]

for func_name in functions_to_check:
    try:
        func = getattr(renderer3d, func_name)
        available_functions.append(func_name)
    except AttributeError:
        pass

# Настройка доступных функций
has_camera_controls = "RotateCamera" in available_functions
has_move_camera = "MoveCamera" in available_functions
has_zoom_camera = "ZoomCamera" in available_functions
has_clear_scene = "ClearScene" in available_functions
has_reset_camera = "ResetCamera" in available_functions
has_object_count = "GetObjectCount" in available_functions
has_background_color = "SetBackgroundColor" in available_functions

# Общая проверка на расширенные функции
has_extended_functions = has_background_color and has_object_count and has_reset_camera

print(f"✅ Доступно функций: {len(available_functions)}")
print(f"🎮 Управление камерой: {'✅' if has_camera_controls else '❌'}")
print(f"🔧 Расширенные функции: {'✅' if has_extended_functions else '❌'}")
print(f"📋 Доступные функции: {', '.join(available_functions)}")

if "RotateCamera" in available_functions:
    renderer3d.RotateCamera.argtypes = [ctypes.c_float, ctypes.c_float]

if "MoveCamera" in available_functions:
    renderer3d.MoveCamera.argtypes = [ctypes.c_float, ctypes.c_float]

if "ZoomCamera" in available_functions:
    renderer3d.ZoomCamera.argtypes = [ctypes.c_float]

if "ClearScene" in available_functions:
    renderer3d.ClearScene.argtypes = []

if "IsRunning" in available_functions:
    renderer3d.IsRunning.restype = ctypes.c_bool

if "CloseRenderer3D" in available_functions:
    renderer3d.CloseRenderer3D.restype = None

if "GetObjectCount" in available_functions:
    renderer3d.GetObjectCount.restype = ctypes.c_int

if "SetBackgroundColor" in available_functions:
    renderer3d.SetBackgroundColor.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]

class SDLWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NativeWindow)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_PaintOnScreen)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(16)  # ~60 FPS
        
        self.object_count = 0  # Локальный счетчик
        self.is_initialized = False  # Флаг инициализации
        
        # УБИРАЕМ переменные для управления мышью - теперь DLL сам всё делает!
        # self.left_mouse_pressed = False    
        # self.middle_mouse_pressed = False  
        # self.last_mouse_pos = None
        self.setMouseTracking(True)  # Включаем отслеживание мыши для DLL
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        
        # Делаем виджет фокусируемым
        self.setAcceptDrops(False)

    def resizeEvent(self, event):
        """Обработка изменения размера виджета"""
        super().resizeEvent(event)
        
        # Простое решение: перезапускаем весь рендерер только если сильно изменился размер
        if self.is_initialized:
            old_size = event.oldSize()
            new_size = event.size()
            
            # Проверяем, если изменение размера критичное
            if (abs(new_size.width() - old_size.width()) > 100 or 
                abs(new_size.height() - old_size.height()) > 100):
                
                try:
                    # Останавливаем таймер
                    self.timer.stop()
                    
                    # Переинициализируем рендерер
                    renderer3d.InitRenderer3D(new_size.width(), new_size.height())
                    renderer3d.AddCube(0.0, 0.0, -10.0, 1.0)
                    
                    # Перезапускаем таймер
                    self.timer.start(16)
                    
                except Exception as e:
                    print(f"Ошибка при изменении размера: {e}")
                    # Если не получается, просто продолжаем с текущими настройками

    def enterEvent(self, event):
        """Получаем фокус при наведении мыши"""
        self.setFocus()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Сбрасываем состояние при уходе мыши"""
        # DLL сам управляет состоянием кнопок мыши
        pass

    def showEvent(self, event):
        if not self.is_initialized:
            size = self.size()
            renderer3d.InitRenderer3D(size.width(), size.height())
            
            # Добавим начальную сцену - отодвигаем куб дальше от камеры
            try:
                renderer3d.AddCube(0.0, 0.0, -10.0, 1.0)
                self.object_count += 1
                print(f"✅ Начальный куб добавлен! Позиция: (0, 0, -10), размер: 1.0")
            except Exception as e:
                print(f"❌ Ошибка добавления начального куба: {e}")
            
            self.is_initialized = True

    def mousePressEvent(self, event):
        """Обработка нажатия мыши - ОТКЛЮЧЕНА, так как DLL сам обрабатывает мышь"""
        # Устанавливаем фокус на этот виджет для колесика мыши
        self.setFocus()
        # Больше НЕ обрабатываем мышь в Python - пусть DLL делает всё сам!

    def mouseMoveEvent(self, event):
        """Обработка движения мыши - ОТКЛЮЧЕНА, так как DLL сам обрабатывает мышь"""
        # ВАЖНО: НЕ вызываем RotateCamera из Python!
        # DLL теперь сам обрабатывает SDL события мыши в handleCameraInput()
        pass

    def mouseReleaseEvent(self, event):
        """Обработка отпускания мыши - ОТКЛЮЧЕНА, так как DLL сам обрабатывает мышь"""
        # DLL сам управляет состоянием кнопок мыши
        pass

    def wheelEvent(self, event):
        """Обработка колесика мыши для зума"""
        if has_zoom_camera:
            try:
                # Получаем направление прокрутки
                delta = event.angleDelta().y()
                # ИНВЕРТИРОВАННЫЕ ЗНАЧЕНИЯ: DLL работает наоборот
                # Скролл вверх (delta > 0) = приближение = отрицательный zoom_factor
                zoom_factor = -0.3 if delta > 0 else 0.3
                renderer3d.ZoomCamera(zoom_factor)
            except Exception as e:
                print(f"❌ Ошибка зума: {e}")

    def update_frame(self):
        try:
            if "IsRunning" in available_functions and not renderer3d.IsRunning():
                self.timer.stop()
                if "CloseRenderer3D" in available_functions:
                    renderer3d.CloseRenderer3D()
                QtWidgets.QApplication.quit()
            else:
                renderer3d.RenderFrame()
        except:
            # Если произошла ошибка, просто продолжаем рендерить
            try:
                renderer3d.RenderFrame()
            except:
                pass  # Игнорируем ошибки рендеринга

    def paintEngine(self):
        return None

class MainControlPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.object_count = 1
        self.init_ui()
        
    def init_ui(self):
        # Основной layout на всё окно
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # === 3D ОБЛАСТЬ СЛЕВА ===
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок над 3D областью
        title = QtWidgets.QLabel("🎮 3D Рендерер")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px; 
                font-weight: bold; 
                color: #2c3e50;
                padding: 15px;
                background-color: #ecf0f1;
                border-radius: 8px;
                border: 2px solid #bdc3c7;
            }
        """)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title)
        
        # 3D виджет
        self.sdl_widget = SDLWidget()
        self.sdl_widget.setMinimumSize(800, 600)
        self.sdl_widget.setStyleSheet("""
            QWidget {
                border: 2px solid #34495e;
                border-radius: 8px;
                background-color: #000000;
            }
        """)
        left_layout.addWidget(self.sdl_widget)
        
        main_layout.addWidget(left_panel, 3)
        
        # === ПАНЕЛЬ УПРАВЛЕНИЯ СПРАВА ===
        right_panel = QtWidgets.QWidget()
        right_panel.setFixedWidth(350)
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        right_layout.setSpacing(20)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # === СЧЕТЧИК ОБЪЕКТОВ ===
        self.object_count_label = QtWidgets.QLabel("Объектов в сцене: 1")
        self.object_count_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
                background-color: #3498db;
                padding: 12px;
                border-radius: 6px;
                text-align: center;
            }
        """)
        self.object_count_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.object_count_label)
        
        # === КНОПКИ УПРАВЛЕНИЯ ===
        buttons_group = QtWidgets.QGroupBox("Управление объектами")
        buttons_layout = QtWidgets.QVBoxLayout(buttons_group)
        buttons_layout.setSpacing(10)
        
        # Кнопки в сетке 2x2
        buttons_grid = QtWidgets.QGridLayout()
        buttons_grid.setSpacing(10)
        
        btn_cube = QtWidgets.QPushButton("📦 Добавить куб")
        btn_cube.clicked.connect(self.add_cube)
        btn_cube.setStyleSheet(self.get_clean_button_style("#e74c3c"))
        buttons_grid.addWidget(btn_cube, 0, 0)
        
        btn_random_cube = QtWidgets.QPushButton("🎲 Случайный куб")
        btn_random_cube.clicked.connect(self.add_random_cube)
        btn_random_cube.setStyleSheet(self.get_clean_button_style("#f39c12"))
        buttons_grid.addWidget(btn_random_cube, 0, 1)
        
        btn_cube_line = QtWidgets.QPushButton("📏 Линия кубов")
        btn_cube_line.clicked.connect(self.add_cube_line)
        btn_cube_line.setStyleSheet(self.get_clean_button_style("#9b59b6"))
        buttons_grid.addWidget(btn_cube_line, 1, 0)
        
        btn_cube_circle = QtWidgets.QPushButton("🔵 Круг кубов")
        btn_cube_circle.clicked.connect(self.add_cube_circle)
        btn_cube_circle.setStyleSheet(self.get_clean_button_style("#1abc9c"))
        buttons_grid.addWidget(btn_cube_circle, 1, 1)
        
        btn_demo_scene = QtWidgets.QPushButton("✨ Демо сцена")
        btn_demo_scene.clicked.connect(self.create_demo_scene)
        btn_demo_scene.setStyleSheet(self.get_clean_button_style("#27ae60"))
        buttons_grid.addWidget(btn_demo_scene, 2, 0)
        
        btn_clear = QtWidgets.QPushButton("🗑️ Очистить всё")
        btn_clear.clicked.connect(self.clear_scene)
        btn_clear.setStyleSheet(self.get_clean_button_style("#e67e22"))
        buttons_grid.addWidget(btn_clear, 2, 1)
        
        # Кнопка сброса камеры (если доступна)
        if has_reset_camera:
            btn_reset_camera = QtWidgets.QPushButton("🔄 Сбросить камеру")
            btn_reset_camera.clicked.connect(self.reset_camera)
            btn_reset_camera.setStyleSheet(self.get_clean_button_style("#3498db"))
            buttons_grid.addWidget(btn_reset_camera, 3, 0, 1, 2)  # На всю ширину
        
        # СЕКРЕТНАЯ КНОПКА КАЗИНО
        btn_secret_casino = QtWidgets.QPushButton("🎰 Секретное казино")
        btn_secret_casino.clicked.connect(self.open_casino)
        btn_secret_casino.setStyleSheet(self.get_clean_button_style("#8e44ad"))
        buttons_grid.addWidget(btn_secret_casino, 4, 0, 1, 2)  # На всю ширину
        
        buttons_layout.addLayout(buttons_grid)
        right_layout.addWidget(buttons_group)
        
        # === НАСТРОЙКИ ===
        settings_group = QtWidgets.QGroupBox("Настройки объектов")
        settings_layout = QtWidgets.QFormLayout(settings_group)
        settings_layout.setSpacing(10)
        
        # Размер
        self.size_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.size_slider.setRange(10, 300)
        self.size_slider.setValue(100)
        self.size_label = QtWidgets.QLabel("1.0")
        self.size_slider.valueChanged.connect(lambda v: self.size_label.setText(f"{v/100:.1f}"))
        
        size_layout = QtWidgets.QHBoxLayout()
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_label)
        settings_layout.addRow("Размер:", size_layout)
        
        # Позиция X
        self.pos_x_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.pos_x_slider.setRange(-500, 500)
        self.pos_x_slider.setValue(0)
        self.pos_x_label = QtWidgets.QLabel("0.0")
        self.pos_x_slider.valueChanged.connect(lambda v: self.pos_x_label.setText(f"{v/100:.1f}"))
        
        pos_x_layout = QtWidgets.QHBoxLayout()
        pos_x_layout.addWidget(self.pos_x_slider)
        pos_x_layout.addWidget(self.pos_x_label)
        settings_layout.addRow("Позиция X:", pos_x_layout)
        
        # Позиция Y
        self.pos_y_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.pos_y_slider.setRange(-500, 500)
        self.pos_y_slider.setValue(0)
        self.pos_y_label = QtWidgets.QLabel("0.0")
        self.pos_y_slider.valueChanged.connect(lambda v: self.pos_y_label.setText(f"{v/100:.1f}"))
        
        pos_y_layout = QtWidgets.QHBoxLayout()
        pos_y_layout.addWidget(self.pos_y_slider)
        pos_y_layout.addWidget(self.pos_y_label)
        settings_layout.addRow("Позиция Y:", pos_y_layout)
        
        # Позиция Z
        self.pos_z_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.pos_z_slider.setRange(-2000, -200)
        self.pos_z_slider.setValue(-1000)
        self.pos_z_label = QtWidgets.QLabel("-10.0")
        self.pos_z_slider.valueChanged.connect(lambda v: self.pos_z_label.setText(f"{v/100:.1f}"))
        
        pos_z_layout = QtWidgets.QHBoxLayout()
        pos_z_layout.addWidget(self.pos_z_slider)
        pos_z_layout.addWidget(self.pos_z_label)
        settings_layout.addRow("Позиция Z:", pos_z_layout)
        
        right_layout.addWidget(settings_group)
        
        # === ИНФОРМАЦИЯ ===
        info_group = QtWidgets.QGroupBox("Управление")
        info_layout = QtWidgets.QVBoxLayout(info_group)
        
        info_text = QtWidgets.QLabel(
            "Управление мышью в 3D области:\n\n"
            "• ЛКМ + движение = орбитальное вращение камеры\n"
            "• СКМ + движение = панорамирование (перемещение центра обзора)\n"
            "• Колесо мыши = приближение/отдаление\n\n"
            "✨ Новая орбитальная камера!\n"
            "Камера теперь вращается вокруг центра сцены."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 6px;
                border: 1px solid #dee2e6;
            }
        """)
        info_layout.addWidget(info_text)
        
        right_layout.addWidget(info_group)
        right_layout.addStretch()  # Добавляем растяжение внизу
        
        main_layout.addWidget(right_panel, 1)
        
        # Настройка общих стилей
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 15px;
                background-color: #34495e;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QSlider::groove:horizontal {
                border: none;
                height: 8px;
                background-color: #ecf0f1;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background-color: #3498db;
                border: none;
                width: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            QSlider::handle:horizontal:hover {
                background-color: #2980b9;
            }
            QLabel {
                color: #2c3e50;
                font-size: 13px;
            }
        """)

    def get_clean_button_style(self, color):
        """Возвращает чистый стиль для кнопок"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-radius: 6px;
                padding: 12px;
                min-height: 25px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
            }}
        """

    def darken_color(self, hex_color, factor=0.9):
        """Затемняет цвет для hover эффекта"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"

    def get_current_position(self):
        x = self.pos_x_slider.value() / 100.0
        y = self.pos_y_slider.value() / 100.0
        z = self.pos_z_slider.value() / 100.0
        return x, y, z
    
    def get_current_size(self):
        return self.size_slider.value() / 100.0
    
    def add_cube(self):
        x, y, z = self.get_current_position()
        size = self.get_current_size()
        try:
            renderer3d.AddCube(x, y, z, size)
            self.object_count += 1
            self.update_object_count()
            print(f"✅ Куб добавлен! Позиция: ({x:.1f}, {y:.1f}, {z:.1f}), размер: {size:.1f}")
        except Exception as e:
            print(f"❌ Ошибка добавления куба: {e}")
    
    def add_random_cube(self):
        x = random.uniform(-5, 5)
        y = random.uniform(-3, 3)
        z = random.uniform(-15, -8)
        size = random.uniform(0.3, 1.5)
        try:
            renderer3d.AddCube(x, y, z, size)
            self.object_count += 1
            self.update_object_count()
            print(f"✅ Случайный куб добавлен! Позиция: ({x:.1f}, {y:.1f}, {z:.1f}), размер: {size:.1f}")
        except Exception as e:
            print(f"❌ Ошибка добавления случайного куба: {e}")
    
    def add_cube_line(self):
        for i in range(5):
            x = (i - 2) * 1.5
            y = 0
            z = -10
            size = 0.5
            renderer3d.AddCube(x, y, z, size)
            self.object_count += 1
        self.update_object_count()
    
    def add_cube_circle(self):
        radius = 3.0
        num_cubes = 8
        for i in range(num_cubes):
            angle = (i / num_cubes) * 2 * math.pi
            x = math.cos(angle) * radius
            z = math.sin(angle) * radius - 10
            y = 0
            size = 0.4
            renderer3d.AddCube(x, y, z, size)
            self.object_count += 1
        self.update_object_count()
    
    def clear_scene(self):
        if has_clear_scene:
            renderer3d.ClearScene()
            self.object_count = 0
            self.update_object_count()
        else:
            reply = QtWidgets.QMessageBox.question(
                self, 'Очистка сцены', 
                'Очистить сцену? (Приложение будет перезапущено)\n\n'
                'В текущей версии DLL нет функции очистки.',
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                QtWidgets.QApplication.quit()
    
    def update_object_count(self):
        if has_object_count:
            try:
                count = renderer3d.GetObjectCount()
                self.object_count_label.setText(f"Объектов в сцене: {count}")
            except:
                self.object_count_label.setText(f"Объектов в сцене: {self.object_count}")
        else:
            self.object_count_label.setText(f"Объектов в сцене: {self.object_count}")
    
    def create_demo_scene(self):
        # Создаем красивую демо-сцену
        initial_count = self.object_count
        
        # Центральный большой куб
        renderer3d.AddCube(0, 0, -12, 1.5)
        self.object_count += 1
        
        # Малые кубы вокруг
        for i in range(4):
            angle = (i / 4) * 2 * math.pi
            x = math.cos(angle) * 3.5
            z = math.sin(angle) * 3.5 - 12
            renderer3d.AddCube(x, 0, z, 0.5)
            self.object_count += 1
        
        # Башня кубов
        for i in range(5):
            renderer3d.AddCube(4, i * 1.2 - 2, -15, 0.6)
            self.object_count += 1
        
        # Случайные кубы
        for _ in range(10):
            x = random.uniform(-8, 8)
            y = random.uniform(-3, 3)
            z = random.uniform(-20, -8)
            size = random.uniform(0.2, 0.8)
            renderer3d.AddCube(x, y, z, size)
            self.object_count += 1
        
        self.update_object_count()

    def reset_camera(self):
        if has_reset_camera:
            try:
                renderer3d.ResetCamera()
                print("📷 Камера сброшена в исходное положение")
            except Exception as e:
                print(f"❌ Ошибка сброса камеры: {e}")
        else:
            print("⚠️ Функция ResetCamera недоступна в текущей DLL")

    def open_casino(self):
        """Открывает окно секретного казино"""
        casino_window = SlotMachineWindow(self)
        casino_window.exec()

class SlotMachineWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎰 Казино 3D Рендерера")
        self.setFixedSize(400, 380)  # Увеличил высоту для кнопки блэкджека
        self.coins = 100  # Устанавливаем монеты ПЕРЕД инициализацией UI
        
        # Для анимации
        self.animation_timer = QtCore.QTimer()
        self.animation_timer.timeout.connect(self.animate_reels)
        self.animation_counter = 0
        self.final_result = []
        self.symbols = ["🍒", "🍋", "🍊", "🍇", "💎", "⭐", "🎯", "🔥"]
        
        self.init_ui()
        
    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Заголовок
        title = QtWidgets.QLabel("🎰 Слот Машина")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                background-color: #3498db;
                padding: 10px;
                border-radius: 6px;
                text-align: center;
            }
        """)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Счетчик монет
        self.coins_label = QtWidgets.QLabel(f"💰 Монеты: {self.coins}")
        self.coins_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: white;
                background-color: #27ae60;
                padding: 8px;
                border-radius: 4px;
                text-align: center;
            }
        """)
        self.coins_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.coins_label)
        
        # Барабаны - компактно
        reels_layout = QtWidgets.QHBoxLayout()
        reels_layout.setSpacing(8)
        
        self.reels = []
        
        for i in range(3):
            reel = QtWidgets.QLabel("🎲")
            reel.setStyleSheet("""
                QLabel {
                    font-size: 32px;
                    background-color: white;
                    border: 2px solid #34495e;
                    border-radius: 6px;
                    padding: 8px;
                    text-align: center;
                    min-width: 60px;
                    max-width: 60px;
                    min-height: 60px;
                    max-height: 60px;
                }
            """)
            reel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.reels.append(reel)
            reels_layout.addWidget(reel)
        
        layout.addLayout(reels_layout)
        
        # Кнопка КРУТИТЬ
        self.spin_button = QtWidgets.QPushButton("🎰 Крутить! (10 монет)")
        self.spin_button.clicked.connect(self.spin_reels)
        self.spin_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 6px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        layout.addWidget(self.spin_button)
        
        # Результат
        self.result_label = QtWidgets.QLabel("Добро пожаловать в казино!")
        self.result_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #ecf0f1;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #bdc3c7;
                text-align: center;
            }
        """)
        self.result_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)
        
        # Кнопка перехода к блэкджеку
        blackjack_button = QtWidgets.QPushButton("🃏 Играть в Блэкджек")
        blackjack_button.clicked.connect(self.open_blackjack)
        blackjack_button.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
        """)
        layout.addWidget(blackjack_button)
        
        # Кнопка закрыть
        close_button = QtWidgets.QPushButton("❌ Закрыть")
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        layout.addWidget(close_button)
        
        # Общий стиль окна
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
    
    def spin_reels(self):
        if self.coins < 10:
            self.result_label.setText("❌ Недостаточно монет!")
            self.result_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: white;
                    background-color: #e74c3c;
                    padding: 8px;
                    border-radius: 4px;
                    text-align: center;
                }
            """)
            return
            
        self.coins -= 10
        self.update_coins_display()
        
        # Отключаем кнопку во время анимации
        self.spin_button.setEnabled(False)
        self.result_label.setText("🎰 Крутим...")
        self.result_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f39c12;
                padding: 8px;
                border-radius: 4px;
                text-align: center;
            }
        """)
        
        # Генерируем финальный результат
        self.final_result = [random.choice(self.symbols) for _ in range(3)]
        
        # Запускаем анимацию
        self.animation_counter = 0
        self.animation_timer.start(100)  # Обновляем каждые 100мс
        
    def animate_reels(self):
        """Анимация кручения барабанов"""
        # Показываем случайные символы во время анимации
        for i, reel in enumerate(self.reels):
            # Первые 20 итераций - быстрая смена символов
            if self.animation_counter < 20:
                reel.setText(random.choice(self.symbols))
                # Добавляем эффект "кручения" - меняем стиль
                reel.setStyleSheet("""
                    QLabel {
                        font-size: 32px;
                        background-color: #f39c12;
                        border: 3px solid #e67e22;
                        border-radius: 6px;
                        padding: 8px;
                        text-align: center;
                        min-width: 60px;
                        max-width: 60px;
                        min-height: 60px;
                        max-height: 60px;
                    }
                """)
            # Барабаны останавливаются по очереди
            elif self.animation_counter == 20 + i * 5:
                reel.setText(self.final_result[i])
                # Возвращаем обычный стиль
                reel.setStyleSheet("""
                    QLabel {
                        font-size: 32px;
                        background-color: white;
                        border: 2px solid #27ae60;
                        border-radius: 6px;
                        padding: 8px;
                        text-align: center;
                        min-width: 60px;
                        max-width: 60px;
                        min-height: 60px;
                        max-height: 60px;
                    }
                """)
        
        self.animation_counter += 1
        
        # Останавливаем анимацию после того как все барабаны остановились
        if self.animation_counter >= 35:  # 20 + 3*5 = 35
            self.animation_timer.stop()
            self.finish_spin()
    
    def finish_spin(self):
        """Завершаем спин и показываем результат"""
        # Проверяем выигрыш
        winnings = self.check_winnings(self.final_result)
        self.coins += winnings
        self.update_coins_display()
        
        # Возвращаем обычный стиль барабанам
        for reel in self.reels:
            reel.setStyleSheet("""
                QLabel {
                    font-size: 32px;
                    background-color: white;
                    border: 2px solid #34495e;
                    border-radius: 6px;
                    padding: 8px;
                    text-align: center;
                    min-width: 60px;
                    max-width: 60px;
                    min-height: 60px;
                    max-height: 60px;
                }
            """)
        
        if winnings > 0:
            self.result_label.setText(f"🎉 Выиграли {winnings} монет! 🎉")
            self.result_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: white;
                    background-color: #27ae60;
                    padding: 8px;
                    border-radius: 4px;
                    text-align: center;
                }
            """)
            
            # Анимация выигрыша - мигание барабанов
            QtCore.QTimer.singleShot(500, self.flash_winning_reels)
        else:
            self.result_label.setText("😢 В этот раз не повезло...")
            self.result_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: #2c3e50;
                    background-color: #ecf0f1;
                    padding: 8px;
                    border-radius: 4px;
                    border: 1px solid #bdc3c7;
                    text-align: center;
                }
            """)
            
        # Включаем кнопку обратно
        self.spin_button.setEnabled(True)
    
    def flash_winning_reels(self):
        """Мигание барабанов при выигрыше"""
        for reel in self.reels:
            reel.setStyleSheet("""
                QLabel {
                    font-size: 32px;
                    background-color: #f1c40f;
                    border: 3px solid #f39c12;
                    border-radius: 6px;
                    padding: 8px;
                    text-align: center;
                    min-width: 60px;
                    max-width: 60px;
                    min-height: 60px;
                    max-height: 60px;
                }
            """)
        
        # Возвращаем обычный стиль через полсекунды
        QtCore.QTimer.singleShot(500, lambda: self.restore_normal_reels())
    
    def restore_normal_reels(self):
        """Возвращаем обычный стиль барабанам"""
        for reel in self.reels:
            reel.setStyleSheet("""
                QLabel {
                    font-size: 32px;
                    background-color: white;
                    border: 2px solid #34495e;
                    border-radius: 6px;
                    padding: 8px;
                    text-align: center;
                    min-width: 60px;
                    max-width: 60px;
                    min-height: 60px;
                    max-height: 60px;
                }
            """)
        
    def check_winnings(self, result):
        """Проверяет выигрышные комбинации"""
        # Джекпот - все символы одинаковые
        if result[0] == result[1] == result[2]:
            if result[0] == "💎":
                return 1000  # Джекпот бриллианты
            elif result[0] == "⭐":
                return 500   # Звезды
            elif result[0] == "🔥":
                return 300   # Огонь
            else:
                return 100   # Другие тройки
                
        # Пара символов
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            if "💎" in result:
                return 50
            elif "⭐" in result:
                return 30
            else:
                return 20
                
        return 0
        
    def update_coins_display(self):
        self.coins_label.setText(f"💰 Монеты: {self.coins}")
        if self.coins < 10:
            self.coins_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: white;
                    background-color: #e74c3c;
                    padding: 8px;
                    border-radius: 4px;
                    text-align: center;
                }
            """)
        else:
            self.coins_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: white;
                    background-color: #27ae60;
                    padding: 8px;
                    border-radius: 4px;
                    text-align: center;
                }
            """)

    def open_blackjack(self):
        """Открывает игру в блэкджек с текущими монетами"""
        blackjack_window = BlackjackWindow(self, self.coins)
        result = blackjack_window.exec()
        if result:
            # Обновляем монеты после игры в блэкджек
            self.coins = blackjack_window.coins
            self.update_coins_display()

class BlackjackWindow(QtWidgets.QDialog):
    def __init__(self, parent=None, coins=100):
        super().__init__(parent)
        self.setWindowTitle("🃏 Блэкджек")
        self.setFixedSize(500, 600)
        self.coins = coins
        self.bet = 0
        self.player_cards = []
        self.dealer_cards = []
        self.game_in_progress = False
        self.dealer_hidden = True
        
        # Колода карт
        self.deck = self.create_deck()
        random.shuffle(self.deck)
        
        self.init_ui()
        
    def create_deck(self):
        """Создает колоду карт"""
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = []
        for suit in suits:
            for rank in ranks:
                deck.append(f"{rank}{suit}")
        return deck
        
    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Заголовок
        title = QtWidgets.QLabel("🃏 Блэкджек")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                background-color: #2c3e50;
                padding: 10px;
                border-radius: 6px;
                text-align: center;
            }
        """)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Счетчик монет
        self.coins_label = QtWidgets.QLabel(f"💰 Монеты: {self.coins}")
        self.coins_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: white;
                background-color: #27ae60;
                padding: 8px;
                border-radius: 4px;
                text-align: center;
            }
        """)
        self.coins_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.coins_label)
        
        # Ставка
        bet_layout = QtWidgets.QHBoxLayout()
        bet_label = QtWidgets.QLabel("Ставка:")
        bet_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        bet_layout.addWidget(bet_label)
        
        self.bet_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.bet_slider.setRange(10, min(100, self.coins))
        self.bet_slider.setValue(10)
        self.bet_value_label = QtWidgets.QLabel("10")
        self.bet_slider.valueChanged.connect(lambda v: self.bet_value_label.setText(str(v)))
        
        bet_layout.addWidget(self.bet_slider)
        bet_layout.addWidget(self.bet_value_label)
        layout.addLayout(bet_layout)
        
        # Карты дилера
        dealer_label = QtWidgets.QLabel("🎩 Дилер:")
        dealer_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #e74c3c;")
        layout.addWidget(dealer_label)
        
        self.dealer_cards_label = QtWidgets.QLabel("🂠 🂠")
        self.dealer_cards_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                background-color: #2c3e50;
                color: white;
                padding: 10px;
                border-radius: 6px;
                text-align: center;
                min-height: 40px;
            }
        """)
        self.dealer_cards_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.dealer_cards_label)
        
        self.dealer_score_label = QtWidgets.QLabel("Очки: ?")
        self.dealer_score_label.setStyleSheet("font-weight: bold; text-align: center;")
        self.dealer_score_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.dealer_score_label)
        
        # Карты игрока
        player_label = QtWidgets.QLabel("👤 Ваши карты:")
        player_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #3498db;")
        layout.addWidget(player_label)
        
        self.player_cards_label = QtWidgets.QLabel("🂠 🂠")
        self.player_cards_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                background-color: #3498db;
                color: white;
                padding: 10px;
                border-radius: 6px;
                text-align: center;
                min-height: 40px;
            }
        """)
        self.player_cards_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.player_cards_label)
        
        self.player_score_label = QtWidgets.QLabel("Очки: 0")
        self.player_score_label.setStyleSheet("font-weight: bold; text-align: center;")
        self.player_score_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.player_score_label)
        
        # Кнопки управления игрой
        game_buttons_layout = QtWidgets.QHBoxLayout()
        
        self.start_button = QtWidgets.QPushButton("🎮 Начать игру")
        self.start_button.clicked.connect(self.start_game)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        game_buttons_layout.addWidget(self.start_button)
        
        self.hit_button = QtWidgets.QPushButton("🃏 Еще карту")
        self.hit_button.clicked.connect(self.hit)
        self.hit_button.setEnabled(False)
        self.hit_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        game_buttons_layout.addWidget(self.hit_button)
        
        self.stand_button = QtWidgets.QPushButton("🛑 Остановиться")
        self.stand_button.clicked.connect(self.stand)
        self.stand_button.setEnabled(False)
        self.stand_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        game_buttons_layout.addWidget(self.stand_button)
        
        layout.addLayout(game_buttons_layout)
        
        # Результат игры
        self.result_label = QtWidgets.QLabel("Сделайте ставку и начните игру!")
        self.result_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #ecf0f1;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #bdc3c7;
                text-align: center;
            }
        """)
        self.result_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)
        
        # Кнопка закрыть
        close_button = QtWidgets.QPushButton("❌ Назад к слотам")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        layout.addWidget(close_button)
        
        # Общий стиль окна
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
    def start_game(self):
        """Начинает новую игру"""
        if self.coins < 10:
            self.result_label.setText("❌ Недостаточно монет для игры!")
            return
            
        self.bet = self.bet_slider.value()
        if self.bet > self.coins:
            self.result_label.setText("❌ Ставка больше доступных монет!")
            return
            
        self.coins -= self.bet
        self.update_coins_display()
        
        # Сброс игры
        self.player_cards = []
        self.dealer_cards = []
        self.game_in_progress = True
        self.dealer_hidden = True
        
        # Раздача карт
        self.player_cards.append(self.deal_card())
        self.dealer_cards.append(self.deal_card())
        self.player_cards.append(self.deal_card())
        self.dealer_cards.append(self.deal_card())
        
        self.update_display()
        
        # Проверка на блэкджек
        if self.calculate_score(self.player_cards) == 21:
            self.dealer_hidden = False
            self.update_display()
            if self.calculate_score(self.dealer_cards) == 21:
                self.end_game("🟡 Ничья! Блэкджек у обоих!", self.bet)
            else:
                self.end_game("🎉 БЛЭКДЖЕК! Вы выиграли!", int(self.bet * 2.5))
            return
            
        # Активируем кнопки
        self.start_button.setEnabled(False)
        self.hit_button.setEnabled(True)
        self.stand_button.setEnabled(True)
        
        self.result_label.setText(f"💰 Ставка: {self.bet} монет. Ваш ход!")
        
    def deal_card(self):
        """Раздает карту из колоды"""
        if len(self.deck) < 10:
            self.deck = self.create_deck()
            random.shuffle(self.deck)
        return self.deck.pop()
        
    def calculate_score(self, cards):
        """Подсчитывает очки руки"""
        score = 0
        aces = 0
        
        for card in cards:
            rank = card[:-1]  # Убираем масть
            if rank in ['J', 'Q', 'K']:
                score += 10
            elif rank == 'A':
                aces += 1
                score += 11
            else:
                score += int(rank)
        
        # Обработка тузов
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
            
        return score
        
    def update_display(self):
        """Обновляет отображение карт и очков"""
        # Карты игрока
        player_display = " ".join(self.player_cards)
        self.player_cards_label.setText(player_display)
        player_score = self.calculate_score(self.player_cards)
        self.player_score_label.setText(f"Очки: {player_score}")
        
        # Карты дилера
        if self.dealer_hidden and len(self.dealer_cards) > 0:
            dealer_display = f"🂠 {self.dealer_cards[1] if len(self.dealer_cards) > 1 else ''}"
            self.dealer_score_label.setText("Очки: ?")
        else:
            dealer_display = " ".join(self.dealer_cards)
            dealer_score = self.calculate_score(self.dealer_cards)
            self.dealer_score_label.setText(f"Очки: {dealer_score}")
            
        self.dealer_cards_label.setText(dealer_display)
        
    def hit(self):
        """Игрок берет еще карту"""
        self.player_cards.append(self.deal_card())
        self.update_display()
        
        player_score = self.calculate_score(self.player_cards)
        if player_score > 21:
            self.end_game("💥 Перебор! Вы проиграли!", 0)
        elif player_score == 21:
            self.stand()  # Автоматически останавливаемся при 21
            
    def stand(self):
        """Игрок останавливается, ход дилера"""
        self.dealer_hidden = False
        self.hit_button.setEnabled(False)
        self.stand_button.setEnabled(False)
        
        # Дилер добирает карты
        while self.calculate_score(self.dealer_cards) < 17:
            self.dealer_cards.append(self.deal_card())
            
        self.update_display()
        
        # Определяем победителя
        player_score = self.calculate_score(self.player_cards)
        dealer_score = self.calculate_score(self.dealer_cards)
        
        if dealer_score > 21:
            self.end_game("🎉 Дилер перебрал! Вы выиграли!", self.bet * 2)
        elif dealer_score > player_score:
            self.end_game("😞 Дилер выиграл!", 0)
        elif player_score > dealer_score:
            self.end_game("🎉 Вы выиграли!", self.bet * 2)
        else:
            self.end_game("🟡 Ничья!", self.bet)
            
    def end_game(self, message, winnings):
        """Завершает игру"""
        self.game_in_progress = False
        self.coins += winnings
        self.update_coins_display()
        
        self.result_label.setText(message)
        if winnings > 0:
            self.result_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: white;
                    background-color: #27ae60;
                    padding: 10px;
                    border-radius: 6px;
                    text-align: center;
                }
            """)
        else:
            self.result_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: white;
                    background-color: #e74c3c;
                    padding: 10px;
                    border-radius: 6px;
                    text-align: center;
                }
            """)
            
        # Активируем кнопку новой игры
        self.start_button.setEnabled(True)
        self.hit_button.setEnabled(False)
        self.stand_button.setEnabled(False)
        
        # Обновляем слайдер ставок
        self.bet_slider.setMaximum(min(100, self.coins))
        
    def update_coins_display(self):
        """Обновляет отображение монет"""
        self.coins_label.setText(f"💰 Монеты: {self.coins}")
        if self.coins < 10:
            self.coins_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: white;
                    background-color: #e74c3c;
                    padding: 8px;
                    border-radius: 4px;
                    text-align: center;
                }
            """)
        else:
            self.coins_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: white;
                    background-color: #27ae60;
                    padding: 8px;
                    border-radius: 4px;
                    text-align: center;
                }
            """)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎮 3D Рендерер v2.0 - Единая панель управления")
        self.setMinimumSize(1200, 800)
        self.setFixedSize(1200, 800)
        
        # Устанавливаем единую панель управления как центральный виджет
        self.control_panel = MainControlPanel()
        self.setCentralWidget(self.control_panel)
        
        # Статус бар
        self.status_bar = self.statusBar()
        status_msg = "🚀 3D Рендерер готов к работе! "
        if not has_camera_controls:
            status_msg += "⚠️ Управление камерой недоступно "
        if not (has_background_color and has_object_count and has_reset_camera):
            status_msg += "⚠️ Некоторые функции недоступны"
        self.status_bar.showMessage(status_msg)
        
        # Меню
        self.create_menu()
    
    def create_menu(self):
        menubar = self.menuBar()
        
        # Файл
        file_menu = menubar.addMenu('📁 Файл')
        
        exit_action = QtGui.QAction('🚪 Выход', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Помощь
        help_menu = menubar.addMenu('❓ Помощь')
        
        about_action = QtGui.QAction('ℹ️ О программе', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Инструменты
        tools_menu = menubar.addMenu('🔧 Инструменты')
        
        if not (has_background_color and has_object_count and has_reset_camera):
            compile_action = QtGui.QAction('⚙️ Перекомпилировать DLL', self)
            compile_action.triggered.connect(self.show_compile_info)
            tools_menu.addAction(compile_action)
    
    def show_about(self):
        QtWidgets.QMessageBox.about(
            self,
            "О программе",
            "🎮 3D Рендерер v2.0\n\n"
            "Единая панель управления!\n"
            "Всё в одном месте!\n\n"
            "Особенности:\n"
            f"• {'✅' if has_camera_controls else '❌'} Интуитивное управление камерой\n"
            "• ✅ Большие удобные кнопки\n"
            "• ✅ Настраиваемые параметры объектов\n"
            "• ✅ 3D область и управление в одном окне\n"
            f"• {'✅' if (has_background_color and has_object_count and has_reset_camera) else '❌'} Расширенные функции\n\n"
            "Технологии: C++, OpenGL, SDL2, PyQt6"
        )
    
    def show_compile_info(self):
        QtWidgets.QMessageBox.information(
            self,
            "Компиляция DLL",
            "🔧 Для получения всех функций необходимо:\n\n"
            "1. Открыть Visual Studio\n"
            "2. Загрузить проект из main/src/renderer3d/\n"
            "3. Скомпилировать проект\n"
            "4. Скопировать новую DLL в папку test/\n\n"
            "После этого все расширенные функции\n"
            "будут доступны!"
        )

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')  # Современный стиль
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec()) 