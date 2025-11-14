import pygame
import sys
import math
from pynput import mouse, keyboard
import threading
from typing import Set, Tuple, List
import os


class BongoCat:
    def __init__(self):
        # Инициализация Pygame
        pygame.init()

        # Настройки окна
        self.window_width = 612
        self.window_height = 354

        # Создаем окно поверх всех окон без рамки
        self.screen = pygame.display.set_mode((self.window_width, self.window_height),
                                              pygame.NOFRAME)
        pygame.display.set_caption("Bongo Cat Stream Overlay")

        # Прозрачное окно
        self.screen.set_colorkey((0, 0, 0))
        self.make_window_transparent()

        # Загрузка изображений
        self.load_images()

        # Углы коврика в перспективе (по часовой стрелке, начиная с левого верхнего)
        self.mat_corners = [
            (175, 316),  # Левый верхний (ближний к коту)
            (-8, 248),  # Левый нижний
            (74, 184),  # Правый нижний
            (266, 229)  # Правый верхний (ближний к коту)
        ]

        # Получаем разрешение экрана для масштабирования
        self.screen_width, self.screen_height = self.get_screen_resolution()

        # Состояния
        self.mouse_position = [400, 300]  # Начальная позиция мыши
        self.keys_pressed: Set = set()
        self.running = True

        # Настройки позиций
        self.background_pos = (0, 0)

        # Фиксированная позиция левой лапки (для клавиатуры)
        self.left_arm_pos = (20, 5)  # Подбери правильные координаты

        # Фиксированная позиция точки привязки правой лапки
        self.right_arm_anchor = (350, 250)  # Подбери правильные координаты

        # Запуск отслеживания ввода
        self.start_input_listeners()

        print("Bongo Cat запущен! Нажмите ESC для выхода.")
        print("Движение мыши ограничено областью коврика с учетом перспективы.")

    def get_screen_resolution(self):
        """Получает разрешение основного монитора"""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        except:
            return 1920, 1080

    def make_window_transparent(self):
        """Делает окно прозрачным и поверх всех окон"""
        try:
            if os.name == 'nt':
                import ctypes
                hwnd = pygame.display.get_wm_info()["window"]
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001)
        except:
            print("Не удалось установить окно поверх всех.")

    def load_images(self):
        """Загружает все изображения с проверкой"""
        try:
            self.background = pygame.image.load('images/mousebg.png').convert_alpha()
            print(f"Фон загружен: {self.background.get_size()}")

            # Проверяем каждое изображение отдельно
            try:
                self.left_arm = pygame.image.load('images/left.png').convert_alpha()
                print(f"Левая лапка (left.png) загружена: {self.left_arm.get_size()}")
            except Exception as e:
                print(f"Ошибка загрузки left.png: {e}")
                self.left_arm = None

            try:
                self.left_arm_up = pygame.image.load('images/up.png').convert_alpha()
                print(f"Поднятая лапка (up.png) загружена: {self.left_arm_up.get_size()}")
            except Exception as e:
                print(f"Ошибка загрузки up.png: {e}")
                self.left_arm_up = None

            try:
                self.right_arm = pygame.image.load('images/right.png').convert_alpha()
                print(f"Правая лапка (right.png) загружена: {self.right_arm.get_size()}")
            except Exception as e:
                print(f"Ошибка загрузки right.png: {e}")
                self.right_arm = None

            try:
                self.mouse_img = pygame.image.load('images/mouse.png').convert_alpha()
                print(f"Мышь (mouse.png) загружена: {self.mouse_img.get_size()}")
            except Exception as e:
                print(f"Ошибка загрузки mouse.png: {e}")
                self.mouse_img = None

        except Exception as e:
            print(f"Критическая ошибка загрузки изображений: {e}")
            sys.exit(1)

    def bilinear_interpolation(self, u: float, v: float, points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Билинейная интерполяция для преобразования координат в четырехугольнике"""
        x = (1 - u) * (1 - v) * points[0][0] + u * (1 - v) * points[1][0] + u * v * points[2][0] + (1 - u) * v * \
            points[3][0]
        y = (1 - u) * (1 - v) * points[0][1] + u * (1 - v) * points[1][1] + u * v * points[2][1] + (1 - u) * v * \
            points[3][1]
        return x, y

    def map_mouse_to_mat(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Преобразует реальные координаты мыши в координаты на коврике с учетом перспективы"""
        # Нормализуем координаты мыши от 0 до 1
        u = max(0, min(1, screen_x / self.screen_width))
        v = max(0, min(1, screen_y / self.screen_height))

        # Преобразуем в координаты на коврике с помощью билинейной интерполяции
        mat_x, mat_y = self.bilinear_interpolation(u, v, self.mat_corners)

        return int(mat_x), int(mat_y)

    def start_input_listeners(self):
        """Запускает потоки для отслеживания мыши и клавиатуры"""

        # Мышь
        def mouse_listener():
            def on_move(x, y):
                # Преобразуем реальные координаты в координаты на коврике
                mat_x, mat_y = self.map_mouse_to_mat(x, y)
                self.mouse_position = [mat_x, mat_y]

            with mouse.Listener(on_move=on_move) as listener:
                listener.join()

        # Клавиатура
        def keyboard_listener():
            def on_press(key):
                try:
                    self.keys_pressed.add(key.char.upper() if hasattr(key, 'char') else str(key))
                except AttributeError:
                    self.keys_pressed.add(str(key))

            def on_release(key):
                try:
                    key_str = key.char.upper() if hasattr(key, 'char') else str(key)
                    self.keys_pressed.discard(key_str)
                except AttributeError:
                    self.keys_pressed.discard(str(key))

            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()

        threading.Thread(target=mouse_listener, daemon=True).start()
        threading.Thread(target=keyboard_listener, daemon=True).start()

    def calculate_arm_position(self, base_x: int, base_y: int, target_x: int, target_y: int,
                               max_length: int = 150) -> Tuple[int, int]:
        """Рассчитывает позицию правой лапки для следования за мышью"""
        dx = target_x - base_x
        dy = target_y - base_y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance > max_length:
            scale = max_length / distance
            dx *= scale
            dy *= scale

        return int(base_x + dx), int(base_y + dy)

    def draw(self):
        """Отрисовывает все элементы кота"""
        self.screen.fill((0, 0, 0))

        # 1. Фон
        self.screen.blit(self.background, self.background_pos)

        # 2. Левая лапка (для клавиатуры) - меняем изображение в зависимости от состояния
        if self.keys_pressed and self.left_arm is not None:
            # Если клавиши нажаты - отображаем опущенную лапку (left.png)
            self.screen.blit(self.left_arm, self.left_arm_pos)

            # ОТЛАДКА: рисуем рамку вокруг левой лапки (красная когда нажата)
            debug_color = (255, 0, 0)  # Красный
            left_rect = self.left_arm.get_rect(topleft=self.left_arm_pos)
            pygame.draw.rect(self.screen, debug_color, left_rect, 2)
        elif self.left_arm_up is not None:
            # Если клавиши не нажаты - отображаем поднятую лапку (up.png)
            self.screen.blit(self.left_arm_up, self.left_arm_pos)

            # ОТЛАДКА: рисуем рамку вокруг левой лапки (зеленая когда поднята)
            debug_color = (0, 255, 0)  # Зеленый
            left_rect = self.left_arm_up.get_rect(topleft=self.left_arm_pos)
            pygame.draw.rect(self.screen, debug_color, left_rect, 2)
        else:
            # Если изображения не загружены, рисуем прямоугольник
            debug_color = (255, 255, 0)  # Желтый
            pygame.draw.rect(self.screen, debug_color, (self.left_arm_pos[0], self.left_arm_pos[1], 50, 50), 2)

        # 3. Правая лапка (следует за мышью) - прикреплена к телу
        if self.right_arm is not None:
            target_x, target_y = self.calculate_arm_position(
                self.right_arm_anchor[0], self.right_arm_anchor[1],
                self.mouse_position[0], self.mouse_position[1]
            )

            # Отрисовываем правую лапку с привязкой к точке анкера
            right_arm_rect = self.right_arm.get_rect(center=(target_x, target_y))
            self.screen.blit(self.right_arm, right_arm_rect)

            # ОТЛАДКА: рисуем рамку вокруг правой лапки
            debug_color = (0, 0, 255)  # Синий
            pygame.draw.rect(self.screen, debug_color, right_arm_rect, 2)
        else:
            # Если изображение не загружено, рисуем круг вместо лапки
            debug_color = (255, 0, 0)  # Красный
            target_x, target_y = self.calculate_arm_position(
                self.right_arm_anchor[0], self.right_arm_anchor[1],
                self.mouse_position[0], self.mouse_position[1]
            )
            pygame.draw.circle(self.screen, debug_color, (target_x, target_y), 25, 2)

        # 4. Мышь (отображаем в преобразованных координатах коврика)
        if self.mouse_img is not None:
            mouse_x = self.mouse_position[0] - self.mouse_img.get_width() // 2
            mouse_y = self.mouse_position[1] - self.mouse_img.get_height() // 2
            self.screen.blit(self.mouse_img, (mouse_x, mouse_y))
        else:
            # Если изображение не загружено, рисуем круг вместо мыши
            debug_color = (255, 255, 255)  # Белый
            pygame.draw.circle(self.screen, debug_color, self.mouse_position, 10, 2)

        # 5. ОТЛАДКА: рисуем контур коврика
        debug_color = (255, 0, 0)  # Красный
        pygame.draw.polygon(self.screen, debug_color, self.mat_corners, 2)

        # Рисуем точки углов для настройки
        for i, corner in enumerate(self.mat_corners):
            pygame.draw.circle(self.screen, debug_color, corner, 5)
            font = pygame.font.Font(None, 24)
            text = font.render(str(i + 1), True, debug_color)
            self.screen.blit(text, (corner[0] + 10, corner[1] - 10))

        # ОТЛАДКА: рисуем точку привязки правой лапки
        pygame.draw.circle(self.screen, (0, 255, 0), self.right_arm_anchor, 5)

        # ОТЛАДКА: отображаем информацию о состоянии
        font = pygame.font.Font(None, 36)
        keys_text = font.render(f"Нажатые клавиши: {len(self.keys_pressed)}", True, (255, 255, 255))
        self.screen.blit(keys_text, (10, 10))

        pygame.display.flip()

    def handle_events(self):
        """Обрабатывает события Pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def run(self):
        """Главный цикл"""
        clock = pygame.time.Clock()

        while self.running:
            self.handle_events()
            self.draw()
            clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    cat = BongoCat()
    cat.run()