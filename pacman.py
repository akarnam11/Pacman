import pygame
import numpy as np
import tcod
import random
from enum import Enum


class RenderGame:
    def __init__(self, input_width, input_height):
        pygame.init()
        self.width = input_width  # set the width and height to parameters
        self.height = input_height  # that are passed in
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Pacman")  # set caption of the game to "Pacman"
        self.clock = pygame.time.Clock()  # keeps track of the time
        self.cookies = []
        self.game_objects = []
        self.walls = []
        self.done_running = False

    def tick(self, frames_per_sec):
        black = (0, 0, 0)  # initialize the black color according to its RGB values
        while not self.done_running:
            for object in self.game_objects:
                object.tick()
                object.draw()

            pygame.display.flip()
            self.clock.tick(frames_per_sec)
            self.screen.fill(black)
            self.handle_events()
        print("Game Over ...")

    def add_game_object(self, obj):
        self.game_objects.append(obj)

    def add_wall_to_game(self, obj):
        self.add_game_object(obj)
        self.walls.append(obj)

    def handle_events(self):
        pass


class GameObject:
    def __init__(self, in_surface, x, y, input_size, input_color=(255,0,0), is_circle=False):
        self.size = input_size
        self.renderer: RenderGame = in_surface
        self.surface = in_surface.screen
        self.x = x
        self.y = y
        self.color = input_color
        self.circle = is_circle
        self.shape = pygame.Rect(x, y, input_size, input_size)

    def draw(self):
        if self.circle:
            pygame.draw.circle(self.surface, self.color, self.x, self.y, self.size)
        else:
            rectangle = pygame.Rect(self.x, self.y, self.size, self.size)
            pygame.draw.rect(self.surface, self.color, rectangle, border_radius=4)

    def tick(self):
        pass


class WallObject(GameObject):
    def __init__(self, input_surface, x, y, input_size, input_color=(0, 0, 255)):
        super().__init__(input_surface, x * input_size, y * input_size, input_size, input_color)

