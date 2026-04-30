import glob
import json
import os
import time

import pygame

from mazerunner.settings import (
    CELL_EMPTY, CELL_WALL, CELL_START, CELL_END, CELL_COLORS as _CELL_COLORS,
    GRID_COLS, GRID_ROWS, CELL_SIZE, PANEL_W,
    TOP_BAR_H, EDITOR_TOOLBAR_H, MAZES_DIR,
)

_PANEL_ITEM_H = 34
_PANEL_HEADER_H = 28


# ---------------------------------------------------------------------------
# Maze editor
# ---------------------------------------------------------------------------

class MazeEditor:
    _TOOLS = ["Wall", "Erase", "Start", "End"]

    def __init__(self):
        self.visible = False
        self.tool = "Wall"
        self.grid = self._empty_grid()
        self.start_cell: tuple[int, int] | None = None
        self.end_cell: tuple[int, int] | None = None
        self.current_name: str | None = None

        self._dragging = False
        self._maze_list: list[str] = []

        # confirm-load popup
        self._pending_load: str | None = None
        self._confirm_yes: pygame.Rect | None = None
        self._confirm_no: pygame.Rect | None = None

        # name-input popup
        self._show_name_input = False
        self._name_input_text = ""
        self._ni_save_btn: pygame.Rect | None = None
        self._ni_cancel_btn: pygame.Rect | None = None
        self._ni_error = ""

        # cached button rects (rebuilt each draw)
        self._font = None
        self._tool_btns: dict[str, pygame.Rect] = {}
        self._action_btns: dict[str, pygame.Rect] = {}
        self._panel_items: list[tuple[str | None, pygame.Rect]] = []

    # ------------------------------------------------------------------ api

    def open(self):
        self.visible = True
        self._refresh_maze_list()

    # ---------------------------------------------------------------- fonts

    @property
    def font(self):
        if self._font is None:
            self._font = pygame.font.SysFont(None, 26)
        return self._font

    # ------------------------------------------------------------ geometry

    def _grid_top(self):
        return TOP_BAR_H + EDITOR_TOOLBAR_H

    def _cell_at(self, pos) -> tuple[int, int] | None:
        x, y = pos
        gt = self._grid_top()
        if x < PANEL_W or y < gt:
            return None
        col = (x - PANEL_W) // CELL_SIZE
        row = (y - gt) // CELL_SIZE
        if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
            return row, col
        return None

    # --------------------------------------------------------- maze state

    def _empty_grid(self):
        return [[CELL_EMPTY] * GRID_COLS for _ in range(GRID_ROWS)]

    def _apply(self, row, col):
        if self.tool == "Wall":
            if self.start_cell == (row, col):
                self.start_cell = None
            if self.end_cell == (row, col):
                self.end_cell = None
            self.grid[row][col] = CELL_WALL
        elif self.tool == "Erase":
            if self.start_cell == (row, col):
                self.start_cell = None
            if self.end_cell == (row, col):
                self.end_cell = None
            self.grid[row][col] = CELL_EMPTY
        elif self.tool == "Start":
            if self.start_cell:
                r, c = self.start_cell
                self.grid[r][c] = CELL_EMPTY
            self.start_cell = (row, col)
            self.grid[row][col] = CELL_START
        elif self.tool == "End":
            if self.end_cell:
                r, c = self.end_cell
                self.grid[r][c] = CELL_EMPTY
            self.end_cell = (row, col)
            self.grid[row][col] = CELL_END

    def _new_maze(self):
        self.grid = self._empty_grid()
        self.start_cell = None
        self.end_cell = None
        self.current_name = None

    def _do_load(self, name: str):
        path = os.path.join(MAZES_DIR, f"{name}.json")
        if not os.path.exists(path):
            return
        with open(path) as f:
            data = json.load(f)
        self.grid = data["grid"]
        s, e = data.get("start"), data.get("end")
        self.start_cell = tuple(s) if s else None
        self.end_cell = tuple(e) if e else None
        self.current_name = name

    def _do_save(self, name: str):
        os.makedirs(MAZES_DIR, exist_ok=True)
        path = os.path.join(MAZES_DIR, f"{name}.json")
        with open(path, "w") as f:
            json.dump({
                "cols": GRID_COLS, "rows": GRID_ROWS, "cell_size": CELL_SIZE,
                "grid": self.grid,
                "start": list(self.start_cell) if self.start_cell else None,
                "end": list(self.end_cell) if self.end_cell else None,
            }, f)
        self.current_name = name
        self._refresh_maze_list()

    def _refresh_maze_list(self):
        if not os.path.isdir(MAZES_DIR):
            self._maze_list = []
            return
        files = glob.glob(os.path.join(MAZES_DIR, "*.json"))
        self._maze_list = sorted(
            os.path.splitext(os.path.basename(f))[0] for f in files
        )

    # --------------------------------------------------------------- draw

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        sw, sh = surface.get_size()
        surface.fill((20, 20, 20))

        self._draw_header(surface, sw)
        self._draw_toolbar(surface, sw)
        self._draw_panel(surface, sh)
        self._draw_grid(surface)

        if self._pending_load is not None:
            self._draw_confirm_popup(surface, sw, sh)
        elif self._show_name_input:
            self._draw_name_input_popup(surface, sw, sh)

    def _draw_header(self, surface, sw):
        pygame.draw.rect(surface, (40, 40, 40), (0, 0, sw, TOP_BAR_H))
        title = "Maze Editor" + (f"  —  {self.current_name}" if self.current_name else "  —  New Maze")
        font = pygame.font.SysFont(None, 30)
        t = font.render(title, True, (200, 200, 200))
        surface.blit(t, (sw // 2 - t.get_width() // 2, TOP_BAR_H // 2 - t.get_height() // 2))

    def _draw_toolbar(self, surface, sw):
        pygame.draw.rect(surface, (45, 45, 45), (0, TOP_BAR_H, sw, EDITOR_TOOLBAR_H))
        btn_y = TOP_BAR_H + 6
        btn_h = EDITOR_TOOLBAR_H - 12

        self._tool_btns = {}
        bx = PANEL_W + 8
        for label in self._TOOLS:
            w = self.font.size(label)[0] + 20
            r = pygame.Rect(bx, btn_y, w, btn_h)
            active = self.tool == label
            pygame.draw.rect(surface, (80, 120, 180) if active else (65, 65, 65), r, border_radius=4)
            txt = self.font.render(label, True, (230, 230, 230))
            surface.blit(txt, (r.x + 10, r.y + (btn_h - txt.get_height()) // 2))
            self._tool_btns[label] = r
            bx += w + 6

        self._action_btns = {}
        action_defs = [("Cancel", (80, 80, 80)), ("Save", (70, 140, 70)), ("Clear", (140, 70, 70))]
        abx = sw - 8
        for label, color in action_defs:
            w = self.font.size(label)[0] + 20
            abx -= w
            r = pygame.Rect(abx, btn_y, w, btn_h)
            abx -= 6
            pygame.draw.rect(surface, color, r, border_radius=4)
            txt = self.font.render(label, True, (230, 230, 230))
            surface.blit(txt, (r.x + 10, r.y + (btn_h - txt.get_height()) // 2))
            self._action_btns[label] = r

    def _draw_panel(self, surface, sh):
        gt = self._grid_top()
        pygame.draw.rect(surface, (32, 32, 32), (0, gt, PANEL_W, sh - gt))
        pygame.draw.line(surface, (70, 70, 70), (PANEL_W, gt), (PANEL_W, sh), 1)

        # Section header
        pygame.draw.rect(surface, (40, 40, 40), (0, gt, PANEL_W, _PANEL_HEADER_H))
        ht = self.font.render("Mazes", True, (140, 140, 140))
        surface.blit(ht, (PANEL_W // 2 - ht.get_width() // 2, gt + (_PANEL_HEADER_H - ht.get_height()) // 2))

        self._panel_items = []
        item_y = gt + _PANEL_HEADER_H
        mouse = pygame.mouse.get_pos()

        # "New" entry
        new_rect = pygame.Rect(0, item_y, PANEL_W, _PANEL_ITEM_H)
        is_new_current = self.current_name is None
        hovered = new_rect.collidepoint(mouse) and not is_new_current
        bg = (50, 90, 50) if is_new_current else ((55, 75, 55) if hovered else (38, 38, 38))
        pygame.draw.rect(surface, bg, new_rect)
        txt = self.font.render("+ New", True, (160, 220, 160) if is_new_current else (130, 190, 130))
        surface.blit(txt, (new_rect.x + 10, new_rect.y + (_PANEL_ITEM_H - txt.get_height()) // 2))
        self._panel_items.append((None, new_rect))
        item_y += _PANEL_ITEM_H

        pygame.draw.line(surface, (55, 55, 55), (4, item_y), (PANEL_W - 4, item_y), 1)
        item_y += 1

        for name in self._maze_list:
            if item_y + _PANEL_ITEM_H > sh:
                break
            r = pygame.Rect(0, item_y, PANEL_W, _PANEL_ITEM_H)
            is_current = name == self.current_name
            hovered = r.collidepoint(mouse) and not is_current
            if is_current:
                bg = (55, 85, 145)
            elif hovered:
                bg = (50, 50, 60)
            else:
                bg = (38, 38, 38)
            pygame.draw.rect(surface, bg, r)

            max_chars = 17
            display = name if len(name) <= max_chars else name[:max_chars - 1] + "…"
            color = (210, 225, 255) if is_current else (185, 185, 185)
            txt = self.font.render(display, True, color)
            surface.blit(txt, (r.x + 10, r.y + (_PANEL_ITEM_H - txt.get_height()) // 2))
            self._panel_items.append((name, r))
            item_y += _PANEL_ITEM_H

    def _draw_grid(self, surface):
        gt = self._grid_top()
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                cx = PANEL_W + col * CELL_SIZE
                cy = gt + row * CELL_SIZE
                cell_rect = pygame.Rect(cx, cy, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, _CELL_COLORS[self.grid[row][col]], cell_rect)
                pygame.draw.rect(surface, (160, 160, 160), cell_rect, 1)

    def _draw_confirm_popup(self, surface, sw, sh):
        w, h = 420, 160
        dlg = pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)
        self._draw_overlay(surface, sw, sh)
        pygame.draw.rect(surface, (45, 45, 45), dlg, border_radius=8)
        pygame.draw.rect(surface, (90, 90, 90), dlg, 2, border_radius=8)

        name = self._pending_load or ""
        display = name if len(name) <= 22 else name[:21] + "…"
        surface.blit(self.font.render(f'Load  "{display}" ?', True, (210, 210, 210)),
                     (dlg.x + 16, dlg.y + 22))
        surface.blit(self.font.render("Unsaved changes will be lost.", True, (140, 140, 140)),
                     (dlg.x + 16, dlg.y + 52))

        yes_btn = pygame.Rect(dlg.right - 174, dlg.bottom - 44, 70, 30)
        no_btn  = pygame.Rect(dlg.right - 94,  dlg.bottom - 44, 70, 30)
        self._confirm_yes, self._confirm_no = yes_btn, no_btn
        for btn, label, color in [
            (yes_btn, "Yes", (65, 130, 65)),
            (no_btn,  "No",  (130, 65, 65)),
        ]:
            pygame.draw.rect(surface, color, btn, border_radius=4)
            t = self.font.render(label, True, (230, 230, 230))
            surface.blit(t, (btn.x + (btn.w - t.get_width()) // 2, btn.y + (btn.h - t.get_height()) // 2))

    def _draw_name_input_popup(self, surface, sw, sh):
        w, h = 440, 190
        dlg = pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)
        self._draw_overlay(surface, sw, sh)
        pygame.draw.rect(surface, (45, 45, 45), dlg, border_radius=8)
        pygame.draw.rect(surface, (90, 90, 90), dlg, 2, border_radius=8)

        font_title = pygame.font.SysFont(None, 30)
        surface.blit(font_title.render("Save Maze As", True, (210, 210, 210)),
                     (dlg.x + 16, dlg.y + 16))

        input_rect = pygame.Rect(dlg.x + 16, dlg.y + 58, dlg.w - 32, 34)
        pygame.draw.rect(surface, (55, 55, 55), input_rect, border_radius=4)
        pygame.draw.rect(surface, (90, 120, 170), input_rect, 2, border_radius=4)
        cursor = "|" if int(time.time() * 2) % 2 == 0 else ""
        txt = self.font.render(self._name_input_text + cursor, True, (220, 220, 220))
        surface.blit(txt, (input_rect.x + 8, input_rect.y + (34 - txt.get_height()) // 2))

        if self._ni_error:
            surface.blit(self.font.render(self._ni_error, True, (210, 100, 100)),
                         (dlg.x + 16, dlg.y + 100))

        save_ok = bool(self._name_input_text.strip())
        save_btn   = pygame.Rect(dlg.right - 174, dlg.bottom - 44, 70, 30)
        cancel_btn = pygame.Rect(dlg.right - 94,  dlg.bottom - 44, 70, 30)
        self._ni_save_btn, self._ni_cancel_btn = save_btn, cancel_btn
        for btn, label, color in [
            (save_btn,   "Save",   (65, 130, 65) if save_ok else (45, 80, 45)),
            (cancel_btn, "Cancel", (80, 80, 80)),
        ]:
            pygame.draw.rect(surface, color, btn, border_radius=4)
            t = self.font.render(label, True, (230, 230, 230))
            surface.blit(t, (btn.x + (btn.w - t.get_width()) // 2, btn.y + (btn.h - t.get_height()) // 2))

    @staticmethod
    def _draw_overlay(surface, sw, sh):
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

    # ------------------------------------------------------------ events

    def handle_event(self, event) -> bool:
        if not self.visible:
            return False

        if self._pending_load is not None:
            return self._handle_confirm_event(event)
        if self._show_name_input:
            return self._handle_name_input_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.visible = False
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            for name, r in self._panel_items:
                if r.collidepoint(pos):
                    if name is None:
                        self._new_maze()
                    else:
                        self._pending_load = name
                    return True

            for label, r in self._tool_btns.items():
                if r.collidepoint(pos):
                    self.tool = label
                    return True

            for label, r in self._action_btns.items():
                if r.collidepoint(pos):
                    if label == "Save":
                        if self.current_name is None:
                            self._name_input_text = ""
                            self._ni_error = ""
                            self._show_name_input = True
                        else:
                            self._do_save(self.current_name)
                    elif label == "Clear":
                        self.grid = self._empty_grid()
                        self.start_cell = None
                        self.end_cell = None
                    elif label == "Cancel":
                        self.visible = False
                    return True

            cell = self._cell_at(pos)
            if cell:
                self._apply(*cell)
                self._dragging = True
            return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
            return True

        if event.type == pygame.MOUSEMOTION and self._dragging:
            if self.tool in ("Wall", "Erase"):
                cell = self._cell_at(event.pos)
                if cell:
                    self._apply(*cell)
            return True

        return True  # consume all events while editor is open

    def _handle_confirm_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._pending_load = None
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self._pending_load is not None:
                    self._do_load(self._pending_load)
                self._pending_load = None
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._confirm_yes and self._confirm_yes.collidepoint(event.pos):
                if self._pending_load is not None:
                    self._do_load(self._pending_load)
                self._pending_load = None
            elif self._confirm_no and self._confirm_no.collidepoint(event.pos):
                self._pending_load = None
            return True
        return True

    def _handle_name_input_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            key = event.key
            if key == pygame.K_ESCAPE:
                self._show_name_input = False
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._try_save_named()
            elif key == pygame.K_BACKSPACE:
                self._name_input_text = self._name_input_text[:-1]
                self._ni_error = ""
            else:
                ch = event.unicode
                if ch.isprintable() and ch not in r'/\:*?"<>|' and len(self._name_input_text) < 40:
                    self._name_input_text += ch
                    self._ni_error = ""
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._ni_save_btn and self._ni_save_btn.collidepoint(event.pos):
                self._try_save_named()
            elif self._ni_cancel_btn and self._ni_cancel_btn.collidepoint(event.pos):
                self._show_name_input = False
            return True
        return True

    def _try_save_named(self):
        name = self._name_input_text.strip()
        if not name:
            self._ni_error = "Name cannot be empty."
            return
        self._do_save(name)
        self._show_name_input = False
