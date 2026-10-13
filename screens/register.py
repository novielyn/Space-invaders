import time

import pygame

from database import register_player

# Shared notebook-style helpers live in screens/login.py
from screens.login import (
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    BACKGROUND_MUSIC,
    MAX_FIELD_LENGTH,
    INK,
    INK_SOFT,
    ERROR,
    SUCCESS,
    INFO,
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
    sfx,
    hand_font,
    put_text,
    alpha_rect,
    draw_background,
    draw_tab,
    draw_tape,
    draw_space_picture,
    draw_notepad,
    draw_ruled_lines,
    draw_field,
    draw_media_controls,
)

import random

FIELDS = ("username", "email", "password")


def register_screen(screen, clock):

    input_font = hand_font(22)
    label_font = hand_font(17)
    small_font = hand_font(16)
    heading_font = hand_font(24, True)
    caption_font = hand_font(26, True)
    big_font = hand_font(28, True)
    action_font = hand_font(40, True)
    tab_font = hand_font(15, True)

    rng = random.Random(11)
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
    email = ""
    password = ""

    active = "username"

    message = ""
    message_color = ERROR

    registered_at = None

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

    def fail(text):
        nonlocal message, message_color
        message = text
        message_color = ERROR
        sfx("sound_error")
        return False

    def try_register():
        nonlocal message, message_color

        clean_username = username.strip()
        clean_email = email.strip().lower()
        clean_password = password.strip()

        if not clean_username:
            return fail("Enter a username.")
        if len(clean_username) < 3:
            return fail("Username needs 3+ characters.")
        if not clean_email:
            return fail("Enter your email.")
        if "@" not in clean_email or "." not in clean_email:
            return fail("Enter a valid email.")
        if not clean_password:
            return fail("Enter a password.")
        if len(clean_password) < 6:
            return fail("Password needs 6+ characters.")

        try:
            result = register_player(
                clean_username, clean_email, clean_password
            )
            if result is not None:
                message = "REGISTRATION SUCCESSFUL"
                message_color = SUCCESS
                sfx("sound_success")
                return True
        except Exception as error:
            print("Registration error:", error)

        return fail("Username or email already exists.")

    def submit():
        nonlocal registered_at
        sfx("sound_click")
        if try_register():
            registered_at = time.time()

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

        content_x = left_page.x + 44
        content_w = left_page.w - 110

        username_box = pygame.Rect(content_x, left_page.y + 106, content_w, 46)
        email_box = pygame.Rect(content_x, username_box.bottom + 44, content_w, 46)
        password_box = pygame.Rect(content_x, email_box.bottom + 44, content_w, 46)
        boxes = {
            "username": username_box,
            "email": email_box,
            "password": password_box,
        }

        footer_y = password_box.bottom + 30
        prompt_img = small_font.render("Already registered?", True, INK_SOFT)
        link_img = small_font.render(" Login", True, ERROR)
        total_w = prompt_img.get_width() + link_img.get_width()
        footer_x = left_page.centerx - 20 - total_w // 2
        link_x = footer_x + prompt_img.get_width()
        login_link = pygame.Rect(link_x, footer_y, link_img.get_width(), link_img.get_height())

        # right page
        pol_w = int(min(right_page.w - 90, 280, (right_page.h - 170) * 1.2))
        pic_h = int(pol_w * 0.72)
        pol_h = pic_h + 66
        polaroid = pygame.Rect(0, 0, pol_w, pol_h)
        polaroid.midtop = (right_page.centerx, right_page.y + 34)
        picture_rect = pygame.Rect(polaroid.x + 12, polaroid.y + 12, pol_w - 24, pic_h)
        controls_center = (right_page.centerx, polaroid.bottom + 28)
        desc_box = pygame.Rect(
            right_page.x + 40,
            controls_center[1] + 30,
            right_page.w - 80,
            max(50, right_page.bottom - 26 - (controls_center[1] + 30)),
        )
        media_box = pygame.Rect(0, 0, 40, 44)
        media_box.center = controls_center

        note_rect = pygame.Rect(book.right - 34, book.y + 18, 150, 230)

        side_tabs = {
            "register": (pygame.Rect(book.x - 58, book.y + 60, 78, 30), SIDE_YELLOW, "Sign up"),
            "login": (pygame.Rect(book.x - 58, book.y + 98, 78, 30), SIDE_YELLOW, "Login"),
            "back": (pygame.Rect(book.x - 58, book.y + 150, 78, 30), SIDE_PINK, "Back"),
        }
        top_tabs = {
            "user": (pygame.Rect(left_page.x + 30, book.y - 36, 72, 48), TAB_PINK, "User"),
            "mail": (pygame.Rect(left_page.x + 108, book.y - 36, 72, 48), TAB_ORANGE, "Mail"),
            "pass": (pygame.Rect(left_page.x + 186, book.y - 36, 72, 48), TAB_YELLOW, "Pass"),
            "d1": (pygame.Rect(right_page.x + 30, book.y - 36, 72, 48), TAB_PURPLE, ""),
            "d2": (pygame.Rect(right_page.x + 108, book.y - 36, 72, 48), TAB_PURPLE, ""),
            "d3": (pygame.Rect(right_page.x + 186, book.y - 36, 72, 48), TAB_BLUE, ""),
        }

        return_rect = pygame.Rect(30, height - 78, 190, 56)
        done_rect = pygame.Rect(width - 220, height - 78, 190, 56)

        if time.time() - cursor_timer > 0.5:
            cursor_visible = not cursor_visible
            cursor_timer = time.time()

        # ---------- events ----------
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                stop_music()
                return "quit", None

            if registered_at is not None:
                continue  # ignore input during the success pause

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                clicked_box = next(
                    (name for name, r in boxes.items() if r.collidepoint(pos)),
                    None,
                )

                if clicked_box:
                    active = clicked_box
                    message = ""
                    sfx("sound_hover")

                elif done_rect.collidepoint(pos):
                    submit()

                elif (
                    return_rect.collidepoint(pos)
                    or login_link.collidepoint(pos)
                    or side_tabs["login"][0].collidepoint(pos)
                    or side_tabs["back"][0].collidepoint(pos)
                ):
                    sfx("sound_back")
                    stop_music()
                    return "login", None

                elif side_tabs["register"][0].collidepoint(pos):
                    active = "username"
                    sfx("sound_click")

                elif top_tabs["user"][0].collidepoint(pos):
                    active = "username"
                    sfx("sound_hover")

                elif top_tabs["mail"][0].collidepoint(pos):
                    active = "email"
                    sfx("sound_hover")

                elif top_tabs["pass"][0].collidepoint(pos):
                    active = "password"
                    sfx("sound_hover")

                elif media_box.collidepoint(pos):
                    toggle_music()
                    sfx("sound_click")

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F11:
                    toggle_fullscreen()

                elif event.key == pygame.K_ESCAPE:
                    sfx("sound_back")
                    stop_music()
                    return "login", None

                elif event.key in (pygame.K_TAB, pygame.K_DOWN):
                    active = FIELDS[(FIELDS.index(active) + 1) % len(FIELDS)]
                    sfx("sound_hover")

                elif event.key == pygame.K_UP:
                    active = FIELDS[(FIELDS.index(active) - 1) % len(FIELDS)]
                    sfx("sound_hover")

                elif event.key == pygame.K_BACKSPACE:
                    if active == "username":
                        username = username[:-1]
                    elif active == "email":
                        email = email[:-1]
                    else:
                        password = password[:-1]

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if active == "username":
                        active = "email"
                        sfx("sound_hover")
                    elif active == "email":
                        active = "password"
                        sfx("sound_hover")
                    else:
                        submit()

                elif event.unicode and event.unicode.isprintable():
                    if active == "username" and len(username) < MAX_FIELD_LENGTH:
                        username += event.unicode
                    elif active == "email" and len(email) < MAX_FIELD_LENGTH:
                        email += event.unicode
                    elif active == "password" and len(password) < MAX_FIELD_LENGTH:
                        password += event.unicode

        # ---------- draw ----------
        draw_background(screen, width, height, tick)

        draw_notepad(screen, note_rect, big_font, tab_font, False,
                     footer="Be brave, pilot!")

        for key, (r, col, label) in side_tabs.items():
            draw_tab(screen, r, col, label, tab_font, r.collidepoint(mouse_pos), vertical=True)

        for key, (r, col, label) in top_tabs.items():
            draw_tab(screen, r, col, label, tab_font, r.collidepoint(mouse_pos))

        pygame.draw.rect(screen, (60, 40, 36), book.move(8, 10), border_radius=10)
        pygame.draw.rect(screen, PAPER_SHADE, book, border_radius=10)
        pygame.draw.rect(screen, OUTLINE, book, 3, border_radius=10)

        pygame.draw.rect(screen, PAPER, left_page, border_radius=6)
        pygame.draw.rect(screen, PAPER, right_page, border_radius=6)

        for i in range(24):
            a = 70 - i * 3
            if a <= 0:
                break
            alpha_rect(screen, (120, 100, 70, a), pygame.Rect(book.centerx - 24 + i, book.y + 10, 1, book_h - 20))
            alpha_rect(screen, (120, 100, 70, a), pygame.Rect(book.centerx + 24 - i, book.y + 10, 1, book_h - 20))
        pygame.draw.line(screen, SPINE, (book.centerx, book.y + 8), (book.centerx, book.bottom - 8), 2)

        draw_ruled_lines(screen, left_page, left_page.y + 90)

        put_text(screen, heading_font, "Register", INK, (left_page.centerx - 20, left_page.y + 30), "midtop")
        pygame.draw.line(
            screen, INK_SOFT,
            (left_page.centerx - 80, left_page.y + 66),
            (left_page.centerx + 40, left_page.y + 66), 2,
        )

        sb = pygame.Rect(left_page.right - 34, left_page.y + 44, 14, left_page.h - 100)
        pygame.draw.rect(screen, (245, 238, 220), sb, border_radius=6)
        pygame.draw.rect(screen, OUTLINE, sb, 2, border_radius=6)
        thumb = pygame.Rect(sb.x + 2, sb.y + 4, sb.w - 4, sb.h // 3)
        pygame.draw.rect(screen, (200, 184, 150), thumb, border_radius=5)

        draw_field(screen, username_box, "Username", username, active == "username",
                   False, input_font, label_font, cursor_visible, "your name, pilot")
        draw_field(screen, email_box, "Email", email, active == "email",
                   False, input_font, label_font, cursor_visible, "you@email.com")
        draw_field(screen, password_box, "Password", password, active == "password",
                   True, input_font, label_font, cursor_visible, "secret code (6+)")

        hovered_link = login_link.collidepoint(mouse_pos)
        link_img = small_font.render(" Login", True, INK if hovered_link else ERROR)
        screen.blit(prompt_img, (footer_x, footer_y))
        screen.blit(link_img, (link_x, footer_y))
        if hovered_link:
            pygame.draw.line(screen, ERROR,
                             (link_x + 8, login_link.bottom),
                             (login_link.right, login_link.bottom), 2)

        put_text(screen, tab_font, "Press Tab to switch", INK_SOFT,
                 (left_page.x + 28, left_page.bottom - 16), "bottomleft")

        # polaroid
        pygame.draw.rect(screen, (190, 178, 150), polaroid.move(5, 6), border_radius=4)
        pygame.draw.rect(screen, (255, 255, 252), polaroid, border_radius=4)
        pygame.draw.rect(screen, OUTLINE, polaroid, 2, border_radius=4)

        pic = draw_space_picture(picture_rect.size, tick, stars)
        screen.blit(pic, picture_rect)
        pygame.draw.rect(screen, OUTLINE, picture_rect, 3)

        put_text(screen, caption_font, "Join the Fleet", INK,
                 (polaroid.centerx, polaroid.bottom - 28), "center")

        draw_tape(screen, (polaroid.x + 10, polaroid.y + 6), 40)
        draw_tape(screen, (polaroid.right - 10, polaroid.bottom - 8), 40)

        draw_media_controls(
            screen, controls_center, music_playing,
            media_box.collidepoint(mouse_pos),
        )

        pygame.draw.rect(screen, (255, 252, 242), desc_box, border_radius=6)
        pygame.draw.rect(screen, OUTLINE, desc_box, 2, border_radius=6)
        for x in range(desc_box.x + 8, desc_box.right - 8, 10):
            pygame.draw.circle(screen, INK_SOFT, (x, desc_box.y + 8), 1)

        if message:
            put_text(screen, input_font, message, message_color,
                     (desc_box.centerx, desc_box.centery + 4), "center")
        else:
            put_text(screen, input_font, "Join the Galactic Battlefield", INK_SOFT,
                     (desc_box.centerx, desc_box.centery + 4), "center")

        # bottom actions
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

        # show the success message briefly, then go back to login
        if registered_at is not None and time.time() - registered_at > 0.8:
            stop_music()
            return "login", None