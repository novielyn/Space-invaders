import math
import random

import pygame

from screens.login import (
    INK,
    INK_SOFT,
    ERROR,
    PAPER,
    OUTLINE,
    TAB_PINK,
    TAB_YELLOW,
    TAB_BLUE,
    TAB_ORANGE,
    TAB_PURPLE,
    SIDE_PINK,
    hand_font,
    put_text,
    draw_background,
    draw_tab,
)
from screens.menu import (
    book_layout,
    draw_book,
    polaroid_layout,
    draw_polaroid,
    draw_desc_box,
)
from screens.profile import (
    tag_button,
    draw_ship_backdrop,
    draw_ship_into,
    normalize_ship_id,
    get_value,
    SHIP_NAMES,
    GOLD_INK,
    GREEN_INK,
)

try:
    from managers.ui_sounds import ui_sounds
except Exception:
    ui_sounds = None


# ---------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------
def _ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def _snd(name, *args):
    try:
        if ui_sounds:
            fn = getattr(ui_sounds, name, None)
            if callable(fn):
                fn(*args)
    except Exception:
        pass


class _Paper:
    """One piece of confetti."""

    def __init__(self, x, y, color, strength):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2.5, 7.0) * strength
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(1.5, 4.0)
        self.size = random.randint(5, 9)
        self.color = color
        self.max_life = random.randint(50, 95)
        self.life = self.max_life
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-9, 9)

    def update(self):
        self.vy += 0.18
        self.vx *= 0.99
        self.x += self.vx
        self.y += self.vy
        self.angle += self.spin
        self.life -= 1
        return self.life > 0

    def draw(self, surface):
        alpha = int(255 * max(0.0, self.life / self.max_life))
        piece = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.rect(piece, (*self.color, alpha),
                         pygame.Rect(self.size // 2, self.size // 2, self.size, self.size),
                         border_radius=2)
        piece = pygame.transform.rotate(piece, self.angle)
        surface.blit(piece, (self.x - piece.get_width() / 2, self.y - piece.get_height() / 2))


def _get_ship_id(player):
    value = (
        get_value(player, "equipped_ship", None)
        or get_value(player, "selected_ship", None)
        or get_value(player, "ship", None)
        or "starter"
    )
    return normalize_ship_id(value) or "starter"


# ---------------------------------------------------------------
# Game over screen
# ---------------------------------------------------------------
def game_over_screen(screen, clock, score, high_score, player=None, toggle_fullscreen=None):
    """Returns ("retry" | "menu" | "quit", screen)."""
    _snd("reset_hover", "game_over")

    heading_font = hand_font(40, True)
    row_font = hand_font(22)
    value_font = hand_font(30, True)
    stamp_font = hand_font(24, True)
    button_font = hand_font(24, True)
    tab_font = hand_font(15, True)
    body_font = hand_font(17)
    small_font = hand_font(15)
    caption_font = hand_font(26, True)

    rng = random.Random(33)
    stars = [(rng.random(), rng.random(), rng.choice((1, 1, 2))) for _ in range(45)]

    ship_id = _get_ship_id(player)
    ship_name = SHIP_NAMES.get(ship_id, ship_id.upper())

    is_new_high_score = score > 0 and score >= high_score

    names = ("retry", "menu")
    labels = ("Retry", "Main Menu")
    colors = (TAB_YELLOW, TAB_BLUE)

    selected = 0
    tick = 0
    fade_frames = 24
    count_frames = 50
    confetti_fired = False
    particles = []

    while True:
        tick += 1
        width, height = screen.get_size()
        mouse = pygame.mouse.get_pos()

        # ---------- layout ----------
        book, lp, rp = book_layout(width, height)
        polaroid, picture, controls_center, desc_box = polaroid_layout(rp)

        x0 = lp.x + 34
        right_edge = lp.right - 36

        buttons = {
            "retry": pygame.Rect(x0, lp.y + 290, right_edge - x0, 46),
            "menu": pygame.Rect(x0, lp.y + 348, right_edge - x0, 46),
        }
        side_back = pygame.Rect(book.x - 58, book.y + 60, 78, 30)

        _snd("update_hover", buttons, mouse, "game_over")

        # ---------- events ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", screen

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11 and toggle_fullscreen:
                    screen = toggle_fullscreen()
                    continue
                if event.key == pygame.K_ESCAPE:
                    _snd("back")
                    return "menu", screen
                if event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % 2
                    _snd("play", "hover")
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % 2
                    _snd("play", "hover")
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if selected == 0:
                        _snd("click")
                        return "retry", screen
                    _snd("back")
                    return "menu", screen
                elif event.key == pygame.K_r:
                    _snd("click")
                    return "retry", screen

            elif event.type == pygame.MOUSEMOTION:
                for i, name in enumerate(names):
                    if buttons[name].collidepoint(event.pos):
                        selected = i

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if side_back.collidepoint(event.pos):
                    _snd("back")
                    return "menu", screen
                for name, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if name == "menu":
                            _snd("back")
                        else:
                            _snd("click")
                        return name, screen

        # ---------- draw ----------
        draw_background(screen, width, height, tick)

        draw_tab(screen, side_back, SIDE_PINK, "Menu", tab_font,
                 side_back.collidepoint(mouse), vertical=True)

        tabs = (
            (pygame.Rect(lp.x + 30, book.y - 36, 96, 48), TAB_PINK, "Result"),
            (pygame.Rect(rp.x + 30, book.y - 36, 72, 48), TAB_PURPLE, ""),
            (pygame.Rect(rp.x + 108, book.y - 36, 72, 48), TAB_ORANGE, ""),
        )
        for rect, color, label in tabs:
            draw_tab(screen, rect, color, label, tab_font, label == "Result")

        draw_book(screen, book, lp, rp)

        # heading with animated underline
        slide = int((1 - _ease_out_cubic(tick / 22)) * -30)
        put_text(screen, heading_font, "Game Over", ERROR,
                 (lp.centerx, lp.y + 26 + slide), "midtop")
        line_t = _ease_out_cubic((tick - 16) / 20)
        if line_t > 0:
            half = int(80 * line_t)
            pygame.draw.line(screen, INK_SOFT,
                             (lp.centerx - half, lp.y + 78),
                             (lp.centerx + half, lp.y + 78), 3)

        # score rows
        if tick <= count_frames:
            shown = int(score * _ease_out_cubic(tick / count_frames))
        else:
            shown = score

        rows = (
            ("Score", f"{shown:,}", INK),
            ("High score", f"{max(high_score, score):,}", GOLD_INK),
        )
        for i, (label, value, color) in enumerate(rows):
            line_y = lp.y + 150 + i * 56
            put_text(screen, row_font, label, INK_SOFT, (x0, line_y - 8), "bottomleft")
            put_text(screen, value_font, value, color, (right_edge, line_y - 8), "bottomright")
            pygame.draw.line(screen, (205, 196, 176), (x0 - 6, line_y), (right_edge + 6, line_y), 1)

        # new high score stamp
        if is_new_high_score and tick > count_frames:
            pulse = (math.sin(tick * 0.12) + 1) / 2
            stamp = stamp_font.render("NEW HIGH SCORE!", True, GREEN_INK)
            pad_x, pad_y = 18, 8
            box = pygame.Surface((stamp.get_width() + pad_x * 2,
                                  stamp.get_height() + pad_y * 2), pygame.SRCALPHA)
            pygame.draw.rect(box, (*GREEN_INK, 40 + int(40 * pulse)), box.get_rect(), border_radius=8)
            pygame.draw.rect(box, GREEN_INK, box.get_rect(), 3, border_radius=8)
            box.blit(stamp, (pad_x, pad_y))
            box = pygame.transform.rotate(box, 3)
            screen.blit(box, box.get_rect(center=(lp.centerx, lp.y + 232)))

        # confetti trigger
        if tick > count_frames and not confetti_fired:
            confetti_fired = True
            cx, cy = lp.centerx, lp.y + 150
            palette = (
                [(230, 180, 60), (255, 255, 255), (240, 120, 150), (110, 170, 240)]
                if is_new_high_score
                else [(110, 170, 240), (255, 255, 255)]
            )
            for _ in range(90 if is_new_high_score else 28):
                particles.append(_Paper(cx, cy, random.choice(palette),
                                        1.3 if is_new_high_score else 0.8))
            if is_new_high_score:
                _snd("play", "hover")

        # buttons
        for i, name in enumerate(names):
            intro = _ease_out_cubic((tick - 12 - i * 6) / 20)
            if intro <= 0:
                continue
            rect = buttons[name].move(0, int((1 - intro) * 30))
            hovered = rect.collidepoint(mouse) or selected == i
            tag_button(screen, rect, labels[i], button_font, hovered, colors[i])

        # right page: ship polaroid
        pic = draw_ship_backdrop(picture.size, tick, stars)
        draw_ship_into(pic, ship_id, tick)
        draw_polaroid(screen, polaroid, picture, pic, ship_name.title(), caption_font)

        draw_desc_box(screen, desc_box)
        put_text(screen, body_font,
                 "New personal best!" if is_new_high_score else "Better luck next flight",
                 INK, (desc_box.centerx, desc_box.centery - 4), "midbottom")
        put_text(screen, small_font, "Press R to retry", INK_SOFT,
                 (desc_box.centerx, desc_box.centery + 2), "midtop")

        # confetti on top
        particles = [p for p in particles if p.update()]
        for p in particles:
            p.draw(screen)

        # fade in
        if tick <= fade_frames:
            alpha = int(255 * (1 - _ease_out_cubic(tick / fade_frames)))
            if alpha > 0:
                overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, alpha))
                screen.blit(overlay, (0, 0))

        pygame.display.flip()
        clock.tick(60)