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
