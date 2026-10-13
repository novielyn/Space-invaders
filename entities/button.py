import math

import pygame

# Journal theme
try:
    from screens.login import (
        INK,
        OUTLINE,
        ERROR,
        TAB_PINK,
        TAB_YELLOW,
        TAB_BLUE,
        hand_font,
    )
except Exception:
    INK = (60, 44, 40)
    OUTLINE = (60, 44, 40)
    ERROR = (200, 50, 60)
    TAB_PINK = (250, 170, 190)
    TAB_YELLOW = (250, 225, 130)
    TAB_BLUE = (150, 190, 235)

    def hand_font(size, bold=False):
        return pygame.font.SysFont("Arial", size, bold=bold)


# =============================================================
# SETTINGS
# =============================================================

try:
    from settings import PREFERENCES
except Exception:
    PREFERENCES = {
        "mobilecontrols": False
    }


BUTTON_SHADOW = (150, 130, 100)


def _darken(color, amount=22):
    return tuple(max(0, c - amount) for c in color[:3])


def _mix(a, b, t):
    return tuple(
        int(a[i] + (b[i] - a[i]) * t)
        for i in range(3)
    )


class MobileButtons:

    def __init__(self, screen_width=800, screen_height=600):

        self.screen_width = screen_width
        self.screen_height = screen_height

        # =====================================================
        # BUTTON SIZE
        # =====================================================

        self.button_width = 90
        self.button_height = 60

        self.fire_width = 120
        self.fire_height = 70

        # =====================================================
        # POSITION
        # =====================================================

        bottom_margin = 25

        self.left = pygame.Rect(
            20,
            screen_height - self.button_height - bottom_margin,
            self.button_width,
            self.button_height,
        )

        self.right = pygame.Rect(
            125,
            screen_height - self.button_height - bottom_margin,
            self.button_width,
            self.button_height,
        )

        self.fire = pygame.Rect(
            screen_width - self.fire_width - 25,
            screen_height - self.fire_height - bottom_margin,
            self.fire_width,
            self.fire_height,
        )

        # =====================================================
        # STATE
        # =====================================================

        self.left_pressed = False
        self.right_pressed = False
        self.fire_pressed = False

        self.animation_timer = 0

        # =====================================================
        # FONTS
        # =====================================================

        self.font = hand_font(26, True)
        self.fire_font = hand_font(28, True)

        self._label_fonts = {}

    # =========================================================
    # CHECK WHETHER BUTTONS ARE ENABLED
    # =========================================================

    def mobile_controls_enabled(self):
        """
        Returns True when the player has enabled Mobile Controls.

        IMPORTANT:
        In your requested behavior:

            Mobile Controls ON  -> buttons HIDDEN
            Mobile Controls OFF -> buttons SHOWN
        """

        try:
            return bool(
                PREFERENCES.get(
                    "mobilecontrols",
                    False
                )
            )
        except Exception:
            return False

    def buttons_should_show(self):
        """
        Your requested behavior:

        mobilecontrols = True
            -> DO NOT SHOW

        mobilecontrols = False
            -> SHOW
        """

        return not self.mobile_controls_enabled()

    # =========================================================
    # HANDLE INPUT
    # =========================================================

    def handle_mouse(self, player, events):

        # -----------------------------------------------------
        # MOBILE CONTROLS ON = NO MOBILE BUTTON INPUT
        # -----------------------------------------------------

        if not self.buttons_should_show():

            self.left_pressed = False
            self.right_pressed = False
            self.fire_pressed = False

            return False

        firing = False

        self.animation_timer += 1

        self.left_pressed = False
        self.right_pressed = False
        self.fire_pressed = False

        # =====================================================
        # MOUSE
        # =====================================================

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        if mouse_pressed:

            if self.left.collidepoint(mouse_pos):
                self.left_pressed = True

            if self.right.collidepoint(mouse_pos):
                self.right_pressed = True

            if self.fire.collidepoint(mouse_pos):
                self.fire_pressed = True
                firing = True

        # =====================================================
        # MOVEMENT
        # =====================================================

        if self.left_pressed and not self.right_pressed:

            try:
                player.move_left()
            except Exception:
                pass

        elif self.right_pressed and not self.left_pressed:

            try:
                player.move_right()
            except Exception:
                pass

        return firing

    # =========================================================
    # HELPERS
    # =========================================================

    def _label_font(self, size):

        font = self._label_fonts.get(size)

        if font is None:

            font = hand_font(
                size,
                True
            )

            self._label_fonts[size] = font

        return font

    # =========================================================
    # GLOW
    # =========================================================

    def draw_glow(
        self,
        screen,
        rect,
        color,
        strength=3
    ):

        pygame.draw.rect(
            screen,
            BUTTON_SHADOW,
            rect.move(0, 3),
            border_radius=12
        )

    # =========================================================
    # DRAW BUTTON
    # =========================================================

    def draw_button(
        self,
        screen,
        rect,
        base_color,
        pressed,
        label,
        text_size=26,
    ):

        draw_rect = rect.move(
            0,
            3 if pressed else 0
        )

        # Paper shadow
        pygame.draw.rect(
            screen,
            BUTTON_SHADOW,
            rect.move(0, 5),
            border_radius=12
        )

        color = (
            _darken(base_color)
            if pressed
            else base_color
        )

        pygame.draw.rect(
            screen,
            color,
            draw_rect,
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            OUTLINE,
            draw_rect,
            3 if pressed else 2,
            border_radius=12
        )

        if label:

            font = self._label_font(
                text_size
            )

            text = font.render(
                label,
                True,
                INK
            )

            screen.blit(
                text,
                text.get_rect(
                    center=draw_rect.center
                )
            )

    # =========================================================
    # DRAW FIRE BUTTON
    # =========================================================

    def draw_fire_button(self, screen):

        pulse = (
            math.sin(
                self.animation_timer * 0.12
            ) + 1
        ) / 2

        draw_rect = self.fire.move(
            0,
            4 if self.fire_pressed else 0
        )

        pygame.draw.rect(
            screen,
            BUTTON_SHADOW,
            self.fire.move(0, 6),
            border_radius=13
        )

        fill = TAB_PINK

        if self.fire_pressed:

            fill = _darken(
                fill,
                28
            )

        pygame.draw.rect(
            screen,
            fill,
            draw_rect,
            border_radius=13
        )

        border = _mix(
            OUTLINE,
            ERROR,
            pulse
        )

        pygame.draw.rect(
            screen,
            border,
            draw_rect,
            3,
            border_radius=13
        )

        # Flame
        cx = draw_rect.centerx
        cy = draw_rect.centery - 10

        flame = [
            (cx, cy - 15),
            (cx - 10, cy + 5),
            (cx, cy + 12),
            (cx + 10, cy + 5),
        ]

        pygame.draw.polygon(
            screen,
            (245, 150, 50),
            flame
        )

        pygame.draw.polygon(
            screen,
            OUTLINE,
            flame,
            2
        )

        text = self.fire_font.render(
            "Fire",
            True,
            INK
        )

        screen.blit(
            text,
            (
                draw_rect.centerx
                - text.get_width() // 2,

                draw_rect.bottom
                - text.get_height()
                - 3,
            ),
        )

    # =========================================================
    # DRAW ARROW
    # =========================================================

    def draw_arrow(
        self,
        screen,
        rect,
        direction,
        pressed
    ):

        center_x = rect.centerx

        center_y = (
            rect.centery
            + (3 if pressed else 0)
        )

        size = 16

        if direction == "left":

            points = [
                (
                    center_x + size,
                    center_y - size
                ),
                (
                    center_x - size,
                    center_y
                ),
                (
                    center_x + size,
                    center_y + size
                ),
            ]

        else:

            points = [
                (
                    center_x - size,
                    center_y - size
                ),
                (
                    center_x + size,
                    center_y
                ),
                (
                    center_x - size,
                    center_y + size
                ),
            ]

        pygame.draw.polygon(
            screen,
            INK,
            points
        )

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self, screen):

        # =====================================================
        # IMPORTANT
        #
        # Mobile Controls ON:
        #     DO NOT DRAW ANYTHING
        #
        # Mobile Controls OFF:
        #     DRAW BUTTONS
        # =====================================================

        if not self.buttons_should_show():

            # Clear button pressed states too
            self.left_pressed = False
            self.right_pressed = False
            self.fire_pressed = False

            return

        # =====================================================
        # DRAW LEFT
        # =====================================================

        self.draw_button(
            screen,
            self.left,
            TAB_BLUE,
            self.left_pressed,
            "",
            26
        )

        self.draw_arrow(
            screen,
            self.left,
            "left",
            self.left_pressed
        )

        # =====================================================
        # DRAW RIGHT
        # =====================================================

        self.draw_button(
            screen,
            self.right,
            TAB_BLUE,
            self.right_pressed,
            "",
            26
        )

        self.draw_arrow(
            screen,
            self.right,
            "right",
            self.right_pressed
        )

        # =====================================================
        # DRAW FIRE
        # =====================================================

        self.draw_fire_button(
            screen
        )