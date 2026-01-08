"""
Snake Lite - CSE 310 Game Framework Module
Python + Arcade

Controls:
- Arrow keys: change direction
Goal:
- Eat food to score points and grow
Difficulty:
- Level increases every 5 points, snake moves faster
"""

import random
import arcade
import warnings
from arcade.exceptions import PerformanceWarning

warnings.filterwarnings("ignore", category=PerformanceWarning)

# -----------------------------
# Configuration constants
# -----------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Snake Lite (Python Arcade)"

CELL_SIZE = 20  # grid size for snake movement
UI_HEIGHT = 50  # pixels reserved for score at the top
GRID_COLS = SCREEN_WIDTH // CELL_SIZE
GRID_ROWS = (SCREEN_HEIGHT - UI_HEIGHT) // CELL_SIZE

MOVE_INTERVAL_START = 0.20  # seconds between moves at level 1
MOVE_INTERVAL_MIN = 0.06  # fastest allowed move interval


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp a number between min_value and max_value."""
    return max(min_value, min(value, max_value))


def random_grid_position(excluded: set[tuple[int, int]]) -> tuple[int, int]:
    """
    Return a random (col, row) grid position not in excluded.
    Ensures food doesn't spawn on the snake or in the UI area.
    """
    while True:
        col = random.randrange(0, GRID_COLS)
        row = random.randrange(0, GRID_ROWS)
        pos = (col, row)

        screen_x, screen_y = (  # noqa: F841
            pos[0] * CELL_SIZE + CELL_SIZE / 2,
            pos[1] * CELL_SIZE + CELL_SIZE / 2,
        )
        ui_boundary = SCREEN_HEIGHT - UI_HEIGHT

        if pos not in excluded and screen_y < ui_boundary:
            return pos


class SnakeGame(arcade.Window):
    """Main window class for the Snake game."""

    def __init__(self):
        """Initialize the Snake game window with default settings and initial game state."""
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)

        # Game state
        self.score = 0
        self.level = 1
        self.game_over = False

        # Snake state (list of (col,row) segments; head at index 0)
        self.snake: list[tuple[int, int]] = []
        self.direction = (1, 0)  # moving right initially
        self.next_direction = (1, 0)

        # Food position in grid coordinates
        self.food = (0, 0)

        # Timing for grid-based movement
        self.move_interval = MOVE_INTERVAL_START
        self.time_since_move = 0.0

    def setup(self):
        """Initialize or reset the game to a starting state."""
        self.score = 0
        self.level = 1
        self.game_over = False

        # Start snake at a random position (ensuring enough space for initial length)
        start_col = random.randrange(2, GRID_COLS - 2)
        start_row = random.randrange(1, GRID_ROWS - 1)
        self.snake = [
            (start_col, start_row),
            (start_col - 1, start_row),
            (start_col - 2, start_row),
        ]

        self.direction = (1, 0)
        self.next_direction = (1, 0)

        # Place food not on the snake
        self.spawn_food()

        # Reset speed
        self.move_interval = MOVE_INTERVAL_START
        self.time_since_move = 0.0

    def spawn_food(self):
        """Spawn food at a random grid location not occupied by the snake."""
        excluded = set(self.snake)
        self.food = random_grid_position(excluded)

    def on_draw(self):
        """Render the screen."""
        self.clear()

        # Draw HUD
        arcade.draw_text(
            f"Score: {self.score}   Level: {self.level}",
            10,
            SCREEN_HEIGHT - 30,
            arcade.color.WHITE,
            16,
        )

        # Draw separator line between game area and UI
        separator_y = SCREEN_HEIGHT - UI_HEIGHT
        arcade.draw_line(
            0, separator_y, SCREEN_WIDTH, separator_y, arcade.color.DARK_GRAY, 2
        )

        if self.game_over:
            arcade.draw_text(
                "GAME OVER - Press R to Restart",
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                arcade.color.RED,
                24,
                anchor_x="center",
            )
            return

        # Draw food
        fx, fy = self.grid_to_screen_center(*self.food)
        arcade.draw.draw_circle_filled(fx, fy, CELL_SIZE * 0.45, arcade.color.LIME)

        # Draw snake
        for i, (col, row) in enumerate(self.snake):
            x, y = self.grid_to_screen_center(col, row)
            color = arcade.color.CYAN if i == 0 else arcade.color.DARK_CYAN
            half = (CELL_SIZE - 2) / 2
            arcade.draw.draw_lrbt_rectangle_filled(
                x - half,  # left
                x + half,  # right
                y - half,  # bottom
                y + half,  # top
                color,
            )

    def on_update(self, delta_time: float):
        """Update game logic each frame."""
        if self.game_over:
            return

        # Track time until the next grid movement
        self.time_since_move += delta_time
        if self.time_since_move >= self.move_interval:
            self.time_since_move = 0.0
            self.step_snake()

    def step_snake(self):
        """
        Move the snake one grid cell and handle collisions, eating food,
        and level progression.
        """
        # Apply buffered direction change (prevents instant reverse)
        self.direction = self.next_direction

        head_col, head_row = self.snake[0]
        dx, dy = self.direction
        new_head = (head_col + dx, head_row + dy)

        # Collision with walls -> game over
        if not (0 <= new_head[0] < GRID_COLS and 0 <= new_head[1] < GRID_ROWS):
            self.game_over = True
            return

        # Collision with self -> game over
        if new_head in self.snake:
            self.game_over = True
            return

        # Move: insert new head
        self.snake.insert(0, new_head)

        # Check food
        if new_head == self.food:
            self.score += 1
            self.spawn_food()
            self.update_level_and_speed()
            # Do NOT remove tail (snake grows)
        else:
            # Remove tail to keep length constant
            self.snake.pop()

    def update_level_and_speed(self):
        """
        Increase level every 5 points and speed up snake.
        """
        new_level = 1 + (self.score // 5)
        if new_level != self.level:
            self.level = new_level

        # Speed increases as level increases (interval decreases)
        # Clamp to avoid becoming impossible.
        target_interval = MOVE_INTERVAL_START - (self.level - 1) * 0.02
        self.move_interval = clamp(
            target_interval, MOVE_INTERVAL_MIN, MOVE_INTERVAL_START
        )

    def on_key_press(self, key: int, modifiers: int):
        """Handle keyboard input for direction changes and restarting."""
        if key == arcade.key.R:
            self.setup()
            return

        if self.game_over:
            return

        # Determine new direction based on arrow keys
        if key == arcade.key.UP:
            self.try_set_direction(0, 1)
        elif key == arcade.key.DOWN:
            self.try_set_direction(0, -1)
        elif key == arcade.key.LEFT:
            self.try_set_direction(-1, 0)
        elif key == arcade.key.RIGHT:
            self.try_set_direction(1, 0)

    def try_set_direction(self, dx: int, dy: int):
        """
        Attempt to change direction.
        Prevents reversing directly into yourself (e.g., right -> left).
        """
        current_dx, current_dy = self.direction
        # Block direct reverse
        if (dx, dy) == (-current_dx, -current_dy):
            return
        self.next_direction = (dx, dy)

    @staticmethod
    def grid_to_screen_center(col: int, row: int) -> tuple[float, float]:
        """Convert grid coordinates (col,row) to screen center pixel coordinates."""
        x = col * CELL_SIZE + CELL_SIZE / 2
        y = row * CELL_SIZE + CELL_SIZE / 2
        return x, y


def main():
    """Program entry point."""
    window = SnakeGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
