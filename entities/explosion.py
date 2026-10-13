import pygame
import random
import math


class Explosion:
   
    # =========================================================
    # COLORS
    # =========================================================

    COLORS = [
        (255, 255, 240),   # white-hot
        (255, 240, 150),   # bright yellow
        (255, 200, 60),    # yellow
        (255, 120, 25),    # orange
        (255, 50, 15),     # red
    ]

    SPARK_COLOR = (255, 235, 160)

    # =========================================================
    # EXPLOSION PRESETS
    # =========================================================

    PRESETS = {

        "small": {
            "duration": 0.42,
            "particles": 18,
            "sparks": 12,
            "radius": 32,
            "shake": 2.0
        },

        "normal": {
            "duration": 0.60,
            "particles": 32,
            "sparks": 22,
            "radius": 62,
            "shake": 4.0
        },

        "large": {
            "duration": 0.90,
            "particles": 60,
            "sparks": 40,
            "radius": 105,
            "shake": 8.0
        }
    }

    # =========================================================
    # INITIALIZE
    # =========================================================

    def __init__(
        self,
        x,
        y,
        size="normal"
    ):

        self.x = float(x)
        self.y = float(y)

        preset = self.PRESETS.get(
            size,
            self.PRESETS["normal"]
        )

        self.duration = preset["duration"]
        self.max_radius = preset["radius"]
        self.shake_strength = preset["shake"]

        self.timer = 0.0

        # =====================================================
        # PARTICLES
        # =====================================================

        self.particles = []

        for _ in range(preset["particles"]):

            angle = random.uniform(
                0,
                math.tau
            )

            # Stronger particles near the beginning.
            speed = random.uniform(
                70,
                360
            )

            self.particles.append({

                "x": self.x,
                "y": self.y,

                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,

                "size": random.uniform(
                    2.5,
                    7.5
                ),

                "life": random.uniform(
                    0.35,
                    0.75
                ),

                "max_life": 0.75,

                "drag": random.uniform(
                    1.8,
                    3.5
                ),

                "gravity": random.uniform(
                    30,
                    100
                ),

                "color": random.choice(
                    self.COLORS
                ),

                "rotation": random.uniform(
                    0,
                    math.tau
                ),

                "rotation_speed": random.uniform(
                    -8,
                    8
                )
            })

        # =====================================================
        # SPARKS
        # =====================================================

        self.sparks = []

        for _ in range(preset["sparks"]):

            angle = random.uniform(
                0,
                math.tau
            )

            speed = random.uniform(
                180,
                650
            )

            self.sparks.append({

                "x": self.x,
                "y": self.y,

                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,

                "life": random.uniform(
                    0.18,
                    0.50
                ),

                "max_life": 0.50,

                "length": random.uniform(
                    7,
                    22
                ),

                "width": random.choice(
                    [1, 2, 2, 3]
                )
            })

        # =====================================================
        # SHOCKWAVE
        # =====================================================

        self.shockwave_radius = 5
        self.shockwave_alpha = 255

        # Second shockwave gives a more cinematic effect.
        self.second_wave_radius = 2
        self.second_wave_alpha = 180

        # =====================================================
        # CORE
        # =====================================================

        self.core_radius = 4
        self.flash_alpha = 255

        # =====================================================
        # GLOW
        # =====================================================

        self.glow_surface = self.create_glow_surface()

    # =========================================================
    # CREATE GLOW
    # =========================================================

    def create_glow_surface(self):

        size = 240

        surface = pygame.Surface(
            (size, size),
            pygame.SRCALPHA
        )

        center = (
            size // 2,
            size // 2
        )

        # Very soft outer glow
        pygame.draw.circle(
            surface,
            (255, 70, 10, 15),
            center,
            110
        )

        pygame.draw.circle(
            surface,
            (255, 100, 15, 25),
            center,
            85
        )

        pygame.draw.circle(
            surface,
            (255, 160, 30, 40),
            center,
            60
        )

        pygame.draw.circle(
            surface,
            (255, 220, 80, 60),
            center,
            38
        )

        return surface

    # =========================================================
    # EASING
    # =========================================================

    @staticmethod
    def ease_out_expo(t):

        if t >= 1:
            return 1

        return 1 - pow(
            2,
            -10 * t
        )

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt=1 / 60):

        if self.finished():
            return

        self.timer += dt

        progress = min(
            1.0,
            self.timer / self.duration
        )

        # =====================================================
        # SHOCKWAVE
        # =====================================================

        wave_progress = self.ease_out_expo(
            progress
        )

        self.shockwave_radius = (
            5
            + self.max_radius
            * wave_progress
        )

        self.shockwave_alpha = int(
            255
            * (1.0 - progress)
        )

        # Second wave expands later.
        second_progress = max(
            0,
            (progress - 0.15)
            / 0.85
        )

        self.second_wave_radius = (
            5
            + self.max_radius
            * 0.72
            * self.ease_out_expo(
                second_progress
            )
        )

        self.second_wave_alpha = int(
            170
            * (1.0 - second_progress)
        )

        # =====================================================
        # CORE FLASH
        # =====================================================

        if progress < 0.12:

            flash_progress = (
                progress / 0.12
            )

            self.core_radius = int(
                8
                + 65
                * self.ease_out_expo(
                    flash_progress
                )
            )

            self.flash_alpha = int(
                255
                * (
                    1
                    - flash_progress
                )
            )

        else:

            fade_progress = (
                (progress - 0.12)
                / 0.88
            )

            self.core_radius = int(
                32
                * (
                    1
                    - fade_progress
                )
            )

            self.flash_alpha = int(
                255
                * (
                    1
                    - fade_progress
                )
            )

        # =====================================================
        # PARTICLES
        # =====================================================

        for particle in self.particles:

            particle["x"] += (
                particle["vx"]
                * dt
            )

            particle["y"] += (
                particle["vy"]
                * dt
            )

            # Gravity
            particle["vy"] += (
                particle["gravity"]
                * dt
            )

            # Frame-independent drag
            drag = max(
                0.0,
                1.0
                - particle["drag"]
                * dt
            )

            particle["vx"] *= drag
            particle["vy"] *= drag

            # Fade
            particle["life"] -= dt

            # Shrink
            particle["size"] *= (
                1.0 - 2.5 * dt
            )

            # Rotation
            particle["rotation"] += (
                particle["rotation_speed"]
                * dt
            )

        # =====================================================
        # SPARKS
        # =====================================================

        for spark in self.sparks:

            old_x = spark["x"]
            old_y = spark["y"]

            spark["x"] += (
                spark["vx"]
                * dt
            )

            spark["y"] += (
                spark["vy"]
                * dt
            )

            drag = max(
                0.0,
                1.0
                - 4.5 * dt
            )

            spark["vx"] *= drag
            spark["vy"] *= drag

            spark["life"] -= dt

            # Store previous position for streak rendering.
            spark["old_x"] = old_x
            spark["old_y"] = old_y

        # =====================================================
        # CLEANUP
        # =====================================================

        self.particles = [
            particle
            for particle in self.particles
            if (
                particle["life"] > 0
                and particle["size"] > 0.5
            )
        ]

        self.sparks = [
            spark
            for spark in self.sparks
            if spark["life"] > 0
        ]

    # =========================================================
    # DRAW GLOW
    # =========================================================

    def draw_glow(self, screen):

        progress = min(
            1.0,
            self.timer / self.duration
        )

        # Strong at beginning, then fades.
        alpha = int(
            190
            * (
                1
                - progress
            )
        )

        if alpha <= 0:
            return

        glow = self.glow_surface.copy()

        glow.set_alpha(
            alpha
        )

        rect = glow.get_rect(
            center=(
                int(self.x),
                int(self.y)
            )
        )

        screen.blit(
            glow,
            rect
        )

    # =========================================================
    # DRAW PARTICLES
    # =========================================================

    def draw_particles(self, screen):

        for particle in self.particles:

            size = max(
                1,
                int(
                    particle["size"]
                )
            )

            alpha = int(
                255
                * max(
                    0,
                    particle["life"]
                    / particle["max_life"]
                )
            )

            if alpha <= 0:
                continue

            color = particle["color"]

            surface_size = size * 4

            surface = pygame.Surface(
                (
                    surface_size,
                    surface_size
                ),
                pygame.SRCALPHA
            )

            center = (
                surface_size // 2,
                surface_size // 2
            )

            # Particle glow
            pygame.draw.circle(
                surface,
                (
                    color[0],
                    color[1],
                    color[2],
                    alpha // 4
                ),
                center,
                size * 2
            )

            # Main particle
            pygame.draw.circle(
                surface,
                (
                    color[0],
                    color[1],
                    color[2],
                    alpha
                ),
                center,
                size
            )

            # White-hot center
            if size >= 3:

                pygame.draw.circle(
                    surface,
                    (
                        255,
                        255,
                        240,
                        alpha
                    ),
                    center,
                    max(
                        1,
                        size // 3
                    )
                )

            screen.blit(
                surface,
                (
                    int(
                        particle["x"]
                        - surface_size / 2
                    ),
                    int(
                        particle["y"]
                        - surface_size / 2
                    )
                )
            )

    # =========================================================
    # DRAW SPARKS
    # =========================================================

    def draw_sparks(self, screen):

        for spark in self.sparks:

            life_ratio = max(
                0,
                spark["life"]
                / spark["max_life"]
            )

            alpha = int(
                255
                * life_ratio
            )

            if alpha <= 0:
                continue

            start_x = int(
                spark["x"]
            )

            start_y = int(
                spark["y"]
            )

            # Use velocity direction.
            velocity_length = math.hypot(
                spark["vx"],
                spark["vy"]
            )

            if velocity_length <= 0:
                continue

            direction_x = (
                spark["vx"]
                / velocity_length
            )

            direction_y = (
                spark["vy"]
                / velocity_length
            )

            length = (
                spark["length"]
                * (
                    0.4
                    + life_ratio
                )
            )

            end_x = int(
                start_x
                - direction_x
                * length
            )

            end_y = int(
                start_y
                - direction_y
                * length
            )

            # Glow streak
            pygame.draw.line(
                screen,
                (
                    255,
                    150,
                    40
                ),
                (
                    start_x,
                    start_y
                ),
                (
                    end_x,
                    end_y
                ),
                spark["width"] + 2
            )

            # Bright core
            pygame.draw.line(
                screen,
                (
                    255,
                    240,
                    170
                ),
                (
                    start_x,
                    start_y
                ),
                (
                    end_x,
                    end_y
                ),
                spark["width"]
            )

    # =========================================================
    # DRAW SHOCKWAVE
    # =========================================================

    def draw_shockwave(self, screen):

        x = int(self.x)
        y = int(self.y)

        # Main wave
        if self.shockwave_alpha > 0:

            surface_size = int(
                self.shockwave_radius * 2
                + 20
            )

            surface = pygame.Surface(
                (
                    surface_size,
                    surface_size
                ),
                pygame.SRCALPHA
            )

            center = (
                surface_size // 2,
                surface_size // 2
            )

            pygame.draw.circle(
                surface,
                (
                    255,
                    190,
                    70,
                    self.shockwave_alpha
                ),
                center,
                int(
                    self.shockwave_radius
                ),
                3
            )

            screen.blit(
                surface,
                (
                    x
                    - surface_size // 2,
                    y
                    - surface_size // 2
                )
            )

        # Secondary wave
        if self.second_wave_alpha > 0:

            surface_size = int(
                self.second_wave_radius * 2
                + 12
            )

            surface = pygame.Surface(
                (
                    surface_size,
                    surface_size
                ),
                pygame.SRCALPHA
            )

            center = (
                surface_size // 2,
                surface_size // 2
            )

            pygame.draw.circle(
                surface,
                (
                    255,
                    100,
                    30,
                    self.second_wave_alpha
                ),
                center,
                int(
                    self.second_wave_radius
                ),
                2
            )

            screen.blit(
                surface,
                (
                    x
                    - surface_size // 2,
                    y
                    - surface_size // 2
                )
            )

    # =========================================================
    # DRAW CORE
    # =========================================================

    def draw_core(self, screen):

        if self.core_radius <= 0:
            return

        x = int(self.x)
        y = int(self.y)

        radius = int(
            self.core_radius
        )

        # Outer orange energy
        pygame.draw.circle(
            screen,
            (
                255,
                80,
                10
            ),
            (
                x,
                y
            ),
            radius
        )

        # Yellow
        pygame.draw.circle(
            screen,
            (
                255,
                190,
                40
            ),
            (
                x,
                y
            ),
            max(
                1,
                int(radius * 0.68)
            )
        )

        # White-hot center
        pygame.draw.circle(
            screen,
            (
                255,
                255,
                240
            ),
            (
                x,
                y
            ),
            max(
                1,
                int(radius * 0.30)
            )
        )

    # =========================================================
    # DRAW FLASH
    # =========================================================

    def draw_flash(self, screen):

        if self.flash_alpha <= 0:
            return

        radius = int(
            self.core_radius * 1.4
        )

        if radius <= 0:
            return

        surface_size = radius * 2 + 10

        surface = pygame.Surface(
            (
                surface_size,
                surface_size
            ),
            pygame.SRCALPHA
        )

        center = (
            surface_size // 2,
            surface_size // 2
        )

        pygame.draw.circle(
            surface,
            (
                255,
                245,
                180,
                self.flash_alpha // 5
            ),
            center,
            radius
        )

        pygame.draw.circle(
            surface,
            (
                255,
                255,
                230,
                self.flash_alpha
            ),
            center,
            max(
                1,
                radius // 4
            )
        )

        screen.blit(
            surface,
            (
                int(self.x)
                - surface_size // 2,
                int(self.y)
                - surface_size // 2
            )
        )

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self, screen):

        # Back → front rendering order.

        self.draw_glow(screen)

        self.draw_shockwave(screen)

        self.draw_particles(screen)

        self.draw_sparks(screen)

        self.draw_flash(screen)

        self.draw_core(screen)

    # =========================================================
    # SCREEN SHAKE
    # =========================================================

    def get_shake_offset(self):

        if self.finished():
            return 0, 0

        progress = min(
            1.0,
            self.timer / self.duration
        )

        strength = (
            self.shake_strength
            * (
                1.0
                - progress
            )
        )

        if strength <= 0:
            return 0, 0

        return (
            random.uniform(
                -strength,
                strength
            ),
            random.uniform(
                -strength,
                strength
            )
        )

    # =========================================================
    # FINISHED
    # =========================================================

    def finished(self):

        return (
            self.timer
            >= self.duration
        )

    # =========================================================
    # CENTER
    # =========================================================

    def get_position(self):

        return (
            self.x,
            self.y
        )