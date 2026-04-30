import glob
import json
import os

import pygame

from mazerunner.settings import MAZES_DIR


class MazeLoadDialog:
    _ITEM_H = 38

    def __init__(self):
        self.visible = False
        self._maze_list: list[str] = []
        self._selected: str | None = None
        self._loaded_data: dict | None = None
        self._font = None
        self._title_font = None
        self._item_rects: list[tuple[str, pygame.Rect]] = []
        self._load_btn: pygame.Rect | None = None
        self._cancel_btn: pygame.Rect | None = None

    @property
    def font(self):
        if self._font is None:
            self._font = pygame.font.SysFont(None, 28)
        return self._font

    @property
    def title_font(self):
        if self._title_font is None:
            self._title_font = pygame.font.SysFont(None, 34)
        return self._title_font

    def open(self):
        self.visible = True
        self._selected = None
        self._loaded_data = None
        self._refresh()

    def pop_loaded(self) -> dict | None:
        """Returns maze data if user just confirmed a load, then clears it."""
        data = self._loaded_data
        self._loaded_data = None
        return data

    def _refresh(self):
        if not os.path.isdir(MAZES_DIR):
            self._maze_list = []
            return
        files = glob.glob(os.path.join(MAZES_DIR, "*.json"))
        self._maze_list = sorted(
            os.path.splitext(os.path.basename(f))[0] for f in files
        )

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        sw, sh = surface.get_size()
        w, h = 500, 440
        dlg = pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (38, 38, 38), dlg, border_radius=8)
        pygame.draw.rect(surface, (90, 90, 90), dlg, 2, border_radius=8)

        title = self.title_font.render("Load Maze", True, (220, 220, 220))
        surface.blit(title, (dlg.x + 16, dlg.y + 14))

        # List area
        list_rect = pygame.Rect(dlg.x + 16, dlg.y + 58, dlg.w - 32, dlg.h - 114)
        pygame.draw.rect(surface, (28, 28, 28), list_rect, border_radius=4)
        pygame.draw.rect(surface, (70, 70, 70), list_rect, 1, border_radius=4)

        self._item_rects = []
        mouse = pygame.mouse.get_pos()

        if not self._maze_list:
            msg = self.font.render("No saved mazes found.", True, (110, 110, 110))
            surface.blit(msg, (list_rect.x + 12, list_rect.y + 14))
        else:
            item_y = list_rect.y + 4
            for name in self._maze_list:
                if item_y + self._ITEM_H > list_rect.bottom - 4:
                    break
                r = pygame.Rect(list_rect.x + 4, item_y, list_rect.w - 8, self._ITEM_H)
                is_sel = name == self._selected
                hovered = r.collidepoint(mouse) and not is_sel
                if is_sel:
                    bg = (55, 88, 155)
                elif hovered:
                    bg = (50, 50, 60)
                else:
                    bg = (36, 36, 36)
                pygame.draw.rect(surface, bg, r, border_radius=3)
                color = (210, 225, 255) if is_sel else (185, 185, 185)
                txt = self.font.render(name, True, color)
                surface.blit(txt, (r.x + 12, r.y + (self._ITEM_H - txt.get_height()) // 2))
                self._item_rects.append((name, r))
                item_y += self._ITEM_H + 2

        # Buttons
        btn_y = dlg.bottom - 46
        load_ok = self._selected is not None
        load_btn  = pygame.Rect(dlg.right - 182, btn_y, 78, 32)
        cancel_btn = pygame.Rect(dlg.right - 96,  btn_y, 78, 32)
        self._load_btn, self._cancel_btn = load_btn, cancel_btn

        pygame.draw.rect(surface, (65, 130, 65) if load_ok else (42, 75, 42), load_btn, border_radius=4)
        pygame.draw.rect(surface, (75, 75, 75), cancel_btn, border_radius=4)

        for btn, label in [(load_btn, "Load"), (cancel_btn, "Cancel")]:
            t = self.font.render(label, True, (230, 230, 230))
            surface.blit(t, (btn.x + (btn.w - t.get_width()) // 2,
                             btn.y + (btn.h - t.get_height()) // 2))

    def handle_event(self, event) -> bool:
        if not self.visible:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.visible = False
                return True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self._selected:
                self._do_load()
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for name, r in self._item_rects:
                if r.collidepoint(pos):
                    if name == self._selected:
                        self._do_load()
                    else:
                        self._selected = name
                    return True
            if self._load_btn and self._load_btn.collidepoint(pos) and self._selected:
                self._do_load()
                return True
            if self._cancel_btn and self._cancel_btn.collidepoint(pos):
                self.visible = False
                return True
            return True  # eat all clicks while open

        return False

    def _do_load(self):
        path = os.path.join(MAZES_DIR, f"{self._selected}.json")
        if not os.path.exists(path):
            return
        with open(path) as f:
            self._loaded_data = json.load(f)
        self.visible = False
