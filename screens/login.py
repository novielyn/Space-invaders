import math
import random
import time

import pygame

from database import login_player

try:
    import theme
except Exception:
    theme = None


DEFAULT_WIDTH = 900
DEFAULT_HEIGHT = 600

BACKGROUND_MUSIC = "assets/sounds/login_music.mp3"

MAX_FIELD_LENGTH = 40

FIELDS = ("username", "password")

# ---------- palette (journal look) ----------
INK = (58, 46, 44)
INK_SOFT = (120, 104, 98)
PAPER = (251, 246, 233)
PAPER_SHADE = (232, 222, 198)
LINE = (205, 196, 176)
SPINE = (170, 150, 120)
OUTLINE = (70, 52, 48)
HIGHLIGHT = (255, 214, 102)
ERROR = (190, 50, 60)
SUCCESS = (50, 140, 80)
INFO = (60, 100, 170)

TAB_PINK = (246, 138, 150)
TAB_ORANGE = (250, 176, 120)
TAB_YELLOW = (252, 226, 120)
TAB_PURPLE = (190, 140, 230)
TAB_BLUE = (120, 170, 240)
SIDE_YELLOW = (253, 232, 130)
SIDE_PINK = (244, 120, 150)

NOTE_TAN = (190, 160, 110)


# ---------- helpers ----------
def sfx(name):
    """Play a theme sound if it exists, never crash."""
    if theme is None:
        return
    fn = getattr(theme, name, None)
    if fn:
        try:
            fn()
        except Exception:
            pass


def hand_font(size, bold=False):
    return pygame.font.SysFont(
        "segoeprint,bradleyhandITC,comicsansms,chalkboard,"
        "comicneue,dejavusans,arial",
        size,
        bold,
    )


def put_text(surf, font, s, color, pos, anchor="topleft"):
    img = font.render(s, True, color)
    rect = img.get_rect()
    setattr(rect, anchor, pos)
    surf.blit(img, rect)
    return rect


def alpha_rect(surf, color, rect, radius=0):
    tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(
        tmp, color, tmp.get_rect(), border_radius=radius
    )
    surf.blit(tmp, rect.topleft)


def draw_background(screen, w, h, tick):
    # warm wall gradient
    for y in range(0, h, 4):
        t = y / h
        c = (
            int(206 - 40 * t),
            int(128 - 30 * t),
            int(126 - 30 * t),
        )
        pygame.draw.rect(screen, c, (0, y, w, 4))

    # brick pattern
    brick_h, brick_w = 34, 82
    for row in range(0, int(h * 0.62) // brick_h + 1):
        offset = (row % 2) * (brick_w // 2)
        for col in range(-1, w // brick_w + 2):
            r = pygame.Rect(
                col * brick_w - offset,
                row * brick_h,
                brick_w - 3,
                brick_h - 3,
            )
            alpha_rect(screen, (120, 50, 50, 55), r, 3)

    # soft window light
    glow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(
        glow,
        (255, 240, 210, 40),
        (int(w * 0.9), int(h * 0.15)),
        int(h * 0.5),
    )
    screen.blit(glow, (0, 0))

    # wooden table
    table = pygame.Rect(0, int(h * 0.80), w, h - int(h * 0.80))
    pygame.draw.rect(screen, (112, 76, 58), table)
    for i in range(0, w, 60):
        pygame.draw.line(
            screen,
            (96, 64, 48),
            (i, table.y),
            (i - 20, table.bottom),
            2,
        )


def draw_tab(screen, rect, color, label, font, hovered, vertical=False):
    r = rect.copy()
    if hovered:
        if vertical:
            r.x -= 8
        else:
            r.y -= 5
    pygame.draw.rect(
        screen,
        color,
        r,
        border_radius=8,
    )
    pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
    if label:
        put_text(screen, font, label, INK, r.center, "center")


def draw_tape(screen, center, angle, size=(96, 30)):
    tape = pygame.Surface(size, pygame.SRCALPHA)
    tape.fill((214, 210, 196, 185))
    for x in range(0, size[0], 6):
        pygame.draw.line(tape, (200, 196, 180, 120), (x, 0), (x, size[1]))
    tape = pygame.transform.rotate(tape, angle)
    screen.blit(tape, tape.get_rect(center=center))


def draw_space_picture(size, tick, stars):
    pic = pygame.Surface(size)
    w, h = size

    for y in range(h):
        t = y / h
        pygame.draw.line(
            pic,
            (int(18 + 40 * t), int(14 + 18 * t), int(48 + 60 * t)),
            (0, y),
            (w, y),
        )

    for i, (sx, sy, sr) in enumerate(stars):
        tw = 150 + int(90 * math.sin(tick * 0.05 + i))
        pygame.draw.circle(
            pic,
            (tw, tw, min(255, tw + 30)),
            (int(sx * w), int(sy * h)),
            sr,
        )

    # planet + ring
    px, py, pr = int(w * 0.76), int(h * 0.68), int(h * 0.26)
    pygame.draw.circle(pic, (226, 112, 100), (px, py), pr)
    pygame.draw.circle(pic, (246, 160, 130), (px - pr // 4, py - pr // 4), pr // 2)
    ring = pygame.Rect(0, 0, int(pr * 2.8), int(pr * 0.7))
    ring.center = (px, py)
    pygame.draw.ellipse(pic, (255, 214, 140), ring, 3)

    # little ship
    sx = int(w * 0.18 + math.sin(tick * 0.03) * w * 0.08)
    sy = int(h * 0.34 + math.cos(tick * 0.045) * h * 0.05)
    pygame.draw.polygon(
        pic,
        (230, 235, 245),
        [(sx + 26, sy), (sx - 14, sy - 12), (sx - 6, sy), (sx - 14, sy + 12)],
    )
    pygame.draw.circle(pic, (90, 170, 240), (sx + 8, sy), 4)
    flame = random.randint(8, 16)
    pygame.draw.polygon(
        pic,
        (255, 170, 60),
        [(sx - 8, sy - 4), (sx - 8 - flame, sy), (sx - 8, sy + 4)],
    )
    return pic


def draw_notepad(screen, rect, font_big, small_font, hovered,
                 footer="Forgot password?"):
    pygame.draw.rect(screen, (60, 44, 40), rect.move(6, 6), border_radius=6)
    pygame.draw.rect(screen, NOTE_TAN, rect, border_radius=6)
    pygame.draw.rect(screen, OUTLINE, rect, 2, border_radius=6)

    # spiral rings
    for x in range(rect.x + 14, rect.right - 8, 16):
        pygame.draw.line(screen, (230, 230, 230), (x, rect.y - 10), (x + 4, rect.y + 14), 3)
        pygame.draw.circle(screen, (60, 60, 60), (x, rect.y + 6), 3)

    put_text(
        screen,
        font_big,
        "NOTES",
        INK if not hovered else (120, 40, 40),
        (rect.centerx, rect.y + 52),
        "center",
    )

    # paw print
    cx, cy = rect.centerx, rect.y + 118
    pygame.draw.ellipse(screen, INK, (cx - 22, cy - 6, 44, 36))
    for dx, dy in ((-30, -12), (-12, -28), (12, -28), (30, -12)):
        pygame.draw.ellipse(screen, INK, (cx + dx - 8, cy + dy - 10, 16, 20))

    put_text(
        screen,
        small_font,
        footer,
        (80, 55, 40),
        (rect.centerx, rect.bottom - 40),
        "center",
    )


def draw_ruled_lines(screen, page, start_y, step=30):
    y = start_y
    while y < page.bottom - 30:
        pygame.draw.line(screen, LINE, (page.x + 16, y), (page.right - 16, y), 1)
        y += step


def draw_field(screen, box, label, value, active, masked, font,
               label_font, cursor_visible, placeholder):
    put_text(screen, label_font, label, INK_SOFT, (box.x, box.y - 28))

    if active:
        alpha_rect(screen, (*HIGHLIGHT, 130), box, 10)

    pygame.draw.rect(
        screen, (255, 252, 242), box, border_radius=10
    )
    pygame.draw.rect(
        screen,
        OUTLINE if active else INK_SOFT,
        box,
        3 if active else 2,
        border_radius=10,
    )

    shown = ("\u2022" * len(value)) if masked else value
    text_area_right = box.right - 14

    if shown:
        img = font.render(shown, True, INK)
        # keep the tail of the text visible
        max_w = text_area_right - (box.x + 14)
        if img.get_width() > max_w:
            clip = pygame.Rect(img.get_width() - max_w, 0, max_w, img.get_height())
            screen.blit(img, (box.x + 14, box.centery - img.get_height() // 2), clip)
            end_x = box.x + 14 + max_w
        else:
            screen.blit(img, (box.x + 14, box.centery - img.get_height() // 2))
            end_x = box.x + 14 + img.get_width()
    else:
        put_text(screen, font, placeholder, (170, 156, 146),
                 (box.x + 14, box.centery), "midleft")
        end_x = box.x + 14

    if active and cursor_visible:
        pygame.draw.line(
            screen, INK,
            (end_x + 3, box.centery - 14),
            (end_x + 3, box.centery + 14), 2,
        )


def draw_media_controls(screen, center, playing, hover_play):
    cx, cy = center
    col = INK
    # rewind
    for off in (-78, -58):
        pygame.draw.polygon(screen, col, [(cx + off, cy), (cx + off + 16, cy - 12), (cx + off + 16, cy + 12)], 2)
    # play / pause button
    box = pygame.Rect(0, 0, 40, 44)
    box.center = (cx, cy)
    pygame.draw.rect(screen, (240, 230, 205) if not hover_play else HIGHLIGHT, box, border_radius=6)
    pygame.draw.rect(screen, INK, box, 2, border_radius=6)
    if playing:
        pygame.draw.rect(screen, INK, (cx - 9, cy - 12, 6, 24))
        pygame.draw.rect(screen, INK, (cx + 3, cy - 12, 6, 24))
    else:
        pygame.draw.polygon(screen, INK, [(cx - 8, cy - 12), (cx + 12, cy), (cx - 8, cy + 12)])
    # forward
    for off in (58, 78):
        pygame.draw.polygon(screen, col, [(cx + off, cy - 12), (cx + off + 16, cy), (cx + off, cy + 12)], 2)
    return box


def login_screen(screen, clock):

    input_font = hand_font(22)
    label_font = hand_font(17)
    small_font = hand_font(16)
    heading_font = hand_font(24, True)
    caption_font = hand_font(26, True)
    big_font = hand_font(28, True)
    action_font = hand_font(40, True)
    tab_font = hand_font(15, True)

    rng = random.Random(7)
    stars = [
        (rng.random(), rng.random(), rng.choice((1, 1, 2)))
        for _ in range(45)
    ]

    music_started = False
    music_playing = False

    try:
        pygame.mixer.music.load(BACKGROUND_MUSIC)
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(-1)
        music_started = True
        music_playing = True
    except Exception:
        music_started = False

    username = ""
    password = ""
    active = "username"

    message = ""
    message_color = ERROR

    cursor_visible = True
    cursor_timer = time.time()

    tick = 0

    is_fullscreen = (screen.get_flags() & pygame.FULLSCREEN) != 0

    def toggle_fullscreen():
        nonlocal screen, is_fullscreen
        is_fullscreen = not is_fullscreen
        if is_fullscreen:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT))

    def try_login():
        nonlocal message, message_color

        clean_username = username.strip()
        clean_password = password.strip()

        if not clean_username or not clean_password:
            message = "Enter username and password."
            message_color = ERROR
            sfx("sound_error")
            return None

        player = login_player(clean_username, clean_password)

        if player:
            message = "LOGIN SUCCESSFUL"
            message_color = SUCCESS
            sfx("sound_success")
            return player

        message = "Invalid username or password."
        message_color = ERROR
        sfx("sound_error")
        return None

    def stop_music():
        if music_started:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def toggle_music():
        nonlocal music_playing
        if not music_started:
            return
        try:
            if music_playing:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
            music_playing = not music_playing
        except Exception:
            pass

    while True:

        tick += 1

        width, height = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()

        # ---------- layout ----------
        book_w = min(width - 230, 940)
        book_h = min(height - 150, 520)
        book = pygame.Rect(0, 0, book_w, book_h)
        book.center = (width // 2 - 30, height // 2 - 8)

        left_page = pygame.Rect(book.x + 12, book.y + 10, book_w // 2 - 12, book_h - 20)
        right_page = pygame.Rect(book.centerx, book.y + 10, book_w // 2 - 12, book_h - 20)

        # left content
        content_x = left_page.x + 44
        content_w = left_page.w - 110
        user_box = pygame.Rect(content_x, left_page.y + 112, content_w, 50)
        pass_box = pygame.Rect(content_x, user_box.bottom + 56, content_w, 50)

        signup_y = pass_box.bottom + 40
        prompt_img = small_font.render("No account?", True, INK_SOFT)
        link_img = small_font.render(" Sign up", True, ERROR)
        total_w = prompt_img.get_width() + link_img.get_width()
        footer_x = left_page.centerx - 20 - total_w // 2
        link_x = footer_x + prompt_img.get_width()
        register_link = pygame.Rect(link_x, signup_y, link_img.get_width(), link_img.get_height())

        # right content
        pol_w = int(min(right_page.w - 90, 280, (right_page.h - 170) * 1.2))
        pic_h = int(pol_w * 0.72)
        pol_h = pic_h + 66
        polaroid = pygame.Rect(0, 0, pol_w, pol_h)
        polaroid.midtop = (right_page.centerx, right_page.y + 34)
        picture_rect = pygame.Rect(
            polaroid.x + 12, polaroid.y + 12, pol_w - 24, pic_h
        )
        controls_center = (right_page.centerx, polaroid.bottom + 28)
        desc_box = pygame.Rect(
            right_page.x + 40,
            controls_center[1] + 30,
            right_page.w - 80,
            max(50, right_page.bottom - 26 - (controls_center[1] + 30)),
        )

        # notepad (behind the book, right side)
        note_rect = pygame.Rect(book.right - 34, book.y + 18, 150, 230)
        note_hover = note_rect.collidepoint(mouse_pos) and mouse_pos[0] > book.right

        # side tabs (left of book) & top tabs
        side_tabs = {
            "login": (pygame.Rect(book.x - 58, book.y + 60, 78, 30), SIDE_YELLOW, "Login"),
            "signup": (pygame.Rect(book.x - 58, book.y + 98, 78, 30), SIDE_YELLOW, "Sign up"),
            "quit": (pygame.Rect(book.x - 58, book.y + 150, 78, 30), SIDE_PINK, "Quit"),
        }
        top_tabs = {
            "user": (pygame.Rect(left_page.x + 30, book.y - 36, 72, 48), TAB_PINK, "User"),
            "pass": (pygame.Rect(left_page.x + 108, book.y - 36, 72, 48), TAB_ORANGE, "Pass"),
            "star": (pygame.Rect(left_page.x + 186, book.y - 36, 72, 48), TAB_YELLOW, "\u2605"),
            "d1": (pygame.Rect(right_page.x + 30, book.y - 36, 72, 48), TAB_PURPLE, ""),
            "d2": (pygame.Rect(right_page.x + 108, book.y - 36, 72, 48), TAB_PURPLE, ""),
            "d3": (pygame.Rect(right_page.x + 186, book.y - 36, 72, 48), TAB_BLUE, ""),
        }

        return_rect = pygame.Rect(30, height - 78, 190, 56)
        done_rect = pygame.Rect(width - 220, height - 78, 190, 56)

        media_box = pygame.Rect(0, 0, 40, 44)
        media_box.center = controls_center

        if time.time() - cursor_timer > 0.5:
            cursor_visible = not cursor_visible
            cursor_timer = time.time()

        # ---------- events ----------
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                stop_music()
                return "quit", None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                if user_box.collidepoint(pos):
                    active = "username"
                    message = ""
                    sfx("sound_hover")

                elif pass_box.collidepoint(pos):
                    active = "password"
                    message = ""
                    sfx("sound_hover")

                elif done_rect.collidepoint(pos):
                    sfx("sound_click")
                    player = try_login()
                    if player:
                        stop_music()
                        return "menu", player

                elif return_rect.collidepoint(pos) or side_tabs["quit"][0].collidepoint(pos):
                    sfx("sound_back")
                    stop_music()
                    return "quit", None

                elif register_link.collidepoint(pos) or side_tabs["signup"][0].collidepoint(pos):
                    sfx("sound_click")
                    stop_music()
                    return "register", None

                elif side_tabs["login"][0].collidepoint(pos):
                    active = "username"
                    sfx("sound_click")

                elif top_tabs["user"][0].collidepoint(pos):
                    active = "username"
                    sfx("sound_hover")

                elif top_tabs["pass"][0].collidepoint(pos):
                    active = "password"
                    sfx("sound_hover")

                elif media_box.collidepoint(pos):
                    toggle_music()
                    sfx("sound_click")

                elif note_hover:
                    sfx("sound_click")
                    message = "Password reset coming soon."
                    message_color = INFO

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F11:
                    toggle_fullscreen()

                elif event.key == pygame.K_ESCAPE:
                    sfx("sound_back")
                    stop_music()
                    return "quit", None

                elif event.key in (pygame.K_TAB, pygame.K_DOWN):
                    active = FIELDS[(FIELDS.index(active) + 1) % len(FIELDS)]
                    sfx("sound_hover")

                elif event.key == pygame.K_UP:
                    active = FIELDS[(FIELDS.index(active) - 1) % len(FIELDS)]
                    sfx("sound_hover")

                elif event.key == pygame.K_BACKSPACE:
                    if active == "username":
                        username = username[:-1]
                    else:
                        password = password[:-1]

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if active == "username":
                        active = "password"
                        sfx("sound_hover")
                    else:
                        sfx("sound_click")
                        player = try_login()
                        if player:
                            stop_music()
                            return "menu", player

                elif event.unicode and event.unicode.isprintable():
                    if active == "username" and len(username) < MAX_FIELD_LENGTH:
                        username += event.unicode
                    elif active == "password" and len(password) < MAX_FIELD_LENGTH:
                        password += event.unicode

        # ---------- draw ----------
        draw_background(screen, width, height, tick)

        # notepad first (sits behind the book)
        draw_notepad(screen, note_rect, big_font, tab_font, note_hover)

        # side tabs poke out from behind the book
        for key, (r, col, label) in side_tabs.items():
            draw_tab(screen, r, col, label, tab_font, r.collidepoint(mouse_pos), vertical=True)

        # top tabs
        for key, (r, col, label) in top_tabs.items():
            draw_tab(screen, r, col, label, tab_font, r.collidepoint(mouse_pos))

        # book shadow + cover
        pygame.draw.rect(screen, (60, 40, 36), book.move(8, 10), border_radius=10)
        pygame.draw.rect(screen, PAPER_SHADE, book, border_radius=10)
        pygame.draw.rect(screen, OUTLINE, book, 3, border_radius=10)

        # pages
        pygame.draw.rect(screen, PAPER, left_page, border_radius=6)
        pygame.draw.rect(screen, PAPER, right_page, border_radius=6)

        # spine shading
        for i in range(24):
            a = 70 - i * 3
            if a <= 0:
                break
            alpha_rect(screen, (120, 100, 70, a), pygame.Rect(book.centerx - 24 + i, book.y + 10, 1, book_h - 20))
            alpha_rect(screen, (120, 100, 70, a), pygame.Rect(book.centerx + 24 - i, book.y + 10, 1, book_h - 20))
        pygame.draw.line(screen, SPINE, (book.centerx, book.y + 8), (book.centerx, book.bottom - 8), 2)

        # ruled lines on left page
        draw_ruled_lines(screen, left_page, left_page.y + 90)

        # left heading
        put_text(screen, heading_font, "Login", INK, (left_page.centerx - 20, left_page.y + 34), "midtop")
        pygame.draw.line(
            screen, INK_SOFT,
            (left_page.centerx - 70, left_page.y + 72),
            (left_page.centerx + 30, left_page.y + 72), 2,
        )

        # fake scrollbar like in the reference
        sb = pygame.Rect(left_page.right - 34, left_page.y + 44, 14, left_page.h - 100)
        pygame.draw.rect(screen, (245, 238, 220), sb, border_radius=6)
        pygame.draw.rect(screen, OUTLINE, sb, 2, border_radius=6)
        thumb = pygame.Rect(sb.x + 2, sb.y + 4, sb.w - 4, sb.h // 3)
        pygame.draw.rect(screen, (200, 184, 150), thumb, border_radius=5)

        # inputs
        draw_field(screen, user_box, "Username", username, active == "username",
                   False, input_font, label_font, cursor_visible, "your name, pilot")
        draw_field(screen, pass_box, "Password", password, active == "password",
                   True, input_font, label_font, cursor_visible, "secret code")

        # sign up footer
        hovered_link = register_link.collidepoint(mouse_pos)
        link_img = small_font.render(" Sign up", True, INK if hovered_link else ERROR)
        screen.blit(prompt_img, (footer_x, signup_y))
        screen.blit(link_img, (link_x, signup_y))
        if hovered_link:
            pygame.draw.line(screen, ERROR,
                             (link_x + 8, register_link.bottom),
                             (register_link.right, register_link.bottom), 2)

        # page footers ("Previous" / "Next" feel)
        put_text(screen, tab_font, "Press Tab to switch", INK_SOFT,
                 (left_page.x + 28, left_page.bottom - 16), "bottomleft")

        # right page: polaroid
        pygame.draw.rect(screen, (190, 178, 150), polaroid.move(5, 6), border_radius=4)
        pygame.draw.rect(screen, (255, 255, 252), polaroid, border_radius=4)
        pygame.draw.rect(screen, OUTLINE, polaroid, 2, border_radius=4)

        pic = draw_space_picture(picture_rect.size, tick, stars)
        screen.blit(pic, picture_rect)
        pygame.draw.rect(screen, OUTLINE, picture_rect, 3)

        put_text(
            screen, caption_font, "Galactic Battlefield", INK,
            (polaroid.centerx, polaroid.bottom - 28), "center",
        )

        draw_tape(screen, (polaroid.x + 10, polaroid.y + 6), 40)
        draw_tape(screen, (polaroid.right - 10, polaroid.bottom - 8), 40)

        # media controls
        draw_media_controls(
            screen, controls_center, music_playing,
            media_box.collidepoint(mouse_pos),
        )

        # description box (doubles as status message)
        pygame.draw.rect(screen, (255, 252, 242), desc_box, border_radius=6)
        pygame.draw.rect(screen, OUTLINE, desc_box, 2, border_radius=6)
        for x in range(desc_box.x + 8, desc_box.right - 8, 10):
            pygame.draw.circle(screen, INK_SOFT, (x, desc_box.y + 8), 1)

        if message:
            put_text(screen, input_font, message, message_color,
                     (desc_box.centerx, desc_box.centery + 4), "center")
        else:
            put_text(screen, input_font, "Enter the Galactic Battlefield", INK_SOFT,
                     (desc_box.centerx, desc_box.centery + 4), "center")

        # bottom actions: Return / Done
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
        put_text(screen, action_font, "Done", (60, 44, 40), (done_rect.x + 12, done_rect.centery + 3), "midleft")
        put_text(screen, action_font, "Done", done_col, (done_rect.x + 10, done_rect.centery), "midleft")
        cx, cy = done_rect.right - 36, done_rect.centery
        pygame.draw.lines(screen, (245, 235, 220), False,
                          [(cx - 14, cy), (cx - 4, cy + 12), (cx + 18, cy - 14)], 5)

        pygame.display.flip()
        clock.tick(60)