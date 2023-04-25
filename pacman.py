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
    Chase = 1
    Scatter = 2


class PointTypes(Enum):
    """
    Point increases for the main character in the game.
    """
    Cookie = 10
    Powerup = 50
    Ghost = 400


def screen_to_maze(input_coords, input_size=32):
    """
    Converts a pygame screen coordinate to a maze coordinate.
    :param input_coords: coordinates of a character or object in the pygame screen.
    :param input_size: factor to divide the coordinates by
    :return: a tuple for the x, y coordinates for the maze ascii table of type int
    """
    return int(input_coords[0] / input_size), int(input_coords[1] / input_size)


def maze_to_screen(input_coords, input_size=32):
    """
    Convert a maze coordinate to a pygame screen coordinate.

    :param input_coords: coordinates of the maze ascii table
    :param input_size: factor to multiply the coordinates by
    :return: tuple of the converted coordinates
    """
    return input_coords[0] * input_size, input_coords[1] * input_size


class GameObject:
    """
    Class to hold various game objects in the game. Parent class that other instances
    of the game will inherit from.
    """

    def __init__(self, input_surface, x, y, in_size: int, input_color=(255, 0, 0), is_circle: bool = False):
        self._size = in_size
        self._renderer: RenderGame = input_surface
        self._surface = input_surface._screen
        self.y = y
        self.x = x
        self._color = input_color
        self._circle = is_circle
        self._shape = pygame.Rect(self.x, self.y, in_size, in_size)

    def draw(self):
        """
        Draws the object onto the game's screen depending on if it's a circle or rectangle.
        """
        if self._circle:
            pygame.draw.circle(self._surface, self._color, (self.x, self.y), self._size)
        else:
            rect_object = pygame.Rect(self.x, self.y, self._size, self._size)
            pygame.draw.rect(self._surface, self._color, rect_object, border_radius=1)

    def tick(self):
        pass

    def get_shape(self):
        return pygame.Rect(self.x, self.y, self._size, self._size)

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


class WallObject(GameObject):
    """
    Class to handle Wall objects. Inherited from the GameObject class.
    """

    def __init__(self, input_surface, x, y, input_size: int, input_color=(0, 0, 255)):
        """
        Initializer function.
        :param input_surface: takes care of rendering on the game's surface
        :param x: position on the game
        :param y: position on the game
        :param input_size: size of the walls
        :param input_color: color of the walls, initially set to blue
        """
        super().__init__(input_surface, x * input_size, y * input_size, input_size, input_color)


class RenderGame:
    """
    Class to Render the pygame screen.
    """

    def __init__(self, input_width: int, input_height: int):
        """
        Initialize all the parameters needed for this class. Some features include:
        clock that is set to the pygame clock,
        screen which is set to the width and height from the pygame display class
        :param input_width: width of the game screen
        :param input_height: height of the game screen
        """
        pygame.init()
        self._width = input_width
        self._height = input_height
        self._screen = pygame.display.set_mode((input_width, input_height))
        pygame.display.set_caption('Pacman')
        self._clock = pygame.time.Clock()

        self._done_running = False
        self._won_game = False
        self._game_objects = []
        self._walls = []
        self._cookies = []
        self._powerups = []
        self._ghosts = []
        self._hero: Hero = None

        self._lives = 3
        self._score = 0
        self._score_cookie_pickup = 10
        self._score_ghost_eaten = 400
        self._score_powerup_pickup = 50
        self._special_ability_active = False  # powerup, special ability
        self._curr_mode = GhostMoves.Scatter
        self._mode_switch_event = pygame.USEREVENT + 1  # custom event
        self._special_ability_end_event = pygame.USEREVENT + 2
        self._pakupaku_event = pygame.USEREVENT + 3
        self._modes = [
            (7, 20),
            (7, 20),
            (5, 20),
            (5, 999999)  # 'infinite' chase seconds
        ]
        self._current_phase = 0

    def tick(self, frames_per_second: int):
        """
        Continue to render the game while the game isn't running. When game ends
        print end of game on screen.
        :param frames_per_second: parameter for how fast to tick the game.
        :return: Returns Nothing
        """
        black = (0, 0, 0)

        self.handle_mode_switch()
        pygame.time.set_timer(self._pakupaku_event, 200)  # open close mouth
        while not self._done_running:
            for game_object in self._game_objects:
                game_object.tick()
                game_object.draw()

            self.display_text(f"[Score: {self._score}]  [Lives: {self._lives}]")

            if self._hero is None:
                self.display_text("You Died...", (self._width / 2 - 256, self._height / 2 - 256), 100)
            if self.get_game_won():
                self.display_text("You Won...", (self._width / 2 - 256, self._height / 2 - 256), 100)
            pygame.display.flip()
            self._clock.tick(frames_per_second)
            self._screen.fill(black)
            self._handle_events()

        print("Game over...")

    def handle_mode_switch(self):
        """
        Find the current mode that the game is running then switch the mode based on the current phase.
        Set the timer using the timing that the game is going to be running under.
        """
        curr_phase_timings = self._modes[self._current_phase]
        print(f"Current Phase: {str(self._current_phase)}, Current Phase Timings: {str(curr_phase_timings)}")
        scatter_timing = curr_phase_timings[0]
        chase_timing = curr_phase_timings[1]

        if self._curr_mode == GhostMoves.Chase:
            self._current_phase += 1
            self.set_current_mode(GhostMoves.Scatter)
        else:
            self.set_current_mode(GhostMoves.Chase)

        used_timing = None
        if self._curr_mode == GhostMoves.Scatter:
            used_timing = scatter_timing
        else:
            used_timing = chase_timing
        pygame.time.set_timer(self._mode_switch_event, used_timing * 1000)

    def add_game_object(self, obj: GameObject):
        """
        Add a game object (wall, character, anything else) to the game.
        :param obj: item to add to the game_objects list, from the GameObject class
        """
        self._game_objects.append(obj)

    def add_cookie(self, obj: GameObject):
        """
        Appends a new cookie to the list of cookies.
        :param obj: a GameObject that details a cookie.
        :return: Nothing
        """
        self._game_objects.append(obj)
        self._cookies.append(obj)

    def add_ghost(self, obj: GameObject):
        """
        Appends a new ghost to the list of game objects and ghosts.
        :param obj: a GameObject that details a cookie.
        :return: Nothing
        """
        self._game_objects.append(obj)
        self._ghosts.append(obj)

    def add_powerup(self, obj: GameObject):
        """
        Appends a new powerup to the list of game objects and powerups.
        :param obj: a GameObject that details a powerup.
        :return: Nothing
        """
        self._game_objects.append(obj)
        self._powerups.append(obj)

    def add_wall(self, obj: WallObject):
        """
        Add a wall to the game and append it to the walls list.
        :param obj: Wall type
        """
        self.add_game_object(obj)
        self._walls.append(obj)

    def add_hero(self, input_hero):
        """
        Add hero object to the game.
        :param input_hero: hero object to be added
        """
        self.add_game_object(input_hero)
        self._hero = input_hero

    def start_end_ability_timeout(self):
        """
        Sets a timer for the special ability to end.
        :return: Nothing
        """
        pygame.time.set_timer(self._special_ability_end_event, 15000)  # 15s

    def activate_special_ability(self):
        """
        Activates special ability and changes the game mode to have the ghosts scatter.
        Starts the end game timer.
        """
        self._special_ability_active = True
        self.set_current_mode(GhostMoves.Scatter)
        self.start_end_ability_timeout()

    def is_special_ability_active(self):
        return self._special_ability_active

    def set_game_won(self):
        self._won_game = True

    def get_game_won(self):
        return self._won_game

    def add_score(self, input_score: PointTypes):
        """
        Increase the user's game score based on the point type.
        :param input_score: PointTypes variable that can increase the score
        """
        self._score += input_score.value

    def get_hero_position(self):
        """
        Gets the hero's current position if there is a hero on the screen.
        :return: (0, 0) if no hero, otherwise the hero's position through a call to the get_position function.
        """
        if self._hero is None:
            return 0, 0
        return self._hero.get_position()

    def set_current_mode(self, input_mode: GhostMoves):
        """
        Set current mode to the mode being passed in.
        :param input_mode: GhostMoves variable that dictates what mode the game is in.
        """
        self._curr_mode = input_mode

    def get_current_mode(self):
        return self._curr_mode

    def end_game(self):
        """
        Removes the hero from the game.
        """
        if self._hero in self._game_objects:
            self._game_objects.remove(self._hero)
        self._hero = None

    def kill_pacman(self):
        """
        Used when the main character dies in the game.
        """
        self._lives -= 1
        self._hero.set_position(32, 32)
        self._hero.set_direction(Directions.Nothing)
        if self._lives == 0:
            self.end_game()

    def get_walls(self):
        """
        Accessor function to return the walls list.
        :return: walls list
        """
        return self._walls

    def get_cookies(self):
        return self._cookies

    def get_ghosts(self):
        return self._ghosts

    def get_powerups(self):
        return self._powerups

    def get_game_objects(self):
        return self._game_objects

    def _handle_events(self):
        """
        Loop through the events in the game using the pygame.event.get() function and perform
        a certain action based on the event that happens.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._done_running = True

            if event.type == self._mode_switch_event:
                self.handle_mode_switch()

            if event.type == self._special_ability_end_event:
                self._special_ability_active = False

            if event.type == self._pakupaku_event:
                if self._hero is None:
                    break
                self._hero.mouth_open = not self._hero.mouth_open

        pressed = pygame.key.get_pressed()
        if self._hero is None:
            return
        if pressed[pygame.K_UP]:  # sets direction based on what key was pressed in the game
            self._hero.set_direction(Directions.Up)
        elif pressed[pygame.K_LEFT]:
            self._hero.set_direction(Directions.Left)
        elif pressed[pygame.K_DOWN]:
            self._hero.set_direction(Directions.Down)
        elif pressed[pygame.K_RIGHT]:
            self._hero.set_direction(Directions.Right)

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
        self._screen.blit(text_surface, input_position)


class Movers(GameObject):
    """
    Movable Objects that inherits from the GameObject class. Functions to take care of movements
    """
    def __init__(self, input_surface, x, y, input_size: int, input_color=(255, 0, 0), is_circle: bool = False):
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
        self.current_direction = Directions.Nothing
        self.direction_buffer = Directions.Nothing
        self.last_working_direction = Directions.Nothing
        self.location_queue = []
        self.next_target = None
        self.image = pygame.image.load('images/ghosts.png')

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
        self.current_direction = input_direction
        self.direction_buffer = input_direction

    def wall_collision(self, input_position):
        """
        Checks whether the object has collided with any of the walls in the game.
        Loops through all the walls and creates a Rect object from the pygame library.
        :param input_position: Current position of the object
        :return: Boolean value of whether the object collides with a wall or not
        """
        collision_rect = pygame.Rect(input_position[0], input_position[1], self._size, self._size)
        collides = False
        walls = self._renderer.get_walls()
        for wall in walls:
            collides = collision_rect.colliderect(wall.get_shape())
            if collides:
                break
        return collides

    def check_collision_in_direction(self, input_direction: Directions):
        """
        Checks the direction the object is trying to move and updates its desired position.
        :param input_direction: direction that the character wants to move in
        :return: call to wall_collision and the desired position
        """
        desired_pos = (0, 0)
        if input_direction == Directions.Nothing:
            return False, desired_pos
        if input_direction == Directions.Up:
            desired_pos = (self.x, self.y - 1)
        elif input_direction == Directions.Down:
            desired_pos = (self.x, self.y + 1)
        elif input_direction == Directions.Left:
            desired_pos = (self.x - 1, self.y)
        elif input_direction == Directions.Right:
            desired_pos = (self.x + 1, self.y)

        return self.wall_collision(desired_pos), desired_pos

    def automatic_move(self, in_direction: Directions):
        """
        Placeholder function for other classes to inherit from.
        :param in_direction: Directions variable.
        """
        pass

    def tick(self):
        """
        Calls other functions as the time played increases.
        """
        self.reached_target()
        self.automatic_move(self.current_direction)

    def reached_target(self):
        """
        Placeholder function.
        """
        pass

    def draw(self):
        """
        Draws the movable object onto the game's screen.
        """
        self.image = pygame.transform.scale(self.image, (32, 32))
        self._surface.blit(self.image, self.get_shape())


class Hero(Movers):
    def __init__(self, input_surface, x, y, input_size: int):
        """
        Initialization function that inherits from the Movers class.
        :param input_surface: surface for making the initialization from the Movable Object class.
        :param x: x coordinate
        :param y: y coordinate
        :param input_size: size of character
        """
        super().__init__(input_surface, x, y, input_size, (255, 255, 0), False)
        self.last_non_colliding_position = (0, 0)
        self.open = pygame.image.load("images/pac.png")
        self.closed = pygame.image.load("images/jr_pac.png")
        self.image = self.open
        self.mouth_open = True

    def tick(self):
        """
        Check if the position is within the boundaries of the screen. Move the object in the direction
        if there are no objections, and check for collisions.
        :return: Nothing, make calls to handle cookie pickup and ghosts.
        """
        if self.x < 0:
            self.x = self._renderer._width

        if self.x > self._renderer._width:
            self.x = 0
        self.last_non_colliding_position = self.get_position()
        if self.check_collision_in_direction(self.direction_buffer)[0]:
            self.automatic_move(self.current_direction)
        else:
            self.automatic_move(self.direction_buffer)
            self.current_direction = self.direction_buffer
        if self.wall_collision((self.x, self.y)):
            self.set_position(self.last_non_colliding_position[0], self.last_non_colliding_position[1])
        self.handle_cookies()
        self.handle_ghosts()

    def automatic_move(self, input_direction: Directions):
        """
        If there are no collisions, then update the last working direction to the current direction.
        Else set the current direction to the last working direction
        :param input_direction: current direction character is moving
        """
        collision_result = self.check_collision_in_direction(input_direction)

        desired_position_collides = collision_result[0]
        if not desired_position_collides:
            self.last_working_direction = self.current_direction
            desired_position = collision_result[1]
            self.set_position(desired_position[0], desired_position[1])
        else:
            self.current_direction = self.last_working_direction

    def handle_cookies(self):
        """
        Get the cookies, powerups, and game objects. If the character collides with a cookie,
        then remove that cookie from the screen and game objects, and add points to the game score.
        Loop through the powerups and if the character collides with a powerup,
        remove that powerup from the game objects and increase the game score. Activate the
        character's special ability.
        """
        collision_rect = pygame.Rect(self.x, self.y, self._size, self._size)
        cookies = self._renderer.get_cookies()
        powerups = self._renderer.get_powerups()
        game_objects = self._renderer.get_game_objects()
        cookie_to_remove = None
        for cookie in cookies:
            collides = collision_rect.colliderect(cookie.get_shape())
            if collides and cookie in game_objects:
                game_objects.remove(cookie)
                self._renderer.add_score(PointTypes.Cookie)
                cookie_to_remove = cookie
        if cookie_to_remove is not None:
            cookies.remove(cookie_to_remove)
        if len(self._renderer.get_cookies()) == 0:
            self._renderer.set_game_won()
        for powerup in powerups:
            collides = collision_rect.colliderect(powerup.get_shape())
            if collides and powerup in game_objects:
                if not self._renderer.is_special_ability_active():
                    game_objects.remove(powerup)
                    self._renderer.add_score(PointTypes.Powerup)
                    self._renderer.activate_special_ability()

    def handle_ghosts(self):
        """
        Get all the ghosts in the game and if the character collides with any of them,
        and the special ability is active then remove that ghost from the game. If the
        special ability is not active, then decrease one of the pacman's lives.
        """
        collision_rect = pygame.Rect(self.x, self.y, self._size, self._size)
        ghosts = self._renderer.get_ghosts()
        game_objects = self._renderer.get_game_objects()
        for ghost in ghosts:
            collides = collision_rect.colliderect(ghost.get_shape())
            if collides and ghost in game_objects:
                if self._renderer.is_special_ability_active():
                    game_objects.remove(ghost)
                    self._renderer.add_score(PointTypes.Ghost)
                else:
                    if not self._renderer.get_game_won():
                        self._renderer.kill_pacman()

    def draw(self):
        """
        Chooses the image to be drawn onto the screen at the current moment. Calls the
        parent class' draw function to put it onto the screen. Also rotates the image
        a certain direction based on the direction the character is moving.
        """
        if self.mouth_open:
            self.image = self.open
        else:
            self.image = self.closed
        self.image = pygame.transform.rotate(self.image, self.current_direction.value)
        super(Hero, self).draw()


class Ghost(Movers):
    """
    Ghost class for the ghosts in the game that inherits from the Movers class above,
    since ghosts are also movable objects in this game.
    """
    def __init__(self, input_surface, x, y, input_size: int, game_controller, sprite_path="images/fright.png"):
        """
        Initializer function for a ghost object
        :param input_surface: creates the ghost on the pygame surface
        :param x: x coordinate of the ghost
        :param y: y coordinate of the ghost
        :param input_size: size of the ghost
        :param game_controller: controller for the game's objects
        :param sprite_path: image to load the sprite ghost
        """
        super().__init__(input_surface, x, y, input_size)
        self.game_controller = game_controller
        self.normal_sprite = pygame.image.load(sprite_path)
        self.fright_sprite = pygame.image.load("images/fright.png")

    def reached_target(self):
        """
        If the ghost has reached its target destination, set its destination to somewhere new.
        Calculate the direction in which it needs to go.
        """
        if (self.x, self.y) == self.next_target:
            self.next_target = self.get_next_location()
        self.current_direction = self.calculate_direction_to_next_target()

    def set_new_path(self, input_path):
        """
        Set the ghost on a new path. Edits the ghost's next target and appends
        to the location queue for ghosts to move next.
        :param input_path: path for new ghost to go through.
        """
        for item in input_path:
            self.location_queue.append(item)
        self.next_target = self.get_next_location()

    def calculate_direction_to_next_target(self) -> Directions:
        """
        Move the ghost in a direction determined by what mode the game is in and if the
        special ability is active.
        :return: Directions variable for ghost to move in.
        """
        if self.next_target is None:
            if self._renderer.get_current_mode() == GhostMoves.Chase and not self._renderer.is_special_ability_active():
                self.request_path_to_player(self)
            else:
                self.game_controller.request_new_random_path(self)
            return Directions.Nothing

        x_diff = self.next_target[0] - self.x
        y_diff = self.next_target[1] - self.y
        if x_diff == 0:
            if y_diff > 0:
                return Directions.Down
            return Directions.Up
        if y_diff == 0:
            if x_diff < 0:
                return Directions.Left
            return Directions.Right
        if self._renderer.get_current_mode() == GhostMoves.Chase and not self._renderer.is_special_ability_active():
            self.request_path_to_player(self)
        else:
            self.game_controller.request_new_random_path(self)
        return Directions.Nothing

    def request_path_to_player(self, input_ghost):
        """
        Function to get the shortest path from the ghost to the main character and set a path to the main character.
        :param input_ghost: ghost that will move towards the player
        """
        player_position = screen_to_maze(input_ghost._renderer.get_hero_position())
        curr_maze_coords = screen_to_maze(input_ghost.get_position())
        path = self.game_controller.p.get_path(curr_maze_coords[1], curr_maze_coords[0],
                                               player_position[1], player_position[0])
        new_path = [maze_to_screen(item) for item in path]
        input_ghost.set_new_path(new_path)

    def automatic_move(self, input_direction: Directions):
        """
        Set the ghost's position based on the direction the ghost is moving in.
        :param input_direction: direction that the ghost is moving in
        """
        if input_direction == Directions.Up:
            self.set_position(self.x, self.y - 1)
        elif input_direction == Directions.Down:
            self.set_position(self.x, self.y + 1)
        elif input_direction == Directions.Left:
            self.set_position(self.x - 1, self.y)
        elif input_direction == Directions.Right:
            self.set_position(self.x + 1, self.y)

    def draw(self):
        """
        Choose an image for the ghost based on whether the special ability is active.
        Call the parent class' draw function using the current ghost.
        """
        if self._renderer.is_special_ability_active():
            self.image = self.fright_sprite
        else:
            self.image = self.normal_sprite
        super(Ghost, self).draw()


class Cookie(GameObject):
    """
    For cookies in the game inheriting from the game object class.
    """
    def __init__(self, in_surface, x, y):
        super().__init__(in_surface, x, y, 4, (255, 255, 0), True)


class Powerup(GameObject):
    """
    Used for powerups in the game inheriting from the game object class.
    """
    def __init__(self, in_surface, x, y):
        super().__init__(in_surface, x, y, 6, (255, 255, 255), True)


class Pathfinder:
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
        self.pf = tcod.path.AStar(cost=cost, diagonal=0)

    def get_path(self, from_x, from_y, to_x, to_y) -> object:
        """
        Calculate and return the path as a series of steps.
        :param from_x: x coordinate of the maze
        :param from_y: y coordinate of the maze
        :param to_x: x coordinate to go to
        :param to_y: y coordinate to go to
        :return: series of paths to get from one location in the maze to another
        """
        res = self.pf.get_path(from_x, from_y, to_x, to_y)
        return [(sub[1], sub[0]) for sub in res]


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
            "X XXXX XXXXX XX XXXXX XXXX X",
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
            "X                          X",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]  # X = wall, P = pac-man, G = ghost

        self.numpy_maze = []  # use to convert maze where 0 is wall and 1 is free space
        self.cookie_spaces = []
        self.powerup_spaces = []
        self.reachable_spaces = []  # holds the passable parts of the array
        self.ghost_spawns = []
        self.ghost_colors = [
            "images/ghosts.png",
            "images/pinky.png",
            "images/clyde.png",
            "images/inky.png"
        ]
        self.size = (0, 0)
        self.convert_maze_to_np()
        self.p = Pathfinder(self.numpy_maze)

    def request_new_random_path(self, input_ghost: Ghost):
        """
        Function to generate a random path for each ghost in the game using the pathfinder class.
        :param input_ghost: ghost object
        :return: Nothing, sets the new path for a given ghost
        """
        random_space = random.choice(self.reachable_spaces)
        current_maze_coord = screen_to_maze(input_ghost.get_position())
        path = self.p.get_path(current_maze_coord[1], current_maze_coord[0], random_space[1],
                               random_space[0])
        test_path = [maze_to_screen(item) for item in path]
        input_ghost.set_new_path(test_path)

    def convert_maze_to_np(self):
        """
        Converts the ascii maze above to a numpy maze for easy pathfinding.
        :return: Returns Nothing, but fills the numpy maze with 0's (walls) and 1's (free space).
        """
        for x, row in enumerate(self.ascii_maze):
            self.size = (len(row), x + 1)
            binary_row = []
            for y, column in enumerate(row):
                if column == "G":
                    self.ghost_spawns.append((y, x))

                if column == "X":
                    binary_row.append(0)
                else:
                    binary_row.append(1)
                    self.cookie_spaces.append((y, x))
                    self.reachable_spaces.append((y, x))

            self.numpy_maze.append(binary_row)

        for i in range(4):
            random_choice = random.choice(self.reachable_spaces)
            self.powerup_spaces.append((random_choice[0], random_choice[1]))


if __name__ == "__main__":
    unified_size = 32
    pacman_game = GameController()
    size = pacman_game.size
    game_renderer = RenderGame(size[0] * unified_size, size[1] * unified_size)

    for y, row in enumerate(pacman_game.numpy_maze):
        for x, column in enumerate(row):
            if column == 0:
                game_renderer.add_wall(WallObject(game_renderer, x, y, unified_size))

    for cookie_space in pacman_game.cookie_spaces:
        translated = maze_to_screen(cookie_space)
        cookie = Cookie(game_renderer, translated[0] + unified_size / 2, translated[1] + unified_size / 2)
        game_renderer.add_cookie(cookie)

    for powerup_space in pacman_game.powerup_spaces:
        translated = maze_to_screen(powerup_space)
        powerup = Powerup(game_renderer, translated[0] + unified_size / 2, translated[1] + unified_size / 2)
        game_renderer.add_powerup(powerup)

    for i, ghost_spawn in enumerate(pacman_game.ghost_spawns):
        translated = maze_to_screen(ghost_spawn)
        ghost = Ghost(game_renderer, translated[0], translated[1], unified_size, pacman_game,
                      pacman_game.ghost_colors[i % 4])
        game_renderer.add_ghost(ghost)

    pacman = Hero(game_renderer, unified_size, unified_size, unified_size)
    game_renderer.add_hero(pacman)
    game_renderer.set_current_mode(GhostMoves.Chase)
    game_renderer.tick(120)
