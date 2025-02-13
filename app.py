import csv
import logging
import pygame
from fire_sim import Fire, generate_positions


def show_input_window():
    """ Окно ввода количества очагов и препятствий перед игрой. """
    pygame.init()
    screen = pygame.display.set_mode((500, 400))
    pygame.display.set_caption("Настройки игры")
    font = pygame.font.Font(None, 36)
    white = (255, 255, 255)
    black = (0, 0, 0)
    red = (255, 0, 0)  # Цвет для сообщения об ошибке

    # Поля ввода размещаем ниже текста
    input_boxes = [
        {"rect": pygame.Rect(300, 180, 100, 40), "text": "", "active": False},  # Поле для очагов
        {"rect": pygame.Rect(300, 240, 100, 40), "text": "", "active": False}  # Поле для препятствий
    ]

    instructions = [
        "Имеется поле 10x10 клеток.",
        "Введите:"
    ]

    error_message = ""  # Сообщение об ошибке
    running = True
    while running:
        screen.fill(white)

        # Отображаем инструкции
        y = 50
        for line in instructions:
            text_surface = font.render(line, True, black)
            screen.blit(text_surface, (50, y))
            y += 40

        # Отображаем поля ввода
        for idx, box in enumerate(input_boxes):
            pygame.draw.rect(screen, (200, 200, 200), box["rect"])
            text_surface = font.render(box["text"], True, black)
            screen.blit(text_surface, (box["rect"].x + 10, box["rect"].y + 10))
            # Отображаем подсказку рядом с полем ввода
            if idx == 0:
                hint = "Количество очагов"
            else:
                hint = "Количество препятствий"
            hint_surface = font.render(hint, True, black)
            screen.blit(hint_surface, (box["rect"].x - 300, box["rect"].y + 10))

        # Отображаем сообщение об ошибке, если оно есть
        if error_message:
            error_surface = font.render(error_message, True, red)
            screen.blit(error_surface, (50, 300))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for box in input_boxes:
                    box["active"] = box["rect"].collidepoint(event.pos)
            elif event.type == pygame.KEYDOWN:
                for box in input_boxes:
                    if box["active"]:
                        if event.key == pygame.K_RETURN:
                            try:
                                fire_count = int(input_boxes[0]["text"]) if input_boxes[0]["text"] else 0
                                obstacle_count = int(input_boxes[1]["text"]) if input_boxes[1]["text"] else 0

                                # Проверяем, что сумма не превышает 50%
                                if fire_count + obstacle_count > 50:
                                    error_message = "Ошибка: Сумма очагов и препятствий не должна превышать 50."
                                else:
                                    running = False  # Завершаем работу окна
                            except ValueError:
                                error_message = "Ошибка: Введите числовые значения."
                        elif event.key == pygame.K_BACKSPACE:
                            box["text"] = box["text"][:-1]
                        elif event.unicode.isdigit():
                            box["text"] += event.unicode

    pygame.quit()
    return fire_count, obstacle_count

def show_summary_window(fire_count, obstacle_count, iteration_count):
    """ Отображает итоговое окно с информацией о завершенной игре. """
    pygame.init()
    screen = pygame.display.set_mode((400, 300))  # Размер окна
    pygame.display.set_caption("Результаты игры")

    font = pygame.font.Font(None, 36)  # Шрифт
    white = (255, 255, 255)
    black = (0, 0, 0)

    screen.fill(white)

    # Текстовые строки
    text1 = font.render(f"Очагов: {fire_count}", True, black)
    text2 = font.render(f"Препятствий: {obstacle_count}", True, black)
    text3 = font.render(f"Итераций: {iteration_count}", True, black)


    # Размещаем текст на экране
    screen.blit(text1, (50, 50))
    screen.blit(text2, (50, 100))
    screen.blit(text3, (50, 150))

    pygame.display.flip()  # Обновляем экран

    # Ждем нажатия кнопки закрытия
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False

    pygame.quit()


def run():
    pygame.init()
    running = True
    fire_count, obstacle_count = show_input_window()  # Получение входных данных
    fire_coords, obstacles_coords = generate_positions(fire_count, obstacle_count, (0,9))

    game = Fire(fire_coords, obstacles_coords)
    game.render()

    iteration_count = 0
    total_reward = 0  # Суммарная награда

    # Настройка логирования в файл
    logging.basicConfig(filename='logs.csv', level=logging.INFO,
                        format='%(asctime)s,%(message)s',
                        filemode='w')
    logger = logging.getLogger()

    # Запись заголовков в CSV файл
    with open('logs.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Итерация", "Заряд", "Средства", "Очагов осталось", "Вознаграждение"])

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Определяем действие агента
            if game.position in game.fires and game.extinguisher_count > 0:
                reward = game.extinguish()  # Тушение пожара
            elif game.battery_level < 10 or game.extinguisher_count == 0:
                reward = game.recharge()  # Перезарядка на базе
            else:
                reward = game.move()  # Движение к ближайшему огню

            total_reward += reward  # Обновление суммарной награды
            game.render()
            iteration_count += 1

            log_message = [iteration_count, game.battery_level, game.extinguisher_count,
                           len(game.fires), reward]
            logger.info(','.join(map(str, log_message)))  # Логирование в CSV файл

            # Запись в файл
            with open('logs.csv', mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(log_message)

            pygame.time.delay(50)  # Пауза для анимации

            if not game.fires:  # Завершение, если все очаги потушены
                print("Все очаги потушены. Игра завершена.")
                running = False

    except Exception as e:
        logging.error(f"Ошибка: {e}")
    finally:
        # Отображаем итоговые результаты
        show_summary_window(fire_count, obstacle_count, iteration_count, total_reward)
        pygame.quit()


# Функция для отображения итогового окна
def show_summary_window(fire_count, obstacle_count, iteration_count, total_reward):
    # Окно для отображения итогов
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Итоги игры")

    font = pygame.font.SysFont("Arial", 20)

    # Текст для отображения
    text1 = font.render(f"Количество итераций: {iteration_count}", True, (0, 0, 0))
    text2 = font.render(f"Количество очагов: {fire_count}", True, (0, 0, 0))
    text3 = font.render(f"Количество препятствий: {obstacle_count}", True, (0, 0, 0))
    text4 = font.render(f"Суммарная награда: {total_reward}", True, (0, 0, 0))
    text5 = font.render(f"Игра завершена", True, (0, 0, 0))

    # Отображаем текст
    screen.fill((255, 255, 255))
    screen.blit(text1, (20, 20))
    screen.blit(text2, (20, 50))
    screen.blit(text3, (20, 80))
    screen.blit(text4, (20, 110))
    screen.blit(text5, (20, 130))

    # Обновление экрана
    pygame.display.update()

    # Ожидание выхода
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
    pygame.quit()

