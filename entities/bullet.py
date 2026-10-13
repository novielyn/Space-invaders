import pygame
import math
import random


class Bullet:
    WIDTH = 26
    HEIGHT = 72

    DEFAULT_SPEED = 900
    DEFAULT_DAMAGE = 1

    MAX_TRAIL = 32
    MAX_PARTICLES = 65
    MAX_SMOKE = 26
    MAX_EMBERS = 40
    MAX_HEAT_WAVES = 8

    SHIP_STYLES = {
        "starter": {
            "width": 26,
            "height": 72,
            "speed": 900,
            "damage": 1,
            "theme": "fire",
        },
        "falcon": {
            "width": 18,
            "height": 78,
            "speed": 1020,
            "damage": 1,
            "theme": "laser",
        },
        "viper": {
            "width": 22,
            "height": 70,
            "speed": 950,
            "damage": 1,
            "theme": "toxic",
        },
        "wraith": {
            "width": 24,
            "height": 76,
            "speed": 930,
            "damage": 2,
            "theme": "void",
        },
        "dragon": {
            "width": 30,
            "height": 86,
            "speed": 980,
            "damage": 2,
            "theme": "dragon",
        },
    }

    def __init__(
        self,
        x,
        y,
        damage=DEFAULT_DAMAGE,
        speed=DEFAULT_SPEED,
        ship_id="starter",
    ):
        self.ship_id = str(ship_id or "starter").lower()

        aliases = {
            "default": "starter",
            "basic": "starter",
            "starter_ship": "starter",
            "blue": "falcon",
            "green": "viper",
            "purple": "wraith",
            "dragon_ship": "dragon",
        }

        self.ship_id = aliases.get(
            self.ship_id,
            self.ship_id
        )

        if self.ship_id not in self.SHIP_STYLES:
            self.ship_id = "starter"

        style = self.SHIP_STYLES[self.ship_id]

        self.theme = style["theme"]

        self.width = style["width"]
        self.height = style["height"]

        self.x = float(
            x - self.width / 2
        )

        self.y = float(
            y - self.height
        )

        self.previous_x = self.x
        self.previous_y = self.y

        self.speed = float(
            speed if speed != self.DEFAULT_SPEED
            else style["speed"]
        )

        self.damage = (
            damage
            if damage != self.DEFAULT_DAMAGE
            else style["damage"]
        )

        self.is_active = True
        self.has_hit = False

        self.time = random.uniform(
            0.0,
            math.tau
        )

        self.pulse = 0.0
        self.pulse_fast = 0.0
        self.rotation = random.uniform(
            -0.08,
            0.08
        )

        self.flicker_intensity = 1.0
        self.age = 0.0

        self.trail = []
        self.particles = []
        self.smoke = []
        self.embers = []
        self.heat_waves = []
        self.flash_particles = []

        self.spawn_timer = 0.0
        self.smoke_timer = 0.0
        self.ember_timer = 0.0
        self.heat_timer = 0.0
        self.flash_timer = 0.0

    def update(self, dt=1 / 60):
        if not self.is_active:
            return

        dt = min(dt, 0.05)

        self.age += dt

        self.previous_x = self.x
        self.previous_y = self.y

        self.time += dt * 14.0

        self.pulse = (
            math.sin(self.time) + 1.0
        ) * 0.5

        self.pulse_fast = (
            math.sin(self.time * 2.7) + 1.0
        ) * 0.5

        self.flicker_intensity = (
            0.82
            + 0.18 * math.sin(self.time * 3.1)
            + 0.10 * math.sin(self.time * 7.9)
            + 0.06 * math.sin(self.time * 15.3)
        )

        center_x = (
            self.x
            + self.width / 2
        )

        tail_y = (
            self.y
            + self.height * 0.88
        )

        self._spawn_trail(
            center_x,
            tail_y
        )

        self.y -= self.speed * dt

        self.spawn_timer += dt
        self.smoke_timer += dt
        self.ember_timer += dt
        self.heat_timer += dt
        self.flash_timer += dt

        if self.theme == "fire":
            while self.spawn_timer >= 0.009:
                self.spawn_timer -= 0.009
                self._spawn_particle()

            while self.smoke_timer >= 0.040:
                self.smoke_timer -= 0.040
                if random.random() < 0.75:
                    self._spawn_smoke()

            while self.ember_timer >= 0.030:
                self.ember_timer -= 0.030
                if random.random() < 0.60:
                    self._spawn_ember()

            while self.heat_timer >= 0.10:
                self.heat_timer -= 0.10
                if random.random() < 0.55:
                    self._spawn_heat_wave()

        elif self.theme == "dragon":
            while self.spawn_timer >= 0.010:
                self.spawn_timer -= 0.010
                self._spawn_particle()

            while self.smoke_timer >= 0.055:
                self.smoke_timer -= 0.055
                if random.random() < 0.45:
                    self._spawn_smoke()

            while self.ember_timer >= 0.025:
                self.ember_timer -= 0.025
                if random.random() < 0.75:
                    self._spawn_ember()

            while self.heat_timer >= 0.08:
                self.heat_timer -= 0.08
                if random.random() < 0.70:
                    self._spawn_heat_wave()

        else:
            while self.spawn_timer >= 0.014:
                self.spawn_timer -= 0.014
                self._spawn_particle()

            while self.ember_timer >= 0.035:
                self.ember_timer -= 0.035
                if random.random() < 0.55:
                    self._spawn_ember()

        while self.flash_timer >= 0.07:
            self.flash_timer -= 0.07

            if random.random() < 0.30:
                self._spawn_flash()

        self._update_trail(dt)
        self._update_particles(dt)
        self._update_smoke(dt)
        self._update_embers(dt)
        self._update_heat_waves(dt)
        self._update_flash_particles(dt)

        if self.y + self.height < -160:
            self.destroy()

    def _spawn_trail(self, center_x, tail_y):
        if self.theme == "laser":
            count = 2
            spread = 1.5
            life = (0.20, 0.34)
            size = (3.0, 7.0)

        elif self.theme == "toxic":
            count = 2
            spread = 3.0
            life = (0.24, 0.40)
            size = (4.0, 9.0)

        elif self.theme == "void":
            count = 2
            spread = 3.5
            life = (0.25, 0.45)
            size = (5.0, 10.0)

        elif self.theme == "dragon":
            count = 3
            spread = 5.0
            life = (0.30, 0.50)
            size = (5.0, 13.0)

        else:
            count = 2
            spread = 3.0
            life = (0.28, 0.45)
            size = (5.5, 12.0)

        for _ in range(count):
            self.trail.append({
                "x": center_x + random.uniform(
                    -spread,
                    spread
                ),
                "y": tail_y + random.uniform(
                    -2,
                    3
                ),
                "life": random.uniform(
                    life[0],
                    life[1]
                ),
                "max_life": life[1],
                "size": random.uniform(
                    size[0],
                    size[1]
                ),
                "layer": random.randint(
                    0,
                    1
                ),
                "wobble_phase": random.uniform(
                    0,
                    math.tau
                ),
                "wobble_speed": random.uniform(
                    7,
                    14
                ),
                "wobble_amp": random.uniform(
                    0.6,
                    2.5
                ),
            })

        if len(self.trail) > self.MAX_TRAIL:
            self.trail = self.trail[
                -self.MAX_TRAIL:
            ]

    def get_rect(self):
        return pygame.Rect(
            int(
                self.x
                + self.width * 0.22
            ),
            int(
                self.y
                + self.height * 0.06
            ),
            int(
                self.width * 0.56
            ),
            int(
                self.height * 0.80
            ),
        )

    def get_previous_rect(self):
        return pygame.Rect(
            int(
                self.previous_x
                + self.width * 0.22
            ),
            int(
                self.previous_y
                + self.height * 0.06
            ),
            int(
                self.width * 0.56
            ),
            int(
                self.height * 0.80
            ),
        )

    def get_swept_rect(self):
        current = self.get_rect()
        previous = self.get_previous_rect()

        left = min(
            current.left,
            previous.left
        )

        top = min(
            current.top,
            previous.top
        )

        right = max(
            current.right,
            previous.right
        )

        bottom = max(
            current.bottom,
            previous.bottom
        )

        return pygame.Rect(
            left,
            top,
            right - left,
            bottom - top,
        )

    def collides_with(self, target):
        if (
            not self.is_active
            or self.has_hit
        ):
            return False

        swept = self.get_swept_rect()

        if hasattr(target, "get_rect"):
            target_rect = target.get_rect()

        elif hasattr(target, "rect"):
            target_rect = target.rect

        else:
            return False

        return swept.colliderect(
            target_rect
        )

    def impact(self):
        if (
            not self.is_active
            or self.has_hit
        ):
            return

        self.has_hit = True
        self.is_active = False

    def destroy(self):
        self.is_active = False

        self.trail.clear()
        self.particles.clear()
        self.smoke.clear()
        self.embers.clear()
        self.heat_waves.clear()
        self.flash_particles.clear()

    def get_center(self):
        return (
            self.x + self.width / 2,
            self.y + self.height / 2
        )

    def _spawn_particle(self):
        if len(self.particles) >= self.MAX_PARTICLES:
            return

        cx = (
            self.x
            + self.width / 2
        )

        ty = (
            self.y
            + self.height * 0.80
        )

        if self.theme == "laser":
            self.particles.append({
                "x": cx + random.uniform(-3, 3),
                "y": ty + random.uniform(-4, 4),
                "vx": random.uniform(-35, 35),
                "vy": random.uniform(50, 180),
                "life": random.uniform(0.10, 0.25),
                "max_life": 0.25,
                "size": random.uniform(1.0, 3.0),
                "phase": random.uniform(0, math.tau),
                "type": "laser",
                "gravity": 0,
                "drag": 0.98,
            })

        elif self.theme == "toxic":
            self.particles.append({
                "x": cx + random.uniform(-5, 5),
                "y": ty + random.uniform(-4, 6),
                "vx": random.uniform(-70, 70),
                "vy": random.uniform(55, 180),
                "life": random.uniform(0.16, 0.35),
                "max_life": 0.35,
                "size": random.uniform(1.5, 4.5),
                "phase": random.uniform(0, math.tau),
                "type": "toxic",
                "gravity": random.uniform(10, 40),
                "drag": 0.97,
            })

        elif self.theme == "void":
            self.particles.append({
                "x": cx + random.uniform(-5, 5),
                "y": ty + random.uniform(-5, 5),
                "vx": random.uniform(-55, 55),
                "vy": random.uniform(45, 150),
                "life": random.uniform(0.18, 0.40),
                "max_life": 0.40,
                "size": random.uniform(1.5, 4.5),
                "phase": random.uniform(0, math.tau),
                "type": "void",
                "gravity": -15,
                "drag": 0.98,
            })

        elif self.theme == "dragon":
            self.particles.append({
                "x": cx + random.uniform(-7, 7),
                "y": ty + random.uniform(-5, 7),
                "vx": random.uniform(-80, 80),
                "vy": random.uniform(70, 230),
                "life": random.uniform(0.18, 0.45),
                "max_life": 0.45,
                "size": random.uniform(1.5, 5.5),
                "phase": random.uniform(0, math.tau),
                "type": "dragon",
                "gravity": random.uniform(20, 80),
                "drag": 0.97,
            })

        else:
            angle = random.uniform(
                -0.90,
                0.90
            )

            speed_m = random.uniform(
                0.65,
                1.35
            )

            ptype = random.choices(
                [
                    "flame",
                    "spark",
                    "hot"
                ],
                weights=[
                    0.50,
                    0.32,
                    0.18
                ],
            )[0]

            base_spd = (
                140
                if ptype == "spark"
                else 85
            )

            self.particles.append({
                "x": cx + random.uniform(-5, 5),
                "y": ty + random.uniform(-4, 7),
                "vx": (
                    math.sin(angle)
                    * random.uniform(
                        30,
                        base_spd
                    )
                    * speed_m
                ),
                "vy": random.uniform(
                    85,
                    300
                ) * speed_m,
                "life": random.uniform(
                    0.15,
                    0.45
                ),
                "max_life": 0.45,
                "size": random.uniform(
                    1.4,
                    5.5
                ),
                "phase": random.uniform(
                    0,
                    math.tau
                ),
                "type": ptype,
                "gravity": random.uniform(
                    55,
                    130
                ),
                "drag": random.uniform(
                    0.955,
                    0.99
                ),
            })

    def _spawn_smoke(self):
        if len(self.smoke) >= self.MAX_SMOKE:
            return

        cx = (
            self.x
            + self.width / 2
        )

        self.smoke.append({
            "x": cx + random.uniform(-7, 7),
            "y": (
                self.y
                + self.height * 0.92
                + random.uniform(-3, 3)
            ),
            "vx": random.uniform(
                -25,
                25
            ),
            "vy": random.uniform(
                18,
                80
            ),
            "life": random.uniform(
                0.40,
                0.90
            ),
            "max_life": 0.90,
            "size": random.uniform(
                3.5,
                8.0
            ),
            "rot_speed": random.uniform(
                -2,
                2
            ),
            "opacity": random.uniform(
                0.55,
                1.0
            ),
        })

    def _spawn_ember(self):
        if len(self.embers) >= self.MAX_EMBERS:
            return

        cx = (
            self.x
            + self.width / 2
        )

        angle = random.uniform(
            -1.4,
            1.4
        )

        speed = random.uniform(
            35,
            200
        )

        self.embers.append({
            "x": cx + random.uniform(-7, 7),
            "y": (
                self.y
                + self.height
                * random.uniform(
                    0.45,
                    0.92
                )
            ),
            "vx": (
                math.sin(angle)
                * speed
            ),
            "vy": random.uniform(
                25,
                170
            ),
            "life": random.uniform(
                0.35,
                0.80
            ),
            "max_life": 0.80,
            "size": random.uniform(
                0.9,
                3.0
            ),
            "brightness": random.uniform(
                0.55,
                1.0
            ),
            "twinkle_phase": random.uniform(
                0,
                math.tau
            ),
            "twinkle_speed": random.uniform(
                10,
                28
            ),
            "gravity": random.uniform(
                15,
                90
            ),
            "drag": random.uniform(
                0.965,
                0.995
            ),
        })

    def _spawn_heat_wave(self):
        if len(self.heat_waves) >= self.MAX_HEAT_WAVES:
            return

        self.heat_waves.append({
            "x": (
                self.x
                + self.width / 2
                + random.uniform(-10, 10)
            ),
            "y": (
                self.y
                + self.height
                * random.uniform(
                    0.25,
                    0.72
                )
            ),
            "life": random.uniform(
                0.22,
                0.55
            ),
            "max_life": 0.55,
            "size": random.uniform(
                14,
                26
            ),
            "expansion": random.uniform(
                22,
                48
            ),
        })

    def _spawn_flash(self):
        cx = (
            self.x
            + self.width / 2
        )

        self.flash_particles.append({
            "x": (
                cx
                + random.uniform(-4, 4)
            ),
            "y": (
                self.y
                + self.height
                * random.uniform(
                    0.15,
                    0.55
                )
            ),
            "life": random.uniform(
                0.04,
                0.12
            ),
            "max_life": 0.12,
            "size": random.uniform(
                9,
                20
            ),
        })

    def _update_trail(self, dt):
        alive = []

        for p in self.trail:
            p["life"] -= dt
            p["size"] *= 0.975

            p["wobble_phase"] += (
                dt
                * p["wobble_speed"]
            )

            p["x"] += (
                math.sin(
                    p["wobble_phase"]
                )
                * p["wobble_amp"]
                * dt
                * 12
            )

            if p["life"] > 0:
                alive.append(p)

        self.trail = alive

    def _update_particles(self, dt):
        alive = []

        for p in self.particles:
            p["phase"] += dt * 18.0

            p["vx"] *= p["drag"]

            p["x"] += (
                p["vx"]
                + math.sin(
                    p["phase"]
                ) * 20
            ) * dt

            p["y"] += (
                p["vy"]
                * dt
            )

            p["vy"] += (
                p["gravity"]
                * dt
            )

            p["life"] -= dt

            if p["life"] > 0:
                alive.append(p)

        self.particles = alive

    def _update_smoke(self, dt):
        alive = []

        for s in self.smoke:
            s["x"] += (
                s["vx"]
                * dt
            )

            s["y"] += (
                s["vy"]
                * dt
            )

            s["vy"] += 6 * dt
            s["vx"] *= 0.975
            s["size"] += dt * 12
            s["life"] -= dt

            if s["life"] > 0:
                alive.append(s)

        self.smoke = alive

    def _update_embers(self, dt):
        alive = []

        for e in self.embers:
            e["x"] += (
                e["vx"]
                * dt
            )

            e["y"] += (
                e["vy"]
                * dt
            )

            e["vx"] *= e["drag"]

            e["vy"] += (
                e["gravity"]
                * dt
            )

            e["life"] -= dt

            e["twinkle_phase"] += (
                e["twinkle_speed"]
                * dt
            )

            if e["life"] > 0:
                alive.append(e)

        self.embers = alive

    def _update_heat_waves(self, dt):
        alive = []

        for h in self.heat_waves:
            h["size"] += (
                h["expansion"]
                * dt
            )

            h["life"] -= dt

            if h["life"] > 0:
                alive.append(h)

        self.heat_waves = alive

    def _update_flash_particles(self, dt):
        alive = []

        for f in self.flash_particles:
            f["life"] -= dt

            if f["life"] > 0:
                alive.append(f)

        self.flash_particles = alive

    @staticmethod
    def lerp_color(a, b, t):
        t = max(
            0.0,
            min(1.0, t)
        )

        return (
            int(
                a[0]
                + (b[0] - a[0]) * t
            ),
            int(
                a[1]
                + (b[1] - a[1]) * t
            ),
            int(
                a[2]
                + (b[2] - a[2]) * t
            ),
        )

    def flame_color(self, t):
        colors = [
            (50, 3, 1),
            (75, 5, 2),
            (110, 10, 3),
            (160, 20, 4),
            (200, 35, 6),
            (220, 60, 8),
            (240, 85, 10),
            (255, 120, 15),
            (255, 145, 25),
            (255, 170, 35),
            (255, 195, 50),
        ]

        t = max(
            0.0,
            min(1.0, t)
        )

        position = (
            t
            * (len(colors) - 1)
        )

        index = min(
            int(position),
            len(colors) - 2
        )

        local = (
            position
            - index
        )

        return self.lerp_color(
            colors[index],
            colors[index + 1],
            local
        )

    def draw(self, screen):
        if not self.is_active:
            return

        if self.theme == "laser":
            self._draw_laser(screen)

        elif self.theme == "toxic":
            self._draw_toxic(screen)

        elif self.theme == "void":
            self._draw_void(screen)

        elif self.theme == "dragon":
            self._draw_dragon(screen)

        else:
            self._draw_fire(screen)

    def _draw_fire(self, screen):
        self._draw_heat_distortion(
            screen
        )

        self._draw_smoke(
            screen
        )

        self._draw_trail(
            screen
        )

        self._draw_embers(
            screen
        )

        self._draw_particles(
            screen
        )

        self._draw_outer_glow(
            screen
        )

        self._draw_mid_glow(
            screen
        )

        self._draw_flame_body(
            screen
        )

        self._draw_inner_flame(
            screen
        )

        self._draw_core_streak(
            screen
        )

        self._draw_molten_core(
            screen
        )

        self._draw_flame_tip(
            screen
        )

        self._draw_flash_particles(
            screen
        )

    def _draw_laser(self, screen):
        cx = int(
            self.x
            + self.width / 2
        )

        top = int(
            self.y
            - 10
        )

        bottom = int(
            self.y
            + self.height
            + 15
        )

        pulse = (
            math.sin(
                self.time * 2.8
            )
            + 1
        ) * 0.5

        glow = pygame.Surface(
            (
                70,
                self.height + 50
            ),
            pygame.SRCALPHA
        )

        gcx = 35

        for radius in range(
            28,
            4,
            -3
        ):
            alpha = int(
                4
                + 18 * (
                    1
                    - radius / 28
                )
            )

            pygame.draw.ellipse(
                glow,
                (
                    0,
                    180,
                    255,
                    alpha
                ),
                (
                    gcx - radius,
                    20,
                    radius * 2,
                    self.height + 10
                ),
            )

        screen.blit(
            glow,
            (
                cx - 35,
                top - 20
            ),
            special_flags=pygame.BLEND_RGBA_ADD
        )

        pygame.draw.line(
            screen,
            (0, 100, 180),
            (cx, bottom),
            (cx, top),
            8
        )

        pygame.draw.line(
            screen,
            (0, 210, 255),
            (cx, bottom),
            (cx, top),
            4
        )

        pygame.draw.line(
            screen,
            (
                190,
                250,
                255
            ),
            (cx, bottom),
            (cx, top),
            2
        )

        for offset in (-5, 5):
            pygame.draw.line(
                screen,
                (
                    0,
                    140,
                    255
                ),
                (
                    cx + offset,
                    bottom - 8
                ),
                (
                    cx + offset * 0.3,
                    top + 10
                ),
                1
            )

        pulse_r = int(
            8
            + pulse * 3
        )

        pygame.draw.circle(
            screen,
            (
                0,
                220,
                255
            ),
            (
                cx,
                int(
                    self.y
                    + self.height * 0.72
                )
            ),
            pulse_r,
            2
        )

    def _draw_toxic(self, screen):
        cx = int(
            self.x
            + self.width / 2
        )

        top = int(
            self.y
        )

        bottom = int(
            self.y
            + self.height
        )

        pulse = (
            math.sin(
                self.time * 3.2
            )
            + 1
        ) * 0.5

        glow = pygame.Surface(
            (
                70,
                self.height + 40
            ),
            pygame.SRCALPHA
        )

        center = 35

        for r in range(
            30,
            4,
            -3
        ):
            alpha = int(
                3
                + 22
                * (
                    1
                    - r / 30
                )
            )

            pygame.draw.ellipse(
                glow,
                (
                    40,
                    255,
                    90,
                    alpha
                ),
                (
                    center - r,
                    15,
                    r * 2,
                    self.height + 10
                ),
            )

        screen.blit(
            glow,
            (
                cx - 35,
                top - 15
            ),
            special_flags=pygame.BLEND_RGBA_ADD
        )

        points = [
            (
                cx,
                top - 8
            ),
            (
                cx - 8,
                top + 16
            ),
            (
                cx - 5,
                top + 40
            ),
            (
                cx - 7,
                bottom
            ),
            (
                cx,
                bottom + 12
            ),
            (
                cx + 7,
                bottom
            ),
            (
                cx + 5,
                top + 40
            ),
            (
                cx + 8,
                top + 16
            ),
        ]

        pygame.draw.polygon(
            screen,
            (
                20,
                130,
                45
            ),
            points
        )

        pygame.draw.line(
            screen,
            (
                80,
                255,
                100
            ),
            (
                cx,
                bottom
            ),
            (
                cx,
                top
            ),
            6
        )

        pygame.draw.line(
            screen,
            (
                180,
                255,
                150
            ),
            (
                cx,
                bottom - 3
            ),
            (
                cx,
                top + 7
            ),
            2
        )

        for i in range(4):
            phase = (
                self.time * 4
                + i * 1.7
            )

            px = (
                cx
                + math.sin(phase)
                * (
                    5
                    + pulse * 3
                )
            )

            py = (
                top
                + 12
                + i
                * (
                    self.height
                    / 5
                )
            )

            pygame.draw.circle(
                screen,
                (
                    90,
                    255,
                    110
                ),
                (
                    int(px),
                    int(py)
                ),
                2
            )

    def _draw_void(self, screen):
        cx = int(
            self.x
            + self.width / 2
        )

        cy = int(
            self.y
            + self.height * 0.42
        )

        pulse = (
            math.sin(
                self.time * 2.2
            )
            + 1
        ) * 0.5

        glow = pygame.Surface(
            (
                100,
                130
            ),
            pygame.SRCALPHA
        )

        gc = (
            50,
            65
        )

        for r in range(
            45,
            5,
            -4
        ):
            alpha = int(
                3
                + 28
                * (
                    1
                    - r / 45
                )
            )

            pygame.draw.circle(
                glow,
                (
                    150,
                    40,
                    255,
                    alpha
                ),
                (
                    50,
                    65
                ),
                r
            )

        screen.blit(
            glow,
            (
                cx - 50,
                cy - 65
            ),
            special_flags=pygame.BLEND_RGBA_ADD
        )

        points = []

        segments = 18

        for i in range(
            segments
        ):
            t = i / (
                segments - 1
            )

            angle = (
                t * math.tau
                + self.time * 0.8
            )

            radius = (
                7
                + math.sin(
                    self.time * 3
                    + i * 1.7
                ) * 2
                + pulse * 3
            )

            px = (
                cx
                + math.cos(angle)
                * radius
            )

            py = (
                cy
                + math.sin(angle)
                * radius
                * 1.8
            )

            points.append(
                (
                    int(px),
                    int(py)
                )
            )

        if len(points) >= 3:
            pygame.draw.polygon(
                screen,
                (
                    90,
                    15,
                    160
                ),
                points
            )

        pygame.draw.ellipse(
            screen,
            (
                15,
                5,
                25
            ),
            (
                cx - 7,
                cy - 22,
                14,
                44
            )
        )

        pygame.draw.ellipse(
            screen,
            (
                210,
                70,
                255
            ),
            (
                cx - 3,
                cy - 18,
                6,
                36
            )
        )

        for i in range(7):
            angle = (
                self.time * 2
                + i
                * math.tau
                / 7
            )

            radius = (
                15
                + pulse * 7
            )

            px = (
                cx
                + math.cos(angle)
                * radius
            )

            py = (
                cy
                + math.sin(angle)
                * radius
                * 1.6
            )

            pygame.draw.circle(
                screen,
                (
                    175,
                    55,
                    255
                ),
                (
                    int(px),
                    int(py)
                ),
                2
            )

    def _draw_dragon(self, screen):
        cx = int(
            self.x
            + self.width / 2
        )

        top = int(
            self.y
        )

        bottom = int(
            self.y
            + self.height
        )

        pulse = (
            math.sin(
                self.time * 2.5
            )
            + 1
        ) * 0.5

        glow = pygame.Surface(
            (
                100,
                self.height + 70
            ),
            pygame.SRCALPHA
        )

        gcx = 50

        for r in range(
            42,
            4,
            -3
        ):
            alpha = int(
                5
                + 25
                * (
                    1
                    - r / 42
                )
            )

            pygame.draw.ellipse(
                glow,
                (
                    255,
                    175,
                    25,
                    alpha
                ),
                (
                    gcx - r,
                    25,
                    r * 2,
                    self.height + 5
                ),
            )

        screen.blit(
            glow,
            (
                cx - 50,
                top - 25
            ),
            special_flags=pygame.BLEND_RGBA_ADD
        )

        flame = [
            (
                cx,
                top - 18
            ),
            (
                cx - 12,
                top + 8
            ),
            (
                cx - 8,
                top + 24
            ),
            (
                cx - 14,
                top + 43
            ),
            (
                cx - 7,
                top + 63
            ),
            (
                cx - 9,
                bottom + 10
            ),
            (
                cx,
                bottom - 4
            ),
            (
                cx + 9,
                bottom + 10
            ),
            (
                cx + 7,
                top + 63
            ),
            (
                cx + 14,
                top + 43
            ),
            (
                cx + 8,
                top + 24
            ),
            (
                cx + 12,
                top + 8
            ),
        ]

        pygame.draw.polygon(
            screen,
            (
                190,
                80,
                10
            ),
            flame
        )

        pygame.draw.line(
            screen,
            (
                255,
                190,
                35
            ),
            (
                cx,
                bottom
            ),
            (
                cx,
                top
            ),
            8
        )

        pygame.draw.line(
            screen,
            (
                255,
                230,
                100
            ),
            (
                cx,
                bottom - 2
            ),
            (
                cx,
                top + 4
            ),
            3
        )

        wing_left = [
            (
                cx - 5,
                top + 30
            ),
            (
                cx - 23,
                top + 45
            ),
            (
                cx - 12,
                top + 52
            ),
            (
                cx - 4,
                top + 45
            ),
        ]

        wing_right = [
            (
                cx + 5,
                top + 30
            ),
            (
                cx + 23,
                top + 45
            ),
            (
                cx + 12,
                top + 52
            ),
            (
                cx + 4,
                top + 45
            ),
        ]

        pygame.draw.polygon(
            screen,
            (
                55,
                150,
                230
            ),
            wing_left
        )

        pygame.draw.polygon(
            screen,
            (
                55,
                150,
                230
            ),
            wing_right
        )

        pygame.draw.line(
            screen,
            (
                150,
                220,
                255
            ),
            (
                cx - 5,
                top + 34
            ),
            (
                cx - 20,
                top + 45
            ),
            2
        )

        pygame.draw.line(
            screen,
            (
                150,
                220,
                255
            ),
            (
                cx + 5,
                top + 34
            ),
            (
                cx + 20,
                top + 45
            ),
            2
        )

        for i in range(5):
            angle = (
                self.time * 3.0
                + i * math.tau / 5
            )

            radius = (
                12
                + pulse * 8
            )

            px = (
                cx
                + math.cos(angle)
                * radius
            )

            py = (
                top
                + self.height * 0.48
                + math.sin(angle)
                * radius
            )

            pygame.draw.circle(
                screen,
                (
                    255,
                    190,
                    40
                ),
                (
                    int(px),
                    int(py)
                ),
                2
            )

    def _draw_heat_distortion(self, screen):
        for hw in self.heat_waves:
            ratio = max(
                0.0,
                hw["life"]
                / hw["max_life"]
            )

            base_alpha = int(
                16
                * ratio
                * ratio
            )

            radius = max(
                4,
                int(hw["size"])
            )

            size = (
                radius * 2
                + 4
            )

            surface = pygame.Surface(
                (
                    size,
                    size
                ),
                pygame.SRCALPHA
            )

            c = size // 2

            for r_off in range(
                0,
                radius,
                2
            ):
                r = radius - r_off

                t = (
                    r_off
                    / max(
                        1,
                        radius
                    )
                )

                a = max(
                    0,
                    int(
                        base_alpha
                        * (
                            1.0
                            - t
                        )
                    )
                )

                if self.theme == "dragon":
                    color = (
                        255,
                        155,
                        25
                    )
                else:
                    color = (
                        200,
                        60,
                        8
                    )

                pygame.draw.circle(
                    surface,
                    (
                        color[0],
                        color[1],
                        color[2],
                        a
                    ),
                    (
                        c,
                        c
                    ),
                    r,
                    1
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
                    )
                ),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

    def _draw_smoke(self, screen):
        for s in self.smoke:
            ratio = max(
                0.0,
                s["life"]
                / s["max_life"]
            )

            alpha = int(
                55
                * ratio
                * ratio
                * s["opacity"]
            )

            radius = max(
                2,
                int(s["size"])
            )

            size = (
                radius * 4
                + 4
            )

            surface = pygame.Surface(
                (
                    size,
                    size
                ),
                pygame.SRCALPHA
            )

            c = size // 2

            if self.theme == "dragon":
                smoke_col = (
                    85,
                    55,
                    30
                )
            else:
                smoke_col = (
                    55,
                    30,
                    18
                )

            for layer in range(3):
                r = max(
                    1,
                    radius
                    - layer * 2
                )

                a = min(
                    255,
                    alpha
                    + layer * 6
                )

                pygame.draw.circle(
                    surface,
                    (
                        smoke_col[0],
                        smoke_col[1],
                        smoke_col[2],
                        a
                    ),
                    (
                        c,
                        c
                    ),
                    r
                )

            screen.blit(
                surface,
                (
                    int(
                        s["x"]
                        - size / 2
                    ),
                    int(
                        s["y"]
                        - size / 2
                    )
                )
            )

    def _draw_trail(self, screen):
        if not self.trail:
            return

        total = max(
            1,
            len(self.trail) - 1
        )

        for i, pt in enumerate(
            self.trail
        ):
            ratio = max(
                0.0,
                pt["life"]
                / pt["max_life"]
            )

            progress = (
                i
                / total
            )

            radius = max(
                1,
                int(
                    pt["size"]
                    * (
                        0.18
                        + progress
                        * 0.82
                    )
                )
            )

            if self.theme == "laser":
                color = (
                    0,
                    200,
                    255
                )

            elif self.theme == "toxic":
                color = (
                    60,
                    240,
                    80
                )

            elif self.theme == "void":
                color = (
                    165,
                    50,
                    255
                )

            elif self.theme == "dragon":
                if progress < 0.5:
                    color = (
                        255,
                        175,
                        25
                    )
                else:
                    color = (
                        60,
                        170,
                        255
                    )

            else:
                color = self.flame_color(
                    0.04
                    + progress
                    * 0.85
                )

            alpha = int(
                170
                * ratio
                * (
                    0.25
                    + progress
                    * 0.75
                )
                * self.flicker_intensity
            )

            size = (
                radius * 6
                + 6
            )

            surface = pygame.Surface(
                (
                    size,
                    size
                ),
                pygame.SRCALPHA
            )

            c = size // 2

            pygame.draw.circle(
                surface,
                (
                    color[0],
                    color[1],
                    color[2],
                    min(
                        255,
                        alpha
                    )
                ),
                (
                    c,
                    c
                ),
                radius
            )

            if progress > 0.55:
                pygame.draw.circle(
                    surface,
                    (
                        min(
                            255,
                            color[0]
                            + 50
                        ),
                        min(
                            255,
                            color[1]
                            + 40
                        ),
                        min(
                            255,
                            color[2]
                            + 30
                        ),
                        int(
                            alpha
                            * 0.65
                        )
                    ),
                    (
                        c,
                        c
                    ),
                    max(
                        1,
                        radius // 2
                    )
                )

            screen.blit(
                surface,
                (
                    int(
                        pt["x"]
                        - size / 2
                    ),
                    int(
                        pt["y"]
                        - size / 2
                    )
                ),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

    def _draw_embers(self, screen):
        for em in self.embers:
            ratio = max(
                0.0,
                em["life"]
                / em["max_life"]
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
                    0.45
                    + twinkle
                    * 0.55
                )
            )

            alpha = int(
                235
                * ratio
                * bright
            )

            r = max(
                1,
                int(
                    em["size"]
                    * (
                        0.35
                        + ratio
                        * 0.65
                    )
                )
            )

            if self.theme == "dragon":
                color = self.lerp_color(
                    (
                        40,
                        100,
                        190
                    ),
                    (
                        255,
                        190,
                        40
                    ),
                    ratio
                )

            else:
                color = self.lerp_color(
                    (
                        75,
                        5,
                        2
                    ),
                    (
                        255,
                        150,
                        30
                    ),
                    ratio
                    * bright
                )

            size = (
                r * 8
                + 4
            )

            surface = pygame.Surface(
                (
                    size,
                    size
                ),
                pygame.SRCALPHA
            )

            c = size // 2

            pygame.draw.circle(
                surface,
                (
                    color[0],
                    color[1],
                    color[2],
                    min(
                        255,
                        int(
                            alpha
                            * 0.30
                        )
                    )
                ),
                (
                    c,
                    c
                ),
                r + 4
            )

            pygame.draw.circle(
                surface,
                (
                    color[0],
                    color[1],
                    color[2],
                    min(
                        255,
                        alpha
                    )
                ),
                (
                    c,
                    c
                ),
                r
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
                    )
                ),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

    def _draw_particles(self, screen):
        for p in self.particles:
            ratio = max(
                0.0,
                p["life"]
                / p["max_life"]
            )

            ptype = p["type"]

            if ptype == "laser":
                color = (
                    80,
                    230,
                    255
                )

            elif ptype == "toxic":
                color = (
                    80,
                    255,
                    100
                )

            elif ptype == "void":
                color = (
                    190,
                    70,
                    255
                )

            elif ptype == "dragon":
                color = self.lerp_color(
                    (
                        50,
                        150,
                        255
                    ),
                    (
                        255,
                        195,
                        40
                    ),
                    ratio
                )

            elif ptype == "spark":
                color = self.lerp_color(
                    (
                        240,
                        85,
                        10
                    ),
                    (
                        255,
                        195,
                        50
                    ),
                    ratio
                    * 0.6
                )

            elif ptype == "hot":
                color = self.lerp_color(
                    (
                        255,
                        120,
                        15
                    ),
                    (
                        255,
                        220,
                        80
                    ),
                    ratio
                    * 0.5
                )

            else:
                color = self.flame_color(
                    ratio
                )

            alpha = int(
                235
                * ratio
            )

            radius = max(
                1,
                int(
                    p["size"]
                    * (
                        0.2
                        + ratio
                        * 0.8
                    )
                )
            )

            size = (
                radius * 6
                + 6
            )

            surface = pygame.Surface(
                (
                    size,
                    size
                ),
                pygame.SRCALPHA
            )

            c = size // 2

            pygame.draw.circle(
                surface,
                (
                    color[0],
                    color[1],
                    color[2],
                    int(
                        alpha
                        * 0.25
                    )
                ),
                (
                    c,
                    c
                ),
                radius + 3
            )

            pygame.draw.circle(
                surface,
                (
                    color[0],
                    color[1],
                    color[2],
                    min(
                        255,
                        alpha
                    )
                ),
                (
                    c,
                    c
                ),
                radius
            )

            screen.blit(
                surface,
                (
                    int(
                        p["x"]
                        - size / 2
                    ),
                    int(
                        p["y"]
                        - size / 2
                    )
                ),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

    def _draw_outer_glow(self, screen):
        cx = int(
            self.x
            + self.width / 2
        )

        cy = int(
            self.y
            + self.height * 0.50
        )

        radius = int(
            36
            + self.pulse * 14
        )

        size = (
            radius * 2
            + 4
        )

        surface = pygame.Surface(
            (
                size,
                size
            ),
            pygame.SRCALPHA
        )

        c = size // 2

        for r in range(
            radius,
            2,
            -1
        ):
            t = (
                1.0
                - r / radius
            )

            a = int(
                (
                    1
                    + 22
                    * t
                    * t
                    * t
                )
                * self.flicker_intensity
            )

            col = self.lerp_color(
                (
                    75,
                    5,
                    2
                ),
                (
                    220,
                    60,
                    8
                ),
                t * t
            )

            pygame.draw.circle(
                surface,
                (
                    col[0],
                    col[1],
                    col[2],
                    a
                ),
                (
                    c,
                    c
                ),
                r
            )

        screen.blit(
            surface,
            (
                cx - c,
                cy - c
            ),
            special_flags=pygame.BLEND_RGBA_ADD
        )

    def _draw_mid_glow(self, screen):
        cx = int(
            self.x
            + self.width / 2
        )

        cy = int(
            self.y
            + self.height * 0.35
        )

        radius = int(
            20
            + self.pulse_fast
            * 10
        )

        size = (
            radius * 2
            + 4
        )

        surface = pygame.Surface(
            (
                size,
                size
            ),
            pygame.SRCALPHA
        )

        c = size // 2

        for r in range(
            radius,
            1,
            -2
        ):
            t = (
                1.0
                - r / radius
            )

            a = int(
                (
                    3
                    + 20
                    * t
                    * t
                )
                * self.flicker_intensity
            )

            col = self.lerp_color(
                (
                    200,
                    35,
                    6
                ),
                (
                    255,
                    120,
                    15
                ),
                t
            )

            pygame.draw.circle(
                surface,
                (
                    col[0],
                    col[1],
                    col[2],
                    a
                ),
                (
                    c,
                    c
                ),
                r
            )

        screen.blit(
            surface,
            (
                cx - c,
                cy - c
            ),
            special_flags=pygame.BLEND_RGBA_ADD
        )

    def _draw_flame_body(self, screen):
        cx = (
            self.x
            + self.width / 2
        )

        points = [
            (
                cx,
                self.y - 1
            )
        ]

        segs = 24

        for i in range(
            segs + 1
        ):
            t = (
                i / segs
            )

            wf = math.sin(
                math.pi * t
            )

            turb = (
                math.sin(
                    self.time * 6.5
                    + i * 1.8
                )
                * 2.2
            )

            flk = (
                math.sin(
                    self.time * 11
                    + i * 2.6
                )
                * 1.4
            )

            micro = (
                math.sin(
                    self.time * 18
                    + i * 3.3
                )
                * 0.7
            )

            w = (
                self.width
                * 0.55
                * wf
                * (
                    0.82
                    + self.pulse
                    * 0.18
                )
                * self.flicker_intensity
            )

            side = (
                -1
                if i % 2 == 0
                else 1
            )

            px = (
                cx
                + side * w
                + turb
                + flk
                + micro
            )

            py = (
                self.y
                + self.height
                * (
                    0.04
                    + t * 0.86
                )
            )

            points.append(
                (
                    px,
                    py
                )
            )

        points.append(
            (
                cx,
                self.y
                + self.height
                * 1.08
            )
        )

        pad = 35

        surface = pygame.Surface(
            (
                self.width
                + pad * 2,
                self.height
                + pad * 2
            ),
            pygame.SRCALPHA
        )

        ox = (
            pad
            - self.x
        )

        oy = (
            pad
            - self.y
        )

        transformed = [
            (
                int(px + ox),
                int(py + oy)
            )
            for px, py in points
        ]

        pygame.draw.polygon(
            surface,
            (
                75,
                5,
                2,
                90
            ),
            transformed
        )

        pygame.draw.polygon(
            surface,
            (
                110,
                10,
                3,
                120
            ),
            transformed
        )

        pygame.draw.polygon(
            surface,
            (
                140,
                15,
                5,
                110
            ),
            transformed
        )

        screen.blit(
            surface,
            (
                int(
                    self.x
                    - pad
                ),
                int(
                    self.y
                    - pad
                )
            ),
            special_flags=pygame.BLEND_RGBA_ADD
        )

    def _draw_inner_flame(self, screen):
        cx = (
            self.x
            + self.width / 2
        )

        points = [
            (
                cx,
                self.y
                + self.height
                * 0.02
            )
        ]

        segs = 18

        for i in range(
            segs + 1
        ):
            t = (
                i / segs
            )

            w = (
                self.width
                * 0.35
                * math.sin(
                    math.pi * t
                )
            )

            wb = (
                math.sin(
                    self.time * 9
                    + i * 2.1
                )
                * 1.2
            )

            mc = (
                math.sin(
                    self.time * 16
                    + i * 3.6
                )
                * 0.5
            )

            side = (
                -1
                if i % 2 == 0
                else 1
            )

            px = (
                cx
                + side * w
                + wb
                + mc
            )

            py = (
                self.y
                + self.height
                * (
                    0.07
                    + t * 0.76
                )
            )

            points.append(
                (
                    px,
                    py
                )
            )

        points.append(
            (
                cx,
                self.y
                + self.height
                * 0.88
            )
        )

        pad = 22

        surface = pygame.Surface(
            (
                self.width
                + pad * 2,
                self.height
                + pad * 2
            ),
            pygame.SRCALPHA
        )

        ox = (
            pad
            - self.x
        )

        oy = (
            pad
            - self.y
        )

        transformed = [
            (
                int(px + ox),
                int(py + oy)
            )
            for px, py in points
        ]

        pygame.draw.polygon(
            surface,
            (
                220,
                60,
                8,
                150
            ),
            transformed
        )

        pygame.draw.polygon(
            surface,
            (
                240,
                85,
                10,
                130
            ),
            transformed
        )

        screen.blit(
            surface,
            (
                int(
                    self.x
                    - pad
                ),
                int(
                    self.y
                    - pad
                )
            ),
            special_flags=pygame.BLEND_RGBA_ADD
        )

    def _draw_core_streak(self, screen):
        cx = (
            self.x
            + self.width / 2
        )

        points = [
            (
                cx,
                self.y
                + self.height
                * 0.06
            )
        ]

        segs = 12

        for i in range(
            segs + 1
        ):
            t = (
                i / segs
            )

            w = (
                self.width
                * 0.16
                * math.sin(
                    math.pi * t
                )
            )

            wb = (
                math.sin(
                    self.time * 13
                    + i * 2.9
                )
                * 0.7
            )

            side = (
                -1
                if i % 2 == 0
                else 1
            )

            px = (
                cx
                + side * w
                + wb
            )

            py = (
                self.y
                + self.height
                * (
                    0.10
                    + t * 0.65
                )
            )

            points.append(
                (
                    px,
                    py
                )
            )

        points.append(
            (
                cx,
                self.y
                + self.height
                * 0.80
            )
        )

        pad = 16

        surface = pygame.Surface(
            (
                self.width
                + pad * 2,
                self.height
                + pad * 2
            ),
            pygame.SRCALPHA
        )

        ox = (
            pad
            - self.x
        )

        oy = (
            pad
            - self.y
        )

        transformed = [
            (
                int(px + ox),
                int(py + oy)
            )
            for px, py in points
        ]

        pygame.draw.polygon(
            surface,
            (
                255,
                120,
                15,
                160
            ),
            transformed
        )

        pygame.draw.polygon(
            surface,
            (
                255,
                170,
                35,
                110
            ),
            transformed
        )

        screen.blit(
            surface,
            (
                int(
                    self.x
                    - pad
                ),
                int(
                    self.y
                    - pad
                )
            ),
            special_flags=pygame.BLEND_RGBA_ADD
        )

    def _draw_molten_core(self, screen):
        cx = int(
            self.x
            + self.width / 2
        )

        cy = int(
            self.y
            + self.height
            * 0.36
        )

        cw = int(
            7
            + self.pulse * 3
        )

        ch = int(
            30
            + self.pulse * 7
        )

        surface = pygame.Surface(
            (
                cw * 7,
                ch * 4
                + 12
            ),
            pygame.SRCALPHA
        )

        sx = (
            surface.get_width()
            // 2
        )

        sy = (
            surface.get_height()
            // 2
        )

        pygame.draw.ellipse(
            surface,
            (
                240,
                85,
                10,
                70
            ),
            (
                sx - cw - 4,
                sy - ch - 3,
                (cw + 4) * 2,
                (ch + 3) * 2
            )
        )

        pygame.draw.ellipse(
            surface,
            (
                255,
                120,
                15,
                190
            ),
            (
                sx - cw,
                sy - ch,
                cw * 2,
                ch * 2
            )
        )

        aw = max(
            3,
            int(
                cw * 0.70
            )
        )

        ah = max(
            8,
            int(
                ch * 0.78
            )
        )

        pygame.draw.ellipse(
            surface,
            (
                255,
                145,
                25,
                220
            ),
            (
                sx - aw,
                sy - ah,
                aw * 2,
                ah * 2
            )
        )

        gw = max(
            2,
            int(
                cw * 0.45
            )
        )

        gh = max(
            6,
            int(
                ch * 0.55
            )
        )

        pygame.draw.ellipse(
            surface,
            (
                255,
                170,
                35,
                240
            ),
            (
                sx - gw,
                sy - gh,
                gw * 2,
                gh * 2
            )
        )

        mw = max(
            1,
            cw // 3
        )

        mh = max(
            4,
            ch // 2
        )

        pygame.draw.ellipse(
            surface,
            (
                255,
                220,
                80,
                230
            ),
            (
                sx - mw,
                sy - mh,
                mw * 2,
                mh * 2
            )
        )

        screen.blit(
            surface,
            (
                cx
                - surface.get_width()
                // 2,
                cy
                - surface.get_height()
                // 2
            ),
            special_flags=pygame.BLEND_RGBA_ADD
        )

    def _draw_flame_tip(self, screen):
        cx = int(
            self.x
            + self.width / 2
        )

        tip_y = int(
            self.y + 1
        )

        p = (
            1.0
            + self.pulse
            * 0.35
        )

        length = int(
            18 * p
        )

        width = int(
            9 * p
        )

        outer = [
            (
                cx,
                tip_y
                - length
                - 5
            ),
            (
                cx
                - width
                - 3,
                tip_y + 5
            ),
            (
                cx,
                tip_y + 3
            ),
            (
                cx
                + width
                + 3,
                tip_y + 5
            ),
        ]

        mid = [
            (
                cx,
                tip_y
                - length
                - 1
            ),
            (
                cx
                - width,
                tip_y + 4
            ),
            (
                cx,
                tip_y + 2
            ),
            (
                cx
                + width,
                tip_y + 4
            ),
        ]

        inner = [
            (
                cx,
                tip_y
                - length
                + 3
            ),
            (
                cx - 3,
                tip_y + 3
            ),
            (
                cx,
                tip_y + 1
            ),
            (
                cx + 3,
                tip_y + 3
            ),
        ]

        sw = (
            self.width
            * 3
            + 14
        )

        sh = (
            self.height // 2
            + 24
        )

        surface = pygame.Surface(
            (
                int(sw),
                int(sh)
            ),
            pygame.SRCALPHA
        )

        ox = (
            sw // 2
            - cx
        )

        oy = (
            18
            - tip_y
        )

        def transform(points):
            return [
                (
                    int(x + ox),
                    int(y + oy)
                )
                for x, y in points
            ]

        pygame.draw.polygon(
            surface,
            (
                220,
                60,
                8,
                110
            ),
            transform(outer)
        )

        pygame.draw.polygon(
            surface,
            (
                255,
                120,
                15,
                180
            ),
            transform(mid)
        )

        pygame.draw.polygon(
            surface,
            (
                255,
                170,
                35,
                220
            ),
            transform(inner)
        )

        pygame.draw.circle(
            surface,
            (
                255,
                145,
                25,
                90
            ),
            (
                int(
                    sw // 2
                ),
                int(
                    18 - 3
                )
            ),
            int(
                6 * p
            ),
        )

        screen.blit(
            surface,
            (
                int(
                    cx
                    - sw // 2
                ),
                int(
                    tip_y - 18
                )
            ),
            special_flags=pygame.BLEND_RGBA_ADD
        )

    def _draw_flash_particles(self, screen):
        for f in self.flash_particles:
            ratio = max(
                0.0,
                f["life"]
                / f["max_life"]
            )

            alpha = int(
                180 * ratio
            )

            radius = max(
                2,
                int(
                    f["size"]
                    * ratio
                )
            )

            size = (
                radius * 2
                + 6
            )

            surface = pygame.Surface(
                (
                    size,
                    size
                ),
                pygame.SRCALPHA
            )

            c = size // 2

            if self.theme == "laser":
                color = (
                    0,
                    220,
                    255
                )

            elif self.theme == "toxic":
                color = (
                    90,
                    255,
                    110
                )

            elif self.theme == "void":
                color = (
                    190,
                    70,
                    255
                )

            elif self.theme == "dragon":
                color = (
                    255,
                    195,
                    45
                )

            else:
                color = (
                    255,
                    170,
                    35
                )

            pygame.draw.circle(
                surface,
                (
                    color[0],
                    color[1],
                    color[2],
                    alpha
                ),
                (
                    c,
                    c
                ),
                radius
            )

            pygame.draw.circle(
                surface,
                (
                    color[0],
                    color[1],
                    color[2],
                    int(
                        alpha
                        * 0.45
                    )
                ),
                (
                    c,
                    c
                ),
                radius + 4
            )

            screen.blit(
                surface,
                (
                    int(
                        f["x"]
                        - size / 2
                    ),
                    int(
                        f["y"]
                        - size / 2
                    )
                ),
                special_flags=pygame.BLEND_RGBA_ADD,
            )


if __name__ == "__main__":
    pygame.init()

    WIDTH = 800
    HEIGHT = 900

    screen = pygame.display.set_mode(
        (
            WIDTH,
            HEIGHT
        )
    )

    pygame.display.set_caption(
        "Space Invaders - Weapon Test"
    )

    clock = pygame.time.Clock()

    bullets = []

    ship_ids = [
        "starter",
        "falcon",
        "viper",
        "wraith",
        "dragon",
    ]

    selected_ship = 0

    spawn_timer = 0.0

    running = True

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif (
                event.type
                == pygame.MOUSEBUTTONDOWN
            ):
                mx, my = pygame.mouse.get_pos()

                bullets.append(
                    Bullet(
                        mx,
                        my + 40,
                        ship_id=ship_ids[
                            selected_ship
                        ]
                    )
                )

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_SPACE:
                    selected_ship = (
                        selected_ship + 1
                    ) % len(ship_ids)

                elif event.key == pygame.K_c:
                    bullets.clear()

                elif event.key == pygame.K_ESCAPE:
                    running = False

        spawn_timer += dt

        if spawn_timer >= 0.55:
            spawn_timer -= 0.55

            x = random.randint(
                100,
                WIDTH - 100
            )

            bullets.append(
                Bullet(
                    x,
                    HEIGHT + 20,
                    ship_id=ship_ids[
                        selected_ship
                    ]
                )
            )

        for bullet in bullets:
            bullet.update(dt)

        bullets = [
            bullet
            for bullet in bullets
            if bullet.is_active
        ]

        screen.fill(
            (
                5,
                3,
                8
            )
        )

        random.seed(42)

        for _ in range(50):
            sx = random.randint(
                0,
                WIDTH
            )

            sy = random.randint(
                0,
                HEIGHT
            )

            br = random.randint(
                20,
                65
            )

            screen.set_at(
                (
                    sx,
                    sy
                ),
                (
                    br,
                    max(0, br - 5),
                    max(0, br - 10)
                )
            )

        random.seed()

        for bullet in bullets:
            bullet.draw(screen)

        font = pygame.font.SysFont(
            "consolas",
            16
        )

        lines = [
            f"Ship: {ship_ids[selected_ship].upper()}",
            f"FPS: {clock.get_fps():.0f}",
            f"Bullets: {len(bullets)}",
            "SPACE: change ship | Click: fire | C: clear | ESC: quit",
        ]

        for i, line in enumerate(lines):
            text = font.render(
                line,
                True,
                (
                    180,
                    160,
                    150
                )
            )

            screen.blit(
                text,
                (
                    10,
                    10 + i * 20
                )
            )

        pygame.display.flip()

    pygame.quit()