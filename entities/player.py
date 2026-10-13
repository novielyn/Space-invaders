import pygame
import math
import random


SHIP_THEMES = {
    "starter": {
        "rank": "ROOKIE",
        "effect_rate": 1.0,
        "speed": 7.0,
        "colors": {
            "MOLTEN_CORE": (255, 220, 60),
            "BRIGHT_LAVA": (255, 180, 30),
            "LAVA": (255, 140, 20),
            "ORANGE_LAVA": (255, 105, 12),
            "DEEP_ORANGE": (240, 75, 8),
            "RED_LAVA": (210, 45, 5),
            "DEEP_RED": (170, 25, 3),
            "DARK_RED": (120, 12, 2),
            "BLOOD": (80, 6, 1),
            "EMBER_DARK": (45, 3, 1),
            "OBSIDIAN": (25, 18, 15),
            "DARK_ROCK": (40, 28, 22),
            "ROCK": (55, 40, 32),
            "WARM_ROCK": (70, 45, 30),
            "SMOKE": (50, 35, 25),
            "DARK_SMOKE": (28, 18, 12),
            "HEAT_GLOW": (200, 60, 5),
        },
    },

    "falcon": {
        "rank": "ELITE",
        "effect_rate": 1.2,
        "speed": 8.0,
        "colors": {
            "MOLTEN_CORE": (240, 250, 255),
            "BRIGHT_LAVA": (120, 230, 255),
            "LAVA": (60, 200, 255),
            "ORANGE_LAVA": (30, 150, 255),
            "DEEP_ORANGE": (20, 100, 220),
            "RED_LAVA": (15, 70, 180),
            "DEEP_RED": (10, 50, 140),
            "DARK_RED": (8, 35, 100),
            "BLOOD": (5, 20, 70),
            "EMBER_DARK": (3, 10, 40),
            "OBSIDIAN": (15, 20, 35),
            "DARK_ROCK": (25, 35, 55),
            "ROCK": (35, 50, 75),
            "WARM_ROCK": (60, 90, 130),
            "SMOKE": (30, 45, 65),
            "DARK_SMOKE": (15, 25, 40),
            "HEAT_GLOW": (30, 150, 255),
        },
    },

    "viper": {
        "rank": "MASTER",
        "effect_rate": 1.45,
        "speed": 8.5,
        "colors": {
            "MOLTEN_CORE": (200, 255, 120),
            "BRIGHT_LAVA": (150, 255, 60),
            "LAVA": (100, 230, 30),
            "ORANGE_LAVA": (60, 200, 20),
            "DEEP_ORANGE": (40, 170, 15),
            "RED_LAVA": (25, 140, 10),
            "DEEP_RED": (15, 110, 8),
            "DARK_RED": (10, 80, 5),
            "BLOOD": (6, 50, 3),
            "EMBER_DARK": (3, 25, 2),
            "OBSIDIAN": (10, 20, 10),
            "DARK_ROCK": (18, 35, 18),
            "ROCK": (28, 50, 25),
            "WARM_ROCK": (45, 80, 35),
            "SMOKE": (22, 40, 24),
            "DARK_SMOKE": (12, 22, 13),
            "HEAT_GLOW": (60, 200, 20),
        },
    },

    "wraith": {
        "rank": "GRANDMASTER",
        "effect_rate": 1.75,
        "speed": 9.0,
        "colors": {
            "MOLTEN_CORE": (230, 200, 255),
            "BRIGHT_LAVA": (190, 120, 255),
            "LAVA": (150, 70, 255),
            "ORANGE_LAVA": (120, 40, 230),
            "DEEP_ORANGE": (95, 25, 200),
            "RED_LAVA": (75, 15, 170),
            "DEEP_RED": (55, 10, 140),
            "DARK_RED": (40, 6, 100),
            "BLOOD": (25, 3, 70),
            "EMBER_DARK": (12, 2, 40),
            "OBSIDIAN": (12, 8, 20),
            "DARK_ROCK": (22, 14, 35),
            "ROCK": (35, 22, 50),
            "WARM_ROCK": (60, 40, 80),
            "SMOKE": (28, 18, 42),
            "DARK_SMOKE": (15, 10, 25),
            "HEAT_GLOW": (120, 40, 230),
        },
    },

    "dragon": {
        "rank": "MYTHIC",
        "effect_rate": 2.1,
        "speed": 9.5,
        "colors": {
            "MOLTEN_CORE": (255, 250, 210),
            "BRIGHT_LAVA": (255, 215, 90),
            "LAVA": (255, 175, 40),
            "ORANGE_LAVA": (255, 130, 20),
            "DEEP_ORANGE": (240, 90, 15),
            "RED_LAVA": (220, 55, 10),
            "DEEP_RED": (180, 30, 8),
            "DARK_RED": (130, 15, 5),
            "BLOOD": (85, 8, 3),
            "EMBER_DARK": (45, 4, 2),
            "OBSIDIAN": (20, 12, 8),
            "DARK_ROCK": (35, 22, 14),
            "ROCK": (50, 35, 20),
            "WARM_ROCK": (90, 65, 30),
            "SMOKE": (45, 32, 18),
            "DARK_SMOKE": (24, 16, 9),
            "HEAT_GLOW": (255, 130, 20),
        },
    },
}


SHIP_ORDER = (
    "starter",
    "falcon",
    "viper",
    "wraith",
    "dragon",
)


SHIP_FX = {
    "starter": {
        "style": "plasma",
        "engine_shape": "flame",
        "charge_shape": "ring",
        "muzzle_shape": "diamond",
        "turbo_shape": "flame",
        "intensity": 1.0,
    },

    "falcon": {
        "style": "laser",
        "engine_shape": "jet",
        "charge_shape": "orbit",
        "muzzle_shape": "cross",
        "turbo_shape": "jet",
        "intensity": 1.08,
    },

    "viper": {
        "style": "toxic",
        "engine_shape": "split",
        "charge_shape": "toxic",
        "muzzle_shape": "needle",
        "turbo_shape": "split",
        "intensity": 1.18,
    },

    "wraith": {
        "style": "void",
        "engine_shape": "void",
        "charge_shape": "void",
        "muzzle_shape": "void",
        "turbo_shape": "void",
        "intensity": 1.32,
    },

    "dragon": {
        "style": "dragon",
        "engine_shape": "dragon",
        "charge_shape": "dragon",
        "muzzle_shape": "dragon",
        "turbo_shape": "dragon",
        "intensity": 1.55,
    },
}


class Player:

    def __init__(self, screen_width, screen_height, ship_id="starter"):

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.width = 120
        self.height = 100

        self.x = screen_width // 2 - self.width // 2
        self.y = screen_height - self.height - 35

        self.speed = 7.0
        self.base_speed = 7.0

        self.is_blinking = False
        self.blink_timer = 0

        self.animation_timer = 0

        self.weapon_recoil = 0
        self.muzzle_flash_timer = 0
        self.muzzle_flash_duration = 7

        self.charge_timer = 0
        self.is_charging = False

        self.engine_particles = []
        self.lava_drips = []
        self.heat_waves = []
        self.ember_particles = []
        self.magma_sparks = []

        self.roll = 0
        self.target_roll = 0

        self.shake = 0

        self.engine_phase = 0
        self.lava_phase = 0
        self.heat_phase = 0

        self.set_ship(ship_id)

        self.image = None
        self._build_ship_surface()

    def set_ship(self, ship_id):

        theme = SHIP_THEMES.get(
            ship_id,
            SHIP_THEMES["starter"],
        )

        self.ship_id = (
            ship_id
            if ship_id in SHIP_THEMES
            else "starter"
        )

        self.rank = theme["rank"]
        self.effect_rate = theme["effect_rate"]

        self.speed = float(
            theme.get("speed", 7.0)
        )

        self.base_speed = self.speed

        self.fx = SHIP_FX.get(
            self.ship_id,
            SHIP_FX["starter"],
        )

        self.fx_intensity = self.fx["intensity"]

        colors = theme["colors"]

        self.COLOR_MOLTEN_CORE = colors["MOLTEN_CORE"]
        self.COLOR_BRIGHT_LAVA = colors["BRIGHT_LAVA"]
        self.COLOR_LAVA = colors["LAVA"]
        self.COLOR_ORANGE_LAVA = colors["ORANGE_LAVA"]
        self.COLOR_DEEP_ORANGE = colors["DEEP_ORANGE"]
        self.COLOR_RED_LAVA = colors["RED_LAVA"]
        self.COLOR_DEEP_RED = colors["DEEP_RED"]
        self.COLOR_DARK_RED = colors["DARK_RED"]
        self.COLOR_BLOOD = colors["BLOOD"]
        self.COLOR_EMBER_DARK = colors["EMBER_DARK"]
        self.COLOR_OBSIDIAN = colors["OBSIDIAN"]
        self.COLOR_DARK_ROCK = colors["DARK_ROCK"]
        self.COLOR_ROCK = colors["ROCK"]
        self.COLOR_WARM_ROCK = colors["WARM_ROCK"]
        self.COLOR_SMOKE = colors["SMOKE"]
        self.COLOR_DARK_SMOKE = colors["DARK_SMOKE"]
        self.COLOR_HEAT_GLOW = colors["HEAT_GLOW"]

        if getattr(self, "image", None) is not None:
            self._build_ship_surface()

    def _build_ship_surface(self):

        try:

            self.image = pygame.image.load(
                f"assets/images/ship_{self.ship_id}.png"
            ).convert_alpha()

            self.image = pygame.transform.smoothscale(
                self.image,
                (self.width, self.height),
            )

        except Exception:

            self.image = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA,
            )

            cx = self.width // 2

            hull_points = [
                (cx, 0),
                (self.width - 10, self.height - 10),
                (cx + 22, self.height - 22),
                (cx, self.height - 6),
                (cx - 22, self.height - 22),
                (10, self.height - 10),
            ]

            pygame.draw.polygon(
                self.image,
                self.COLOR_OBSIDIAN,
                hull_points,
            )

            inner_hull = [
                (cx, 5),
                (self.width - 16, self.height - 14),
                (cx + 18, self.height - 26),
                (cx, self.height - 10),
                (cx - 18, self.height - 26),
                (16, self.height - 14),
            ]

            pygame.draw.polygon(
                self.image,
                self.COLOR_DARK_ROCK,
                inner_hull,
            )

            crack_color = self.COLOR_ORANGE_LAVA

            cracks = [
                [
                    (cx, 8),
                    (cx - 15, 35),
                    (cx - 28, 60),
                ],
                [
                    (cx, 8),
                    (cx + 12, 30),
                    (cx + 25, 55),
                ],
                [
                    (cx - 5, 40),
                    (cx, 55),
                    (cx + 8, 70),
                ],
                [
                    (cx - 20, 50),
                    (cx - 10, 65),
                    (cx, 75),
                ],
                [
                    (cx + 18, 48),
                    (cx + 10, 62),
                    (cx + 3, 72),
                ],
            ]

            for crack in cracks:

                if len(crack) >= 2:

                    pygame.draw.lines(
                        self.image,
                        crack_color,
                        False,
                        crack,
                        2,
                    )

            core_points = [
                (cx, 12),
                (cx + 16, 45),
                (cx, 62),
                (cx - 16, 45),
            ]

            pygame.draw.polygon(
                self.image,
                self.COLOR_DEEP_RED,
                core_points,
            )

            inner_core = [
                (cx, 18),
                (cx + 9, 42),
                (cx, 55),
                (cx - 9, 42),
            ]

            pygame.draw.polygon(
                self.image,
                self.COLOR_LAVA,
                inner_core,
            )

            center_core = [
                (cx, 25),
                (cx + 4, 40),
                (cx, 48),
                (cx - 4, 40),
            ]

            pygame.draw.polygon(
                self.image,
                self.COLOR_MOLTEN_CORE,
                center_core,
            )

            pygame.draw.polygon(
                self.image,
                self.COLOR_WARM_ROCK,
                hull_points,
                2,
            )

    @staticmethod
    def lerp_color(a, b, t):

        t = max(
            0.0,
            min(1.0, t),
        )

        return (
            int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t),
        )

    def move_left(self):

        self.x -= self.speed
        self.target_roll = -10

        self.weapon_recoil = min(
            self.weapon_recoil + 0.2,
            2,
        )

    def move_right(self):

        self.x += self.speed
        self.target_roll = 10

        self.weapon_recoil = min(
            self.weapon_recoil + 0.2,
            2,
        )

    def stop_roll(self):
        self.target_roll = 0

    def keep_inside_screen(self):

        if self.x < 0:
            self.x = 0

        if self.x + self.width > self.screen_width:
            self.x = (
                self.screen_width
                - self.width
            )

    def shoot_effect(self):

        recoil = {
            "starter": 7,
            "falcon": 5,
            "viper": 6,
            "wraith": 8,
            "dragon": 11,
        }.get(
            self.ship_id,
            7,
        )

        self.weapon_recoil = recoil
        self.muzzle_flash_timer = (
            self.muzzle_flash_duration
        )

        self.shake = {
            "starter": 4,
            "falcon": 3,
            "viper": 4,
            "wraith": 5,
            "dragon": 7,
        }.get(
            self.ship_id,
            4,
        )

    def start_charge(self):

        self.is_charging = True

        self.charge_timer += 1

        self.charge_timer = min(
            self.charge_timer,
            120,
        )

    def release_charge(self):

        charge = self.charge_timer

        self.is_charging = False
        self.charge_timer = 0

        return charge

    def update_blink(self):

        if not self.is_blinking:
            return

        self.blink_timer += 1

        if self.blink_timer >= 120:

            self.is_blinking = False
            self.blink_timer = 0

    def _spawn_scaled(self, spawn_fn):

        rate = self.effect_rate
        whole = int(rate)

        for _ in range(max(0, whole)):
            spawn_fn()

        remainder = rate - whole

        if (
            remainder > 0
            and random.random() < remainder
        ):
            spawn_fn()

    def _spawn_engine_particle(self):

        prob = 0.80

        if random.random() > prob:
            return

        cx = (
            self.x
            + self.width / 2
        )

        by = (
            self.y
            + self.height
            - 7
        )

        spread = 10

        self.engine_particles.append(
            {
                "x": cx + random.uniform(
                    -spread,
                    spread,
                ),
                "y": by + random.uniform(
                    -2,
                    2,
                ),
                "vx": random.uniform(
                    -1.8,
                    1.8,
                ),
                "vy": random.uniform(
                    3.0,
                    5.0,
                ),
                "life": 1.0,
                "size": random.uniform(
                    2.5,
                    7.0,
                ),
                "type": random.choice(
                    [
                        "flame",
                        "spark",
                        "hot",
                    ]
                ),
            }
        )

    def _spawn_lava_drip(self):

        prob = 0.05

        if random.random() > prob:
            return

        side = random.choice(
            [-1, 1]
        )

        offset = (
            random.uniform(
                15,
                45,
            )
            * side
        )

        self.lava_drips.append(
            {
                "x": (
                    self.x
                    + self.width / 2
                    + offset
                ),
                "y": (
                    self.y
                    + self.height
                    * random.uniform(
                        0.4,
                        0.85,
                    )
                ),
                "vx": (
                    random.uniform(
                        -0.8,
                        0.8,
                    )
                    + side * 0.5
                ),
                "vy": random.uniform(
                    1.0,
                    3.5,
                ),
                "life": 1.0,
                "size": random.uniform(
                    1.5,
                    4.0,
                ),
                "glow": random.uniform(
                    0.5,
                    1.0,
                ),
            }
        )

    def _spawn_heat_wave(self):

        prob = 0.03

        if random.random() > prob:
            return

        cx = (
            self.x
            + self.width / 2
        )

        self.heat_waves.append(
            {
                "x": cx + random.uniform(
                    -20,
                    20,
                ),
                "y": (
                    self.y
                    + self.height
                    + random.uniform(
                        5,
                        20,
                    )
                ),
                "life": 1.0,
                "size": random.uniform(
                    15,
                    30,
                ),
                "expansion": random.uniform(
                    20,
                    45,
                ),
            }
        )

    def _spawn_ember(self):

        prob = 0.08

        if random.random() > prob:
            return

        cx = (
            self.x
            + self.width / 2
        )

        angle = random.uniform(
            -1.5,
            1.5,
        )

        speed = random.uniform(
            20,
            120,
        )

        self.ember_particles.append(
            {
                "x": cx + random.uniform(
                    -25,
                    25,
                ),
                "y": (
                    self.y
                    + self.height
                    * random.uniform(
                        0.6,
                        1.0,
                    )
                ),
                "vx": (
                    math.sin(angle)
                    * speed
                    * 0.02
                ),
                "vy": random.uniform(
                    1.5,
                    5.0,
                ),
                "life": 1.0,
                "size": random.uniform(
                    0.8,
                    2.8,
                ),
                "twinkle_phase": random.uniform(
                    0,
                    math.tau,
                ),
                "twinkle_speed": random.uniform(
                    8,
                    20,
                ),
                "brightness": random.uniform(
                    0.5,
                    1.0,
                ),
                "gravity": random.uniform(
                    0.02,
                    0.08,
                ),
            }
        )

    def _spawn_magma_spark(self):

        prob = 0.02

        if random.random() > prob:
            return

        cx = (
            self.x
            + self.width / 2
        )

        self.magma_sparks.append(
            {
                "x": cx + random.uniform(
                    -18,
                    18,
                ),
                "y": (
                    self.y
                    + self.height
                    - random.uniform(
                        0,
                        15,
                    )
                ),
                "vx": random.uniform(
                    -4,
                    4,
                ),
                "vy": random.uniform(
                    5,
                    14,
                ),
                "life": 1.0,
                "size": random.uniform(
                    1.0,
                    3.0,
                ),
            }
        )

    def _update_engine_particles(self):

        alive = []

        for p in self.engine_particles:

            p["x"] += p["vx"]
            p["y"] += p["vy"]

            p["life"] -= 0.055
            p["size"] *= 0.935

            if (
                p["life"] > 0
                and p["size"] > 0.4
            ):
                alive.append(p)

        self.engine_particles = alive

    def _update_lava_drips(self):

        alive = []

        for d in self.lava_drips:

            d["x"] += d["vx"]
            d["y"] += d["vy"]

            d["vy"] += 0.12
            d["life"] -= 0.025
            d["size"] *= 0.992

            if (
                d["life"] > 0
                and d["size"] > 0.3
            ):
                alive.append(d)

        self.lava_drips = alive

    def _update_heat_waves(self):

        alive = []

        for h in self.heat_waves:

            h["size"] += (
                h["expansion"]
                * 0.016
            )

            h["life"] -= 0.04

            if h["life"] > 0:
                alive.append(h)

        self.heat_waves = alive

    def _update_embers(self):

        alive = []

        for e in self.ember_particles:

            e["x"] += e["vx"]
            e["y"] += e["vy"]

            e["vy"] += e["gravity"]

            e["twinkle_phase"] += (
                e["twinkle_speed"]
                * 0.016
            )

            e["life"] -= 0.03

            if (
                e["life"] > 0
                and e["size"] > 0.3
            ):
                alive.append(e)

        self.ember_particles = alive

    def _update_magma_sparks(self):

        alive = []

        for s in self.magma_sparks:

            s["x"] += s["vx"]
            s["y"] += s["vy"]

            s["vy"] += 0.06
            s["vx"] *= 0.98

            s["life"] -= 0.05
            s["size"] *= 0.97

            if (
                s["life"] > 0
                and s["size"] > 0.3
            ):
                alive.append(s)

        self.magma_sparks = alive

    def update_particles(self):

        self._update_engine_particles()
        self._update_lava_drips()
        self._update_heat_waves()
        self._update_embers()
        self._update_magma_sparks()

    def update(self):

        self.animation_timer += 1

        self.engine_phase += 0.25
        self.lava_phase += 0.08
        self.heat_phase += 0.12

        self.roll += (
            self.target_roll
            - self.roll
        ) * 0.15

        if self.weapon_recoil > 0:

            self.weapon_recoil *= 0.82

            if self.weapon_recoil < 0.1:
                self.weapon_recoil = 0

        if self.muzzle_flash_timer > 0:
            self.muzzle_flash_timer -= 1

        if self.shake > 0:

            self.shake *= 0.8

            if self.shake < 0.1:
                self.shake = 0

        self._spawn_scaled(
            self._spawn_engine_particle
        )

        self._spawn_scaled(
            self._spawn_lava_drip
        )

        self._spawn_scaled(
            self._spawn_heat_wave
        )

        self._spawn_scaled(
            self._spawn_ember
        )

        self._spawn_scaled(
            self._spawn_magma_spark
        )

        self.update_particles()
        self.update_blink()

    def _draw_glow(
        self,
        screen,
        position,
        radius,
        color,
        alpha=100,
    ):

        size = radius * 4

        surface = pygame.Surface(
            (size, size),
            pygame.SRCALPHA,
        )

        center = (
            size // 2,
            size // 2,
        )

        for i in range(5, 0, -1):

            r = radius * i // 3

            a = int(
                alpha
                * (1 - i / 6)
            )

            pygame.draw.circle(
                surface,
                (*color, a),
                center,
                max(1, r),
            )

        screen.blit(
            surface,
            (
                position[0]
                - size // 2,
                position[1]
                - size // 2,
            ),
            special_flags=pygame.BLEND_RGBA_ADD,
        )

    def _flame_color(self, t):

        if t < 0.15:

            return self.lerp_color(
                self.COLOR_EMBER_DARK,
                self.COLOR_BLOOD,
                t / 0.15,
            )

        if t < 0.30:

            return self.lerp_color(
                self.COLOR_BLOOD,
                self.COLOR_DARK_RED,
                (t - 0.15) / 0.15,
            )

        if t < 0.45:

            return self.lerp_color(
                self.COLOR_DARK_RED,
                self.COLOR_DEEP_RED,
                (t - 0.30) / 0.15,
            )

        if t < 0.58:

            return self.lerp_color(
                self.COLOR_DEEP_RED,
                self.COLOR_RED_LAVA,
                (t - 0.45) / 0.13,
            )

        if t < 0.70:

            return self.lerp_color(
                self.COLOR_RED_LAVA,
                self.COLOR_DEEP_ORANGE,
                (t - 0.58) / 0.12,
            )

        if t < 0.82:

            return self.lerp_color(
                self.COLOR_DEEP_ORANGE,
                self.COLOR_ORANGE_LAVA,
                (t - 0.70) / 0.12,
            )

        if t < 0.92:

            return self.lerp_color(
                self.COLOR_ORANGE_LAVA,
                self.COLOR_LAVA,
                (t - 0.82) / 0.10,
            )

        return self.lerp_color(
            self.COLOR_LAVA,
            self.COLOR_BRIGHT_LAVA,
            (t - 0.92) / 0.08,
        )

    def _draw_heat_distortion(self, screen):

        for hw in self.heat_waves:

            ratio = max(
                0.0,
                hw["life"],
            )

            alpha = int(
                14
                * ratio
                * ratio
            )

            radius = max(
                4,
                int(hw["size"]),
            )

            size = radius * 2 + 4

            surface = pygame.Surface(
                (size, size),
                pygame.SRCALPHA,
            )

            c = size // 2

            for r_off in range(
                0,
                radius,
                2,
            ):

                r = radius - r_off

                t = (
                    r_off
                    / max(
                        1,
                        radius,
                    )
                )

                a = max(
                    0,
                    int(
                        alpha
                        * (1.0 - t)
                    ),
                )

                col = self.lerp_color(
                    self.COLOR_HEAT_GLOW,
                    self.COLOR_BLOOD,
                    t,
                )

                pygame.draw.circle(
                    surface,
                    (*col, a),
                    (c, c),
                    r,
                    1,
                )

            screen.blit(
                surface,
                (
                    int(
                        hw["x"]
                        - size / 2
                    ),
                    int(
                        hw["y"]
                        - size / 2
                    ),
                ),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

    def _draw_lava_drips(self, screen):

        for d in self.lava_drips:

            ratio = max(
                0.0,
                d["life"],
            )

            alpha = int(
                220
                * ratio
                * d["glow"]
            )

            r = max(
                1,
                int(d["size"]),
            )

            color = self._flame_color(
                ratio
                * d["glow"]
            )

            size = r * 8 + 4

            surface = pygame.Surface(
                (size, size),
                pygame.SRCALPHA,
            )

            c = size // 2

            gr = r + 4

            pygame.draw.circle(
                surface,
                (
                    *self.lerp_color(
                        color,
                        self.COLOR_BLOOD,
                        0.5,
                    ),
                    int(alpha * 0.3),
                ),
                (c, c),
                gr,
            )

            pygame.draw.circle(
                surface,
                (
                    *color,
                    min(255, alpha),
                ),
                (c, c),
                r,
            )

            if d["glow"] > 0.7:

                pygame.draw.circle(
                    surface,
                    (
                        *self.COLOR_BRIGHT_LAVA,
                        int(alpha * 0.4),
                    ),
                    (c, c),
                    max(
                        1,
                        r // 2,
                    ),
                )

            screen.blit(
                surface,
                (
                    int(
                        d["x"]
                        - size / 2
                    ),
                    int(
                        d["y"]
                        - size / 2
                    ),
                ),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

    def _draw_ember_particles(self, screen):

        for em in self.ember_particles:

            ratio = max(
                0.0,
                em["life"],
            )

            twinkle = (
                math.sin(
                    em["twinkle_phase"]
                )
                + 1.0
            ) * 0.5

            bright = (
                em["brightness"]
                * (
                    0.4
                    + twinkle * 0.6
                )
            )

            alpha = int(
                230
                * ratio
                * bright
            )

            r = max(
                1,
                int(
                    em["size"]
                    * (
                        0.3
                        + ratio * 0.7
                    )
                ),
            )

            color = self.lerp_color(
                self.COLOR_BLOOD,
                self.COLOR_LAVA,
                ratio * bright,
            )

            size = r * 8 + 4

            surface = pygame.Surface(
                (size, size),
                pygame.SRCALPHA,
            )

            c = size // 2

            pygame.draw.circle(
                surface,
                (
                    *self.lerp_color(
                        color,
                        self.COLOR_DARK_RED,
                        0.5,
                    ),
                    int(alpha * 0.25),
                ),
                (c, c),
                r + 3,
            )

            pygame.draw.circle(
                surface,
                (
                    *color,
                    min(255, alpha),
                ),
                (c, c),
                r,
            )

            screen.blit(
                surface,
                (
                    int(
                        em["x"]
                        - size / 2
                    ),
                    int(
                        em["y"]
                        - size / 2
                    ),
                ),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

    def _draw_magma_sparks(self, screen):

        for s in self.magma_sparks:

            ratio = max(
                0.0,
                s["life"],
            )

            alpha = int(
                255
                * ratio
            )

            r = max(
                1,
                int(s["size"]),
            )

            color = self._flame_color(
                0.5
                + ratio * 0.4
            )

            sx = int(s["x"])
            sy = int(s["y"])

            ex = int(
                s["x"]
                - s["vx"] * 3
            )

            ey = int(
                s["y"]
                - s["vy"] * 2
            )

            size = max(
                abs(sx - ex),
                abs(sy - ey),
            ) + 20

            surface = pygame.Surface(
                (size, size),
                pygame.SRCALPHA,
            )

            offset = size // 2

            pygame.draw.line(
                surface,
                (*color, alpha),
                (
                    offset
                    + (sx - sx),
                    offset
                    + (sy - sy),
                ),
                (
                    offset
                    + (ex - sx),
                    offset
                    + (ey - sy),
                ),
                max(1, r),
            )

            pygame.draw.circle(
                surface,
                (
                    *self.COLOR_BRIGHT_LAVA,
                    int(alpha * 0.7),
                ),
                (offset, offset),
                max(1, r),
            )

            screen.blit(
                surface,
                (
                    sx - offset,
                    sy - offset,
                ),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

    def _draw_engine_particles(self, screen):

        for p in self.engine_particles:

            size = max(
                1,
                int(p["size"]),
            )

            ratio = max(
                0.0,
                p["life"],
            )

            alpha = int(
                200 * ratio
            )

            ptype = p.get(
                "type",
                "flame",
            )

            if ptype == "spark":

                color = self._flame_color(
                    0.6
                    + ratio * 0.35
                )

            elif ptype == "hot":

                color = self._flame_color(
                    0.7
                    + ratio * 0.25
                )

            else:

                color = self._flame_color(
                    ratio * 0.85
                )

            s = size * 5 + 4

            surface = pygame.Surface(
                (s, s),
                pygame.SRCALPHA,
            )

            c = s // 2

            pygame.draw.circle(
                surface,
                (
                    *self.lerp_color(
                        color,
                        self.COLOR_BLOOD,
                        0.4,
                    ),
                    int(alpha * 0.2),
                ),
                (c, c),
                size * 2,
            )

            pygame.draw.circle(
                surface,
                (
                    *color,
                    min(255, alpha),
                ),
                (c, c),
                size,
            )

            if (
                ptype in (
                    "spark",
                    "hot",
                )
                and ratio > 0.4
            ):

                pygame.draw.circle(
                    surface,
                    (
                        *self.COLOR_BRIGHT_LAVA,
                        int(alpha * 0.5),
                    ),
                    (c, c),
                    max(
                        1,
                        size // 2,
                    ),
                )

            screen.blit(
                surface,
                (
                    int(
                        p["x"]
                        - s / 2
                    ),
                    int(
                        p["y"]
                        - s / 2
                    ),
                ),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

    def _draw_dragon_wing_effect(self, screen):

        if self.ship_id != "dragon":
            return

        cx = int(
            self.x
            + self.width / 2
        )

        cy = int(
            self.y
            + self.height * 0.48
            - self.weapon_recoil
        )

        pulse = (
            math.sin(
                self.animation_timer
                * 0.16
            )
            + 1.0
        ) * 0.5

        flutter = math.sin(
            self.animation_timer
            * 0.24
        ) * 3.0

        spread = (
            48
            + int(pulse * 7)
        )

        wing_alpha = int(
            55
            + pulse * 70
        )

        glow = pygame.Surface(
            (
                self.width + 100,
                self.height + 80,
            ),
            pygame.SRCALPHA,
        )

        gcx = glow.get_width() // 2
        gcy = glow.get_height() // 2

        for side in (-1, 1):

            tip_x = (
                gcx
                + side * spread
            )

            base_x = (
                gcx
                + side * 15
            )

            wing_y = (
                gcy
                + int(flutter)
            )

            pygame.draw.polygon(
                glow,
                (
                    *self.COLOR_DEEP_ORANGE,
                    wing_alpha // 3,
                ),
                [
                    (
                        base_x,
                        gcy - 8,
                    ),
                    (
                        tip_x,
                        wing_y - 12,
                    ),
                    (
                        tip_x + side * 5,
                        wing_y + 4,
                    ),
                    (
                        base_x + side * 10,
                        gcy + 12,
                    ),
                ],
            )

            pygame.draw.line(
                glow,
                (
                    *self.COLOR_ORANGE_LAVA,
                    wing_alpha,
                ),
                (
                    base_x,
                    gcy - 5,
                ),
                (
                    tip_x,
                    wing_y,
                ),
                3,
            )

            pygame.draw.line(
                glow,
                (
                    *self.COLOR_BRIGHT_LAVA,
                    int(
                        wing_alpha
                        * 0.7
                    ),
                ),
                (
                    base_x + side * 5,
                    gcy,
                ),
                (
                    tip_x - side * 4,
                    wing_y + 2,
                ),
                1,
            )

        screen.blit(
            glow,
            (
                cx
                - glow.get_width() // 2,
                cy
                - glow.get_height() // 2,
            ),
            special_flags=pygame.BLEND_RGBA_ADD,
        )

        self._draw_glow(
            screen,
            (cx, cy),
            int(
                25
                + pulse * 8
            ),
            self.COLOR_ORANGE_LAVA,
            int(
                25
                + pulse * 20
            ),
        )

    def _draw_engine_flame(self, screen):

        flame_power = (
            min(
                1.6,
                0.85
                + 0.15
                * self.effect_rate,
            )
            * self.fx_intensity
        )

        flame_height = int(
            (
                16
                + math.sin(
                    self.engine_phase
                ) * 6
                + random.uniform(
                    -2,
                    2,
                )
            )
            * flame_power
        )

        cx = int(
            self.x
            + self.width / 2
        )

        fy = int(
            self.y
            + self.height
            - 7
            + self.weapon_recoil
        )

        pulse = math.sin(
            self.animation_timer
            * 0.3
        )

        style = self.fx[
            "engine_shape"
        ]

        if style == "jet":

            outer_w = (
                16
                + int(
                    abs(pulse) * 5
                )
            )

            points = [
                (
                    cx - outer_w,
                    fy,
                ),
                (
                    cx + outer_w,
                    fy,
                ),
                (
                    cx + int(
                        pulse * 4
                    ),
                    fy
                    + flame_height
                    + 10,
                ),
            ]

            pygame.draw.polygon(
                screen,
                self.COLOR_DEEP_RED,
                points,
            )

            pygame.draw.polygon(
                screen,
                self.COLOR_LAVA,
                [
                    (
                        cx - 9,
                        fy,
                    ),
                    (
                        cx + 9,
                        fy,
                    ),
                    (
                        cx,
                        fy
                        + flame_height,
                    ),
                ],
            )

            pygame.draw.line(
                screen,
                self.COLOR_BRIGHT_LAVA,
                (
                    cx,
                    fy + 2,
                ),
                (
                    cx,
                    fy
                    + flame_height
                    + 5,
                ),
                3,
            )

            return

        if style == "split":

            gap = 7

            for side in (-1, 1):

                scx = (
                    cx
                    + side * gap
                )

                width = 11

                pygame.draw.polygon(
                    screen,
                    self.COLOR_DEEP_RED,
                    [
                        (
                            scx - width,
                            fy,
                        ),
                        (
                            scx + width,
                            fy,
                        ),
                        (
                            scx + side * 2,
                            fy
                            + flame_height
                            + 8,
                        ),
                    ],
                )

                pygame.draw.polygon(
                    screen,
                    self.COLOR_LAVA,
                    [
                        (
                            scx - 6,
                            fy,
                        ),
                        (
                            scx + 6,
                            fy,
                        ),
                        (
                            scx,
                            fy
                            + int(
                                flame_height
                                * 0.7
                            ),
                        ),
                    ],
                )

            return

        if style == "void":

            length = (
                flame_height
                + 15
            )

            self._draw_glow(
                screen,
                (
                    cx,
                    fy
                    + length // 2,
                ),
                22,
                self.COLOR_DEEP_ORANGE,
                70,
            )

            pygame.draw.polygon(
                screen,
                self.COLOR_DEEP_RED,
                [
                    (
                        cx - 15,
                        fy,
                    ),
                    (
                        cx + 15,
                        fy,
                    ),
                    (
                        cx,
                        fy + length,
                    ),
                ],
            )

            pygame.draw.polygon(
                screen,
                self.COLOR_LAVA,
                [
                    (
                        cx - 7,
                        fy,
                    ),
                    (
                        cx + 7,
                        fy,
                    ),
                    (
                        cx,
                        fy
                        + int(
                            length * 0.72
                        ),
                    ),
                ],
            )

            pygame.draw.circle(
                screen,
                self.COLOR_MOLTEN_CORE,
                (
                    cx,
                    fy + 4,
                ),
                3,
            )

            return

        if style == "dragon":

            length = (
                flame_height
                + 25
            )

            self._draw_glow(
                screen,
                (
                    cx,
                    fy
                    + length // 2,
                ),
                32,
                self.COLOR_DEEP_ORANGE,
                95,
            )

            outer = [
                (
                    cx - 22,
                    fy,
                ),
                (
                    cx - 8,
                    fy
                    + length * 0.28,
                ),
                (
                    cx - 2,
                    fy + length,
                ),
                (
                    cx,
                    fy
                    + length * 0.55,
                ),
                (
                    cx + 2,
                    fy + length,
                ),
                (
                    cx + 8,
                    fy
                    + length * 0.28,
                ),
                (
                    cx + 22,
                    fy,
                ),
            ]

            pygame.draw.polygon(
                screen,
                self.COLOR_DEEP_RED,
                outer,
            )

            pygame.draw.polygon(
                screen,
                self.COLOR_ORANGE_LAVA,
                [
                    (
                        cx - 12,
                        fy,
                    ),
                    (
                        cx - 3,
                        fy
                        + length * 0.35,
                    ),
                    (
                        cx,
                        fy
                        + length * 0.85,
                    ),
                    (
                        cx + 3,
                        fy
                        + length * 0.35,
                    ),
                    (
                        cx + 12,
                        fy,
                    ),
                ],
            )

            pygame.draw.polygon(
                screen,
                self.COLOR_MOLTEN_CORE,
                [
                    (
                        cx - 4,
                        fy,
                    ),
                    (
                        cx,
                        fy
                        + length * 0.68,
                    ),
                    (
                        cx + 4,
                        fy,
                    ),
                ],
            )

            return

        outer_w = (
            20
            + int(pulse)
        )

        pygame.draw.polygon(
            screen,
            self.COLOR_DARK_RED,
            [
                (
                    cx - outer_w,
                    fy,
                ),
                (
                    cx + outer_w,
                    fy,
                ),
                (
                    cx,
                    fy
                    + flame_height
                    + 15,
                ),
            ],
        )

        mid_w = (
            14
            + int(
                pulse * 0.5
            )
        )

        pygame.draw.polygon(
            screen,
            self.COLOR_RED_LAVA,
            [
                (
                    cx - mid_w,
                    fy,
                ),
                (
                    cx + mid_w,
                    fy,
                ),
                (
                    cx,
                    fy
                    + flame_height
                    + 8,
                ),
            ],
        )

        pygame.draw.polygon(
            screen,
            self.COLOR_ORANGE_LAVA,
            [
                (
                    cx - 9,
                    fy,
                ),
                (
                    cx + 9,
                    fy,
                ),
                (
                    cx,
                    fy
                    + flame_height,
                ),
            ],
        )

        pygame.draw.polygon(
            screen,
            self.COLOR_LAVA,
            [
                (
                    cx - 4,
                    fy,
                ),
                (
                    cx + 4,
                    fy,
                ),
                (
                    cx,
                    fy
                    + int(
                        flame_height
                        * 0.65
                    ),
                ),
            ],
        )

        pygame.draw.polygon(
            screen,
            self.COLOR_BRIGHT_LAVA,
            [
                (
                    cx - 2,
                    fy,
                ),
                (
                    cx + 2,
                    fy,
                ),
                (
                    cx,
                    fy
                    + int(
                        flame_height
                        * 0.40
                    ),
                ),
            ],
        )

    def _draw_charge_effect(self, screen):

        if not self.is_charging:
            return

        center_x = int(
            self.x
            + self.width / 2
        )

        center_y = int(
            self.y
            + self.height / 2
        )

        ratio = (
            self.charge_timer
            / 120
        )

        pulse = math.sin(
            self.animation_timer
            * 0.3
        )

        radius = int(
            (
                38
                + ratio * 35
                + pulse * 4
            )
            * self.fx_intensity
        )

        style = self.fx[
            "charge_shape"
        ]

        if style == "orbit":

            self._draw_glow(
                screen,
                (
                    center_x,
                    center_y,
                ),
                radius,
                self.COLOR_LAVA,
                75,
            )

            surf = pygame.Surface(
                (
                    radius * 4,
                    radius * 4,
                ),
                pygame.SRCALPHA,
            )

            rc = radius * 2

            pygame.draw.ellipse(
                surf,
                (
                    *self.COLOR_BRIGHT_LAVA,
                    150,
                ),
                (
                    rc - radius,
                    rc - radius // 2,
                    radius * 2,
                    radius,
                ),
                2,
            )

            pygame.draw.ellipse(
                surf,
                (
                    *self.COLOR_LAVA,
                    110,
                ),
                (
                    rc - radius // 2,
                    rc - radius,
                    radius,
                    radius * 2,
                ),
                2,
            )

            screen.blit(
                surf,
                (
                    center_x - rc,
                    center_y - rc,
                ),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

            return

        if style == "toxic":

            self._draw_glow(
                screen,
                (
                    center_x,
                    center_y,
                ),
                radius,
                self.COLOR_LAVA,
                90,
            )

            for i in range(5):

                a = (
                    self.animation_timer
                    * 0.05
                    + i
                    * math.tau
                    / 5
                )

                px = (
                    center_x
                    + math.cos(a)
                    * radius
                    * 0.7
                )

                py = (
                    center_y
                    + math.sin(a)
                    * radius
                    * 0.7
                )

                pygame.draw.circle(
                    screen,
                    self.COLOR_BRIGHT_LAVA,
                    (
                        int(px),
                        int(py),
                    ),
                    3,
                )

            return

        if style == "void":

            self._draw_glow(
                screen,
                (
                    center_x,
                    center_y,
                ),
                radius + 8,
                self.COLOR_DEEP_ORANGE,
                100,
            )

            pygame.draw.circle(
                screen,
                self.COLOR_DEEP_RED,
                (
                    center_x,
                    center_y,
                ),
                radius,
                2,
            )

            pygame.draw.circle(
                screen,
                self.COLOR_LAVA,
                (
                    center_x,
                    center_y,
                ),
                max(
                    4,
                    int(
                        radius * ratio
                    ),
                ),
                2,
            )

            return

        if style == "dragon":

            radius += 10

            self._draw_glow(
                screen,
                (
                    center_x,
                    center_y,
                ),
                radius + 10,
                self.COLOR_ORANGE_LAVA,
                120,
            )

            pygame.draw.circle(
                screen,
                self.COLOR_RED_LAVA,
                (
                    center_x,
                    center_y,
                ),
                radius,
                3,
            )

            for side in (-1, 1):

                pygame.draw.polygon(
                    screen,
                    self.COLOR_LAVA,
                    [
                        (
                            center_x,
                            center_y - radius,
                        ),
                        (
                            center_x
                            + side * radius,
                            center_y,
                        ),
                        (
                            center_x,
                            center_y
                            + radius // 2,
                        ),
                    ],
                )

            pygame.draw.circle(
                screen,
                self.COLOR_MOLTEN_CORE,
                (
                    center_x,
                    center_y,
                ),
                max(
                    4,
                    int(
                        radius * 0.22
                    ),
                ),
            )

            return

        self._draw_glow(
            screen,
            (
                center_x,
                center_y,
            ),
            radius,
            self.COLOR_DEEP_ORANGE,
            70,
        )

        ring_surface = pygame.Surface(
            (
                radius * 4,
                radius * 4,
            ),
            pygame.SRCALPHA,
        )

        rc = radius * 2

        pygame.draw.circle(
            ring_surface,
            (
                *self.COLOR_RED_LAVA,
                120,
            ),
            (
                rc,
                rc,
            ),
            radius,
            2,
        )

        if ratio > 0.3:

            pygame.draw.circle(
                ring_surface,
                (
                    *self.COLOR_ORANGE_LAVA,
                    100,
                ),
                (
                    rc,
                    rc,
                ),
                max(
                    5,
                    int(
                        radius
                        * ratio
                    ),
                ),
                2,
            )

        if ratio > 0.6:

            pygame.draw.circle(
                ring_surface,
                (
                    *self.COLOR_LAVA,
                    80,
                ),
                (
                    rc,
                    rc,
                ),
                max(
                    3,
                    int(
                        radius
                        * ratio
                        * 0.6
                    ),
                ),
                2,
            )

        screen.blit(
            ring_surface,
            (
                center_x - rc,
                center_y - rc,
            ),
            special_flags=pygame.BLEND_RGBA_ADD,
        )

    def _draw_muzzle_flash(self, screen):

        if self.muzzle_flash_timer <= 0:
            return

        cx = int(
            self.x
            + self.width / 2
        )

        cy = int(
            self.y
            - self.weapon_recoil
            - 4
        )

        progress = (
            self.muzzle_flash_timer
            / self.muzzle_flash_duration
        )

        size = int(
            (
                18
                + progress * 25
            )
            * self.fx_intensity
        )

        style = self.fx[
            "muzzle_shape"
        ]

        if style == "cross":

            self._draw_glow(
                screen,
                (
                    cx,
                    cy,
                ),
                size,
                self.COLOR_LAVA,
                120,
            )

            pygame.draw.line(
                screen,
                self.COLOR_BRIGHT_LAVA,
                (
                    cx - size,
                    cy,
                ),
                (
                    cx + size,
                    cy,
                ),
                max(
                    2,
                    size // 5,
                ),
            )

            pygame.draw.line(
                screen,
                self.COLOR_BRIGHT_LAVA,
                (
                    cx,
                    cy - size,
                ),
                (
                    cx,
                    cy + size,
                ),
                max(
                    2,
                    size // 5,
                ),
            )

            return

        if style == "needle":

            self._draw_glow(
                screen,
                (
                    cx,
                    cy,
                ),
                size,
                self.COLOR_LAVA,
                100,
            )

            pygame.draw.polygon(
                screen,
                self.COLOR_BRIGHT_LAVA,
                [
                    (
                        cx,
                        cy - size * 2,
                    ),
                    (
                        cx + size // 3,
                        cy,
                    ),
                    (
                        cx,
                        cy + size // 2,
                    ),
                    (
                        cx - size // 3,
                        cy,
                    ),
                ],
            )

            return

        if style == "void":

            self._draw_glow(
                screen,
                (
                    cx,
                    cy,
                ),
                size + 8,
                self.COLOR_DEEP_ORANGE,
                120,
            )

            pygame.draw.circle(
                screen,
                self.COLOR_DEEP_RED,
                (
                    cx,
                    cy,
                ),
                size,
                3,
            )

            pygame.draw.circle(
                screen,
                self.COLOR_MOLTEN_CORE,
                (
                    cx,
                    cy,
                ),
                max(
                    2,
                    size // 4,
                ),
            )

            return

        if style == "dragon":

            size += 8

            self._draw_glow(
                screen,
                (
                    cx,
                    cy,
                ),
                size + 10,
                self.COLOR_ORANGE_LAVA,
                145,
            )

            pygame.draw.polygon(
                screen,
                self.COLOR_RED_LAVA,
                [
                    (
                        cx,
                        cy - size * 2,
                    ),
                    (
                        cx + size,
                        cy,
                    ),
                    (
                        cx,
                        cy + size,
                    ),
                    (
                        cx - size,
                        cy,
                    ),
                ],
            )

            pygame.draw.polygon(
                screen,
                self.COLOR_BRIGHT_LAVA,
                [
                    (
                        cx,
                        cy - size,
                    ),
                    (
                        cx + size // 3,
                        cy,
                    ),
                    (
                        cx,
                        cy + size // 2,
                    ),
                    (
                        cx - size // 3,
                        cy,
                    ),
                ],
            )

            pygame.draw.circle(
                screen,
                self.COLOR_MOLTEN_CORE,
                (
                    cx,
                    cy,
                ),
                max(
                    3,
                    size // 4,
                ),
            )

            return

        self._draw_glow(
            screen,
            (
                cx,
                cy,
            ),
            size,
            self.COLOR_DEEP_ORANGE,
            110,
        )

        flash_surface = pygame.Surface(
            (
                size * 4,
                size * 4,
            ),
            pygame.SRCALPHA,
        )

        fc = size * 2

        pygame.draw.polygon(
            flash_surface,
            (
                *self.COLOR_ORANGE_LAVA,
                int(
                    200
                    * progress
                ),
            ),
            [
                (
                    fc,
                    fc - size,
                ),
                (
                    fc + size // 3,
                    fc,
                ),
                (
                    fc,
                    fc + size,
                ),
                (
                    fc - size // 3,
                    fc,
                ),
            ],
        )

        pygame.draw.polygon(
            flash_surface,
            (
                *self.COLOR_LAVA,
                int(
                    220
                    * progress
                ),
            ),
            [
                (
                    fc,
                    fc - size // 2,
                ),
                (
                    fc + size // 5,
                    fc,
                ),
                (
                    fc,
                    fc + size // 2,
                ),
                (
                    fc - size // 5,
                    fc,
                ),
            ],
        )

        pygame.draw.circle(
            flash_surface,
            (
                *self.COLOR_BRIGHT_LAVA,
                int(
                    240
                    * progress
                ),
            ),
            (
                fc,
                fc,
            ),
            max(
                3,
                size // 4,
            ),
        )

        screen.blit(
            flash_surface,
            (
                cx - fc,
                cy - fc,
            ),
            special_flags=pygame.BLEND_RGBA_ADD,
        )

    def _draw_hull_glow(self, screen):

        cx = int(
            self.x
            + self.width / 2
        )

        cy = int(
            self.y
            + self.height / 2
        )

        lava_pulse = (
            math.sin(
                self.lava_phase
            )
            + 1.0
        ) * 0.5

        intensity = (
            0.6
            + lava_pulse * 0.4
        )

        intensity *= min(
            1.6,
            0.85
            + 0.15
            * self.effect_rate,
        )

        self._draw_glow(
            screen,
            (
                cx,
                cy + 10,
            ),
            int(
                40
                * intensity
            ),
            self.COLOR_DARK_RED,
            int(
                25
                * intensity
            ),
        )

        self._draw_glow(
            screen,
            (
                cx,
                cy - 5,
            ),
            int(
                30
                * intensity
            ),
            self.COLOR_DEEP_ORANGE,
            int(
                20
                * intensity
            ),
        )

        crack_alpha = int(
            60
            * intensity
        )

        surface = pygame.Surface(
            (
                self.width + 20,
                self.height + 20,
            ),
            pygame.SRCALPHA,
        )

        ox = 10
        oy = 10

        crack_pairs = [
            [
                (
                    cx
                    - self.x
                    - 15
                    + ox,
                    35 + oy,
                ),
                (
                    cx
                    - self.x
                    - 28
                    + ox,
                    60 + oy,
                ),
            ],
            [
                (
                    cx
                    - self.x
                    + 12
                    + ox,
                    30 + oy,
                ),
                (
                    cx
                    - self.x
                    + 25
                    + ox,
                    55 + oy,
                ),
            ],
            [
                (
                    cx
                    - self.x
                    - 5
                    + ox,
                    40 + oy,
                ),
                (
                    cx
                    - self.x
                    + 8
                    + ox,
                    70 + oy,
                ),
            ],
        ]

        for crack in crack_pairs:

            glow_col = self.lerp_color(
                self.COLOR_RED_LAVA,
                self.COLOR_ORANGE_LAVA,
                lava_pulse,
            )

            pygame.draw.line(
                surface,
                (
                    *glow_col,
                    crack_alpha,
                ),
                crack[0],
                crack[1],
                3,
            )

            pygame.draw.line(
                surface,
                (
                    *self.COLOR_LAVA,
                    int(
                        crack_alpha
                        * 0.6
                    ),
                ),
                crack[0],
                crack[1],
                1,
            )

        screen.blit(
            surface,
            (
                int(self.x - 10),
                int(self.y - 10),
            ),
            special_flags=pygame.BLEND_RGBA_ADD,
        )

    def _draw_lava_vein_overlay(self, screen):

        cx = int(
            self.x
            + self.width / 2
        )

        ship_y = int(
            self.y
            - self.weapon_recoil
        )

        pulse = (
            math.sin(
                self.lava_phase * 1.5
            )
            + 1.0
        ) * 0.5

        alpha = int(
            40
            + pulse * 50
        )

        surface = pygame.Surface(
            (
                self.width + 10,
                self.height + 10,
            ),
            pygame.SRCALPHA,
        )

        ox = (
            5
            + (
                cx
                - int(self.x)
                - self.width // 2
            )
        )

        oy = 5

        t = self.lava_phase

        veins = [
            [
                (
                    self.width // 2
                    + ox,
                    15 + oy,
                ),
                (
                    self.width // 2
                    - 12
                    + int(
                        math.sin(t)
                        * 3
                    )
                    + ox,
                    40 + oy,
                ),
                (
                    self.width // 2
                    - 22
                    + int(
                        math.sin(t + 1)
                        * 2
                    )
                    + ox,
                    65 + oy,
                ),
            ],
            [
                (
                    self.width // 2
                    + ox,
                    15 + oy,
                ),
                (
                    self.width // 2
                    + 10
                    + int(
                        math.sin(
                            t + 0.5
                        )
                        * 3
                    )
                    + ox,
                    38 + oy,
                ),
                (
                    self.width // 2
                    + 20
                    + int(
                        math.sin(
                            t + 1.5
                        )
                        * 2
                    )
                    + ox,
                    60 + oy,
                ),
            ],
            [
                (
                    self.width // 2
                    - 8
                    + ox,
                    30 + oy,
                ),
                (
                    self.width // 2
                    + int(
                        math.sin(
                            t + 2
                        )
                        * 4
                    )
                    + ox,
                    52 + oy,
                ),
                (
                    self.width // 2
                    + 6
                    + ox,
                    72 + oy,
                ),
            ],
        ]

        for vein in veins:

            col = self.lerp_color(
                self.COLOR_DEEP_ORANGE,
                self.COLOR_LAVA,
                pulse,
            )

            pygame.draw.lines(
                surface,
                (
                    *col,
                    alpha,
                ),
                False,
                vein,
                2,
            )

            inner_col = self.lerp_color(
                self.COLOR_LAVA,
                self.COLOR_BRIGHT_LAVA,
                pulse,
            )

            pygame.draw.lines(
                surface,
                (
                    *inner_col,
                    int(alpha * 0.5),
                ),
                False,
                vein,
                1,
            )

        screen.blit(
            surface,
            (
                int(self.x - 5),
                int(ship_y - 5),
            ),
            special_flags=pygame.BLEND_RGBA_ADD,
        )

    def draw(self, screen):

        self.animation_timer += 1

        if self.is_blinking:

            if (
                self.blink_timer // 5
            ) % 2 == 0:
                return

        ship_y = int(
            self.y
            - self.weapon_recoil
        )

        rotated = pygame.transform.rotozoom(
            self.image,
            -self.roll,
            1.0,
        )

        rect = rotated.get_rect(
            center=(
                int(
                    self.x
                    + self.width / 2
                ),
                ship_y
                + self.height // 2,
            )
        )

        screen.blit(
            rotated,
            rect,
        )

    def get_rect(self):

        return pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height,
        )


if __name__ == "__main__":

    pygame.init()

    WIDTH = 800
    HEIGHT = 900

    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT)
    )

    pygame.display.set_caption(
        "Ship FX Demo — press 1-5 to switch ships"
    )

    clock = pygame.time.Clock()

    player = Player(
        WIDTH,
        HEIGHT,
        ship_id="starter",
    )

    font = pygame.font.SysFont(
        "consolas",
        16,
    )

    ship_keys = {
        pygame.K_1: "starter",
        pygame.K_2: "falcon",
        pygame.K_3: "viper",
        pygame.K_4: "wraith",
        pygame.K_5: "dragon",
    }

    running = True

    while running:

        dt = (
            clock.tick(60)
            / 1000.0
        )

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    running = False

                elif event.key == pygame.K_SPACE:

                    player.shoot_effect()

                elif event.key == pygame.K_e:

                    player.is_charging = True

                elif event.key in ship_keys:

                    player.set_ship(
                        ship_keys[event.key]
                    )

            elif event.type == pygame.KEYUP:

                if event.key == pygame.K_e:

                    player.release_charge()

        keys = pygame.key.get_pressed()

        moved = False

        if (
            keys[pygame.K_LEFT]
            or keys[pygame.K_a]
        ):

            player.move_left()
            moved = True

        if (
            keys[pygame.K_RIGHT]
            or keys[pygame.K_d]
        ):

            player.move_right()
            moved = True

        if not moved:

            player.stop_roll()

        if keys[pygame.K_e]:

            player.start_charge()

        player.keep_inside_screen()
        player.update()

        screen.fill(
            (5, 3, 6)
        )

        random.seed(42)

        for _ in range(45):

            sx = random.randint(
                0,
                WIDTH,
            )

            sy = random.randint(
                0,
                HEIGHT,
            )

            br = random.randint(
                15,
                55,
            )

            screen.set_at(
                (
                    sx,
                    sy,
                ),
                (
                    br,
                    br - 3,
                    br - 8,
                ),
            )

        random.seed()

        player.draw(screen)

        lines = [
            (
                f"FPS: "
                f"{clock.get_fps():.0f}"
            ),
            (
                f"Ship: "
                f"{player.ship_id.upper()} "
                f"({player.rank}) "
                f"rate x"
                f"{player.effect_rate:.2f}"
            ),
            (
                "A/D or Arrows: move | "
                "SPACE: shoot | "
                "E: charge | "
                "1-5: switch ship"
            ),
        ]

        for i, line in enumerate(lines):

            txt = font.render(
                line,
                True,
                (160, 120, 90),
            )

            screen.blit(
                txt,
                (
                    10,
                    10 + i * 20,
                ),
            )

        pygame.display.flip()

    pygame.quit()