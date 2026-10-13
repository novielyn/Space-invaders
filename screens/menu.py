import math
import random

import pygame

# Shared notebook-style helpers live in screens/login.py
from screens.login import (
    INK,
    INK_SOFT,
    ERROR,
    OUTLINE,
    PAPER,
    PAPER_SHADE,
    SPINE,
    HIGHLIGHT,
    TAB_PINK,
    TAB_ORANGE,
    TAB_YELLOW,
    TAB_PURPLE,
    TAB_BLUE,
    SIDE_YELLOW,
    SIDE_PINK,
    hand_font,
    put_text,
    alpha_rect,
    draw_background,
    draw_tab,
    draw_tape,
    draw_space_picture,
    draw_notepad,
    draw_ruled_lines,
    draw_media_controls,
)

try:
    from managers.ui_sounds import ui_sounds
except Exception:
    ui_sounds = None


# ---------------------------------------------------------------
# Menu data
# ---------------------------------------------------------------
MENU_ITEMS = [
    ("play", "Start", "start",
     "Launch into the Galactic Battlefield and defend the fleet."),
    ("profile", "Profile", "profile",
     "View your pilot stats, rank and progress."),
    ("leaderboard", "Leaderboard", "leaderboard",
     "See how you stack up against the other pilots."),
    ("shop", "Shop", "shop",
     "Spend your credits on new ships and upgrades."),
    ("settings", "Settings", "settings",
     "Adjust the sound, video and controls."),
    ("tutorial", "Tutorial", "tutorial",
     "New here? Learn the controls and how to survive."),
    ("quit", "Quit game", "quit",
     "Leave the battlefield and log out."),
]

RANK_TIERS = [
    (0, "ROOKIE", (150, 158, 185)),
    (500, "ELITE", (70, 200, 120)),
    (1500, "MASTER", (0, 180, 220)),
    (3500, "GRANDMASTER", (55, 130, 255)),
    (7000, "LEGEND", (160, 90, 230)),
    (15000, "MYTHIC", (230, 180, 60)),
    (30000, "MYTHIC IMMORTAL", (240, 50, 100)),
]

# Edit these to match your real game rules.
TUTORIAL_PAGES = [
    {
        "tab": "Move",
        "title": "Controls",
        "lines": [
            "Move your ship with A / D or the arrow keys.",
            "Press SPACE to fire.",
            "Press ESC to pause the battle.",
        ],
        "art": "controls",
    },
    {
        "tab": "Foes",
        "title": "Enemies",
        "lines": [
            "Invaders march sideways and drop lower at each edge.",
            "Shoot them all before they reach you.",
            "The higher rows are worth more points.",
        ],
        "art": "invaders",
    },
    {
        "tab": "Life",
        "title": "Survive",
        "lines": [
            "You start with 3 lives.",
            "Dodge enemy fire and hide behind the barriers.",
            "Lose every life and the battle is over.",
        ],
        "art": "lives",
    },
    {
        "tab": "Rank",
        "title": "Ranks",
        "lines": [
            "Your best score decides your rank.",
            "Climb from Rookie to Mythic Immortal.",
            "Check the Leaderboard to compare with others.",
        ],
        "art": "ranks",
    },
]


# ---------------------------------------------------------------
# Sounds (same ui_sounds hooks as the original menu)
# ---------------------------------------------------------------
def _sound_hover():
    if ui_sounds is None:
        return
    try:
        ui_sounds.play("hover")
        return
    except Exception:
        pass
    try:
        ui_sounds.hover()
    except Exception:
        pass


def _sound_click():
    if ui_sounds is None:
        return
    try:
        ui_sounds.click()
        return
    except Exception:
        pass
    try:
        ui_sounds.play("click")
    except Exception:
        pass


def _sound_back():
    if ui_sounds is None:
        return
    try:
        ui_sounds.back()
    except Exception:
        pass


def _sound_reset():
    if ui_sounds is None:
        return
    try:
        ui_sounds.reset_hover("menu")
    except Exception:
        pass


# ---------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------
def get_player_rank(high_score):
    high_score = high_score or 0
    current = RANK_TIERS[0]
    for tier in RANK_TIERS:
        if high_score >= tier[0]:
            current = tier
    return current[1], current[2]


def player_info(player):
    """Best-effort read of the player's name and rank."""
    name = None
    score = 0
    try:
        if isinstance(player, dict):
            name = player.get("username") or player.get("name")
            score = player.get("high_score", 0)
        elif player is not None:
            name = getattr(player, "username", None) or getattr(player, "name", None)
            score = getattr(player, "high_score", 0)
    except Exception:
        pass
    rank = get_player_rank(score if isinstance(score, (int, float)) else 0)[0]
    return name, rank


def wrap_text(font, text, width):
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        test = (cur + " " + word).strip()
        if font.size(test)[0] <= width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def book_layout(width, height):
    book_w = min(width - 230, 940)
    book_h = min(height - 150, 520)
    book = pygame.Rect(0, 0, book_w, book_h)
    book.center = (width // 2 - 30, height // 2 - 8)
    left_page = pygame.Rect(book.x + 12, book.y + 10, book_w // 2 - 12, book_h - 20)
    right_page = pygame.Rect(book.centerx, book.y + 10, book_w // 2 - 12, book_h - 20)
    return book, left_page, right_page


def polaroid_layout(rp):
    pol_w = int(min(rp.w - 90, 280, (rp.h - 170) * 1.2))
    pic_h = int(pol_w * 0.72)
    polaroid = pygame.Rect(0, 0, pol_w, pic_h + 66)
    polaroid.midtop = (rp.centerx, rp.y + 34)
    picture = pygame.Rect(polaroid.x + 12, polaroid.y + 12, pol_w - 24, pic_h)
    controls_center = (rp.centerx, polaroid.bottom + 28)
    desc = pygame.Rect(
        rp.x + 40,
        controls_center[1] + 30,
        rp.w - 80,
        max(50, rp.bottom - 26 - (controls_center[1] + 30)),
    )
    return polaroid, picture, controls_center, desc


def draw_book(screen, book, lp, rp):
    pygame.draw.rect(screen, (60, 40, 36), book.move(8, 10), border_radius=10)
    pygame.draw.rect(screen, PAPER_SHADE, book, border_radius=10)
    pygame.draw.rect(screen, OUTLINE, book, 3, border_radius=10)
    pygame.draw.rect(screen, PAPER, lp, border_radius=6)
    pygame.draw.rect(screen, PAPER, rp, border_radius=6)
    for i in range(24):
        a = 70 - i * 3
        if a <= 0:
            break
        alpha_rect(screen, (120, 100, 70, a), pygame.Rect(book.centerx - 24 + i, book.y + 10, 1, book.h - 20))
        alpha_rect(screen, (120, 100, 70, a), pygame.Rect(book.centerx + 24 - i, book.y + 10, 1, book.h - 20))
    pygame.draw.line(screen, SPINE, (book.centerx, book.y + 8), (book.centerx, book.bottom - 8), 2)


def draw_polaroid(screen, polaroid, picture, pic, caption, caption_font):
    pygame.draw.rect(screen, (190, 178, 150), polaroid.move(5, 6), border_radius=4)
    pygame.draw.rect(screen, (255, 255, 252), polaroid, border_radius=4)
    pygame.draw.rect(screen, OUTLINE, polaroid, 2, border_radius=4)
    screen.blit(pic, picture)
    pygame.draw.rect(screen, OUTLINE, picture, 3)
    put_text(screen, caption_font, caption, INK, (polaroid.centerx, polaroid.bottom - 28), "center")
    draw_tape(screen, (polaroid.x + 10, polaroid.y + 6), 40)
    draw_tape(screen, (polaroid.right - 10, polaroid.bottom - 8), 40)


def draw_desc_box(screen, box):
    pygame.draw.rect(screen, (255, 252, 242), box, border_radius=6)
    pygame.draw.rect(screen, OUTLINE, box, 2, border_radius=6)
    for x in range(box.x + 8, box.right - 8, 10):
        pygame.draw.circle(screen, INK_SOFT, (x, box.y + 8), 1)


def draw_actions(screen, action_font, return_rect, done_rect, mouse_pos, done_label="Done"):
    ret_hover = return_rect.collidepoint(mouse_pos)
    ret_col = (255, 255, 255) if ret_hover else (245, 235, 220)
    arrow_y = return_rect.centery
    pygame.draw.lines(
        screen, ret_col, False,
        [(return_rect.x + 30, arrow_y - 6), (return_rect.x + 6, arrow_y - 6),
         (return_rect.x + 6, arrow_y + 14), (return_rect.x + 22, arrow_y + 14)], 4,
    )
    put_text(screen, action_font, "Return", (60, 44, 40), (return_rect.x + 46, arrow_y + 3), "midleft")
    put_text(screen, action_font, "Return", ret_col, (return_rect.x + 44, arrow_y), "midleft")

    done_hover = done_rect.collidepoint(mouse_pos)
    done_col = (255, 190, 90) if done_hover else (255, 160, 60)
    put_text(screen, action_font, done_label, (60, 44, 40), (done_rect.x + 12, done_rect.centery + 3), "midleft")
    put_text(screen, action_font, done_label, done_col, (done_rect.x + 10, done_rect.centery), "midleft")
    cx, cy = done_rect.right - 36, done_rect.centery
    pygame.draw.lines(screen, (245, 235, 220), False,
                      [(cx - 14, cy), (cx - 4, cy + 12), (cx + 18, cy - 14)], 5)


def draw_icon(screen, icon, center, color):
    x, y = center
    if icon == "start":
        pygame.draw.polygon(screen, color, [(x - 5, y - 8), (x - 5, y + 8), (x + 8, y)])
    elif icon == "profile":
        pygame.draw.circle(screen, color, (x, y - 4), 4)
        pygame.draw.ellipse(screen, color, (x - 8, y + 2, 16, 9))
    elif icon == "leaderboard":
        pygame.draw.rect(screen, color, (x - 7, y - 8, 14, 10), border_radius=2)
        pygame.draw.line(screen, color, (x, y + 2), (x, y + 7), 2)
        pygame.draw.line(screen, color, (x - 6, y + 8), (x + 6, y + 8), 2)
    elif icon == "shop":
        pygame.draw.rect(screen, color, (x - 8, y - 3, 16, 11), 2)
        pygame.draw.line(screen, color, (x - 4, y - 3), (x - 3, y - 8), 2)
        pygame.draw.line(screen, color, (x + 4, y - 3), (x + 3, y - 8), 2)
    elif icon == "settings":
        pygame.draw.circle(screen, color, (x, y), 6, 2)
        pygame.draw.circle(screen, color, (x, y), 2)
        for a in range(0, 360, 60):
            r = math.radians(a)
            pygame.draw.line(
                screen, color,
                (x + math.cos(r) * 6, y + math.sin(r) * 6),
                (x + math.cos(r) * 9, y + math.sin(r) * 9), 2,
            )
    elif icon == "tutorial":
        pygame.draw.rect(screen, color, (x - 9, y - 7, 9, 14), 2)
        pygame.draw.rect(screen, color, (x, y - 7, 9, 14), 2)
    elif icon == "quit":
        pygame.draw.rect(screen, color, (x - 8, y - 8, 7, 16), 2)
        pygame.draw.line(screen, color, (x - 1, y), (x + 8, y), 2)
        pygame.draw.polygon(screen, color, [(x + 9, y), (x + 3, y - 5), (x + 3, y + 5)])


# ---------------------------------------------------------------
# Quit confirmation (journal style)
# ---------------------------------------------------------------
def confirm_quit(screen, clock):
    snapshot = screen.copy()
    title_font = hand_font(32, True)
    body_font = hand_font(19)
    button_font = hand_font(24, True)
    selected = 1
    tick = 0

    while True:
        tick += 1
        width, height = screen.get_size()
        mouse = pygame.mouse.get_pos()

        screen.blit(snapshot, (0, 0))
        alpha_rect(screen, (0, 0, 0, 160), pygame.Rect(0, 0, width, height))

        card = pygame.Rect(0, 0, min(520, width - 60), 240)
        card.center = (width // 2, height // 2)
        pygame.draw.rect(screen, (60, 40, 36), card.move(6, 8), border_radius=10)
        pygame.draw.rect(screen, PAPER, card, border_radius=10)
        pygame.draw.rect(screen, OUTLINE, card, 3, border_radius=10)
        draw_tape(screen, (card.centerx, card.y + 4), 0, (110, 30))

        put_text(screen, title_font, "Quit game?", INK, (card.centerx, card.y + 56), "center")
        put_text(screen, body_font, "Leave the battlefield and log out?", INK_SOFT,
                 (card.centerx, card.y + 106), "center")

        yes_rect = pygame.Rect(card.x + 60, card.bottom - 76, 150, 46)
        no_rect = pygame.Rect(card.right - 210, card.bottom - 76, 150, 46)

        for index, (label, rect, color) in enumerate(
            (("Yes", yes_rect, TAB_PINK), ("No", no_rect, TAB_YELLOW))
        ):
            active = index == 0 and selected == 0 or index == 1 and selected == 1
            hovered = rect.collidepoint(mouse)
            r = rect.copy()
            if active or hovered:
                r.y -= 3
            pygame.draw.rect(screen, color, r, border_radius=10)
            pygame.draw.rect(screen, OUTLINE, r, 3 if active else 2, border_radius=10)
            put_text(screen, button_font, label, INK, r.center, "center")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                    selected = 0
                    _sound_hover()
                elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                    selected = 1
                    _sound_hover()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    _sound_click()
                    return selected == 0
                elif event.key == pygame.K_ESCAPE:
                    _sound_back()
                    return False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if yes_rect.collidepoint(event.pos):
                    _sound_click()
                    return True
                if no_rect.collidepoint(event.pos):
                    _sound_back()
                    return False

        pygame.display.flip()
        clock.tick(60)


# ---------------------------------------------------------------
# Tutorial artwork
# ---------------------------------------------------------------
INVADER_PATTERN = [
    "  XX  XX  ",
    "   XXXX   ",
    " XXXXXXXX ",
    "XX XX XX X",
    "XXXXXXXXXX",
    "X XXXXX X ",
    "X X    X X",
    "  XX  XX  ",
]


def draw_pixel_invader(screen, topleft, unit, color):
    for row, line in enumerate(INVADER_PATTERN):
        for col, ch in enumerate(line):
            if ch == "X":
                pygame.draw.rect(
                    screen, color,
                    (topleft[0] + col * unit, topleft[1] + row * unit, unit, unit),
                )


def draw_keycap(screen, rect, label, font):
    pygame.draw.rect(screen, (170, 150, 120), rect.move(0, 5), border_radius=8)
    pygame.draw.rect(screen, (246, 238, 214), rect, border_radius=8)
    pygame.draw.rect(screen, OUTLINE, rect, 2, border_radius=8)
    put_text(screen, font, label, INK, rect.center, "center")


def draw_heart(screen, center, size=12, color=(220, 50, 70)):
    x, y = center
    pygame.draw.circle(screen, color, (x - size // 2, y - size // 3), size // 2 + 2)
    pygame.draw.circle(screen, color, (x + size // 2, y - size // 3), size // 2 + 2)
    pygame.draw.polygon(
        screen, color,
        [(x - size - 2, y - size // 5), (x + size + 2, y - size // 5), (x, y + size + 2)],
    )


def draw_tutorial_art(screen, art, area, fonts, tick):
    big, mid, small = fonts
    cx = area.centerx
    y0 = area.y + 20

    if art == "controls":
        draw_keycap(screen, pygame.Rect(cx - 90, y0, 60, 56), "A", big)
        draw_keycap(screen, pygame.Rect(cx + 30, y0, 60, 56), "D", big)
        put_text(screen, mid, "move", INK_SOFT, (cx, y0 + 80), "center")
        draw_keycap(screen, pygame.Rect(cx - 90, y0 + 118, 180, 52), "SPACE", mid)
        put_text(screen, mid, "fire", INK_SOFT, (cx, y0 + 196), "center")

        sx = cx + int(math.sin(tick * 0.04) * 40)
        sy = area.bottom - 28
        pygame.draw.polygon(screen, (90, 90, 110), [(sx, sy - 22), (sx - 18, sy + 10), (sx + 18, sy + 10)])
        pygame.draw.polygon(screen, (230, 80, 70), [(sx, sy - 8), (sx - 7, sy + 10), (sx + 7, sy + 10)])
        shot_y = sy - 28 - (tick * 3) % 60
        pygame.draw.line(screen, (240, 170, 50), (sx, shot_y), (sx, shot_y - 12), 3)

    elif art == "invaders":
        rows = ((130, 60, 180), "30 pts"), ((40, 140, 170), "20 pts"), ((200, 60, 70), "10 pts")
        for i, (color, label) in enumerate(rows):
            y = y0 + i * 88
            bob = int(math.sin(tick * 0.06 + i) * 3)
            draw_pixel_invader(screen, (cx - 90, y + bob), 5, color)
            put_text(screen, mid, label, INK, (cx + 10, y + 20), "midleft")

    elif art == "lives":
        for i in range(3):
            pulse = int(math.sin(tick * 0.08 + i) * 2)
            draw_heart(screen, (cx - 70 + i * 70, y0 + 40), 14 + pulse)
        put_text(screen, mid, "3 lives", INK_SOFT, (cx, y0 + 90), "center")

        barrier = pygame.Rect(cx - 55, y0 + 150, 110, 60)
        pygame.draw.rect(screen, (110, 170, 120), barrier, border_top_left_radius=30, border_top_right_radius=30)
        pygame.draw.rect(screen, (245, 246, 238), (cx - 20, barrier.bottom - 24, 40, 24))
        pygame.draw.rect(screen, OUTLINE, barrier, 2, border_top_left_radius=30, border_top_right_radius=30)
        put_text(screen, mid, "barriers", INK_SOFT, (cx, barrier.bottom + 26), "center")

    elif art == "ranks":
        for i, (score, name, color) in enumerate(RANK_TIERS):
            y = y0 + i * 40
            pygame.draw.circle(screen, color, (area.x + 22, y + 14), 9)
            pygame.draw.circle(screen, OUTLINE, (area.x + 22, y + 14), 9, 2)
            put_text(screen, small, name.title(), INK, (area.x + 46, y + 14), "midleft")
            put_text(screen, small, f"{score}+", INK_SOFT, (area.right - 10, y + 14), "midright")


# ---------------------------------------------------------------
# Tutorial screen
# ---------------------------------------------------------------
def tutorial_screen(screen, clock):
    """Journal-style tutorial. Returns "back" or "quit"."""
    heading_font = hand_font(26, True)
    text_font = hand_font(18)
    small_font = hand_font(16)
    tab_font = hand_font(15, True)
    action_font = hand_font(40, True)
    nav_font = hand_font(18, True)
    art_fonts = (hand_font(30, True), hand_font(22, True), hand_font(18, True))

    page = 0
    tick = 0
    total = len(TUTORIAL_PAGES)

    def go(delta):
        nonlocal page
        new = max(0, min(total - 1, page + delta))
        if new != page:
            page = new
            _sound_click()

    while True:
        tick += 1
        width, height = screen.get_size()
        mouse = pygame.mouse.get_pos()

        book, lp, rp = book_layout(width, height)

        prev_rect = pygame.Rect(lp.x + 24, lp.bottom - 42, 120, 30)
        next_rect = pygame.Rect(rp.right - 144, rp.bottom - 42, 120, 30)
        return_rect = pygame.Rect(30, height - 78, 190, 56)
        done_rect = pygame.Rect(width - 220, height - 78, 190, 56)

        tab_colors = (TAB_PINK, TAB_ORANGE, TAB_YELLOW, TAB_PURPLE)
        tabs = []
        for i, data in enumerate(TUTORIAL_PAGES):
            tabs.append((
                pygame.Rect(lp.x + 30 + i * 78, book.y - 36, 72, 48),
                tab_colors[i % len(tab_colors)],
                data["tab"],
            ))
        deco_tabs = [
            (pygame.Rect(rp.x + 30, book.y - 36, 72, 48), TAB_PURPLE, ""),
            (pygame.Rect(rp.x + 108, book.y - 36, 72, 48), TAB_BLUE, ""),
        ]

        # ---------- draw ----------
        draw_background(screen, width, height, tick)

        for i, (r, col, label) in enumerate(tabs):
            draw_tab(screen, r, col, label, tab_font, i == page or r.collidepoint(mouse))
        for r, col, label in deco_tabs:
            draw_tab(screen, r, col, label, tab_font, r.collidepoint(mouse))

        draw_book(screen, book, lp, rp)

        data = TUTORIAL_PAGES[page]

        step = 28
        draw_ruled_lines(screen, lp, lp.y + 84, step)

        put_text(screen, heading_font, data["title"], INK, (lp.centerx, lp.y + 30), "midtop")
        pygame.draw.line(screen, INK_SOFT,
                         (lp.centerx - 70, lp.y + 66), (lp.centerx + 70, lp.y + 66), 2)

        text_w = lp.w - 70
        line_y = lp.y + 84 + step
        for bullet in data["lines"]:
            wrapped = wrap_text(text_font, bullet, text_w - 22)
            for j, line in enumerate(wrapped):
                if j == 0:
                    put_text(screen, text_font, "\u2022", ERROR, (lp.x + 34, line_y - 4), "bottomleft")
                put_text(screen, text_font, line, INK, (lp.x + 56, line_y - 4), "bottomleft")
                line_y += step
            line_y += step // 2

        # right page artwork
        art_area = rp.inflate(-80, -110)
        art_area.y = rp.y + 40
        draw_tutorial_art(screen, data["art"], art_area, art_fonts, tick)

        # prev / next / page number
        prev_on = page > 0
        next_on = page < total - 1
        prev_col = INK if prev_on and prev_rect.collidepoint(mouse) else (INK_SOFT if prev_on else (190, 180, 165))
        next_col = INK if next_on and next_rect.collidepoint(mouse) else (INK_SOFT if next_on else (190, 180, 165))
        put_text(screen, nav_font, "\u2039 Previous", prev_col, prev_rect.midleft, "midleft")
        put_text(screen, nav_font, "Next \u203a", next_col, next_rect.midright, "midright")
        put_text(screen, small_font, f"{page + 1} / {total}", INK_SOFT,
                 (book.centerx, book.bottom - 28), "center")

        draw_actions(screen, action_font, return_rect, done_rect, mouse)

        # ---------- events ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN):
                    go(1)
                elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP):
                    go(-1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if page < total - 1:
                        go(1)
                    else:
                        _sound_back()
                        return "back"
                elif event.key == pygame.K_ESCAPE:
                    _sound_back()
                    return "back"

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if return_rect.collidepoint(pos) or done_rect.collidepoint(pos):
                    _sound_back()
                    return "back"
                if prev_rect.collidepoint(pos):
                    go(-1)
                elif next_rect.collidepoint(pos):
                    go(1)
                else:
                    for i, (r, col, label) in enumerate(tabs):
                        if r.collidepoint(pos) and i != page:
                            page = i
                            _sound_click()
                            break

        pygame.display.flip()
        clock.tick(60)


# ---------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------
def menu_screen(screen, clock, player=None):
    _sound_reset()

    item_font = hand_font(24, True)
    heading_font = hand_font(26, True)
    caption_font = hand_font(26, True)
    desc_font = hand_font(17)
    small_font = hand_font(15)
    big_font = hand_font(28, True)
    action_font = hand_font(40, True)
    tab_font = hand_font(15, True)

    rng = random.Random(21)
    stars = [
        (rng.random(), rng.random(), rng.choice((1, 1, 2)))
        for _ in range(45)
    ]

    pilot_name, pilot_rank = player_info(player)

    selected = 0
    previous_hover = None
    tick = 0

    def activate(name):
        _sound_click()

        if name == "tutorial":
            if tutorial_screen(screen, clock) == "quit":
                return "quit", player
            return None

        if name == "quit":
            if confirm_quit(screen, clock):
                return "login", None
            return None

        return name, player

    while True:
        tick += 1
        width, height = screen.get_size()
        mouse = pygame.mouse.get_pos()

        # ---------- layout ----------
        book, lp, rp = book_layout(width, height)

        content_x = lp.x + 44
        content_w = lp.w - 110
        step = max(34, min(46, (lp.h - 118) // len(MENU_ITEMS)))
        rows = [
            pygame.Rect(content_x - 8, lp.y + 100 + i * step, content_w + 8, step - 4)
            for i in range(len(MENU_ITEMS))
        ]

        polaroid, picture, controls_center, desc_box = polaroid_layout(rp)
        rewind_rect = pygame.Rect(0, 0, 56, 40)
        rewind_rect.center = (controls_center[0] - 68, controls_center[1])
        forward_rect = pygame.Rect(0, 0, 56, 40)
        forward_rect.center = (controls_center[0] + 68, controls_center[1])
        play_rect = pygame.Rect(0, 0, 40, 44)
        play_rect.center = controls_center

        note_rect = pygame.Rect(book.right - 34, book.y + 18, 150, 230)
        note_hover = note_rect.collidepoint(mouse) and mouse[0] > book.right

        side_tabs = {
            "play": (pygame.Rect(book.x - 58, book.y + 60, 78, 30), SIDE_YELLOW, "Start"),
            "tutorial": (pygame.Rect(book.x - 58, book.y + 98, 78, 30), SIDE_YELLOW, "Help"),
            "quit": (pygame.Rect(book.x - 58, book.y + 150, 78, 30), SIDE_PINK, "Quit"),
        }
        top_tabs = [
            (pygame.Rect(lp.x + 30, book.y - 36, 72, 48), TAB_PINK),
            (pygame.Rect(lp.x + 108, book.y - 36, 72, 48), TAB_ORANGE),
            (pygame.Rect(lp.x + 186, book.y - 36, 72, 48), TAB_YELLOW),
            (pygame.Rect(rp.x + 30, book.y - 36, 72, 48), TAB_PURPLE),
            (pygame.Rect(rp.x + 108, book.y - 36, 72, 48), TAB_PURPLE),
            (pygame.Rect(rp.x + 186, book.y - 36, 72, 48), TAB_BLUE),
        ]

        return_rect = pygame.Rect(30, height - 78, 190, 56)
        done_rect = pygame.Rect(width - 220, height - 78, 190, 56)

        # hover selects, like the original menu
        current_hover = None
        for i, r in enumerate(rows):
            if r.collidepoint(mouse):
                current_hover = i
                break
        if current_hover is not None and current_hover != previous_hover:
            selected = current_hover
            _sound_hover()
        previous_hover = current_hover

        name, label, icon, description = MENU_ITEMS[selected]

        # ---------- draw ----------
        draw_background(screen, width, height, tick)

        draw_notepad(screen, note_rect, big_font, tab_font, note_hover, footer="Tutorial")

        for key, (r, col, text) in side_tabs.items():
            draw_tab(screen, r, col, text, tab_font, r.collidepoint(mouse), vertical=True)
        for r, col in top_tabs:
            draw_tab(screen, r, col, "", tab_font, r.collidepoint(mouse))

        draw_book(screen, book, lp, rp)

        draw_ruled_lines(screen, lp, lp.y + 96)

        put_text(screen, heading_font, "Menu", INK, (lp.centerx - 20, lp.y + 28), "midtop")
        pygame.draw.line(screen, INK_SOFT,
                         (lp.centerx - 60, lp.y + 64), (lp.centerx + 20, lp.y + 64), 2)
        if pilot_name:
            put_text(screen, small_font, f"Pilot: {pilot_name}  \u00b7  {pilot_rank.title()}",
                     INK_SOFT, (lp.centerx - 20, lp.y + 72), "midtop")

        # fake scrollbar like the reference
        sb = pygame.Rect(lp.right - 34, lp.y + 44, 14, lp.h - 100)
        pygame.draw.rect(screen, (245, 238, 220), sb, border_radius=6)
        pygame.draw.rect(screen, OUTLINE, sb, 2, border_radius=6)
        pygame.draw.rect(screen, (200, 184, 150),
                         pygame.Rect(sb.x + 2, sb.y + 4, sb.w - 4, sb.h // 3), border_radius=5)

        for i, r in enumerate(rows):
            is_sel = i == selected
            if is_sel:
                alpha_rect(screen, (*HIGHLIGHT, 130), r, 8)

            put_text(screen, item_font, "\u2022", ERROR if is_sel else INK_SOFT,
                     (r.x + 8, r.centery), "midleft")
            put_text(screen, item_font, MENU_ITEMS[i][1], INK if is_sel else INK_SOFT,
                     (r.x + 30, r.centery), "midleft")

            if is_sel:
                badge = pygame.Rect(0, 0, 36, 30)
                badge.midright = (r.right - 4, r.centery)
                pygame.draw.rect(screen, (255, 196, 90), badge, border_radius=6)
                pygame.draw.rect(screen, OUTLINE, badge, 2, border_radius=6)
                draw_icon(screen, MENU_ITEMS[i][2], badge.center, INK)

        # right page
        pic = draw_space_picture(picture.size, tick, stars)
        draw_polaroid(screen, polaroid, picture, pic, label, caption_font)

        draw_media_controls(screen, controls_center, False, play_rect.collidepoint(mouse))

        draw_desc_box(screen, desc_box)
        lines = wrap_text(desc_font, description, desc_box.w - 24)
        line_h = desc_font.get_linesize()
        total_h = line_h * len(lines)
        ty = desc_box.centery - total_h // 2 + 4
        for line in lines:
            put_text(screen, desc_font, line, INK, (desc_box.centerx, ty), "midtop")
            ty += line_h

        draw_actions(screen, action_font, return_rect, done_rect, mouse, "Open")

        # ---------- events ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", player

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(MENU_ITEMS)
                    _sound_hover()

                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(MENU_ITEMS)
                    _sound_hover()

                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    result = activate(MENU_ITEMS[selected][0])
                    if result is not None:
                        return result

                elif event.key == pygame.K_h:
                    result = activate("tutorial")
                    if result is not None:
                        return result

                elif event.key == pygame.K_ESCAPE:
                    _sound_back()
                    if confirm_quit(screen, clock):
                        return "login", None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                target = None

                for i, r in enumerate(rows):
                    if r.collidepoint(pos):
                        selected = i
                        target = MENU_ITEMS[i][0]
                        break

                if target is None:
                    if done_rect.collidepoint(pos) or play_rect.collidepoint(pos):
                        target = MENU_ITEMS[selected][0]
                    elif return_rect.collidepoint(pos) or side_tabs["quit"][0].collidepoint(pos):
                        target = "quit"
                    elif side_tabs["play"][0].collidepoint(pos):
                        target = "play"
                    elif side_tabs["tutorial"][0].collidepoint(pos) or note_hover:
                        target = "tutorial"
                    elif rewind_rect.collidepoint(pos):
                        selected = (selected - 1) % len(MENU_ITEMS)
                        _sound_hover()
                    elif forward_rect.collidepoint(pos):
                        selected = (selected + 1) % len(MENU_ITEMS)
                        _sound_hover()

                if target is not None:
                    result = activate(target)
                    if result is not None:
                        return result

        pygame.display.flip()
        clock.tick(60)


# ---------------------------------------------------------------
# Backward-compatible helpers
# (other files import these from screens.menu, e.g. draw_menu_button)
# ---------------------------------------------------------------
import os

BG_IMAGE = os.path.join("assets", "images", "bg.png")

WHITE = (248, 246, 244)
GRAY = (145, 153, 178)
MUTED = (94, 106, 137)
CYAN = (0, 220, 255)
CYAN_SOFT = (100, 225, 255)
GREEN = (70, 255, 145)
RED = (255, 24, 52)
GOLD = (255, 210, 90)
PURPLE = (180, 90, 255)
NEON_BLUE = (55, 130, 255)
NEON_MAGENTA = (255, 30, 95)
TITLE_RED = (245, 20, 62)
TITLE_SHADOW = (92, 2, 22)
MENU_BLUE = (145, 164, 207)
MENU_WHITE = (250, 247, 244)
CURSOR_RED = (242, 17, 52)
GOLD_STAR = (255, 215, 105)
BG_TOP = (3, 0, 3)
BG_BOTTOM = (12, 1, 5)

_FONT_CACHE = {}
_FONT_FILE = None
_BG_IMAGE = None
_RAIN = []
_RAIN_SIZE = None


def get_player_rank(high_score):
    """Returns (name, color, progress 0..1, next_threshold or None)."""
    high_score = high_score or 0
    current = RANK_TIERS[0]
    next_rank = None
    for index, tier in enumerate(RANK_TIERS):
        if high_score >= tier[0]:
            current = tier
            next_rank = RANK_TIERS[index + 1] if index + 1 < len(RANK_TIERS) else None
    if next_rank is None:
        return current[1], current[2], 1.0, None
    progress = (high_score - current[0]) / max(1, next_rank[0] - current[0])
    return current[1], current[2], max(0.0, min(1.0, progress)), next_rank[0]


def _find_font_file():
    folders = [os.path.join("assets", "fonts"), "assets"]
    preferred = ["gothic.ttf", "Gothic.ttf", "medieval.ttf", "Medieval.ttf",
                 "cinzel.ttf", "Cinzel.ttf", "menu.ttf", "font.ttf"]
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        for name in preferred:
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                return path
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        try:
            for name in os.listdir(folder):
                if name.lower().endswith((".ttf", ".otf")):
                    return os.path.join(folder, name)
        except Exception:
            pass
    return None


def menu_font(size, bold=False):
    global _FONT_FILE
    size = max(8, int(size))
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    if _FONT_FILE is None:
        _FONT_FILE = _find_font_file()
    try:
        if _FONT_FILE and os.path.isfile(_FONT_FILE):
            font = pygame.font.Font(_FONT_FILE, size)
        else:
            path = pygame.font.match_font("Georgia", bold=bold)
            font = pygame.font.Font(path, size) if path else pygame.font.SysFont("Arial", size, bold=bold)
    except Exception:
        font = pygame.font.SysFont("Arial", size, bold=bold)
    _FONT_CACHE[key] = font
    return font


def get_font(size, bold=False):
    return menu_font(size, bold)


def fit_text(font, text, width):
    text = str(text)
    if font.size(text)[0] <= width:
        return text
    value = text
    while value:
        if font.size(value + "...")[0] <= width:
            return value + "..."
        value = value[:-1]
    return "..."


def ellipsize(font, text, width):
    return fit_text(font, text, width)


def blit_centered(surface, text_surface, center):
    rect = text_surface.get_rect(center=center)
    surface.blit(text_surface, rect)
    return rect


def lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_gradient_background(screen, width, height):
    for y in range(max(1, height)):
        color = lerp_color(BG_TOP, BG_BOTTOM, y / max(1, height - 1))
        pygame.draw.line(screen, color, (0, y), (width, y))


def draw_menu_background(screen, width, height, tick):
    """Dark stormy backdrop (bg.png + overlay + light rain)."""
    global _BG_IMAGE, _RAIN, _RAIN_SIZE

    if _BG_IMAGE is None and os.path.isfile(BG_IMAGE):
        try:
            _BG_IMAGE = pygame.image.load(BG_IMAGE).convert()
        except Exception:
            _BG_IMAGE = None

    if _BG_IMAGE is None:
        draw_gradient_background(screen, width, height)
    else:
        sw, sh = _BG_IMAGE.get_size()
        ratio = sw / max(1, sh)
        if ratio > width / max(1, height):
            nh, nw = height, int(height * ratio)
        else:
            nw, nh = width, int(width / ratio)
        scaled = pygame.transform.smoothscale(_BG_IMAGE, (nw, nh))
        screen.blit(scaled, (-(nw - width) // 2, -(nh - height) // 2))

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))

    if _RAIN_SIZE != (width, height):
        rng = random.Random(913742)
        _RAIN = [
            [rng.uniform(0, width), rng.uniform(0, height),
             rng.uniform(12, 30), rng.uniform(7, 15), rng.randint(25, 70)]
            for _ in range(160)
        ]
        _RAIN_SIZE = (width, height)

    for drop in _RAIN:
        drop[1] += drop[3]
        drop[0] -= drop[3] * 0.18
        if drop[1] > height + 30:
            drop[1] = random.uniform(-120, -10)
            drop[0] = random.uniform(0, width)
        pygame.draw.line(
            overlay, (210, 50, 68, drop[4]),
            (int(drop[0]), int(drop[1])),
            (int(drop[0] - drop[2] * 0.18), int(drop[1] - drop[2])), 1,
        )

    screen.blit(overlay, (0, 0))


def draw_panel(screen, rect, tick=0):
    surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(surface, (5, 2, 7, 220), surface.get_rect(), border_radius=10)
    pygame.draw.rect(surface, (75, 18, 38, 90), surface.get_rect(), 1, border_radius=10)
    screen.blit(surface, rect.topleft)


def draw_glowing_avatar(screen, profile_picture, center_x, center_y, size, tick, cache=None):
    radius = size // 2
    surface = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
    c = size * 3 // 2
    pygame.draw.circle(surface, (255, 20, 50, 30), (c, c), radius + 14)
    pygame.draw.circle(surface, (7, 4, 10), (c, c), radius)
    pygame.draw.circle(surface, TITLE_RED, (c, c), radius, 2)
    screen.blit(surface, (center_x - c, center_y - c))


def draw_menu_cursor(screen, x, y, tick, size=8):
    pulse = (math.sin(tick * 0.08) + 1) * 0.5
    s = size * 5
    surface = pygame.Surface((s, s), pygame.SRCALPHA)
    c = s // 2
    outer = int(size * (1.40 + pulse * 0.12))
    inner = max(4, int(size * 0.70))
    pygame.draw.polygon(surface, (255, 5, 35, 40),
                        [(c, c - outer), (c + outer, c), (c, c + outer), (c - outer, c)])
    pygame.draw.polygon(surface, CURSOR_RED,
                        [(c, c - inner), (c + inner, c), (c, c + inner), (c - inner, c)])
    screen.blit(surface, (int(x - c), int(y - c)))


def draw_menu_icon(screen, icon, center, color, size=18):
    x, y = center
    r = max(4, size // 2)
    if icon == "play":
        pygame.draw.polygon(screen, color, [(x - r // 2, y - r), (x - r // 2, y + r), (x + r, y)])
    elif icon == "trophy":
        pygame.draw.rect(screen, color, (x - r, y - r, r * 2, int(r * 1.45)), border_radius=2)
        pygame.draw.line(screen, color, (x, y + r // 2), (x, y + r + 4), 2)
        pygame.draw.line(screen, color, (x - 6, y + r + 5), (x + 6, y + r + 5), 2)
    elif icon == "user":
        pygame.draw.circle(screen, color, (x, y - 5), 4)
        pygame.draw.ellipse(screen, color, (x - 9, y + 1, 18, 10))
    elif icon == "gear":
        pygame.draw.circle(screen, color, (x, y), r - 2, 2)
        pygame.draw.circle(screen, color, (x, y), 3)
        for angle in range(0, 360, 45):
            a = math.radians(angle)
            pygame.draw.line(screen, color,
                             (x + math.cos(a) * r, y + math.sin(a) * r),
                             (x + math.cos(a) * (r + 4), y + math.sin(a) * (r + 4)), 2)
    elif icon == "logout":
        pygame.draw.rect(screen, color, (x - 8, y - 8, 7, 16), 2)
        pygame.draw.line(screen, color, (x - 1, y), (x + 9, y), 2)
        pygame.draw.polygon(screen, color, [(x + 9, y), (x + 3, y - 5), (x + 3, y + 5)])
    elif icon == "back":
        pygame.draw.polygon(screen, color, [(x + 6, y - 8), (x - 6, y), (x + 6, y + 8)])
    elif icon == "shop":
        pygame.draw.rect(screen, color, (x - 9, y - 5, 18, 13), 2)
        pygame.draw.line(screen, color, (x - 6, y - 5), (x - 4, y - 10), 2)
        pygame.draw.line(screen, color, (x + 6, y - 5), (x + 4, y - 10), 2)
        pygame.draw.circle(screen, color, (x - 5, y + 10), 2)
        pygame.draw.circle(screen, color, (x + 5, y + 10), 2)


def draw_menu_button(screen, rect, text, color=None, icon=None,
                     hover=False, pressed=False, tick=0):
    if color is None:
        color = MENU_BLUE

    draw_rect = rect.copy()
    if pressed:
        draw_rect.y += 3

    if hover:
        big = draw_rect.inflate(22, 22)
        glow = pygame.Surface(big.size, pygame.SRCALPHA)
        pulse = (math.sin(tick * 0.12) + 1) * 0.5
        pygame.draw.rect(glow, (*CURSOR_RED, int(25 + pulse * 35)),
                         glow.get_rect(), border_radius=12)
        screen.blit(glow, big.topleft)

    font = menu_font(max(18, min(30, rect.height - 6)), True)
    shown = MENU_WHITE if hover else color
    label = font.render(fit_text(font, text, rect.width - 60), True, shown)

    if icon:
        draw_menu_icon(screen, icon, (draw_rect.x + 24, draw_rect.centery), shown, 17)
        label_x = draw_rect.x + 46
    else:
        label_x = draw_rect.centerx - label.get_width() // 2

    screen.blit(label, (label_x, draw_rect.centery - label.get_height() // 2))

    if hover:
        draw_menu_cursor(screen, draw_rect.left - 17, draw_rect.centery, tick,
                         max(6, rect.height // 8))