import time
import math

import pygame


class BossBullet:

    def __init__(self, x, y, screen_height):
        self.width = 18
        self.height = 45

        self.x = x - self.width // 2
        self.y = y

        self.speed = 7
        self.screen_height = screen_height

        self.active = True

        # ---------------------------------------------------
        # VISUAL EXTRAS
        # ---------------------------------------------------

        self.spawn_time = time.time()

        # Trail of recent positions, used to draw a fading streak
        # behind the bullet as it falls.
        self.trail = []
        self.max_trail_length = 6

    def update(self):
        # Record where we were before moving, for the trail effect
        self.trail.append((self.x, self.y))

        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)

        self.y += self.speed

        if self.y > self.screen_height:
            self.active = False

    def get_rect(self):
        return pygame.Rect(
            self.x,
            self.y,
            self.width,
            self.height
        )

    def draw(self, screen):
        elapsed = time.time() - self.spawn_time

        # -----------------------------------------------------
        # MOTION TRAIL
        # (fading, shrinking copies of the bullet behind it)
        # -----------------------------------------------------

        trail_count = len(self.trail)

        for i, (trail_x, trail_y) in enumerate(self.trail):
            fade = (i + 1) / (trail_count + 1)

            trail_alpha = int(90 * fade)
            trail_scale = 0.5 + 0.5 * fade

            trail_width = max(2, int(self.width * trail_scale))
            trail_height = max(2, int(self.height * trail_scale))

            trail_surface = pygame.Surface(
                (trail_width, trail_height),
                pygame.SRCALPHA
            )

            pygame.draw.ellipse(
                trail_surface,
                (255, 40, 40, trail_alpha),
                (0, 0, trail_width, trail_height)
            )

            screen.blit(
                trail_surface,
                (
                    trail_x + (self.width - trail_width) // 2,
                    trail_y + (self.height - trail_height) // 2
                )
            )

        # -----------------------------------------------------
        # PULSING OUTER GLOW
        # -----------------------------------------------------

        pulse = (math.sin(elapsed * 10) + 1) / 2
        glow_padding = 16 + int(pulse * 10)
        glow_alpha = 70 + int(pulse * 50)

        glow_size = (
            self.width + glow_padding * 2,
            self.height + glow_padding * 2
        )

        glow = pygame.Surface(glow_size, pygame.SRCALPHA)

        pygame.draw.ellipse(
            glow,
            (255, 0, 0, glow_alpha),
            (
                glow_padding - 6,
                glow_padding - 6,
                self.width + 12,
                self.height + 12
            )
        )

        screen.blit(
            glow,
            (self.x - glow_padding, self.y - glow_padding)
        )

        # -----------------------------------------------------
        # BULLET BODY
        # -----------------------------------------------------

        pygame.draw.rect(
            screen,
            (255, 40, 40),
            (
                self.x,
                self.y,
                self.width,
                self.height
            ),
            border_radius=8
        )

        # Thin darker outline so the bullet reads clearly against
        # bright backgrounds
        pygame.draw.rect(
            screen,
            (140, 0, 0),
            (
                self.x,
                self.y,
                self.width,
                self.height
            ),
            width=2,
            border_radius=8
        )

        # -----------------------------------------------------
        # ENERGY CORE HIGHLIGHT
        # (brightness pulses in sync with the outer glow)
        # -----------------------------------------------------

        core_brightness = 200 + int(pulse * 55)
        core_color = (255, core_brightness, core_brightness)

        pygame.draw.rect(
            screen,
            core_color,
            (
                self.x + 5,
                self.y,
                8,
                self.height
            ),
            border_radius=4
        )

        # Small bright tip flare at the leading edge
        flare_radius = 4 + int(pulse * 2)

        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (self.x + self.width // 2, self.y + self.height - 6),
            flare_radius
        )