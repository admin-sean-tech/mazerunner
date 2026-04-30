import pygame


# ---------------------------------------------------------------------------
# Config dialog
# ---------------------------------------------------------------------------
class ConfigDialog:
    def __init__(self, config):
        self.config = config
        self.visible = False
        self._font = None
        self._title_font = None
        self._rect = None
        self._dec_btn = self._inc_btn = self._close_btn = None

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

    def draw(self, surface):
        if not self.visible:
            return
        sw, sh = surface.get_size()
        w, h = 380, 240
        self._rect = pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)
        dlg = self._rect

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (40, 40, 40), dlg, border_radius=8)
        pygame.draw.rect(surface, (100, 100, 100), dlg, 2, border_radius=8)

        surface.blit(self.title_font.render("Config", True, (220, 220, 220)),
                     (dlg.x + 16, dlg.y + 14))

        surface.blit(self.font.render("Game Mode:", True, (180, 180, 180)),
                     (dlg.x + 16, dlg.y + 74))

        self._dec_btn = pygame.Rect(dlg.x + 190, dlg.y + 70, 28, 28)
        self._inc_btn = pygame.Rect(dlg.x + 260, dlg.y + 70, 28, 28)
        for btn, sym in [(self._dec_btn, "<"), (self._inc_btn, ">")]:
            pygame.draw.rect(surface, (70, 110, 160), btn, border_radius=4)
            s = self.font.render(sym, True, (220, 220, 220))
            surface.blit(s, (btn.x + (btn.w - s.get_width()) // 2,
                             btn.y + (btn.h - s.get_height()) // 2))
        surface.blit(self.font.render(str(self.config["game_mode"]), True, (220, 220, 220)),
                     (dlg.x + 226, dlg.y + 74))

        self._close_btn = pygame.Rect(dlg.right - 90, dlg.bottom - 46, 74, 30)
        pygame.draw.rect(surface, (80, 140, 80), self._close_btn, border_radius=4)
        ct = self.font.render("Close", True, (220, 220, 220))
        surface.blit(ct, (self._close_btn.x + (self._close_btn.w - ct.get_width()) // 2,
                          self._close_btn.y + (self._close_btn.h - ct.get_height()) // 2))

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.visible = False
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self._close_btn and self._close_btn.collidepoint(pos):
                self.visible = False
            elif self._dec_btn and self._dec_btn.collidepoint(pos):
                self.config["game_mode"] = max(1, self.config["game_mode"] - 1)
            elif self._inc_btn and self._inc_btn.collidepoint(pos):
                self.config["game_mode"] += 1
            elif self._rect and not self._rect.collidepoint(pos):
                self.visible = False
            return True
        return False
