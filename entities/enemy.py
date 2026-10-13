import pygame
import random
import math


# ---------------------------------------------------------------------
# Shared caches. Enemies are created in big batches every wave, so loading
# and scaling the image per enemy (and building a new alpha Surface per
# trail point every frame) caused hitches and lag.
# ---------------------------------------------------------------------

_IMAGE_CACHE = {}
_GLOW_CACHE = {}
_DOT_CACHE = {}
_ROTATE_CACHE = {}


def get_glow_dot(color, radius, alpha):
    """Soft round dot used for engine trails / particles (cached)."""
    radius = max(1, int(radius))
    alpha = max(0, min(255, int(alpha) // 8 * 8))
    key = (color, radius, alpha)

    surface = _DOT_CACHE.get(key)

    if surface is None:
        if len(_DOT_CACHE) > 500:
            _DOT_CACHE.clear()

        size = radius * 4
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(
            surface,
            (color[0], color[1], color[2], alpha),
            (size // 2, size // 2),
            radius,
        )
        _DOT_CACHE[key] = surface

    return surface


class Enemy:

    def __init__(
        self,
        index,
        total_enemies,
        screen_width,
        screen_height,
        enemy_type="normal"
    ):

        self.index = index
        self.total_enemies = total_enemies

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.enemy_type = enemy_type

        if enemy_type == "fast":

            self.width = 85
            self.height = 65

            self.speed = 10
            self.health = 1
            self.max_health = 1

            self.entry_speed = 7
            self.attack_speed = 15

            image_path = "assets/images/enemy_fast.png"

            self.color = (255, 70, 70)
            self.glow_color = (255, 40, 40)

        elif enemy_type == "tank":

            self.width = 120
            self.height = 90

            self.speed = 5
            self.health = 3
            self.max_health = 3

            self.entry_speed = 4
            self.attack_speed = 7

            image_path = "assets/images/enemy_tank.png"

            self.color = (190, 70, 255)
            self.glow_color = (150, 30, 255)

        else:

            self.width = 100
            self.height = 75

            self.speed = 7
            self.health = 1
            self.max_health = 1

            self.entry_speed = 5
            self.attack_speed = 9

            image_path = "assets/images/enemy.png"

            self.color = (50, 255, 120)
            self.glow_color = (20, 220, 100)

        self.is_alive = True

        spacing = screen_width / (total_enemies + 1)

        self.formation_x = (
            spacing * (index + 1)
            - self.width / 2
        )

        self.formation_y = 100

        self.x = self.formation_x
        self.y = -self.height - 30

        self.state = "entering"

        self.target_x = self.x
        self.target_y = self.y

        self.attack_angle = 0

        self.velocity_x = 0
        self.velocity_y = 0

        self.attack_progress = 0

        self.animation_timer = random.uniform(0, 200)

        self.hover_offset = random.uniform(0, math.tau)

        self.rotation_angle = 0

        self.hit_flash_timer = 0
        self.hit_flash_duration = 8

        self.damage_pulse = 0

        self.trail = []
        self.max_trail = 18

        self.engine_particles = []

        self.attack_cooldown = 0

        self.death_timer = 0
        self.death_duration = 0.35

        self.shield_pulse = random.uniform(0, math.tau)

        self._flash_cache = {}

        # ---- image: loaded + scaled once per type, shared by every enemy ----
        cache_key = (image_path, self.width, self.height)
        cached = _IMAGE_CACHE.get(cache_key)

        if cached is None:

            try:

                loaded = pygame.image.load(image_path).convert_alpha()

                cached = pygame.transform.smoothscale(
                    loaded,
                    (self.width, self.height)
                )

            except Exception as error:

                print("Could not load enemy image:", error)

                self.image = pygame.Surface(
                    (self.width, self.height),
                    pygame.SRCALPHA
                )

                self.create_futuristic_enemy()

                cached = self.image

            _IMAGE_CACHE[cache_key] = cached

        self.image = cached

        self.glow_image = self.create_glow()

    def create_futuristic_enemy(self):

        w = self.width
        h = self.height

        pygame.draw.polygon(
            self.image,
            self.color,
            [
                (w // 2, 0),
                (w - 8, h * 0.45),
                (w * 0.78, h),
                (w // 2, h * 0.78),
                (w * 0.22, h),
                (8, h * 0.45)
            ]
        )

        pygame.draw.polygon(
            self.image,
            (18, 22, 32),
            [
                (w // 2, 10),
                (w * 0.70, h * 0.45),
                (w * 0.60, h * 0.72),
                (w // 2, h * 0.62),
                (w * 0.40, h * 0.72),
                (w * 0.30, h * 0.45)
            ]
        )

        pygame.draw.polygon(
            self.image,
            self.color,
            [
                (w * 0.32, h * 0.42),
                (0, h * 0.72),
                (w * 0.28, h * 0.68)
            ]
        )

        pygame.draw.polygon(
            self.image,
            self.color,
            [
                (w * 0.68, h * 0.42),
                (w, h * 0.72),
                (w * 0.72, h * 0.68)
            ]
        )

        pygame.draw.polygon(
            self.image,
            (80, 210, 255),
            [
                (w // 2, h * 0.16),
                (w * 0.60, h * 0.42),
                (w // 2, h * 0.52),
                (w * 0.40, h * 0.42)
            ]
        )

        pygame.draw.polygon(
            self.image,
            (15, 30, 45),
            [
                (w // 2, h * 0.22),
                (w * 0.55, h * 0.40),
                (w // 2, h * 0.46),
                (w * 0.45, h * 0.40)
            ]
        )

        pygame.draw.line(
            self.image,
            (220, 255, 240),
            (w * 0.12, h * 0.65),
            (w * 0.38, h * 0.55),
            2
        )

        pygame.draw.line(
            self.image,
            (220, 255, 240),
            (w * 0.88, h * 0.65),
            (w * 0.62, h * 0.55),
            2
        )

        pygame.draw.polygon(
            self.image,
            self.glow_color,
            [
                (w * 0.34, h * 0.82),
                (w * 0.43, h * 0.70),
                (w * 0.47, h * 0.86)
            ]
        )

        pygame.draw.polygon(
            self.image,
            self.glow_color,
            [
                (w * 0.66, h * 0.82),
                (w * 0.57, h * 0.70),
                (w * 0.53, h * 0.86)
            ]
        )

    def create_glow(self):

        key = (self.width, self.height, self.glow_color)
        cached = _GLOW_CACHE.get(key)

        if cached is not None:
            return cached

        surface = pygame.Surface(
            (
                self.width + 50,
                self.height + 50
            ),
            pygame.SRCALPHA
        )

        w = self.width + 50
        h = self.height + 50

        for i in range(7):

            alpha = 8 + i * 5

            pygame.draw.ellipse(
                surface,
                (
                    self.glow_color[0],
                    self.glow_color[1],
                    self.glow_color[2],
                    alpha
                ),
                (
                    5 + i,
                    5 + i,
                    w - 10 - i * 2,
                    h - 10 - i * 2
                ),
                2
            )

        _GLOW_CACHE[key] = surface

        return surface

    def take_damage(self, damage):

        if not self.is_alive:
            return False

        if self.state in (
            "offscreen",
            "dead"
        ):
            return False

        damage = max(
            0,
            int(damage)
        )

        if damage <= 0:
            return False

        self.health -= damage

        self.hit_flash_timer = (
            self.hit_flash_duration
        )

        self.damage_pulse = 1.0

        if self.health <= 0:

            self.health = 0
            self.is_alive = False
            self.state = "dead"

            self.death_timer = (
                self.death_duration
            )

            return True

        return False

    def start_drop(
        self,
        target_x,
        target_y
    ):

        if not self.is_alive:
            return

        if self.state != "waiting":
            return

        self.state = "attacking"

        self.target_x = target_x
        self.target_y = target_y

        self.attack_progress = 0

        center_x = (
            self.x
            + self.width / 2
        )

        center_y = (
            self.y
            + self.height / 2
        )

        dx = target_x - center_x
        dy = target_y - center_y

        distance = math.hypot(
            dx,
            dy
        )

        if distance > 0:

            self.attack_angle = math.atan2(
                dy,
                dx
            )

        self.velocity_x = (
            math.cos(
                self.attack_angle
            ) * 2
        )

        self.velocity_y = (
            math.sin(
                self.attack_angle
            ) * 2
        )

        self.rotation_angle = 0

        self.trail.clear()
        self.engine_particles.clear()

    def update(self):

        if self.state == "dead":

            self.update_death()

            return

        if not self.is_alive:
            return

        self.animation_timer += 1

        self.shield_pulse += 0.08

        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

        if self.damage_pulse > 0:
            self.damage_pulse -= 0.08

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.state == "entering":

            self.update_entering()

        elif self.state == "waiting":

            self.update_waiting()

        elif self.state == "attacking":

            self.update_attacking()

        elif self.state == "leaving":

            self.update_leaving()

        elif self.state == "offscreen":

            return

        self.update_engine_particles()

    def update_entering(self):

        difference = (
            self.formation_y
            - self.y
        )

        movement = min(
            self.entry_speed,
            max(0, difference)
        )

        self.y += movement

        if self.y >= self.formation_y:

            self.y = self.formation_y

            self.state = "waiting"

            self.velocity_x = 0
            self.velocity_y = 0

    def update_waiting(self):

        hover_time = (
            self.animation_timer
            * 0.045
            + self.hover_offset
        )

        hover_y = (
            math.sin(hover_time)
            * 5
        )

        self.y = (
            self.formation_y
            + hover_y
        )

        formation_wave = math.sin(
            self.animation_timer * 0.025
            + self.hover_offset
        )

        self.x = (
            self.formation_x
            + formation_wave * 3
        )

        self.rotation_angle = (
            math.sin(
                self.animation_timer
                * 0.04
            ) * 3
        )

        self.trail.clear()

    def update_attacking(self):

        self.attack_progress += 1

        acceleration = 0.16

        target_velocity_x = (
            math.cos(
                self.attack_angle
            )
            * self.attack_speed
        )

        target_velocity_y = (
            math.sin(
                self.attack_angle
            )
            * self.attack_speed
        )

        self.velocity_x += (
            target_velocity_x
            - self.velocity_x
        ) * acceleration

        self.velocity_y += (
            target_velocity_y
            - self.velocity_y
        ) * acceleration

        self.x += self.velocity_x
        self.y += self.velocity_y

        if self.enemy_type == "fast":

            movement_angle = math.atan2(
                self.velocity_y,
                self.velocity_x
            )

            self.rotation_angle = (
                -math.degrees(
                    movement_angle
                ) + 90
            )

        else:

            self.rotation_angle = (
                math.sin(
                    self.attack_progress * 0.12
                ) * 8
            )

        self.add_engine_trail()

        if (
            self.y
            > self.screen_height * 0.70
        ):

            self.state = "leaving"

    def update_leaving(self):

        self.y += (
            self.speed + 5
        )

        wave = math.sin(
            self.animation_timer * 0.10
        )

        self.x += wave * 2.5

        if self.enemy_type == "fast":

            self.rotation_angle = 180

        self.add_engine_trail()

        if (
            self.y
            > self.screen_height
            + self.height
        ):

            self.state = "offscreen"

            self.trail.clear()
            self.engine_particles.clear()

    def update_death(self):

        self.death_timer -= 1 / 60

        self.x += math.sin(
            self.animation_timer * 0.7
        ) * 0.5

        self.y -= 0.8

        if self.death_timer <= 0:

            self.state = "offscreen"

            self.trail.clear()
            self.engine_particles.clear()

    def add_engine_trail(self):

        center_x = (
            self.x
            + self.width / 2
        )

        center_y = (
            self.y
            + self.height / 2
        )

        direction_x = (
            -math.cos(
                math.radians(
                    self.rotation_angle
                )
            )
        )

        direction_y = (
            -math.sin(
                math.radians(
                    self.rotation_angle
                )
            )
        )

        self.trail.append(
            {
                "x": center_x,
                "y": center_y,
                "dx": direction_x,
                "dy": direction_y,
                "life": 0.35,
                "max_life": 0.35,
                "size": random.uniform(
                    4,
                    8
                )
            }
        )

        if len(self.trail) > self.max_trail:
            self.trail.pop(0)

        if random.random() < 0.75:

            self.engine_particles.append(
                {
                    "x": center_x,
                    "y": center_y,
                    "vx": random.uniform(
                        -20,
                        20
                    ),
                    "vy": random.uniform(
                        15,
                        50
                    ),
                    "life": random.uniform(
                        0.15,
                        0.30
                    ),
                    "max_life": 0.30,
                    "size": random.uniform(
                        2,
                        4
                    )
                }
            )

    def update_engine_particles(self):

        alive = []

        for particle in self.engine_particles:

            particle["x"] += (
                particle["vx"]
                * 0.016
            )

            particle["y"] += (
                particle["vy"]
                * 0.016
            )

            particle["life"] -= 0.016

            particle["size"] *= 0.97

            if particle["life"] > 0:
                alive.append(
                    particle
                )

        self.engine_particles = alive

    def get_hitbox(self):

        padding_x = int(
            self.width * 0.22
        )

        padding_y = int(
            self.height * 0.20
        )

        return pygame.Rect(
            int(self.x) + padding_x,
            int(self.y) + padding_y,
            max(
                1,
                self.width
                - padding_x * 2
            ),
            max(
                1,
                self.height
                - padding_y * 2
            )
        )

    def get_rect(self):

        return self.get_hitbox()

    def draw_trail(self, screen):

        if len(self.trail) < 2:
            return

        last = max(1, len(self.trail) - 1)

        for i, point in enumerate(self.trail):

            ratio = max(
                0.0,
                point["life"]
                / point["max_life"]
            )

            progress = i / last

            alpha = int(25 + progress * 110)

            radius = max(1, int(point["size"] * ratio))

            # cached dot instead of a brand-new Surface per point per frame
            dot = get_glow_dot(self.glow_color, radius, alpha)

            screen.blit(
                dot,
                dot.get_rect(
                    center=(
                        int(point["x"]),
                        int(point["y"])
                    )
                ),
                special_flags=pygame.BLEND_RGBA_ADD
            )

    def draw_engine_particles(
        self,
        screen
    ):

        for particle in self.engine_particles:

            ratio = max(
                0.0,
                particle["life"]
                / particle["max_life"]
            )

            alpha = int(190 * ratio)

            radius = max(1, int(particle["size"]))

            dot = get_glow_dot(self.glow_color, radius, alpha)

            screen.blit(
                dot,
                dot.get_rect(
                    center=(
                        int(particle["x"]),
                        int(particle["y"])
                    )
                ),
                special_flags=pygame.BLEND_RGBA_ADD
            )

    def draw_tank_shield(self, screen):
        return

    def draw_health_bar(self, screen):

        if self.max_health <= 1:
            return

        if not self.is_alive:
            return

        if self.health >= self.max_health:
            return

        bar_width = self.width
        bar_height = 6

        bar_x = int(self.x)

        bar_y = int(
            self.y - 12
        )

        pygame.draw.rect(
            screen,
            (20, 20, 30),
            (
                bar_x,
                bar_y,
                bar_width,
                bar_height
            ),
            border_radius=3
        )

        health_ratio = (
            self.health
            / self.max_health
        )

        health_width = int(
            bar_width
            * health_ratio
        )

        if health_width > 0:

            pygame.draw.rect(
                screen,
                self.color,
                (
                    bar_x,
                    bar_y,
                    health_width,
                    bar_height
                ),
                border_radius=3
            )

        pygame.draw.rect(
            screen,
            (
                80,
                80,
                100
            ),
            (
                bar_x,
                bar_y,
                bar_width,
                bar_height
            ),
            1,
            border_radius=3
        )

    def draw_hit_flash(self, screen):

        if self.hit_flash_timer <= 0:
            return

        alpha = int(
            120
            * (
                self.hit_flash_timer
                / self.hit_flash_duration
            )
        )

        # only ~8 distinct flash levels, so build each one once
        flash = self._flash_cache.get(alpha)

        if flash is None:
            flash = self.image.copy()
            flash.fill(
                (
                    255,
                    255,
                    255,
                    alpha
                ),
                special_flags=pygame.BLEND_RGBA_ADD
            )
            self._flash_cache[alpha] = flash

        screen.blit(
            flash,
            (
                int(self.x),
                int(self.y)
            )
        )

    def draw_death(self, screen):

        ratio = max(
            0.0,
            self.death_timer
            / self.death_duration
        )

        alpha = int(
            255 * ratio
        )

        scale = (
            1.0
            + (1.0 - ratio) * 0.25
        )

        new_width = max(
            1,
            int(self.width * scale)
        )

        new_height = max(
            1,
            int(self.height * scale)
        )

        # plain scale is much cheaper than smoothscale and the 25% growth
        # over a third of a second is not noticeable
        image = pygame.transform.scale(
            self.image,
            (
                new_width,
                new_height
            )
        )

        image.set_alpha(alpha)

        rect = image.get_rect(
            center=(
                int(
                    self.x
                    + self.width / 2
                ),
                int(
                    self.y
                    + self.height / 2
                )
            )
        )

        screen.blit(
            image,
            rect
        )

    def draw(self, screen):

        if self.state == "offscreen":
            return

        if self.state == "dead":

            self.draw_death(
                screen
            )

            return

        if (
            self.state == "attacking"
            or self.state == "leaving"
        ):

            self.draw_trail(
                screen
            )

            self.draw_engine_particles(
                screen
            )

        offset = 0

        if self.state == "waiting":

            offset = (
                math.sin(
                    self.animation_timer
                    * 0.10
                ) * 2
            )

        if self.hit_flash_timer > 0:

            self.draw_hit_flash(
                screen
            )

        else:

            if (
                self.state == "attacking"
                and self.enemy_type == "fast"
            ):

                # snap to 6 degrees so rotated copies can be reused
                angle = int(round(self.rotation_angle / 6.0)) * 6
                rotate_key = (id(self.image), angle)

                rotated = _ROTATE_CACHE.get(rotate_key)

                if rotated is None:
                    if len(_ROTATE_CACHE) > 200:
                        _ROTATE_CACHE.clear()
                    rotated = pygame.transform.rotate(self.image, angle)
                    _ROTATE_CACHE[rotate_key] = rotated

                rect = rotated.get_rect(
                    center=(
                        int(
                            self.x
                            + self.width / 2
                        ),
                        int(
                            self.y
                            + self.height / 2
                        )
                    )
                )

                screen.blit(
                    rotated,
                    rect
                )

            else:

                screen.blit(
                    self.image,
                    (
                        int(self.x),
                        int(
                            self.y
                            + offset
                        )
                    )
                )

        self.draw_health_bar(
            screen
        )

    def get_center(self):

        return (
            self.x + self.width / 2,
            self.y + self.height / 2
        )