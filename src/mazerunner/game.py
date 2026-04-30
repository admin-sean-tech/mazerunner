import json
import os

import pygame

from mazerunner.config_dialog import ConfigDialog
from mazerunner.hamburger_menu import HamburgerMenu
from mazerunner.maze_editor import MazeEditor
from mazerunner.maze_load_dialog import MazeLoadDialog
from mazerunner.settings import *

_PLAYER_RADIUS = 10   # collision half-size (px)
_PLAYER_SPEED  = 160  # px/second


# ---------------------------------------------------------------------------
# Maze rendering
# ---------------------------------------------------------------------------

def _draw_maze(surface: pygame.Surface, maze: dict):
    grid = maze["grid"]
    for row, cells in enumerate(grid):
        for col, cell in enumerate(cells):
            pygame.draw.rect(
                surface, CELL_COLORS[cell],
                (col * CELL_SIZE, TOP_BAR_H + row * CELL_SIZE, CELL_SIZE, CELL_SIZE),
            )


# ---------------------------------------------------------------------------
# Player icon  (simple person, fits in a CELL_SIZE × CELL_SIZE cell)
# ---------------------------------------------------------------------------

def _draw_player(surface: pygame.Surface, px: float, py: float):
    x, y = int(px), int(py)
    pygame.draw.circle(surface, (255, 213, 128), (x, y - 9), 5)                    # head
    pygame.draw.line(surface, (70, 130, 200), (x, y - 4), (x, y + 5), 3)           # body
    pygame.draw.line(surface, (70, 130, 200), (x - 5, y - 1), (x + 5, y - 1), 2)  # arms
    pygame.draw.line(surface, (50, 50, 100), (x, y + 5), (x - 4, y + 14), 2)       # left leg
    pygame.draw.line(surface, (50, 50, 100), (x, y + 5), (x + 4, y + 14), 2)       # right leg


# ---------------------------------------------------------------------------
# Collision helpers
# ---------------------------------------------------------------------------

def _is_wall(grid: list, row: int, col: int) -> bool:
    if row < 0 or row >= len(grid):
        return True
    row_data = grid[row]
    if col < 0 or col >= len(row_data):
        return True
    return row_data[col] == CELL_WALL


def _move_player(pos: pygame.Vector2, grid: list, dx: float, dy: float, dt: float):
    """Move pos by (dx, dy) direction at _PLAYER_SPEED, blocked by walls."""
    r = _PLAYER_RADIUS - 1  # slightly smaller hitbox for comfortable navigation

    if dx != 0:
        new_x = pos.x + dx * _PLAYER_SPEED * dt
        edge_x = new_x + (r if dx > 0 else -r)
        row_top = (int(pos.y) - r - TOP_BAR_H) // CELL_SIZE
        row_bot = (int(pos.y) + r - TOP_BAR_H) // CELL_SIZE
        col = int(edge_x) // CELL_SIZE
        if not (_is_wall(grid, row_top, col) or _is_wall(grid, row_bot, col)):
            pos.x = new_x

    if dy != 0:
        new_y = pos.y + dy * _PLAYER_SPEED * dt
        edge_y = new_y + (r if dy > 0 else -r)
        col_l = int(pos.x - r) // CELL_SIZE
        col_r = int(pos.x + r) // CELL_SIZE
        row = (int(edge_y) - TOP_BAR_H) // CELL_SIZE
        if not (_is_wall(grid, row, col_l) or _is_wall(grid, row, col_r)):
            pos.y = new_y


def _player_cell(pos: pygame.Vector2) -> tuple[int, int]:
    col = int(pos.x) // CELL_SIZE
    row = (int(pos.y) - TOP_BAR_H) // CELL_SIZE
    return row, col


def _maze_start_pos(maze: dict) -> pygame.Vector2:
    start = maze.get("start")
    if start:
        row, col = start
        return pygame.Vector2(
            col * CELL_SIZE + CELL_SIZE // 2,
            TOP_BAR_H + row * CELL_SIZE + CELL_SIZE // 2,
        )
    # fallback: centre of the grid
    rows = len(maze.get("grid", []))
    cols = len(maze["grid"][0]) if rows else 0
    return pygame.Vector2(cols * CELL_SIZE // 2, TOP_BAR_H + rows * CELL_SIZE // 2)


# ---------------------------------------------------------------------------
# Main game
# ---------------------------------------------------------------------------

class MazeRunner(object):
    def __init__(self):
        self.config = {"game_mode": GAME_MODE}

    def _save(self, player_pos):
        data = {"player_pos": [player_pos.x, player_pos.y], "config": self.config}
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)

    def start(self):
        print("Starting MazeRunner!")
        pygame.init()
        pygame.display.set_caption("Maze Runner")
        screen = pygame.display.set_mode(SCREEN_SIZE)
        clock = pygame.time.Clock()
        running = True
        dt = 0

        active_maze: dict | None = None
        game_won = False
        player_pos = pygame.Vector2(0, 0)

        menu = HamburgerMenu()
        config_dialog = ConfigDialog(self.config)
        maze_editor = MazeEditor()
        load_dialog = MazeLoadDialog()

        while running:
            # ----------------------------------------------------------------
            # Events
            # ----------------------------------------------------------------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue

                if maze_editor.handle_event(event):
                    continue
                if load_dialog.handle_event(event):
                    continue
                if config_dialog.handle_event(event):
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = menu.handle_click(event.pos)
                    if action == "Save":
                        self._save(player_pos)
                    elif action == "Load":
                        load_dialog.open()
                    elif action == "Config":
                        config_dialog.visible = True
                    elif action == "Maze Editor":
                        maze_editor.open()
                    elif action == "Exit":
                        running = False

            # Check if a maze was just selected in the load dialog
            new_maze = load_dialog.pop_loaded()
            if new_maze is not None:
                active_maze = new_maze
                game_won = False
                player_pos = _maze_start_pos(active_maze)

            # ----------------------------------------------------------------
            # Draw
            # ----------------------------------------------------------------
            screen.fill((30, 30, 30))

            if active_maze:
                _draw_maze(screen, active_maze)
                _draw_player(screen, player_pos.x, player_pos.y)
            else:
                font = pygame.font.SysFont(None, 34)
                hint = font.render("Open the menu and choose Load to start.", True, (100, 100, 100))
                screen.blit(hint, (screen.get_width() // 2 - hint.get_width() // 2,
                                   screen.get_height() // 2 - hint.get_height() // 2))

            # Top bar and menu drawn after game content so they sit on top
            pygame.draw.rect(screen, (55, 55, 55), (0, 0, screen.get_width(), TOP_BAR_H))
            menu.draw(screen)

            # Win overlay (drawn before dialogs so dialogs appear above it)
            if game_won:
                overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 110))
                screen.blit(overlay, (0, 0))
                wf = pygame.font.SysFont(None, 64)
                wt = wf.render("You reached the exit!", True, (255, 220, 80))
                screen.blit(wt, (screen.get_width() // 2 - wt.get_width() // 2,
                                  screen.get_height() // 2 - wt.get_height() // 2 - 20))
                sf = pygame.font.SysFont(None, 30)
                st = sf.render("Load another maze from the menu to play again.", True, (180, 180, 180))
                screen.blit(st, (screen.get_width() // 2 - st.get_width() // 2,
                                  screen.get_height() // 2 + 30))

            config_dialog.draw(screen)
            maze_editor.draw(screen)
            load_dialog.draw(screen)

            # ----------------------------------------------------------------
            # Player movement + win check (blocked while any overlay is open)
            # ----------------------------------------------------------------
            any_overlay = (maze_editor.visible or config_dialog.visible or load_dialog.visible)
            if active_maze and not game_won and not any_overlay:
                keys = pygame.key.get_pressed()
                dx = float(keys[pygame.K_d] - keys[pygame.K_a])
                dy = float(keys[pygame.K_s] - keys[pygame.K_w])
                if dx != 0 or dy != 0:
                    _move_player(player_pos, active_maze["grid"], dx, dy, dt)

                end = active_maze.get("end")
                if end and _player_cell(player_pos) == (end[0], end[1]):
                    game_won = True

            pygame.display.flip()
            dt = clock.tick(60) / 1000

        print("Exiting MazeRunner!")
        pygame.quit()
