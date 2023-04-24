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


class GhostMoves(Enum):
    """
    Options for Ghost behavior in the game.
    """
    Chase = 0
    Scatter = 1


class PointTypes(Enum):
    """
    Point increases for the main character in the game.
    """
    Cookies = 10
    PowerUp = 50
    Ghost = 400


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

    def set_position(self, input_x, input_y):
        """
        Sets the object's position.
        :param input_x: x coordinate
        :param input_y: y coordinate
        :return: Nothing
        """
        self.x = input_x
        self.y = input_y

    def get_position(self):
        return self.x, self.y


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
        self.powerups = []
        self.game_objects = []
        self.walls = []
        self.ghosts = []
        self.hero: Hero = None

        self.lives = 3
        self.score = 0
        self.curr_phase = 0
        self.cookie_pickup_score = PointTypes.Cookies
        self.powerup_score = PointTypes.PowerUp
        self.ghost_eaten_score = PointTypes.Ghost
        self.activated_special_ability = False
        self.curr_mode = GhostMoves.Scatter
        self.mode_switch_event = pygame.USEREVENT + 1
        self.end_event = pygame.USEREVENT + 2
        self.paku_event = pygame.USEREVENT + 3
        self.modes = [
            (7, 20),
            (7, 20),
            (5, 20),
            (5, 999999)
        ]
        self.done_running = False
        self.won_game = False

    def tick(self, frames_per_sec):
        """
        Continue to render the game while the game isn't running. When game ends
        print end of game on screen.
        :param frames_per_sec: parameter for how fast to tick the game.
        :return: Returns Nothing
        """
        black = (0, 0, 0)  # initialize the black color according to its RGB values
        while not self.done_running:
            for game_obj in self.game_objects:
                game_obj.tick()
                game_obj.draw()

            self.display_text(f"[Score: {self.score}]   [Lives: {self.lives}]")

            if self.hero is None:
                self.display_text("You Died", (self.width / 2 - 256, self.height / 2 - 256), 100)
            if self.won_game:
                self.display_text("You Won", (self.width / 2 - 256, self.height / 2 - 256), 100)
            pygame.display.flip()
            self.clock.tick(frames_per_sec)
            self.screen.fill(black)
            self.handle_events()
        print("Game Over ...")

    def start_end_game_timeout(self):
        """
        Sets a timer for the game to end.
        :return: Nothing
        """
        pygame.time.set_timer(self.end_event, 15000)  # ends the game in 15 secs

    def activate_special_ability(self):
        """
        Activates special ability and changes the game mode to have the ghosts scatter.
        Starts the end game timer.
        """
        self.activated_special_ability = True
        self.set_curr_mode(GhostMoves.Scatter)
        self.start_end_game_timeout()

    def is_special_ability_active(self):
        return self.activated_special_ability

    def set_game_won(self):
        self.won_game = True

    def get_game_won(self):
        return self.won_game

    def add_score(self, input_score: PointTypes):
        """
        Increase the user's game score based on the point type.
        :param input_score: PointTypes variable that can increase the score
        :return: Nothing
        """
        self.score += input_score.value

    def get_hero_pos(self):
        if self.hero is None:
            return 0, 0
        return self.hero.get_position()

    def set_curr_mode(self, input_mode: GhostMoves):
        """
        Set current mode to the mode being passed in.
        :param input_mode: GhostMoves variable that dictates what mode the game is in.
        """
        self.curr_mode = input_mode

    def get_curr_mode(self):
        return self.curr_mode

    def add_game_object(self, obj: GameObject):
        """
        Add a game object (wall, character, anything else) to the game.
        :param obj: item to add to the game_objects list, from the GameObject class
        """
        self.game_objects.append(obj)

    def get_game_objects(self):
        return self.game_objects

    def add_cookie(self, obj: GameObject):
        """
        Appends a new cookie to the list of cookies.
        :param obj: a GameObject that details a cookie.
        :return: Nothing
        """
        self.game_objects.append(obj)
        self.cookies.append(obj)

    def get_cookies(self):
        return self.cookies

    def add_powerup(self, obj: GameObject):
        """
        Appends a new powerup to the list of game objects and powerups.
        :param obj: a GameObject that details a powerup.
        :return: Nothing
        """
        self.game_objects.append(obj)
        self.powerups.append(obj)

    def get_powerups(self):
        return self.powerups

    def add_ghost(self, obj: GameObject):
        """
        Appends a new ghost to the list of game objects and ghosts.
        :param obj: a GameObject that details a cookie.
        :return: Nothing
        """
        self.game_objects.append(obj)
        self.ghosts.append(obj)

    def get_ghosts(self):
        return self.ghosts

    def handle_mode_switch(self):
        """
        Find the current mode that the game is running then switch the mode based on the current phase.
        Set the timer using the timing that the game is going to be running under. 
        """
        curr_phase_timings = self.modes[self.curr_phase]
        print(f"Current Phase: {str(self.curr_phase)}, Current Phase Timings: {str(curr_phase_timings)}")
        scatter_timing = curr_phase_timings[0]
        chase_timing = curr_phase_timings[1]
        if self.curr_mode == GhostMoves.Scatter:
            self.set_curr_mode(GhostMoves.Chase)
        else:
            self.curr_phase += 1
            self.set_curr_mode(GhostMoves.Scatter)

        used_timing = None
        if self.curr_mode == GhostMoves.Scatter:
            used_timing = scatter_timing
        else:
            used_timing = chase_timing
        pygame.time.set_timer(self.mode_switch_event, used_timing * 1000)


    def handle_events(self):
        """
        Loop through the events in the game using the pygame.event.get() function and perform
        a certain action based on the event that happens.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done_running = True
            if event.type == self.mode_switch_event:
                self.handle_mode_switch()
            if event.type == self.end_event:
                self.activated_special_ability = False
            if event.type == self.paku_event:
                if self.hero is None:
                    break
                self.hero.mouth_is_open = not self.hero.mouth_is_open

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

    def end_game(self):
        """
        Removes the hero from the game.
        """
        if self.hero in self.game_objects:
            self.game_objects.remove(self.hero)
        self.hero = None

    def kill_pacman(self):
        """
        Used when the main character dies in the game.
        """
        self.lives -= 1
        self.hero.set_position(32, 32)
        self.hero.set_direction(Directions.Nothing)
        if self.lives == 0:
            self.end_game()

    def display_text(self, text, input_position=(32, 0), input_size=30):
        """
        Displays text on the game's screen.
        :param text: text to be displayed
        :param input_position: position on screen for text to be displayed
        :param input_size: size of text to be displayed
        :return: Nothing
        """
        font = pygame.font.SysFont('arial', input_size)
        text_surface = font.render(text, False, (255, 255, 255))
        self.screen.blit(text_surface, input_position)  # places an image onto the screen of pygame application


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
    def __init__(self, input_surface, x, y, input_size, game_controller, sprite_path="images/fright.png"):
        """
        Initializer function for a ghost object
        :param input_surface: creates the ghost on the pygame surface
        :param x: x coordinate of the ghost
        :param y: y coordinate of the ghost
        :param input_size: size of the ghost
        :param game_controller:
        :param sprite_path: image to load the sprite ghost
        """
        super().__init__(input_surface, x, y, input_size)
        self.game_controller = game_controller
        self.normal_sprite = pygame.image.load(sprite_path)
        self.fright_sprite = pygame.image.load(sprite_path)

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
        Set the ghost on a new path. Edits the ghost's next target and appends
        to the location queue for ghosts to move next.
        :param input_path: path for new ghost to go through.
        """
        for i in input_path:
            self.location_queue.append(i)
        self.next_target = self.get_next_location()

    def calc_dir_to_next_target(self):
        """
        TODO
        :return:
        """
        pass

    def request_path_to_player(self, input_ghost):
        """

        :param input_ghost:
        :return:
        """


class Hero(Movers):
    def __init__(self, input_surface, x, y, input_size):
        """

        :param input_surface:
        :param x:
        :param y:
        :param input_size:
        """
        super().__init__(input_surface, x, y, input_size, (255, 255, 0), False)
        self.last_position = (0, 0)
        self.image = pygame.image.load("images/pac.png")
        self.closed = pygame.image.load("images/jr_pac.png")
        self.open = self.image
        self.mouth_is_open = True

    def tick(self):
        """

        :return:
        """
        if self.x < 0:
            self.x = self.renderer.width

        if self.x > self.renderer.width:
            self.x = 0
        self.last_position = self.get_position()
        # TODO



class Cookies(GameObject):
    """
    For cookies in the game inheriting from the game object class.
    """
    def __init__(self, input_surface, x, y):
        super().__init__(input_surface, x, y, 4, (255, 255, 0), True)


class PowerUp(GameObject):
    """
    Used for powerups in the game inheriting from the game object class.
    """
    def __init__(self, input_surface, x, y):
        super().__init__(input_surface, x, y, 8, (255, 255, 255), True)


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