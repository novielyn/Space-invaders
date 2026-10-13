import math
import random

import pygame

from settings import (
    DIFFICULTIES,
    DIFFICULTY_ORDER,
    PREFERENCES,
    save_preferences,
    apply_volume_settings,
)

# Shared notebook-style helpers
from screens.login import (
    INK,
    INK_SOFT,
    ERROR,
    SUCCESS,
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
    wrap_text,
)

from entities.button import MobileButtons

try:
    from managers.ui_sounds import ui_sounds
except Exception:
    ui_sounds = None


GOLD_INK = (170, 110, 20)
GREEN_INK = (40, 130, 70)
RULE = (205, 196, 176)
TRACK = (232, 224, 204)
SWITCH_OFF = (205, 196, 176)
KNOB = (250, 244, 228)


# ---------------------------------------------------------------
# Sounds
# ---------------------------------------------------------------
def sound_hover():
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


def sound_click():
    if ui_sounds is None:
        return
    try:
        ui_sounds.click()
    except Exception:
        pass


def sound_back():
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
# Tab icons (drawn on the polaroid picture)
# ---------------------------------------------------------------
def _draw_speaker_icon(screen, center, size, color):
    cx, cy = center
    body = [
        (cx - size, cy - int(size * 0.30)),
        (cx - int(size * 0.35), cy - int(size * 0.30)),
        (cx + int(size * 0.25), cy - size),
        (cx + int(size * 0.25), cy + size),
        (cx - int(size * 0.35), cy + int(size * 0.30)),
        (cx - size, cy + int(size * 0.30)),
    ]
    pygame.draw.polygon(screen, color, body, 3)

    for radius in (int(size * 0.55), int(size * 0.95)):
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = (cx + int(size * 0.35), cy)
        pygame.draw.arc(screen, color, rect, -math.pi / 3, math.pi / 3, 3)


def _draw_bars_icon(screen, center, size, color):
    cx, cy = center
    heights = (int(size * 0.7), int(size * 1.3), int(size * 0.5), int(size * 1.1))
    total_w = size * 2.2
    gap = total_w / len(heights)
    start_x = cx - total_w / 2

    for i, h in enumerate(heights):
        x = int(start_x + i * gap)
        pygame.draw.line(screen, color, (x, cy + h // 2), (x, cy - h // 2), 5)


def _draw_gear_icon(screen, center, size, color):
    cx, cy = center
    r = int(size * 0.55)
    pygame.draw.circle(screen, color, (cx, cy), r, 3)
    pygame.draw.circle(screen, color, (cx, cy), max(2, int(r * 0.35)))

    for angle in range(0, 360, 45):
        radians = math.radians(angle)
        pygame.draw.line(
            screen, color,
            (cx + math.cos(radians) * r, cy + math.sin(radians) * r),
            (cx + math.cos(radians) * (r + int(size * 0.32)),
             cy + math.sin(radians) * (r + int(size * 0.32))),
            3,
        )


def _draw_user_icon(screen, center, size, color):
    cx, cy = center
    pygame.draw.circle(
        screen, color, (cx, cy - int(size * 0.30)), max(3, int(size * 0.32)), 3
    )
    pygame.draw.arc(
        screen, color,
        pygame.Rect(cx - int(size * 0.60), cy - int(size * 0.05),
                    int(size * 1.2), int(size * 1.05)),
        math.radians(0), math.radians(180), 3,
    )


TABS = (
    ("audio", "Audio", _draw_speaker_icon,
     "Tune the master, music and sound effect volumes."),
    ("graphics", "Graphics", _draw_bars_icon,
     "Switch fullscreen and screen shake on or off."),
    ("general", "General", _draw_gear_icon,
     "Pick your difficulty and control layout. Mobile buttons preview below."),
    ("account", "Account", _draw_user_icon,
     "See who is signed in on this pilot log."),
)
TAB_KEYS = tuple(t[0] for t in TABS)
TAB_COLORS = (TAB_PINK, TAB_ORANGE, TAB_YELLOW, TAB_PURPLE)

SLIDERS = (
    ("master_volume", "Master volume"),
    ("music_volume", "Music volume"),
    ("sfx_volume", "SFX volume"),
)


# ---------------------------------------------------------------
# Journal-style widgets. Each returns the rect to hit-test.
# ---------------------------------------------------------------
def draw_slider_row(screen, x, y, width, label, value, label_font, value_font,
                    dragging, hovered):
    put_text(screen, label_font, label, INK, (x, y + 14), "midleft")
    put_text(screen, value_font, f"{int(value * 100)}%",
             GOLD_INK if (dragging or hovered) else INK_SOFT,
             (x + width, y + 14), "midright")

    track = pygame.Rect(x, y + 36, width, 10)
    pygame.draw.rect(screen, TRACK, track, border_radius=5)

    fill_w = int(width * max(0.0, min(1.0, value)))
    if fill_w > 0:
        pygame.draw.rect(screen, ERROR,
                         pygame.Rect(track.x, track.y, fill_w, track.h), border_radius=5)
    pygame.draw.rect(screen, OUTLINE, track, 2, border_radius=5)

    knob_r = 12 if dragging else 10
    knob = (track.x + fill_w, track.centery)
    pygame.draw.circle(screen, (150, 130, 100), (knob[0] + 1, knob[1] + 2), knob_r)
    pygame.draw.circle(screen, KNOB, knob, knob_r)
    pygame.draw.circle(screen, OUTLINE, knob, knob_r, 2)

    pygame.draw.line(screen, RULE, (x - 6, y + 62), (x + width + 6, y + 62), 1)

    return pygame.Rect(x - 8, y + 24, width + 16, 34)


def draw_toggle_row(screen, x, y, width, label, is_on, label_font, hovered):
    put_text(screen, label_font, label, INK, (x, y + 18), "midleft")

    switch = pygame.Rect(x + width - 56, y + 4, 56, 28)
    pygame.draw.rect(screen, GREEN_INK if is_on else SWITCH_OFF, switch, border_radius=14)
    pygame.draw.rect(screen, OUTLINE, switch, 3 if hovered else 2, border_radius=14)

    knob_r = 10
    knob_x = switch.right - knob_r - 5 if is_on else switch.left + knob_r + 5
    pygame.draw.circle(screen, KNOB, (knob_x, switch.centery), knob_r)
    pygame.draw.circle(screen, OUTLINE, (knob_x, switch.centery), knob_r, 2)

    put_text(screen, hand_font(14, True), "ON" if is_on else "OFF",
             GREEN_INK if is_on else INK_SOFT,
             (switch.x - 12, switch.centery), "midright")

    pygame.draw.line(screen, RULE, (x - 6, y + 44), (x + width + 6, y + 44), 1)

    return pygame.Rect(x - 8, y - 2, width + 16, 44)


def draw_radio_row(screen, x, y, width, options, selected_index, font_obj, mouse):
    """Evenly spaced radio options on one ruled line. Returns hit rects."""
    cell_w = width / max(1, len(options))
    rects = []

    for i, label in enumerate(options):
        cell = pygame.Rect(int(x + i * cell_w), y, int(cell_w), 34)
        rects.append(cell)

        is_sel = i == selected_index
        hovered = cell.collidepoint(mouse)

        if hovered and not is_sel:
            alpha_rect(screen, (*HIGHLIGHT, 80), cell, 8)

        shown = fit_text(font_obj, label, int(cell_w) - 30)
        text_w = font_obj.size(shown)[0]
        group_w = 20 + text_w
        gx = cell.centerx - group_w // 2

        center = (gx + 6, cell.centery)
        pygame.draw.circle(screen, OUTLINE if (is_sel or hovered) else INK_SOFT, center, 7, 2)
        if is_sel:
            pygame.draw.circle(screen, ERROR, center, 4)

        put_text(screen, font_obj, shown, INK if (is_sel or hovered) else INK_SOFT,
                 (gx + 20, cell.centery), "midleft")

    pygame.draw.line(screen, RULE, (x - 6, y + 40), (x + width + 6, y + 40), 1)
    return rects


def tag_button_label(screen, rect, label, fnt, hovered, color):
    r = rect.copy()
    if hovered:
        r.y -= 2
    pygame.draw.rect(screen, (150, 130, 100), r.move(0, 3), border_radius=8)
    pygame.draw.rect(screen, color, r, border_radius=8)
    pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
    put_text(screen, fnt, label, INK, r.center, "center")


def draw_mobile_preview(screen, preview, area, enabled, mouse, mouse_down, tick, label_font):
    """Draw the in-match mobile buttons inside `area` using MobileButtons itself."""
    put_text(screen, label_font, "Match buttons", INK_SOFT, (area.x, area.y - 14), "midleft")

    preview.left = pygame.Rect(area.x, area.y + 10, preview.button_width, preview.button_height)
    preview.right = pygame.Rect(preview.left.right + 12, area.y + 10,
                                preview.button_width, preview.button_height)
    preview.fire = pygame.Rect(area.right - preview.fire_width, area.y + 5,
                               preview.fire_width, preview.fire_height)

    held = mouse_down and enabled
    preview.left_pressed = held and preview.left.collidepoint(mouse)
    preview.right_pressed = held and preview.right.collidepoint(mouse)
    preview.fire_pressed = held and preview.fire.collidepoint(mouse)
    preview.animation_timer = tick

    preview.draw(screen)

    if not enabled:
        alpha_rect(screen, (*PAPER, 160), area.inflate(16, 16), 8)
        put_text(screen, label_font, "Turn on Mobile controls to use these",
                 INK_SOFT, area.center, "center")


# ---------------------------------------------------------------
# Settings screen
# ---------------------------------------------------------------
def settings_screen(screen, clock, toggle_fullscreen_callback=None, player=None):
    """Journal-style settings. Returns ("menu" | "quit", screen)."""
    heading_font = hand_font(26, True)
    row_font = hand_font(20, True)
    value_font = hand_font(17, True)
    radio_font = hand_font(17, True)
    body_font = hand_font(17)
    small_font = hand_font(15)
    caption_font = hand_font(26, True)
    big_font = hand_font(28, True)
    action_font = hand_font(40, True)
    tab_font = hand_font(15, True)

    rng = random.Random(44)
    stars = [(rng.random(), rng.random(), rng.choice((1, 1, 2))) for _ in range(45)]

    # Same class the match uses, so the preview looks identical
    mobile_preview = MobileButtons()

    active_tab = "audio"
    dragging = None
    previous_hover = None
    tick = 0

    notification = ""
    notification_color = SUCCESS
    notification_until = 0

    saved_difficulty = PREFERENCES.get("difficulty", "NORMAL")
    if saved_difficulty in DIFFICULTY_ORDER:
        difficulty_index = DIFFICULTY_ORDER.index(saved_difficulty)
    else:
        difficulty_index = DIFFICULTY_ORDER.index("NORMAL")
        PREFERENCES["difficulty"] = "NORMAL"

    def notify(message, color=SUCCESS, ms=1500):
        nonlocal notification, notification_color, notification_until
        notification = message
        notification_color = color
        notification_until = pygame.time.get_ticks() + ms

    def set_fullscreen(value):
        nonlocal screen

        PREFERENCES["fullscreen"] = value

        if toggle_fullscreen_callback is not None:
            screen = toggle_fullscreen_callback()
        elif value:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((1100, 700))

        save_preferences(PREFERENCES)

    def set_slider(key, mouse_x, track_x, track_w):
        t = (mouse_x - track_x) / max(1, track_w)
        PREFERENCES[key] = max(0.0, min(1.0, t))
        apply_volume_settings()

    while True:
        tick += 1

        width, height = screen.get_size()
        mouse = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]

        # ---------- layout ----------
        book, lp, rp = book_layout(width, height)
        polaroid, picture, controls_center, desc_box = polaroid_layout(rp)

        x0 = lp.x + 40
        right_edge = lp.right - 42
        cw = right_edge - x0
        top_y = lp.y + 96

        note_rect = pygame.Rect(book.right - 34, book.y + 18, 150, 230)
        side_back = pygame.Rect(book.x - 58, book.y + 60, 78, 30)

        top_tabs = [
            (pygame.Rect(lp.x + 30 + i * 84, book.y - 36, 78, 48), TAB_COLORS[i], TABS[i][1])
            for i in range(len(TABS))
        ]
        deco_tabs = [
            (pygame.Rect(rp.x + 30, book.y - 36, 72, 48), TAB_PURPLE),
            (pygame.Rect(rp.x + 108, book.y - 36, 72, 48), TAB_BLUE),
        ]

        return_rect = pygame.Rect(30, height - 78, 190, 56)
        done_rect = pygame.Rect(width - 220, height - 78, 190, 56)

        hits = []  # (rect, action)

        # ---------- draw ----------
        draw_background(screen, width, height, tick)

        tab_label = next(t[1] for t in TABS if t[0] == active_tab)
        draw_notepad(screen, note_rect, big_font, tab_font, False, footer=tab_label)

        draw_tab(screen, side_back, SIDE_PINK, "Menu", tab_font,
                 side_back.collidepoint(mouse), vertical=True)
        hits.append((side_back, "back"))

        for r, col, label in top_tabs:
            key = next(t[0] for t in TABS if t[1] == label)
            draw_tab(screen, r, col, label, tab_font, key == active_tab or r.collidepoint(mouse))
            hits.append((r, ("tab", key)))
        for r, col in deco_tabs:
            draw_tab(screen, r, col, "", tab_font, r.collidepoint(mouse))

        draw_book(screen, book, lp, rp)

        put_text(screen, heading_font, tab_label, INK, (lp.centerx, lp.y + 28), "midtop")
        pygame.draw.line(screen, INK_SOFT,
                         (lp.centerx - 70, lp.y + 64), (lp.centerx + 70, lp.y + 64), 2)

        if active_tab == "audio":
            for i, (key, label) in enumerate(SLIDERS):
                row_y = top_y + i * 70
                hit_rect = draw_slider_row(
                    screen, x0, row_y, cw, label,
                    PREFERENCES.get(key, 0.0), row_font, value_font,
                    dragging == key, pygame.Rect(x0 - 8, row_y, cw + 16, 62).collidepoint(mouse),
                )
                hits.append((hit_rect, ("slider", key)))

        elif active_tab == "graphics":
            for i, (key, label) in enumerate((
                ("fullscreen", "Fullscreen"),
                ("screen_shake", "Screen shake"),
            )):
                row_y = top_y + i * 56
                row_rect = pygame.Rect(x0 - 8, row_y - 2, cw + 16, 44)
                hit_rect = draw_toggle_row(
                    screen, x0, row_y, cw, label,
                    PREFERENCES.get(key, False), row_font, row_rect.collidepoint(mouse),
                )
                hits.append((hit_rect, ("toggle", key)))

            put_text(screen, small_font, "Tip: F11 also toggles fullscreen.", INK_SOFT,
                     (x0, top_y + 2 * 56 + 14), "midleft")

        elif active_tab == "general":
            row_rect = pygame.Rect(x0 - 8, top_y - 2, cw + 16, 44)
            hit_rect = draw_toggle_row(
                screen, x0, top_y, cw, "Mobile controls",
                PREFERENCES.get("mobilecontrols", False), row_font,
                row_rect.collidepoint(mouse),
            )
            hits.append((hit_rect, ("toggle", "mobilecontrols")))

            # live preview of the in-match mobile buttons (right under the toggle)
            preview_area = pygame.Rect(x0, top_y + 90, cw, 80)
            draw_mobile_preview(
                screen, mobile_preview, preview_area,
                PREFERENCES.get("mobilecontrols", False),
                mouse, mouse_down, tick, small_font,
            )

            diff_y = top_y + 190
            put_text(screen, row_font, "Difficulty", INK, (x0, diff_y + 10), "midleft")

            options = [DIFFICULTIES[key]["label"].title() for key in DIFFICULTY_ORDER]
            rects = draw_radio_row(
                screen, x0, diff_y + 30, cw, options, difficulty_index, radio_font, mouse
            )
            for i, r in enumerate(rects):
                hits.append((r, ("difficulty", i)))

        else:  # account
            username = None
            if player is not None:
                if isinstance(player, dict):
                    username = player.get("username")
                else:
                    username = getattr(player, "username", None)

            if username:
                put_text(screen, row_font, "Signed in as", INK_SOFT, (x0, top_y + 14), "midleft")
                put_text(screen, row_font, fit_text(row_font, str(username), cw),
                         INK, (x0, top_y + 46), "midleft")
            else:
                put_text(screen, row_font, "Guest session", INK_SOFT, (x0, top_y + 14), "midleft")

            pygame.draw.line(screen, RULE, (x0 - 6, top_y + 70), (x0 + cw + 6, top_y + 70), 1)
            put_text(screen, small_font, "Account management is coming soon.",
                     INK_SOFT, (x0, top_y + 90), "midleft")

        # ---------- right page ----------
        pic = draw_space_picture(picture.size, tick, stars)
        icon_fn = next(t[2] for t in TABS if t[0] == active_tab)
        pw, ph = pic.get_size()
        icon_size = max(20, min(pw, ph) // 6)
        bob = int(math.sin(tick * 0.05) * 3)
        pygame.draw.circle(pic, (245, 235, 210), (pw // 2, ph // 2 + bob),
                           int(icon_size * 1.9), 3)
        icon_fn(pic, (pw // 2, ph // 2 + bob), icon_size, (245, 235, 210))
        draw_polaroid(screen, polaroid, picture, pic, tab_label, caption_font)

        put_text(screen, small_font, "ESC to return  \u00b7  Tab to switch page", INK_SOFT,
                 controls_center, "center")

        draw_desc_box(screen, desc_box)
        description = next(t[3] for t in TABS if t[0] == active_tab)
        lines = wrap_text(body_font, description, desc_box.w - 24)
        line_h = body_font.get_linesize()
        ty = desc_box.centery - (line_h * len(lines)) // 2 + 4
        for line in lines:
            put_text(screen, body_font, line, INK, (desc_box.centerx, ty), "midtop")
            ty += line_h

        draw_actions(screen, action_font, return_rect, done_rect, mouse)
        hits.append((return_rect, "back"))
        hits.append((done_rect, "back"))

        # toast
        if notification and pygame.time.get_ticks() < notification_until:
            img = body_font.render(notification, True, INK)
            toast = pygame.Rect(0, 0, img.get_width() + 40, 40)
            toast.center = (width // 2, height - 40)
            pygame.draw.rect(screen, (60, 40, 36), toast.move(3, 4), border_radius=8)
            pygame.draw.rect(screen, PAPER, toast, border_radius=8)
            pygame.draw.rect(screen, notification_color, toast, 3, border_radius=8)
            screen.blit(img, img.get_rect(center=toast.center))

        # hover sound when the hovered control changes
        hover_key = next((str(a) for r, a in hits if r.collidepoint(mouse)), None)
        if hover_key is not None and hover_key != previous_hover:
            sound_hover()
        previous_hover = hover_key

        pygame.display.flip()

        # ---------- events ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_preferences(PREFERENCES)
                return "quit", screen

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sound_back()
                    save_preferences(PREFERENCES)
                    return "menu", screen

                elif event.key == pygame.K_F11:
                    set_fullscreen(not PREFERENCES.get("fullscreen", False))
                    break  # screen may have changed

                elif event.key == pygame.K_TAB:
                    index = TAB_KEYS.index(active_tab)
                    active_tab = TAB_KEYS[(index + 1) % len(TAB_KEYS)]
                    sound_click()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = next((a for r, a in hits if r.collidepoint(event.pos)), None)
                if action is None:
                    continue

                sound_click()

                if action == "back":
                    save_preferences(PREFERENCES)
                    return "menu", screen

                elif action[0] == "tab":
                    active_tab = action[1]

                elif action[0] == "slider":
                    dragging = action[1]
                    set_slider(dragging, event.pos[0], x0, cw)

                elif action[0] == "toggle":
                    key = action[1]
                    new_value = not PREFERENCES.get(key, False)

                    if key == "fullscreen":
                        set_fullscreen(new_value)
                    else:
                        PREFERENCES[key] = new_value
                        save_preferences(PREFERENCES)

                    names = {
                        "fullscreen": "Fullscreen",
                        "screen_shake": "Screen shake",
                        "mobilecontrols": "Mobile controls",
                    }
                    notify(f"{names.get(key, key)} {'on' if new_value else 'off'}.",
                           SUCCESS if new_value else INK_SOFT)

                elif action[0] == "difficulty":
                    difficulty_index = action[1]
                    PREFERENCES["difficulty"] = DIFFICULTY_ORDER[difficulty_index]
                    save_preferences(PREFERENCES)

                break  # hits are stale after any action

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragging is not None:
                    save_preferences(PREFERENCES)
                dragging = None

        # keep dragging a slider while the button is held
        if dragging is not None and mouse_down:
            set_slider(dragging, mouse[0], x0, cw)

        clock.tick(60)