import pygame
import numpy as np
import tcod
import random
from enum import Enum


class Directions(Enum):
    Nothing = 360
    Left = 180
    Up = 90
    Down = -90
    Right = 0


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

    def add_wall(self, obj):
        self.add_game_object(obj)
        self.walls.append(obj)


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
        if self.circle:  # render the object as either a circle or rectangle
            pygame.draw.circle(self.surface, self.color, self.x, self.y, self.size)
        else:
            rectangle = pygame.Rect(self.x, self.y, self.size, self.size)
            pygame.draw.rect(self.surface, self.color, rectangle, border_radius=4)

    def tick(self):
        pass


class WallObject(GameObject):
    def __init__(self, input_surface, x, y, input_size, input_color=(0, 0, 255)):
        super().__init__(input_surface, x * input_size, y * input_size, input_size, input_color)
# set the parameters for the wall class, the color of the walls is blue


class GameController:
    def __init__(self):
        self.ascii_maze = [
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "XP           XX            X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X XXXXOXXXXX XX XXXXXOXXXX X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X                          X",
            "X XXXX XX XXXXXXXX XX XXXX X",
            "X XXXX XX XXXXXXXX XX XXXX X",
            "X      XX    XX    XX      X",
            "XXXXXX XXXXX XX XXXXX XXXXXX",
            "XXXXXX XXXXX XX XXXXX XXXXXX",
            "XXXXXX XX     G    XX XXXXXX",
            "XXXXXX XX XXX  XXX XX XXXXXX",
            "XXXXXX XX X      X XX XXXXXX",
            "   G      X      X          ",
            "XXXXXX XX X      X XX XXXXXX",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "XXXXXX XX    G     XX XXXXXX",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "X            XX            X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X   XX       G        XX   X",
            "XXX XX XX XXXXXXXX XX XX XXX",
            "XXX XX XX XXXXXXXX XX XX XXX",
            "X      XX    XX    XX      X",
            "X XXXXXXXXXX XX XXXXXXXXXX X",
            "X XXXXXXXXXX XX XXXXXXXXXX X",
            "X   O                 O    X",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]  # X = wall, P = pac-man, G = ghost
        # initialize the maze in ascii chars to later convert to a np maze
        self.numpy_maze = []  # use to convert maze where 0 is wall and 1 is free space
        self.cookie_spaces = []
        self.reachable_spaces = []  # holds the passable parts of the array
        self.ghost_spawns = []

        self.size = (0, 0)
        self.convert_maze_to_np()

    def convert_maze_to_np(self):
        for x, row in enumerate(self.ascii_maze):
            self.size = (len(row), x+1)
            binary_row = []
            for y, col in enumerate(row):
                if col == "G":
                    self.ghost_spawns.append((y, x))
                elif col == "X":
                    binary_row.append(0)
                else:
                    binary_row.append(1)
                    self.cookie_spaces.append((y, x))
                    self.reachable_spaces.append((y, x))
            self.numpy_maze.append(binary_row)


class Movers(GameObject):
    def __init__(self, input_surface, x, y, input_size, input_color=(255,0,0), is_circle=False):
        super().__init__(input_surface, x, y, input_size, input_color, is_circle)


class Ghost(Movers):
    def __init__(self, input_surface, x, y, input_size, game_controller, sprites="images/fright.png"):
        super().init



if __name__ == "__main__":
    size = 32
    game_object = GameController()
    game_size = game_object.size
    rendering = RenderGame(game_size[0] * size, game_size[1] * size)

    for y, row in enumerate(game_object.numpy_maze):
        for x, col in enumerate(row):
            if col == 0:
                rendering.add_wall(WallObject(rendering, x, y, size))
    rendering.tick(120)