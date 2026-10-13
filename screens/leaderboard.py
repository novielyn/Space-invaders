import os
import random

import pygame

try:
    from database import get_leaderboard
except Exception:
    get_leaderboard = None

try:
    from managers.ui_sounds import ui_sounds
except Exception:
    ui_sounds = None

# Shared notebook-style helpers
from screens.login import (
    INK,
    INK_SOFT,
    ERROR,
    OUTLINE,
    PAPER,
    HIGHLIGHT,
    TAB_PINK,
    TAB_ORANGE,
    TAB_YELLOW,
    TAB_PURPLE,
    TAB_BLUE,
    SIDE_PINK,
    hand_font,
    put_text,
    alpha_rect,
    draw_background,
    draw_tab,
    draw_notepad,
    draw_ruled_lines,
    draw_space_picture,
)
from screens.menu import (
    book_layout,
    draw_book,
    polaroid_layout,
    draw_polaroid,
    draw_desc_box,
    draw_actions,
    fit_text,
    get_player_rank,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
IMAGE_DIR = os.path.join(ASSET_DIR, "images")

MAX_ROWS = 7

GOLD_INK = (170, 110, 20)
GREEN_INK = (40, 130, 70)
BLUE_INK = (60, 100, 170)

MEDALS = (
    (230, 180, 60),    # 1st
    (170, 176, 192),   # 2nd
    (190, 120, 70),    # 3rd
)

AVATAR_KINDS = (
    "hood", "ninja", "cat", "wizard",
    "robot", "mohawk", "cap", "visor",
)

_raw_cache = {}
_avatar_cache = {}


# ---------------------------------------------------------------
# Sounds
# ---------------------------------------------------------------
def play_hover():
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


def play_click():
    if ui_sounds is None:
        return
    try:
        ui_sounds.click()
    except Exception:
        pass


def play_back():
    if ui_sounds is None:
        return
    try:
        ui_sounds.back()
        return
    except Exception:
        pass
    try:
        ui_sounds.click()
    except Exception:
        pass


# ---------------------------------------------------------------
# Avatars
# ---------------------------------------------------------------
def load_image(filename):
    if filename in _raw_cache:
        return _raw_cache[filename]

    image = None
    for folder in (ASSET_DIR, IMAGE_DIR):
        path = os.path.join(folder, filename)
        if not os.path.isfile(path):
            continue
        try:
            image = pygame.image.load(path)
            try:
                image = image.convert_alpha()
            except Exception:
                pass
            break
        except Exception:
            image = None

    _raw_cache[filename] = image
    return image


def avatar_kind(username):
    value = str(username if username is not None else "PLAYER")
    return AVATAR_KINDS[sum(ord(c) for c in value) % len(AVATAR_KINDS)]


def get_avatar(username, size, avatar=None):
    size = max(1, int(size))
    kind = avatar if avatar in AVATAR_KINDS else avatar_kind(username)
    key = (kind, size)
    if key in _avatar_cache:
        return _avatar_cache[key]

    image = load_image(f"avatar_{kind}.png") or load_image(f"{kind}.png")
    if image is not None:
        try:
            image = pygame.transform.smoothscale(image, (size, size))
        except Exception:
            image = None

    _avatar_cache[key] = image
    return image


# ---------------------------------------------------------------
# Data
# ---------------------------------------------------------------
def get_value(data, names, default):
    if not isinstance(data, dict):
        return default
    for name in names:
        if name in data and data[name] is not None:
            return data[name]
    return default


def normalize_players(rows):
    players = []
    if rows is None:
        return players

    for row in rows:
        username = "Player"
        player_id = "-"
        score = 0
        matches = "-"
        winrate = "-"
        avatar = None

        if isinstance(row, dict):
            username = get_value(row, ("username", "display_name", "name"), "Player")
            player_id = get_value(row, ("id", "player_id", "user_id", "account_id"), "-")
            score = get_value(row, ("score", "high_score", "total_score"), 0)
            matches = get_value(
                row,
                ("matches", "match_count", "games_played", "total_matches"),
                "-",
            )
            winrate = get_value(row, ("winrate", "win_rate", "win_percentage"), "-")
            avatar = get_value(row, ("avatar", "avatar_kind"), None)

        elif isinstance(row, (tuple, list)):
            if len(row) > 0:
                username = row[0]
            if len(row) > 1:
                score = row[1]
            if len(row) > 2:
                player_id = row[2]
            if len(row) > 3:
                matches = row[3]
            if len(row) > 4:
                winrate = row[4]
            if len(row) > 5:
                avatar = row[5]

        try:
            score = int(float(score or 0))
        except Exception:
            score = 0

        try:
            if matches != "-":
                matches = int(float(matches))
        except Exception:
            matches = "-"

        if winrate != "-":
            try:
                numeric = float(str(winrate).replace("%", "").replace(",", "."))
                if numeric <= 1:
                    numeric *= 100
                winrate = f"{numeric:.2f}%"
            except Exception:
                winrate = str(winrate)

        username = str(username if username is not None else "Player").strip() or "Player"

        players.append({
            "username": username,
            "id": str(player_id if player_id is not None else "-"),
            "score": score,
            "matches": matches,
            "winrate": winrate,
            "avatar": avatar,
        })

    players.sort(key=lambda item: item["score"], reverse=True)
    return players[:MAX_ROWS]


def fetch_leaderboard():
    if get_leaderboard is None:
        return []
    try:
        rows = get_leaderboard(MAX_ROWS)
    except TypeError:
        try:
            rows = get_leaderboard()
        except Exception:
            rows = []
    except Exception:
        rows = []
    return normalize_players(rows)


def current_username(player):
    try:
        if isinstance(player, dict):
            name = player.get("username") or player.get("name")
        elif player is not None:
            name = getattr(player, "username", None) or getattr(player, "name", None)
        else:
            name = None
    except Exception:
        name = None
    return str(name).strip().lower() if name else None


# ---------------------------------------------------------------
# Drawing bits
# ---------------------------------------------------------------
def draw_arrow(screen, center, direction, enabled, hovered):
    cx, cy = center
    color = INK if (enabled and hovered) else (INK_SOFT if enabled else (200, 190, 170))
    for off in (-10, 8):
        if direction < 0:
            pts = [(cx + off, cy), (cx + off + 14, cy - 12), (cx + off + 14, cy + 12)]
        else:
            pts = [(cx + off, cy - 12), (cx + off + 14, cy), (cx + off, cy + 12)]
        pygame.draw.polygon(screen, color, pts, 2)


def draw_rank_badge(screen, center, rank, font_obj):
    x, y = center
    if rank <= 3:
        color = MEDALS[rank - 1]
        pygame.draw.circle(screen, color, (x, y), 15)
        pygame.draw.circle(screen, OUTLINE, (x, y), 15, 2)
        put_text(screen, font_obj, str(rank), INK, (x, y), "center")
    else:
        pygame.draw.circle(screen, (240, 226, 196), (x, y), 15)
        pygame.draw.circle(screen, INK_SOFT, (x, y), 15, 2)
        put_text(screen, font_obj, str(rank), INK_SOFT, (x, y), "center")


def draw_player_portrait(pic, entry, ring_color, initial_font):
    w, h = pic.get_size()
    size = min(w, h) - 54
    center = (w // 2, h // 2)

    image = get_avatar(entry["username"], size, entry.get("avatar"))
    if image is not None:
        pic.blit(image, image.get_rect(center=center))
    else:
        pygame.draw.circle(pic, (240, 226, 196), center, size // 2)
        put_text(pic, initial_font, entry["username"][:1].upper(), INK, center, "center")

    pygame.draw.circle(pic, ring_color, center, size // 2 + 3, 4)


# ---------------------------------------------------------------
# Leaderboard screen
# ---------------------------------------------------------------
def leaderboard_screen(screen, clock, player=None):
    """Journal-style leaderboard. Returns "back" or "quit"."""
    heading_font = hand_font(26, True)
    name_font = hand_font(22, True)
    row_font = hand_font(21, True)
    badge_font = hand_font(17, True)
    score_font = hand_font(20, True)
    body_font = hand_font(17)
    small_font = hand_font(15)
    caption_font = hand_font(26, True)
    big_font = hand_font(28, True)
    action_font = hand_font(40, True)
    tab_font = hand_font(15, True)
    initial_font = hand_font(64, True)

    rng = random.Random(55)
    stars = [(rng.random(), rng.random(), rng.choice((1, 1, 2))) for _ in range(45)]

    players = fetch_leaderboard()
    me = current_username(player)

    selected = 0
    previous_hover = None
    tick = 0

    def move(delta):
        nonlocal selected
        if players:
            selected = (selected + delta) % len(players)
            play_hover()

    def refresh():
        nonlocal players, selected
        players = fetch_leaderboard()
        selected = min(selected, max(0, len(players) - 1))
        play_click()

    while True:
        tick += 1
        width, height = screen.get_size()
        mouse = pygame.mouse.get_pos()

        # ---------- layout ----------
        book, lp, rp = book_layout(width, height)
        polaroid, picture, controls_center, desc_box = polaroid_layout(rp)

        content_x = lp.x + 44
        content_w = lp.w - 84
        step = max(34, min(52, (lp.h - 130) // MAX_ROWS))
        rows = [
            pygame.Rect(content_x - 8, lp.y + 96 + i * step, content_w + 8, step - 4)
            for i in range(len(players))
        ]

        note_rect = pygame.Rect(book.right - 34, book.y + 18, 150, 230)
        side_back = pygame.Rect(book.x - 58, book.y + 60, 78, 30)

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

        prev_rect = pygame.Rect(0, 0, 56, 40)
        prev_rect.center = (controls_center[0] - 62, controls_center[1])
        next_rect = pygame.Rect(0, 0, 56, 40)
        next_rect.center = (controls_center[0] + 62, controls_center[1])

        # hover selects, like the menu
        current_hover = None
        for i, r in enumerate(rows):
            if r.collidepoint(mouse):
                current_hover = i
                break
        if current_hover is not None and current_hover != previous_hover:
            selected = current_hover
            play_hover()
        previous_hover = current_hover

        # ---------- draw ----------
        draw_background(screen, width, height, tick)
        draw_notepad(screen, note_rect, big_font, tab_font, False,
                     footer=f"Top {MAX_ROWS}")

        draw_tab(screen, side_back, SIDE_PINK, "Menu", tab_font,
                 side_back.collidepoint(mouse), vertical=True)
        for r, col in top_tabs:
            draw_tab(screen, r, col, "", tab_font, r.collidepoint(mouse))

        draw_book(screen, book, lp, rp)
        draw_ruled_lines(screen, lp, lp.y + 96, step)

        put_text(screen, heading_font, "Leaderboard", INK, (lp.centerx, lp.y + 28), "midtop")
        pygame.draw.line(screen, INK_SOFT,
                         (lp.centerx - 70, lp.y + 64), (lp.centerx + 70, lp.y + 64), 2)
        put_text(screen, small_font, "Best pilots in the fleet", INK_SOFT,
                 (lp.centerx, lp.y + 72), "midtop")

        if not players:
            put_text(screen, body_font, "No pilots found yet.", INK_SOFT,
                     (lp.centerx, lp.centery), "center")

        for i, (r, entry) in enumerate(zip(rows, players)):
            is_sel = i == selected
            is_me = me is not None and entry["username"].strip().lower() == me

            if is_sel:
                alpha_rect(screen, (*HIGHLIGHT, 130), r, 8)

            draw_rank_badge(screen, (r.x + 26, r.centery), i + 1, badge_font)

            score_text = f"{entry['score']:,}"
            score_w = score_font.size(score_text)[0]
            put_text(screen, score_font, score_text, GOLD_INK if is_sel else INK_SOFT,
                     (r.right - 8, r.centery), "midright")

            name = entry["username"] + ("  (you)" if is_me else "")
            name_x = r.x + 54
            name_w = r.right - 8 - score_w - 14 - name_x
            put_text(screen, row_font, fit_text(row_font, name, name_w),
                     INK if is_sel else INK_SOFT, (name_x, r.centery), "midleft")

        # ---------- right page: selected pilot ----------
        if players:
            selected = max(0, min(selected, len(players) - 1))
            entry = players[selected]
            rank_name, rank_color = get_player_rank(entry["score"])[:2]

            pic = draw_space_picture(picture.size, tick, stars)
            draw_player_portrait(pic, entry, rank_color, initial_font)
            caption = fit_text(caption_font, entry["username"], polaroid.w - 24)
            draw_polaroid(screen, polaroid, picture, pic, caption, caption_font)

            multi = len(players) > 1
            draw_arrow(screen, prev_rect.center, -1, multi, prev_rect.collidepoint(mouse))
            draw_arrow(screen, next_rect.center, 1, multi, next_rect.collidepoint(mouse))

            draw_desc_box(screen, desc_box)
            lines = (
                (f"Rank #{selected + 1}  \u00b7  {rank_name.title()}", body_font, INK),
                (f"Score {entry['score']:,}", body_font, GOLD_INK),
                (f"Matches {entry['matches']}  \u00b7  Winrate {entry['winrate']}", small_font, INK_SOFT),
                (f"ID {entry['id']}", small_font, INK_SOFT),
            )
            line_h = max(f.get_linesize() for _, f, _ in lines)
            ty = desc_box.centery - (line_h * len(lines)) // 2 + 4
            for text_value, fnt, color in lines:
                put_text(screen, fnt, fit_text(fnt, text_value, desc_box.w - 24),
                         color, (desc_box.centerx, ty), "midtop")
                ty += line_h
        else:
            pic = draw_space_picture(picture.size, tick, stars)
            draw_polaroid(screen, polaroid, picture, pic, "Empty", caption_font)
            draw_desc_box(screen, desc_box)
            put_text(screen, body_font, "Play a match to get on the board.", INK_SOFT,
                     desc_box.center, "center")

        draw_actions(screen, action_font, return_rect, done_rect, mouse, "Refresh")

        pygame.display.flip()

        # ---------- events ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    play_back()
                    return "back"
                elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
                    move(-1)
                elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
                    move(1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                    refresh()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                if return_rect.collidepoint(pos) or side_back.collidepoint(pos):
                    play_back()
                    return "back"
                if done_rect.collidepoint(pos):
                    refresh()
                elif prev_rect.collidepoint(pos):
                    move(-1)
                elif next_rect.collidepoint(pos):
                    move(1)
                else:
                    for i, r in enumerate(rows):
                        if r.collidepoint(pos):
                            selected = i
                            play_click()
                            break

        clock.tick(60)


show_leaderboard = leaderboard_screen