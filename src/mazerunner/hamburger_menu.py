import pygame

from mazerunner.settings import TOP_BAR_H, MENU_ITEM_H, MENU_W


# ---------------------------------------------------------------------------
# Hamburger menu
# ---------------------------------------------------------------------------
class HamburgerMenu:
    ITEMS = ["Save", "Load", "Maze Editor", "Config", "Exit"]

    def __init__(self):
        self.rect = pygame.Rect(6, 7, 36, 36)
        self.open = False
        self._font = None

    @property
    def font(self):
        if self._font is None:
            self._font = pygame.font.SysFont(None, 28)
        return self._font

    def _item_rect(self, i):
        return pygame.Rect(self.rect.x, TOP_BAR_H + i * MENU_ITEM_H, MENU_W, MENU_ITEM_H)

    def draw(self, surface):
        bg = (100, 100, 100) if self.open else (70, 70, 70)
        pygame.draw.rect(surface, bg, self.rect, border_radius=4)
        lx, lw = self.rect.x + 7, self.rect.width - 14
        for i in range(3):
            ly = self.rect.y + 10 + i * 8
            pygame.draw.line(surface, (220, 220, 220), (lx, ly), (lx + lw, ly), 2)

        if self.open:
            for i, label in enumerate(self.ITEMS):
                r = self._item_rect(i)
                pygame.draw.rect(surface, (50, 50, 50), r)
                pygame.draw.rect(surface, (80, 80, 80), r, 1)
                txt = self.font.render(label, True, (220, 220, 220))
                surface.blit(txt, (r.x + 12, r.y + (MENU_ITEM_H - txt.get_height()) // 2))

    def handle_click(self, pos):
        """Returns clicked item label, or None."""
        if self.rect.collidepoint(pos):
            self.open = not self.open
            return None
        if self.open:
            for i, label in enumerate(self.ITEMS):
                if self._item_rect(i).collidepoint(pos):
                    self.open = False
                    return label
            self.open = False
        return None
