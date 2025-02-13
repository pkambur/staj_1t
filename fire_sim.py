import numpy as np
import pygame
import random
import math
import const as c
from queue import PriorityQueue


def generate_positions(fire_count, obstacle_count, base_position):
    """ Генерирует случайные позиции для очагов огня и препятствий,
    чтобы клетки базы не попадали на препятствия, а препятствия располагались в случайном порядке. """

    # Генерация всех позиций на поле
    all_positions = [(x, y) for x in range(10) for y in range(10)]
    random.shuffle(all_positions)

    # Отделяем позиции для огня
    fire_positions = all_positions[:fire_count]

    # Убираем базу из списка возможных позиций
    all_positions.remove(base_position)

    # Перемешиваем оставшиеся позиции для препятствий
    random.shuffle(all_positions[fire_count:])

    # Добавляем препятствия с учетом расстояния от базы
    obstacle_positions = []
    for pos in all_positions[fire_count:]:
        if math.dist(pos, base_position) >= 2:
            obstacle_positions.append(pos)
            if len(obstacle_positions) == obstacle_count:
                break

    return fire_positions, obstacle_positions


class Fire:
    def __init__(self, fire_coords, obstacles_coords):
        """ Инициализирует среду с огнем, препятствиями и агентом. """
        pygame.init()
        self.screen_size = c.SCREEN_SIZE
        self.screen = pygame.display.set_mode((self.screen_size, self.screen_size))
        self.cell = c.CELL_SIZE
        self.obstacles = obstacles_coords
        self.fires = set(fire_coords)
        self.visited_fires = set()
        self.base = (0, 9)  # База агента
        self.position = self.base
        self.battery_level = 100
        self.extinguisher_count = 1
        self.update_distances_to_fires()



    def update_distances_to_fires(self):
        """ Обновляет расстояния до всех очагов огня."""
        x_agent, y_agent = self.position
        self.distances_to_fires = [(abs(x - x_agent) + abs(y - y_agent), (x, y)) for x, y in self.fires]
        self.distances_to_fires.sort()

    def find_path(self, goal):
        """ Ищет кратчайший путь к указанной цели (база или огонь) с помощью A* """
        open_set = PriorityQueue()
        open_set.put((0, self.position))
        came_from = {self.position: None}
        g_score = {self.position: 0}
        f_score = {self.position: abs(self.position[0] - goal[0]) + abs(self.position[1] - goal[1])}
        while not open_set.empty():
            _, current = open_set.get()
            if current == goal:
                path = []
                while current:
                    path.append(current)
                    current = came_from[current]
                return path[::-1][1:]
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < 10 and 0 <= neighbor[1] < 10 and neighbor not in self.obstacles:
                    temp_g_score = g_score[current] + 1
                    if neighbor not in g_score or temp_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = temp_g_score
                        f_score[neighbor] = temp_g_score + abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                        open_set.put((f_score[neighbor], neighbor))
        return None

    def move(self):
        """ Управляет движением агента: либо к огню, либо к базе для зарядки."""
        if self.battery_level < 10:
            return self.recharge()
        if self.fires:
            path = self.find_path(
                min(self.fires, key=lambda f: abs(f[0] - self.position[0]) + abs(f[1] - self.position[1])))
            if path and self.battery_level >= len(path) * 5:
                self.position = path[0]
                self.battery_level -= 5
                self.update_distances_to_fires()
                return 1
        return self.recharge()

    def extinguish(self):
        """ Тушит огонь, если агент находится на клетке с очагом."""
        if self.position in self.fires and self.extinguisher_count > 0:
            self.fires.remove(self.position)
            self.extinguisher_count -= 1
            self.update_distances_to_fires()
            return 10
        return -5

    def recharge(self):
        """ Перезаряжает батарею и пополняет тушащие средства, если агент на базе."""
        if self.position == self.base:
            self.battery_level = 100
            self.extinguisher_count = 1
            return 0
        path = self.find_path(self.base)
        if path:
            self.position = path[0]
            self.battery_level -= 5
            return -1
        return -3

    def render(self):
        """ Отображает текущее состояние среды (агента, огонь, препятствия, базу). """
        self.screen.fill(c.WHITE)
        agent_color = (0, 0, 255) if self.battery_level > 50 else (255, 255, 0) if self.battery_level > 20 else (
        255, 0, 0)
        AGENT = pygame.Surface((self.cell, self.cell))
        AGENT.fill(agent_color)
        OBSTACLE = pygame.Surface((self.cell, self.cell))
        OBSTACLE.fill((0, 0, 0))
        FIRE = pygame.Surface((self.cell, self.cell))
        FIRE.fill((255, 0, 0))
        BASE = pygame.Surface((self.cell, self.cell))
        BASE.fill((0, 255, 0))
        for fire in self.fires:
            self.screen.blit(FIRE, (fire[0] * self.cell, fire[1] * self.cell))
        self.screen.blit(AGENT, (self.position[0] * self.cell, self.position[1] * self.cell))
        self.screen.blit(BASE, (self.base[0] * self.cell, self.base[1] * self.cell))
        for obstacle in self.obstacles:
            self.screen.blit(OBSTACLE, (obstacle[0] * self.cell, obstacle[1] * self.cell))
        pygame.font.init()
        font = pygame.font.Font(None, 30)
        text = font.render(f"Осталось очагов: {len(self.fires)}", True, (0, 0, 0))
        self.screen.blit(text, (10, 10))
        pygame.display.flip()



