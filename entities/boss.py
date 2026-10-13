import pygame
import math
import random

# Journal (notebook) theme shared with the menu / leaderboard / profile screens
try:
    from screens.login import INK, INK_SOFT, ERROR, OUTLINE, PAPER, hand_font
except Exception:
    INK = (60, 44, 40)
    INK_SOFT = (120, 100, 90)
    ERROR = (200, 50, 60)
    OUTLINE = (60, 44, 40)
    PAPER = (250, 243, 225)

    def hand_font(size, bold=False):
        return pygame.font.SysFont("Arial", size, bold=bold)


PAPER_SHADOW = (60, 40, 36)
PAPER_TRACK = (225, 214, 190)

# ---------------------------------------------------------------------
# Effect surfaces are built once and reused. Previously the boss created
# 20+ alpha Surfaces every frame (aura, shield, eyes, engines, missile
# trails) plus one huge screen-sized surface per shockwave.
# ---------------------------------------------------------------------

_FX_CACHE = {}


def _fx(key, builder):
    surface = _FX_CACHE.get(key)

    if surface is None:
        if len(_FX_CACHE) > 600:
            _FX_CACHE.clear()
        surface = builder()
        _FX_CACHE[key] = surface

    return surface


class Boss:

    # =========================================================
    # INITIALIZE
    # =========================================================

    def __init__(
        self,
        screen_width,
        screen_height,
        wave=1
    ):

        self.screen_width = screen_width
        self.screen_height = screen_height

        # WAVE
        self.wave = max(1, wave)

        # SIZE
        self.width = 300
        self.height = 190

        # POSITION
        self.x = (
            screen_width // 2
            - self.width // 2
        )

        self.y = -self.height

        self.target_y = 55

        self.direction = 1

        # MOVEMENT
        self.base_speed = 2.5

        self.speed = self.base_speed

        self.timer = 0
        self.animation_timer = 0
        self.float_offset = 0

        # HEALTH
        self.base_health = 100

        self.max_health = self.calculate_max_health()

        self.health = self.max_health

        self.displayed_health = self.max_health

        self.alive = True

        # PHASE
        self.phase = 1

        self.overdrive = False

        # ANIMATION
        self.bob_amount = 5

        self.engine_timer = 0

        # HIT EFFECT
        self.hit_flash_timer = 0

        self.hit_flash_duration = 7

        # SCREEN SHAKE
        self.shake_intensity = 0

        # RANDOM
        self._crack_rng = random.Random(1337)

        self.attack_rng = random.Random()

        self._crack_pattern = (
            self._build_crack_pattern()
        )

        # SKILL SYSTEM
        self.skill_timer = 0

        self.current_skill = None

        self.skill_duration = 0

        self.skill_cooldown = self.get_skill_cooldown()

        self.skill_delay = 8

        self.last_skill = None

        self.combo_ready = False

        # SHIELD
        self.shield_max = (
            35
            + self.wave * 5
        )

        self.shield = 0

        self.shield_active = False

        self.shield_timer = 0

        self.shield_duration = (
            90
            - min(
                30,
                self.wave * 2
            )
        )

        self.shield_cooldown = max(
            80,
            180
            - self.wave * 10
        )

        self.shield_regen_timer = (
            self.shield_cooldown
        )

        # PROJECTILES
        self.missiles = []

        self.eye_shots = []

        self.shockwaves = []

        self.energy_orbs = []

        # DASH
        self.dash_timer = 0

        self.dash_duration = 0

        self.dash_direction = 1

        # EYE TRACKING
        self.eye_target_x = (
            self.screen_width // 2
        )

        self.eye_target_y = (
            self.screen_height // 2
        )

        self.eye_angle_left = 0

        self.eye_angle_right = 0

        self.eye_lerp_speed = 0.28

        # STUN/SHOCK
        self.stun_duration = (
            30
            + self.wave * 2
        )

        self.shock_radius = 65

        # DAMAGE
        self.missile_damage = (
            9
            + self.wave * 2
        )

        self.eye_damage = (
            7
            + self.wave
        )

        self.shockwave_damage = (
            11
            + self.wave * 2
        )

        self.orb_damage = (
            8
            + self.wave
        )

        self.dash_damage = (
            16
            + self.wave * 2
        )

        # RENDER CACHES (per boss)
        self._shock_layer = None
        self._crack_surf = None
        self._scale_cache = {}
        self._flash_cache = {}

        # LOAD IMAGE
        try:

            self.image = pygame.image.load(
                "assets/images/boss.png"
            ).convert_alpha()

            self.image = (
                pygame.transform.smoothscale(
                    self.image,
                    (
                        self.width,
                        self.height
                    )
                )
            )

        except Exception as error:

            print(
                "Could not load boss image:",
                error
            )

            self.image = pygame.Surface(
                (
                    self.width,
                    self.height
                ),
                pygame.SRCALPHA
            )

            self.create_fallback_boss()

    # =========================================================
    # WAVE HEALTH
    # =========================================================

    def calculate_max_health(self):

        wave = max(
            1,
            self.wave
        )

        return int(
            100
            + (wave - 1) * 50
            + ((wave - 1) ** 2) * 6
        )

    # =========================================================
    # SET WAVE
    # =========================================================

    def set_wave(self, wave):

        self.wave = max(
            1,
            int(wave)
        )

        self.max_health = (
            self.calculate_max_health()
        )

        self.health = self.max_health

        self.displayed_health = (
            self.max_health
        )

        self.alive = True

        self.phase = 1

        self.overdrive = False

        self.skill_timer = 0

        self.current_skill = None

        self.skill_duration = 0

        self.skill_delay = 8

        self.last_skill = None

        self.combo_ready = False

        self.missiles.clear()
        self.eye_shots.clear()
        self.shockwaves.clear()
        self.energy_orbs.clear()

        self.shield_max = (
            35
            + self.wave * 5
        )

        self.shield = 0

        self.shield_active = False

        self.shield_regen_timer = (
            self.shield_cooldown
        )

        self.dash_duration = 0
        self.dash_timer = 0

        self.hit_flash_timer = 0
        self.shake_intensity = 0

    # =========================================================
    # FALLBACK BOSS
    # =========================================================

    def create_fallback_boss(self):
        w = self.width
        h = self.height
        surface = self.image
        dark = (18, 12, 35)
        dark2 = (30, 18, 55)
        purple = (105, 35, 180)
        purple2 = (145, 45, 220)
        blue = (40, 150, 255)
        blue2 = (80, 210, 255)
        red = (255, 45, 55)
        metal = (75, 78, 100)
        metal2 = (120, 125, 150)

        pygame.draw.polygon(surface, dark, [(w//2,5),(w-35,45),(w-5,85),(w-40,125),(w-75,115),(w-105,h-5),(w//2+35,h-25),(w//2,h-10),(w//2-35,h-25),(105,h-5),(75,115),(40,125),(5,85),(35,45)])
        pygame.draw.polygon(surface, purple, [(w//2,15),(w-65,60),(w-30,90),(w-80,105),(w-110,145),(w//2+25,125),(w//2,145),(w//2-25,125),(110,145),(80,105),(30,90),(65,60)])
        pygame.draw.polygon(surface, dark2, [(w//2,30),(w-90,70),(w-60,92),(w-105,110),(w//2+22,100),(w//2,118),(w//2-22,100),(105,110),(60,92),(90,70)])
        pygame.draw.polygon(surface, purple2, [(78,65),(5,105),(25,135),(90,115),(120,85)])
        pygame.draw.polygon(surface, purple2, [(w-78,65),(w-5,105),(w-25,135),(w-90,115),(w-120,85)])
        pygame.draw.line(surface, blue,(20,105),(80,90),4)
        pygame.draw.line(surface, blue,(w-20,105),(w-80,90),4)
        pygame.draw.polygon(surface, metal, [(w//2,25),(w//2+38,65),(w//2+28,112),(w//2,135),(w//2-28,112),(w//2-38,65)])
        pygame.draw.polygon(surface, dark, [(w//2,35),(w//2+24,68),(w//2+18,100),(w//2,115),(w//2-18,100),(w//2-24,68)])
        pygame.draw.polygon(surface, blue, [(w//2,48),(w//2+13,72),(w//2+9,96),(w//2,105),(w//2-9,96),(w//2-13,72)])
        pygame.draw.polygon(surface, blue2, [(w//2,56),(w//2+7,73),(w//2+5,89),(w//2,96),(w//2-5,89),(w//2-7,73)])
        pygame.draw.ellipse(surface, red,(82,72,38,22))
        pygame.draw.ellipse(surface, red,(w-120,72,38,22))
        pygame.draw.circle(surface,(255,230,230),(101,83),6)
        pygame.draw.circle(surface,(255,230,230),(w-101,83),6)
        pygame.draw.polygon(surface, metal, [(50,105),(75,98),(92,115),(75,130),(45,122)])
        pygame.draw.polygon(surface, metal, [(w-50,105),(w-75,98),(w-92,115),(w-75,130),(w-45,122)])
        pygame.draw.rect(surface,red,(60,110,20,5))
        pygame.draw.rect(surface,red,(w-80,110,20,5))
        pygame.draw.polygon(surface, dark2, [(105,145),(145,130),(w//2,155),(w-145,130),(w-105,145),(w-125,h-10),(w//2,h-30),(125,h-10)])
        pygame.draw.polygon(surface, metal, [(110,145),(140,140),(155,h-15),(125,h-5)])
        pygame.draw.polygon(surface, metal, [(w-110,145),(w-140,140),(w-155,h-15),(w-125,h-5)])
        pygame.draw.polygon(surface, blue2, [(125,150),(145,150),(140,h-5),(130,h-5)])
        pygame.draw.polygon(surface, blue2, [(w-125,150),(w-145,150),(w-140,h-5),(w-130,h-5)])
        pygame.draw.line(surface, metal2,(w//2,10),(w//2,35),4)

    # =========================================================
    # CRACK PATTERN
    # =========================================================

    def _build_crack_pattern(self):
        cracks = []
        for _ in range(25):
            start_x = self._crack_rng.randint(35, self.width - 35)
            start_y = self._crack_rng.randint(25, self.height - 35)
            points = [(start_x, start_y)]
            x, y = start_x, start_y
            segments = self._crack_rng.randint(2, 5)
            for _ in range(segments):
                x += self._crack_rng.randint(-20, 20)
                y += self._crack_rng.randint(6, 18)
                points.append((x,y))
            reveal_at = self._crack_rng.uniform(0.15, 0.48)
            cracks.append({
                "points": points,
                "reveal_at": reveal_at,
                "flicker_phase": self._crack_rng.uniform(0, math.tau)
            })
        return cracks

    # =========================================================
    # PHASE
    # =========================================================

    def update_phase(self):
        ratio = self.health / max(1, self.max_health)
        previous_phase = self.phase
        if ratio <= 0.25:
            self.phase = 3
        elif ratio <= 0.50:
            self.phase = 2
        else:
            self.phase = 1
        self.overdrive = (self.phase == 3)
        if self.phase > previous_phase:
            self._trigger_phase_transition()
            self.shield = min(self.shield_max, self.shield + 20)
            self.shield_active = True
            self.shield_timer = 90
            self.skill_timer = 0
            self.current_skill = None
            self.combo_ready = False

    def _trigger_phase_transition(self):
        self.shake_intensity = min(22, self.shake_intensity + 16)
        self.missiles.clear()
        self.eye_shots.clear()
        self.energy_orbs.clear()
        self.shockwaves.clear()

    # =========================================================
    # STATS
    # =========================================================

    def get_movement_speed(self):
        speed = 2.6 + (self.wave - 1) * 0.32
        if self.phase == 2:
            speed += 1.5
        elif self.phase == 3:
            speed += 2.8
        return min(9.2, speed)

    def get_skill_cooldown(self):
        cooldown = 60 - self.wave * 4
        if self.phase == 2:
            cooldown -= 16
        elif self.phase == 3:
            cooldown -= 24
        return max(14, cooldown)

    def consume_shake(self):
        if self.shake_intensity <= 0: return 0,0
        dx = random.uniform(-1,1)*self.shake_intensity
        dy = random.uniform(-1,1)*self.shake_intensity
        return dx,dy

    # =========================================================
    # ANGLE HELPERS
    # =========================================================

    def _lerp_angle(self, current, target, speed):
        diff = target - current
        while diff > math.pi: diff -= math.tau
        while diff < -math.pi: diff += math.tau
        new = current + diff * speed
        while new > math.pi: new -= math.tau
        while new < -math.pi: new += math.tau
        return new

    def _predict_target(self, player_rect, speed, delay):
        if player_rect is None:
            return self.screen_width//2, self.screen_height//2
        px, py = player_rect.centerx, player_rect.centery
        vx, vy = 0.0, 0.0
        if hasattr(player_rect, 'vx'):
            vx = getattr(player_rect, 'vx')
        if hasattr(player_rect, 'vy'):
            vy = getattr(player_rect, 'vy')
        pred_x = px + vx * delay * 60.0
        pred_y = py + vy * delay * 60.0
        return pred_x, pred_y

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, player_rect=None):
        if not self.alive: return
        self.timer += 1
        self.animation_timer += 1
        self.engine_timer += 1

        if self.displayed_health > self.health:
            self.displayed_health -= 0.95
            if self.displayed_health < self.health:
                self.displayed_health = self.health

        if self.shake_intensity > 0:
            self.shake_intensity *= 0.87
            if self.shake_intensity < 0.3:
                self.shake_intensity = 0

        if self.y < self.target_y:
            self.y += 4.0
            if self.y >= self.target_y:
                self.y = self.target_y
            self.update_eyes(player_rect)
            return

        self.update_phase()
        movement_speed = self.get_movement_speed()

        if self.dash_duration > 0:
            self.dash_duration -= 1
            if player_rect is not None and self.dash_duration > 5:
                cx = self.x + self.width/2
                px = player_rect.centerx
                if px > cx + 10:
                    self.dash_direction = 1
                elif px < cx - 10:
                    self.dash_direction = -1
            self.x += self.dash_direction * (11 + self.wave * 0.9 + self.phase * 0.7)
            if self.dash_duration <= 0:
                self.dash_timer = max(14, 65 - self.wave*4 - self.phase*10)
        else:
            self.x += self.direction * movement_speed

        if self.x <= 12:
            self.x = 12
            self.direction = 1
        elif self.x + self.width >= self.screen_width - 12:
            self.x = self.screen_width - self.width - 12
            self.direction = -1

        float_speed = 0.05 + self.phase * 0.024 + self.wave * 0.002
        self.float_offset = math.sin(self.animation_timer * float_speed) * self.bob_amount
        self.x += math.sin(self.animation_timer * 0.03) * (0.7 + self.wave * 0.035)

        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

        self.update_eyes(player_rect)
        self.update_shield()
        self.update_skills(player_rect)
        self.update_missiles(player_rect)
        self.update_eye_shots(player_rect)
        self.update_shockwaves()
        self.update_energy_orbs()

    # =========================================================
    # EYES
    # =========================================================

    def update_eyes(self, player_rect):
        if player_rect is None:
            base_x = self.screen_width//2
            base_y = self.screen_height//2
            self.eye_target_x = base_x + math.sin(self.animation_timer*0.016)*150
            self.eye_target_y = base_y + math.cos(self.animation_timer*0.013)*70
        else:
            px, py = player_rect.centerx, player_rect.centery
            self.eye_target_x = px
            self.eye_target_y = py

        eye_y = self.y + self.float_offset + 82
        left_eye_x = self.x + 101
        right_eye_x = self.x + self.width - 101

        target_left = math.atan2(self.eye_target_y - eye_y, self.eye_target_x - left_eye_x)
        target_right = math.atan2(self.eye_target_y - eye_y, self.eye_target_x - right_eye_x)

        lerp = self.eye_lerp_speed + self.phase * 0.035
        if self.overdrive:
            lerp = 0.38
        elif self.phase == 2:
            lerp = 0.32

        self.eye_angle_left = self._lerp_angle(self.eye_angle_left, target_left, lerp)
        self.eye_angle_right = self._lerp_angle(self.eye_angle_right, target_right, lerp)

    # =========================================================
    # SHIELD
    # =========================================================

    def update_shield(self):
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False
        else:
            self.shield_regen_timer -= 1
            if self.shield_regen_timer <= 0 and self.phase >= 2:
                self.shield = self.shield_max
                self.shield_active = True
                self.shield_timer = self.shield_duration
                cd = self.shield_cooldown - self.phase*30 - self.wave*4
                self.shield_regen_timer = max(65, cd)
                self.shake_intensity = min(12, self.shake_intensity + 5)

    # =========================================================
    # SKILLS
    # =========================================================

    def update_skills(self, player_rect=None):
        if self.current_skill is not None:
            return

        self.skill_timer += 1
        self.skill_cooldown = self.get_skill_cooldown()

        if self.skill_timer < self.skill_cooldown:
            return

        self.skill_timer = 0

        # Build skill pool based on phase
        pool = []
        weights = []

        # Core abilities - always available
        pool.extend(["eye_shot", "missiles", "shockwave", "orb_barrage", "dash"])
        weights.extend([2.2, 2.0, 1.6, 1.8, 1.4])

        if self.phase >= 2:
            pool.extend(["double_shock", "eye_barrage"])
            weights.extend([1.6, 2.0])

        if self.phase == 3:
            pool.extend(["mega_orb", "rapid_barrage"])
            weights.extend([1.4, 2.2])

        # Avoid spamming the exact same skill twice in a row
        if self.last_skill in pool:
            try:
                idx = pool.index(self.last_skill)
                weights[idx] *= 0.4
            except ValueError:
                pass

        total = sum(weights)
        if total <= 0:
            skill = pool[0] if pool else "eye_shot"
        else:
            r = self.attack_rng.uniform(0, total)
            s = 0
            skill = pool[-1]
            for p, w in zip(pool, weights):
                s += w
                if r <= s:
                    skill = p
                    break

        self.start_skill(skill, player_rect)

        if self.overdrive:
            if self.attack_rng.random() < 0.55:
                self.skill_timer = -4
        elif self.phase >= 2:
            if self.attack_rng.random() < 0.38:
                self.skill_timer = -3
        else:
            if self.attack_rng.random() < 0.2:
                self.skill_timer = -2

    def start_skill(self, skill, player_rect=None):
        self.current_skill = skill
        self.last_skill = skill

        if skill == "eye_shot":
            self.fire_eye_shot(player_rect)
            self.skill_duration = 14

        elif skill == "eye_barrage":
            count = 5 + min(5, self.wave//2) + self.phase
            for i in range(count):
                delay = i * 4
                eye_x = self.x + self.width/2
                eye_y = self.y + self.float_offset + 82
                self.eye_shots.append({
                    "x": eye_x,
                    "y": eye_y,
                    "speed": 6.2 + self.phase*0.8 + self.wave*0.06,
                    "angle": math.pi/2,
                    "life": 240,
                    "damage": self.eye_damage,
                    "turn": 0.07 + self.phase*0.012 + self.wave*0.001,
                    "delay": delay,
                    "homing": True,
                    "predict": True
                })
            self.skill_duration = 36 + count*2

        elif skill == "missiles":
            count = 3 + self.phase + min(4, self.wave//2)
            for i in range(count):
                offset = (i - (count-1)/2) * 40
                self.missiles.append({
                    "x": self.x + self.width/2 + offset,
                    "y": self.y + self.height - 28,
                    "speed": 3.8 + self.phase*0.7 + self.wave*0.12,
                    "angle": math.pi/2,
                    "life": 360,
                    "damage": self.missile_damage,
                    "turn": 0.058 + self.phase*0.016,
                    "accel": 0.018
                })
            self.skill_duration = 30

        elif skill == "shockwave":
            self.create_shockwave()
            self.skill_duration = 20

        elif skill == "double_shock":
            self.create_shockwave(extra_speed=1.8)
            self.create_shockwave(extra_speed=1.0, delay=5)
            self.skill_duration = 22

        elif skill == "orb_barrage":
            count = 10 + self.phase*3 + min(6, self.wave)
            self.fire_orb_barrage(count, spread=math.pi*0.95)
            self.skill_duration = 38

        elif skill == "mega_orb":
            count = 22
            self.fire_orb_barrage(count, spread=math.pi*1.65, speed_bonus=2.4)
            self.skill_duration = 50

        elif skill == "rapid_barrage":
            for _ in range(2):
                self.fire_eye_shot(player_rect)
            count = 7 + self.phase*2
            self.fire_orb_barrage(count, spread=math.pi*0.85, speed_bonus=0.9)
            self.skill_duration = 24

        elif skill == "dash":
            if player_rect is not None:
                cx = self.x + self.width/2
                px = player_rect.centerx
                if px >= cx:
                    self.dash_direction = 1
                else:
                    self.dash_direction = -1
            else:
                self.dash_direction = self.attack_rng.choice([-1,1])
            self.dash_duration = 22 + min(10, self.wave) + self.phase
            self.shake_intensity = min(17, self.shake_intensity + 8)
            self.skill_duration = self.dash_duration + 3

        else:
            self.fire_eye_shot(player_rect)
            self.skill_duration = 14

    # =========================================================
    # ATTACKS
    # =========================================================

    def fire_eye_shot(self, player_rect=None):
        eye_x = self.x + self.width/2
        eye_y = self.y + self.float_offset + 82
        if player_rect is not None:
            px, py = player_rect.centerx, player_rect.centery
            dx, dy = px-eye_x, py-eye_y
            angle = math.atan2(dy,dx)
        else:
            angle = math.pi/2
        self.eye_shots.append({
            "x": eye_x,
            "y": eye_y,
            "speed": 6.6 + self.phase*0.9 + self.wave*0.07,
            "angle": angle,
            "life": 260,
            "damage": self.eye_damage,
            "turn": 0.08 + self.phase*0.015 + self.wave*0.001,
            "delay": 0,
            "homing": True,
            "predict": True
        })

    def create_shockwave(self, extra_speed=0, delay=0):
        self.shockwaves.append({
            "x": self.x + self.width/2,
            "y": self.y + self.height/2,
            "radius": 25,
            "max_radius": max(self.screen_width,self.screen_height)*1.25,
            "speed": 8.5 + self.phase*2.0 + extra_speed + self.wave*0.22,
            "damage": self.shockwave_damage,
            "hit": False,
            "stun": self.stun_duration,
            "delay": delay
        })
        self.shake_intensity = min(19, self.shake_intensity + 9)

    def fire_orb_barrage(self, count, spread=math.pi, speed_bonus=0):
        center = math.pi/2
        if count <= 1:
            angles=[center]
        else:
            start = center - spread/2
            step = spread/(count-1)
            angles = [start + step*i for i in range(count)]
        cx, cy = self.x+self.width/2, self.y+self.height/2
        for angle in angles:
            speed = 4.0 + self.phase*0.8 + self.wave*0.1 + speed_bonus
            self.energy_orbs.append({
                "x": cx,
                "y": cy,
                "vx": math.cos(angle)*speed,
                "vy": math.sin(angle)*speed,
                "radius": 7,
                "life": 290,
                "damage": self.orb_damage
            })

    # =========================================================
    # PROJECTILE UPDATES
    # =========================================================

    def update_eye_shots(self, player_rect=None):
        for shot in self.eye_shots[:]:
            if shot["delay"] > 0:
                shot["delay"] -= 1
                continue
            shot["life"] -= 1
            if shot["life"] <= 0:
                if shot in self.eye_shots:
                    self.eye_shots.remove(shot)
                continue
            if shot.get("homing", True) and player_rect is not None:
                if shot.get("predict", True):
                    px, py = self._predict_target(player_rect, shot["speed"], 0.08)
                else:
                    px, py = player_rect.centerx, player_rect.centery
                dx, dy = px-shot["x"], py-shot["y"]
                target_angle = math.atan2(dy,dx)
                diff = target_angle - shot["angle"]
                while diff > math.pi: diff -= math.tau
                while diff < -math.pi: diff += math.tau
                turn = shot["turn"]
                if self.overdrive:
                    turn *= 1.35
                diff = max(-turn, min(turn, diff))
                shot["angle"] += diff
            shot["x"] += math.cos(shot["angle"])*shot["speed"]
            shot["y"] += math.sin(shot["angle"])*shot["speed"]
            if shot["x"] < -70 or shot["x"] > self.screen_width+70 or shot["y"] < -70 or shot["y"] > self.screen_height+70:
                if shot in self.eye_shots:
                    self.eye_shots.remove(shot)

    def update_missiles(self, player_rect=None):
        for m in self.missiles[:]:
            m["life"] -= 1
            if m["life"] <= 0:
                if m in self.missiles:
                    self.missiles.remove(m)
                continue
            if player_rect is not None:
                px, py = self._predict_target(player_rect, m["speed"], 0.1)
                dx,dy = px-m["x"], py-m["y"]
                target = math.atan2(dy,dx)
                diff = target - m["angle"]
                while diff > math.pi: diff -= math.tau
                while diff < -math.pi: diff += math.tau
                turn = m["turn"]
                if self.overdrive:
                    turn *= 1.3
                diff = max(-turn,min(turn,diff))
                m["angle"] += diff
            if m.get("accel",0):
                m["speed"] = min(m["speed"] + m["accel"], 10.0 + self.phase*0.5)
            m["x"] += math.cos(m["angle"])*m["speed"]
            m["y"] += math.sin(m["angle"])*m["speed"]
            if m["x"] < -80 or m["x"] > self.screen_width+80 or m["y"] < -80 or m["y"] > self.screen_height+80:
                if m in self.missiles:
                    self.missiles.remove(m)

    def update_shockwaves(self):
        for w in self.shockwaves[:]:
            if w["delay"] > 0:
                w["delay"] -= 1
                continue
            w["radius"] += w["speed"]
            if w["radius"] >= w["max_radius"]:
                if w in self.shockwaves:
                    self.shockwaves.remove(w)

    def update_energy_orbs(self):
        for orb in self.energy_orbs[:]:
            orb["life"] -= 1
            if orb["life"] <= 0:
                if orb in self.energy_orbs:
                    self.energy_orbs.remove(orb)
                continue
            orb["x"] += orb["vx"]
            orb["y"] += orb["vy"]
            if orb["x"] < -50 or orb["x"] > self.screen_width+50 or orb["y"] < -50 or orb["y"] > self.screen_height+50:
                if orb in self.energy_orbs:
                    self.energy_orbs.remove(orb)

    # =========================================================
    # DAMAGE / COLLISION
    # =========================================================

    def take_damage(self, damage):
        if not self.alive: return
        damage = max(0,damage)
        if self.shield_active and self.shield > 0:
            absorbed = min(self.shield, damage)
            self.shield -= absorbed
            damage -= absorbed
            self.hit_flash_timer = 4
            self.shake_intensity = min(10, self.shake_intensity + 1.8)
            if self.shield <= 0:
                self.shield = 0
                self.shield_active = False
                self.shield_regen_timer = self.shield_cooldown
        if damage > 0:
            self.health -= damage
            self.hit_flash_timer = self.hit_flash_duration
            self.shake_intensity = min(19, self.shake_intensity + 3.2)
        self.update_phase()
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.missiles.clear()
            self.eye_shots.clear()
            self.shockwaves.clear()
            self.energy_orbs.clear()

    def get_rect(self):
        return pygame.Rect(
            int(self.x + 30),
            int(self.y + self.float_offset + 20),
            self.width - 60,
            self.height - 45
        )

    def check_skill_collision(self, player_rect):
        if not self.alive: return 0
        dmg = 0
        for m in self.missiles[:]:
            r = pygame.Rect(int(m["x"]-10), int(m["y"]-10), 20,20)
            if r.colliderect(player_rect):
                dmg += m["damage"]
                self.create_explosion(m["x"], m["y"])
                if m in self.missiles:
                    self.missiles.remove(m)
        for s in self.eye_shots[:]:
            if s["delay"] > 0: continue
            r = pygame.Rect(int(s["x"]-9), int(s["y"]-9), 18,18)
            if r.colliderect(player_rect):
                dmg += s["damage"]
                self.create_explosion(s["x"], s["y"])
                if s in self.eye_shots:
                    self.eye_shots.remove(s)
        for w in self.shockwaves[:]:
            if w["delay"] > 0: continue
            dist = math.hypot(player_rect.centerx-w["x"], player_rect.centery-w["y"])
            if abs(dist - w["radius"]) < 22:
                if not w["hit"]:
                    dmg += w["damage"]
                    w["hit"] = True
                    self.shake_intensity = min(17, self.shake_intensity + 6.5)
        for orb in self.energy_orbs[:]:
            r = pygame.Rect(int(orb["x"]-orb["radius"]), int(orb["y"]-orb["radius"]), orb["radius"]*2, orb["radius"]*2)
            if r.colliderect(player_rect):
                dmg += orb["damage"]
                if orb in self.energy_orbs:
                    self.energy_orbs.remove(orb)
        if self.dash_duration > 0:
            dr = pygame.Rect(int(self.x+20), int(self.y+self.float_offset+30), self.width-40, self.height-60)
            if dr.colliderect(player_rect):
                dmg += self.dash_damage
                self.shake_intensity = min(21, self.shake_intensity + 9)
        return dmg

    def create_explosion(self, x,y):
        self.shake_intensity = min(15, self.shake_intensity + 4)

    # =========================================================
    # DRAW
    # =========================================================

    def get_phase_color(self):
        if self.phase==1: return (120,50,220)
        if self.phase==2: return (255,100,30)
        return (255,40,45)

    def draw_phase_aura(self, screen, draw_x, draw_y):
        color = self.get_phase_color()
        pulse = (math.sin(self.animation_timer*(0.052 + self.phase*0.038))+1)/2
        base = 98 + self.phase*24
        radius = int(base + pulse*(12 + self.phase*7))
        cx, cy = draw_x+self.width//2, draw_y+self.height//2
        alpha = min(255, 26 + self.phase*18 + int(pulse*22))
        alpha = alpha // 6 * 6

        def build():
            glow = pygame.Surface((radius*2+30, radius*2+30), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, alpha), (radius+15, radius+15), radius, width=5)
            return glow

        glow = _fx(("aura", radius, color, alpha), build)
        screen.blit(glow, glow.get_rect(center=(cx,cy)))

    def draw_shield(self, screen, draw_x, draw_y):
        if not self.shield_active: return
        cx, cy = draw_x+self.width//2, draw_y+self.height//2
        pulse = (math.sin(self.animation_timer*0.15)+1)/2
        radius = int(122 + pulse*8)
        alpha = int(52 + pulse*52) // 8 * 8

        def build():
            s = pygame.Surface((radius*2+26, radius*2+26), pygame.SRCALPHA)
            pygame.draw.circle(s, (60,190,255,alpha), (radius+13,radius+13), radius, 4)
            return s

        ring = _fx(("shield", radius, alpha), build)
        screen.blit(ring, ring.get_rect(center=(cx,cy)))

        # rotating segments are drawn straight onto the screen (no Surface)
        seg = 10
        for i in range(seg):
            start = self.animation_timer*0.028 + i*math.tau/seg
            end = start + 0.3
            pts=[]
            for j in range(9):
                ang = start + (end-start)*j/8
                pts.append((cx + math.cos(ang)*radius, cy + math.sin(ang)*radius))
            pygame.draw.lines(screen, (115,235,255), False, pts, 2)

    def draw_eyes(self, screen, draw_x, draw_y):
        left_x = draw_x+101
        right_x = draw_x+self.width-101
        eye_y = draw_y+82

        def build_glow():
            g = pygame.Surface((16,16), pygame.SRCALPHA)
            pygame.draw.circle(g,(255,80,80,95),(8,8),6)
            return g

        glow = _fx(("eyeglow",), build_glow)

        for eye_x, angle in ((left_x,self.eye_angle_left),(right_x,self.eye_angle_right)):
            pygame.draw.ellipse(screen,(95,10,30),(eye_x-21, eye_y-12, 42,24))
            pygame.draw.ellipse(screen,(70,8,25),(eye_x-19, eye_y-10, 38,20))
            dist = 8
            px = eye_x + math.cos(angle)*dist
            py = eye_y + math.sin(angle)*dist
            pygame.draw.circle(screen,(255,40,60),(int(px),int(py)),8)
            pygame.draw.circle(screen,(255,160,160),(int(px),int(py)),5)
            pygame.draw.circle(screen,(255,255,255),(int(px-1),int(py-1)),2)
            screen.blit(glow, (int(px-8), int(py-8)))

    def draw_missiles(self, screen):
        for m in self.missiles:
            x,y = int(m["x"]), int(m["y"])
            ang = m["angle"]
            for i in range(6):
                tx = x - math.cos(ang)*i*6
                ty = y - math.sin(ang)*i*6
                r = max(2,6-i)
                a = max(40, 210 - i*32)

                def build(r=r, a=a):
                    s = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
                    pygame.draw.circle(s,(255,95,35,a),(r,r),r)
                    return s

                s = _fx(("mtrail", r, a), build)
                screen.blit(s,(int(tx-r),int(ty-r)))
            pygame.draw.circle(screen,(235,235,240),(x,y),7)
            pygame.draw.circle(screen,(255,55,55),(x,y),4)

    def draw_eye_shots(self, screen):
        for s in self.eye_shots:
            if s["delay"] > 0: continue
            x,y = int(s["x"]), int(s["y"])
            pulse = (math.sin(self.animation_timer*0.32)+1)/2
            r1 = 10 + pulse*2
            r2 = 6 + pulse*1
            pygame.draw.circle(screen,(255,35,55),(x,y),int(r1))
            pygame.draw.circle(screen,(255,150,150),(x,y),int(r2))
            pygame.draw.circle(screen,(255,255,255),(x-2,y-2),2)

    def draw_shockwaves(self, screen):
        active = [w for w in self.shockwaves if w["delay"] <= 0 and int(w["radius"]) > 0]
        if not active:
            return

        # one reusable screen-sized layer for every ring (the old code made a
        # new (radius*2)^2 alpha Surface per shockwave per frame, which gets
        # enormous as the ring expands)
        size = (self.screen_width, self.screen_height)
        layer = self._shock_layer

        if layer is None or layer.get_size() != size:
            layer = pygame.Surface(size, pygame.SRCALPHA)
            self._shock_layer = layer

        layer.fill((0, 0, 0, 0))

        for w in active:
            r = int(w["radius"])
            alpha = max(25, 205 - r//2.4)
            center = (int(w["x"]), int(w["y"]))
            pygame.draw.circle(layer,(255,75,40,min(255,int(alpha))),center,r,8)
            pygame.draw.circle(layer,(255,190,80,min(255,int(alpha*0.75))),center,max(1,r-13),3)

        screen.blit(layer, (0, 0))

    def draw_energy_orbs(self, screen):
        for orb in self.energy_orbs:
            x,y = int(orb["x"]), int(orb["y"])
            r = orb["radius"]
            pulse = (math.sin(self.animation_timer*0.26)+1)/2
            pygame.draw.circle(screen,(50,110,255),(x,y),r+7)
            pygame.draw.circle(screen,(90,200,255),(x,y),r+2)
            pygame.draw.circle(screen,(155,240,255),(x,y),int(r + pulse*1.2))
            pygame.draw.circle(screen,(255,255,255),(x-2,y-2),2)

    def draw_damage_cracks(self, screen, draw_x, draw_y):
        ratio = self.health/max(1,self.max_health)
        if ratio > 0.56: return

        surf = self._crack_surf
        if surf is None:
            surf = pygame.Surface((self.width,self.height), pygame.SRCALPHA)
            self._crack_surf = surf
        surf.fill((0, 0, 0, 0))

        base = (255,200,90) if self.phase < 3 else (255,60,50)
        for c in self._crack_pattern:
            if ratio > c["reveal_at"]: continue
            sev = 1 - max(0,min(1, ratio/max(0.001,c["reveal_at"])))
            flick = (math.sin(self.animation_timer*0.15 + c["flicker_phase"])+1)/2
            alpha = int(98 + sev*135 + flick*42)
            w = 1 + int(sev*2)
            pygame.draw.lines(surf, (*base, min(255,alpha)), False, c["points"], w)
        screen.blit(surf,(draw_x,draw_y))

    def draw_engine_glow(self, screen, draw_x, draw_y):
        pulse = (math.sin(self.engine_timer*0.17)+1)/2
        boost = (self.phase-1)*22
        for side in ("left","right"):
            for s in range(3):
                alpha = int(42 + pulse*47 - s*9 + boost)
                alpha = max(0, min(255, alpha)) // 8 * 8

                def build(alpha=alpha):
                    g = pygame.Surface((66,76), pygame.SRCALPHA)
                    pygame.draw.polygon(g,(40,188,255,alpha), [(23,0),(43,0),(59,70),(33,54),(7,70)])
                    return g

                g = _fx(("engine", alpha), build)

                if side=="left":
                    pos=(draw_x+95 - s*5, draw_y+122)
                else:
                    pos=(draw_x+self.width-161 + s*5, draw_y+122)
                screen.blit(g,pos)

    def draw_health_bar(self, screen):
        # journal-style paper strip, matching the in-game HUD
        bar_w = min(690, self.screen_width-120)
        bar_h = 14
        strip = pygame.Rect(0, 0, bar_w + 24, 54)
        strip.midtop = (self.screen_width // 2, 8)

        pygame.draw.rect(screen, PAPER_SHADOW, strip.move(4, 5), border_radius=8)
        pygame.draw.rect(screen, PAPER, strip, border_radius=8)
        pygame.draw.rect(screen, OUTLINE, strip, 2, border_radius=8)

        font = getattr(self, "_bar_font", None)
        if font is None:
            font = hand_font(15, True)
            self._bar_font = font

        labels = {1: "Boss", 2: "Boss \u00b7 Enraged", 3: "Boss \u00b7 Final phase"}
        label = font.render(labels.get(self.phase, "Boss"), True, ERROR)
        screen.blit(label, (strip.x + 12, strip.y + 5))

        wave_text = font.render(f"Wave {self.wave}", True, INK_SOFT)
        screen.blit(wave_text, (strip.right - 12 - wave_text.get_width(), strip.y + 5))

        bx = strip.x + 12
        by = strip.y + 28
        track = pygame.Rect(bx, by, bar_w, bar_h)
        pygame.draw.rect(screen, PAPER_TRACK, track, border_radius=6)

        hr = max(0,min(1,self.health/max(1,self.max_health)))
        if self.phase==1: hc=(205,60,70)
        elif self.phase==2: hc=(225,110,40)
        else: hc=(190,30,50)

        dr = max(0,min(1,self.displayed_health/max(1,self.max_health)))
        lw = int(bar_w*dr)
        if lw>0:
            pygame.draw.rect(screen,(225,170,150),(bx,by,lw,bar_h),border_radius=min(6, max(1, lw//2)))
        hw = int(bar_w*hr)
        if hw>0:
            pygame.draw.rect(screen,hc,(bx,by,hw,bar_h),border_radius=min(6, max(1, hw//2)))

        if self.shield_active and self.shield>0:
            sr = self.shield/max(1,self.shield_max)
            sw = int(bar_w*sr)
            if sw>0:
                pygame.draw.rect(screen,(75,170,230),(bx,by+bar_h+3,sw,3),border_radius=2)

        pygame.draw.rect(screen, OUTLINE, track, 2, border_radius=6)

    def draw(self, screen):
        if not self.alive: return
        draw_x = int(self.x)
        draw_y = int(self.y + self.float_offset)
        self.draw_phase_aura(screen,draw_x,draw_y)
        self.draw_shockwaves(screen)
        self.draw_energy_orbs(screen)
        self.draw_engine_glow(screen,draw_x,draw_y)
        self.draw_shield(screen,draw_x,draw_y)
        img = self.image
        rx, ry = draw_x, draw_y
        if self.phase==3:
            pulse = (math.sin(self.animation_timer*0.15)+1)/2
            sc = 1.0 + pulse*0.032
            sw, sh = int(self.width*sc), int(self.height*sc)

            # only ~10 distinct pulse sizes, so smoothscale each one once
            img = self._scale_cache.get((sw, sh))
            if img is None:
                img = pygame.transform.smoothscale(self.image,(sw,sh))
                self._scale_cache[(sw, sh)] = img

            rx, ry = draw_x - (sw-self.width)//2, draw_y - (sh-self.height)//2

        if self.hit_flash_timer > 0:
            flash = self._flash_cache.get(img.get_size())
            if flash is None:
                flash = img.copy()
                flash.fill((255,80,80,0), special_flags=pygame.BLEND_RGB_ADD)
                self._flash_cache[img.get_size()] = flash
            screen.blit(flash,(rx,ry))
        else:
            screen.blit(img,(rx,ry))
        self.draw_eyes(screen,draw_x,draw_y)
        self.draw_damage_cracks(screen,draw_x,draw_y)
        self.draw_missiles(screen)
        self.draw_eye_shots(screen)
        self.draw_health_bar(screen)

    def post_update(self):
        if self.current_skill is None: return
        self.skill_duration -= 1
        if self.skill_duration <= 0:
            self.current_skill = None
            self.skill_timer = -self.skill_delay