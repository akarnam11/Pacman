import pygame
import numpy as np
import tcod
import random
from enum import Enum


class Directions(Enum):
    """
    Directions characters can move in the game.
    """
    Nothing = 360
    Left = 180
    Up = 90
    Down = -90
    Right = 0


def maze_to_screen(input_coords, input_size=32):
    """
    Convert a maze coordinate to a pygame screen coordinate.

    :param input_coords: coordinates of the maze ascii table
    :param input_size: factor to multiply the coordinates by
    :return: tuple of the converted coordinates
    """
    return input_coords[0] * input_size, input_coords[1] * input_size


def screen_to_maze(input_coords, input_size=32):
    """
    Converts a pygame screen coordinate to a maze coordinate.
    :param input_coords: coordinates of a character or object in the pygame screen.
    :param input_size: factor to divide the coordinates by
    :return: a tuple for the x, y coordinates for the maze ascii table of type int
    """
    return int(input_coords[0] / input_size), int(input_coords[1] / input_size)


class RenderGame:
    """
    Class to Render the pygame screen.
    """
    def __init__(self, input_width, input_height):
        """
        Initialize all the parameters needed for this class. Some features include:
        clock that is set to the pygame clock,
        screen which is set to the width and height from the pygame display class
        :param input_width: width of the game screen
        :param input_height: height of the game screen
        """
        pygame.init()
        self.width = input_width
        self.height = input_height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Pacman")
        self.clock = pygame.time.Clock()
        self.cookies = []
        self.game_objects = []
        self.walls = []
        self.done_running = False

    def tick(self, frames_per_sec):
        """
        Continue to render the game while the game isn't running. When game ends
        print end of game on screen.
        :param frames_per_sec: parameter for how fast to tick the game.
        :return: Returns Nothing
        """
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
        """
        Add a game object (wall, character, anything else) to the game.
        :param obj: item to add to the game_objects list
        """
        self.game_objects.append(obj)

    def handle_events(self):
        """
        TODO
        """
        pass

    def add_wall(self, obj):
        """
        Add a wall to the game and append it to the walls list.
        :param obj: Wall type
        """
        self.add_game_object(obj)
        self.walls.append(obj)

    def get_walls(self):
        """
        Accessor function to return the walls list.
        :return: walls list
        """
        return self.walls


class GameObject:
    """

    """
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

    def get_shape(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)


class WallObject(GameObject):
    """
    Class to handle Wall objects. Inherited from the GameObject class.
    """
    def __init__(self, input_surface, x, y, input_size, input_color=(0, 0, 255)):
        """
        Initializer function.
        :param input_surface: takes care of rendering on the game's surface
        :param x: position on the game
        :param y: position on the game
        :param input_size: size of the walls
        :param input_color: color of the walls, initially set to blue
        """
        super().__init__(input_surface, x * input_size, y * input_size, input_size, input_color)


class GameController:
    """
    Controls the game and where characters can go. Holds the mazes in ascii and numpy version.
    """
    def __init__(self):
        """
        Initializes the various mazes needed for pathfinding. Holds lists for the
        types of ghosts, cookies, and open spaces in the maze.
        """
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
        self.numpy_maze = []  # use to convert maze where 0 is wall and 1 is free space
        self.cookie_spaces = []
        self.reachable_spaces = []  # holds the passable parts of the array
        self.ghost_spawns = []
        self.ghost_images = [
            "images/ghosts.png",
            "images/pinky.png",
            "images/clyde.png",
            "images/inky.png"
        ]

        self.size = (0, 0)
        self.convert_maze_to_np()
        self.pathfinder = PathFinder(self.numpy_maze)

    def generate_random_path(self, ghost):
        """
        Function to generate a random path for each ghost in the game using the pathfinder class.
        :param ghost: ghost object
        :return: Nothing, sets the new path for a given ghost
        """
        random_coord = random.choice(self.reachable_spaces)
        current_coord = screen_to_maze(ghost.get_position())
        path = self.pathfinder.get_path(current_coord[1], current_coord[0], random_coord[1],
                                        random_coord[0])
        new_path = [maze_to_screen(item) for item in path]
        ghost.set_new_path(new_path)

    def convert_maze_to_np(self):
        """
        Converts the ascii maze above to a numpy maze for easy pathfinding.
        :return: Returns Nothing, but fills the numpy maze with 0's (walls) and 1's (free space).
        """
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
    """
    Movable Objects that inherits from the GameObject class. Functions to take care of movements
    """
    def __init__(self, input_surface, x, y, input_size, input_color=(255,0,0), is_circle=False):
        """
        Initializes various values needed for movable objects in the game.
        Sets directional values for each movable object so that it can move through the maze.
        Makes use of the enum Directions class.
        :param input_surface: initializes the object on the game surface
        :param x: starting x coordinate for the object
        :param y: starting y coordinate for the object
        :param input_size: size of the object
        :param input_color: color of the object (initially set to red)
        :param is_circle: whether the object is a circle or not
        """
        super().__init__(input_surface, x, y, input_size, input_color, is_circle)
        self.curr_direction = Directions.Nothing
        self.dir_buffer = Directions.Nothing
        self.last_working_dir = Directions.Nothing
        self.location_queue = []
        self.next_target = None
        self.image = pygame.image.load("images/ghosts.png")

    def get_next_location(self):
        """
        Accessor to retrieve the next location for an object that is moving through the game.
        :return: Nothing if the object's queue is empty, else return its next destination
        """
        if len(self.location_queue) == 0:
            return None
        return self.location_queue.pop(0)

    def set_direction(self, input_direction):
        """
        Mutator to set the current direction of the object to the parameter passed in.
        :param input_direction: Directions type that tells the object where to go
        """
        self.curr_direction = input_direction
        self.dir_buffer = input_direction

    def wall_collision(self, input_position):
        """
        Checks whether the object has collided with any of the walls in the game.
        Loops through all the walls and creates a Rect object from the pygame library.
        :param input_position: Current position of the object
        :return: Boolean value of whether the object collides with a wall or not
        """
        collision_location = pygame.Rect(input_position[0], input_position[1], self.size, self.size)
        is_collision = False
        walls = self.renderer.get_walls()
        for w in walls:
            is_collision = collision_location.colliderect(w.get_shape())
            if is_collision:
                break
        return is_collision


class Ghost(Movers):
    """
    Ghost class for the ghosts in the game that inherits from the Movers class above,
    since ghosts are also movable objects in this game.
    """
    def __init__(self, input_surface, x, y, input_size, game_controller, input_color=(255, 0, 0)):
        """
        Initializer function for a ghost object
        :param input_surface: creates the ghost on the pygame surface
        :param x: x coordinate of the ghost
        :param y: y coordinate of the ghost
        :param input_size: size of the ghost
        :param game_controller:
        :param input_color: color of the ghost (initialized to red)
        """
        super().__init__(input_surface, x, y, input_size, input_color, False)
        self.game_controller = game_controller

    def reached_target_location(self):
        """
        If the ghost has reached its target destination, set its destination to somewhere new.
        Calculate the direction in which it needs to go.
        """
        if (self.x, self.y) == self.next_target:
            self.next_target = self.get_next_location()
        self.curr_direction = self.calc_dir_to_next_target()

    def set_new_path(self, input_path):
        """
        
        :param input_path:
        :return:
        """
        for i in input_path:
            self.location_queue.append(i)
        self.next_target = self.get_next_location()


class PathFinder:
    """
    Uses the A* algorithm to find the shortest path from one location to another
    within the numpy maze. Makes use of the tcod library that contains the A* algorithm
    """
    def __init__(self, input_array):
        """
        Initializes the cost and path found for a certain object in the game.
        :param input_array: input array for a specific ghost in the game.
        """
        cost = np.array(input_array, dtype=np.bool_).tolist()
        self.path_found = tcod.path.AStar(cost=cost, diagonal=0)

    def get_path(self, from_x, from_y, to_x, to_y):
        """
        Calculate and return the path as a series of steps.
        :param from_x: x coordinate of the maze
        :param from_y: y coordinate of the maze
        :param to_x: x coordinate to go to
        :param to_y: y coordinate to go to
        :return: series of paths to get from one location in the maze to another
        """
        path = self.path_found.get_path(from_x, from_y, to_x, to_y)
        return [(sub[1], sub[0]) for sub in path]


if __name__ == "__main__":
    size = 32
    game_object = GameController()
    game_size = game_object.size
    rendering = RenderGame(game_size[0] * size, game_size[1] * size)

    for y, row in enumerate(game_object.numpy_maze):  # add walls to the game
        for x, col in enumerate(row):
            if col == 0:
                rendering.add_wall(WallObject(rendering, x, y, size))

    for i, spawn_ghost in enumerate(game_object.ghost_spawns):
        translated = maze_to_screen(spawn_ghost)
        ghost = Ghost(rendering, translated[0], translated[1], size, game_object, game_object.ghost_images[i % 4])
        rendering.add_ghost(ghost)

    rendering.tick(120)