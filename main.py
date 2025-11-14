import pygame
import sys
import math
from pynput import mouse, keyboard
import threading
from typing import Set, Tuple
import os


class BongoCat:
    def __init__(self):
        # Инициализация Pygame
        pygame.init()

        # Настройки окна (можно будет потом вынести в конфиг)
        self.window_width = 800
        self.window_height = 600

        # Создаем окно поверх всех окон без рамки
        self.screen = pygame.display.set_mode((self.window_width, self.window_height),
                                              pygame.NOFRAME)
        pygame.display.set_caption("Bongo Cat Stream Overlay")

        # Прозрачное окно
        self.screen.set_colorkey((0, 0, 0))
        self.make_window_transparent()

        # Загрузка изображений с твоими названиями файлов
        self.load_images()

        # Состояния
        self.mouse_position = [400, 300]  # Начальная позиция мыши
        self.keys_pressed: Set = set()
        self.arm_animation_progress = 0
        self.animation_speed = 0.3
        self.running = True

        # Настройки позиций (возможно потребуют настройки под твои изображения)
        self.background_pos = (0, 0)
        self.left_arm_base_pos = (280, 320)  # Базовая позиция левой лапки
        self.right_arm_base_pos = (480, 320)  # Базовая позиция правой лапки

        # Запуск отслеживания ввода
        self.start_input_listeners()

        print("Bongo Cat запущен! Нажмите ESC для выхода.")
        print("Движения мыши и нажатия клавиш отслеживаются автоматически.")

    def make_window_transparent(self):
        """Делает окно прозрачным и поверх всех окон"""
        try:
            # Для Windows
            if os.name == 'nt':
                import ctypes
                hwnd = pygame.display.get_wm_info()["window"]
                # Установка окна поверх всех (HWND_TOPMOST)
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001)
        except:
            print("Не удалось установить окно поверх всех. Работаем в обычном режиме.")

    def load_images(self):
        """Загружает все изображения с твоими названиями файлов"""
        try:
            # Фон с телом кота, столом и клавиатурой
            self.background = pygame.image.load('images/mousebg.png').convert_alpha()

            # Лапки
            self.left_arm = pygame.image.load('images/left.png').convert_alpha()
            self.left_arm_up = pygame.image.load('images/up.png').convert_alpha()
            self.right_arm = pygame.image.load('images/right.png').convert_alpha()

            # Мышь
            self.mouse_img = pygame.image.load('images/mouse.png').convert_alpha()

            print("Все изображения успешно загружены!")

        except Exception as e:
            print(f"Ошибка загрузки изображений: {e}")
            print("Убедитесь, что в папке 'images' есть все необходимые файлы:")
            print("- mousebg.png, left.png, up.png, right.png, mouse.png")
            sys.exit(1)

    def start_input_listeners(self):
        """Запускает потоки для отслеживания мыши и клавиатуры"""

        # Мышь
        def mouse_listener():
            def on_move(x, y):
                # Обновляем позицию мыши (можно добавить смещение если нужно)
                self.mouse_position = [x, y]

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

        # Запуск в отдельных потоках
        threading.Thread(target=mouse_listener, daemon=True).start()
        threading.Thread(target=keyboard_listener, daemon=True).start()

    def calculate_arm_position(self, base_x: int, base_y: int, target_x: int, target_y: int,
                               max_length: int = 100) -> Tuple[int, int]:
        """Рассчитывает позицию правой лапки для следования за мышью"""
        dx = target_x - base_x
        dy = target_y - base_y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance > max_length:
            # Ограничиваем длину, чтобы лапка не растягивалась слишком сильно
            scale = max_length / distance
            dx *= scale
            dy *= scale

        return int(base_x + dx), int(base_y + dy)

    def update_animation(self):
        """Обновляет анимации кота"""
        # Анимация левой лапки (поднимается при нажатии клавиш)
        if self.keys_pressed:
            self.arm_animation_progress = min(1.0, self.arm_animation_progress + self.animation_speed)
        else:
            self.arm_animation_progress = max(0.0, self.arm_animation_progress - self.animation_speed)

    def draw(self):
        """Отрисовывает все элементы кота"""
        # Очистка экрана (прозрачный фон)
        self.screen.fill((0, 0, 0))

        # 1. Фон (тело кота + стол + клавиатура)
        self.screen.blit(self.background, self.background_pos)

        # 2. Правая лапка (следует за мышью)
        target_x, target_y = self.calculate_arm_position(
            self.right_arm_base_pos[0], self.right_arm_base_pos[1],
            self.mouse_position[0], self.mouse_position[1]
        )

        # Отрисовываем правую лапку с учетом смещения к центру изображения
        right_arm_rect = self.right_arm.get_rect(center=(target_x, target_y))
        self.screen.blit(self.right_arm, right_arm_rect)

        # 3. Левая лапка (анимируется при нажатии клавиш)
        left_arm_y_offset = int(40 * self.arm_animation_progress)  # Поднимается на 40 пикселей

        # Выбираем какое изображение использовать для левой лапки
        if self.arm_animation_progress > 0.5:
            current_left_arm = self.left_arm_up
            # Для up.png может потребоваться другое смещение
            left_arm_pos = (self.left_arm_base_pos[0],
                            self.left_arm_base_pos[1] - left_arm_y_offset)
        else:
            current_left_arm = self.left_arm
            left_arm_pos = (self.left_arm_base_pos[0],
                            self.left_arm_base_pos[1] - left_arm_y_offset)

        self.screen.blit(current_left_arm, left_arm_pos)

        # 4. Мышь (отображаем в позиции курсора)
        mouse_x = self.mouse_position[0] - self.mouse_img.get_width() // 2
        mouse_y = self.mouse_position[1] - self.mouse_img.get_height() // 2
        self.screen.blit(self.mouse_img, (mouse_x, mouse_y))

        # Обновление дисплея
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
            self.update_animation()
            self.draw()
            clock.tick(60)  # 60 FPS

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    cat = BongoCat()
    cat.run()