import os
import math
import json
import random
import sys
import pygame

try:
    import theme as game_theme
except Exception:
    game_theme = None

try:
    from PIL import Image, ImageSequence
except Exception:
    Image = None
    ImageSequence = None

# --- CRASH WORKAROUND: STUB MISSING IMPORTS TO PREVENT TRACEBACKS ---
try:
    # If screens.profile exists but lacks 'get_font', inject it programmatically
    import screens.profile as profile_screen
    if not hasattr(profile_screen, 'get_font'):
        profile_screen.get_font = lambda name, size: pygame.font.SysFont("Arial", size, bold=True)
except Exception:
    # If the module isn't loaded yet, stub it in sys.modules so imports do not crash
    try:
        import types
        if 'screens.profile' in sys.modules:
            mod = sys.modules['screens.profile']
            if not hasattr(mod, 'get_font'):
                mod.get_font = lambda name, size: pygame.font.SysFont("Arial", size, bold=True)
    except Exception:
        pass

from entities.player import Player
from entities.button import MobileButtons
from entities.bullet import Bullet
from database import save_score, get_player

try:
    from profile import get_game_loadout, load_game_player_ship
except Exception:
    get_game_loadout = None
    load_game_player_ship = None

from settings import (
    PREFERENCES,
    DIFFICULTIES,
    WHITE,
    CYAN,
    RED,
    GOLD,
    BUTTON_IDLE,
    BUTTON_HOVER,
)


# ----------------------------------------------------------------------
# Journal (notebook) theme, shared with menu / leaderboard / profile
# ----------------------------------------------------------------------

try:
    from screens.login import (
        INK,
        INK_SOFT,
        ERROR,
        OUTLINE,
        PAPER,
        HIGHLIGHT,
        TAB_PINK,
        TAB_ORANGE,
        TAB_YELLOW,
        hand_font,
        put_text,
        alpha_rect,
        draw_tape,
        draw_background as journal_background,
    )
except Exception:
    journal_background = None
    INK = (60, 44, 40)
    INK_SOFT = (120, 100, 90)
    ERROR = (200, 50, 60)
    OUTLINE = (60, 44, 40)
    PAPER = (250, 243, 225)
    HIGHLIGHT = (255, 226, 140)
    TAB_PINK = (250, 170, 190)
    TAB_ORANGE = (250, 190, 120)
    TAB_YELLOW = (250, 225, 130)

    def hand_font(size, bold=False):
        return pygame.font.SysFont("Arial", size, bold=bold)

    def put_text(surface, fnt, value, color, pos, anchor="topleft"):
        image = fnt.render(str(value), True, color)
        rect = image.get_rect()
        setattr(rect, anchor, pos)
        surface.blit(image, rect)
        return rect

    def alpha_rect(surface, color, rect, radius=0):
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(layer, color, layer.get_rect(), border_radius=radius)
        surface.blit(layer, rect.topleft)

    def draw_tape(surface, pos, width=0, size=(70, 22)):
        return None

try:
    from screens.menu import get_player_rank as journal_rank
except Exception:
    journal_rank = None

try:
    from managers.ui_sounds import ui_sounds
except Exception:
    ui_sounds = None

GOLD_INK = (170, 110, 20)
GREEN_INK = (40, 130, 70)
BLUE_INK = (60, 100, 170)
PAPER_SHADOW = (60, 40, 36)
BUTTON_SHADOW = (150, 130, 100)
PAPER_RULE = (205, 196, 176)
PAPER_TRACK = (225, 214, 190)


# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------

USE_SPRITE_OVERRIDES = True

# Draw the same notebook-desk background as the menu / leaderboard / profile.
# Set to False to go back to the old animated space background.
USE_JOURNAL_BACKGROUND = True

# Hard cap on live particles so big fights can't tank the frame rate.
MAX_PARTICLES = 320

SHIP_COLOR_TINTS = {
    "ICE": (170, 225, 255),
    "CYAN": (110, 230, 255),
    "RED": (255, 100, 100),
    "GOLD": (255, 205, 80),
    "YELLOW": (255, 230, 90),
    "PURPLE": (195, 130, 255),
    "GREEN": (130, 255, 150),
    "PINK": (255, 140, 200),
    "ORANGE": (255, 150, 70),
    "WHITE": (255, 255, 255),
}

ENEMY_STATS = {
    "grunt": {"hp": 1, "score": 12, "scale": 1.00, "color": (110, 230, 120), "eye": (255, 255, 255)},
    "scout": {"hp": 1, "score": 25, "scale": 0.80, "color": (90, 200, 255), "eye": (255, 255, 120)},
    "weaver": {"hp": 2, "score": 30, "scale": 0.95, "color": (190, 110, 255), "eye": (255, 255, 255)},
    "diver": {"hp": 2, "score": 40, "scale": 0.95, "color": (255, 80, 100), "eye": (255, 240, 120)},
    "bomber": {"hp": 3, "score": 50, "scale": 1.10, "color": (255, 150, 50), "eye": (40, 20, 10)},
    "tank": {"hp": 5, "score": 75, "scale": 1.15, "color": (140, 155, 185), "eye": (255, 70, 70)},
    "boss": {"hp": 1, "score": 0, "scale": 1.00, "color": (225, 45, 65), "eye": (255, 230, 120)},
}

RARE_ENEMY_ACCENTS = {
    "grunt": (95, 255, 185),
    "scout": (80, 220, 255),
    "weaver": (190, 120, 255),
    "diver": (255, 75, 115),
    "bomber": (255, 165, 55),
    "tank": (180, 205, 235),
}

HUD_BG = (10, 4, 14, 226)
HUD_EDGE = (150, 34, 74)
HUD_DIM = (160, 126, 150)
NEON_WHITE = (245, 228, 240)

DESIGN_RED = (220, 48, 82)
DESIGN_PINK = (255, 105, 165)
DESIGN_PURPLE = (150, 70, 190)
DESIGN_GOLD = (245, 190, 82)
DESIGN_TEXT = (242, 232, 240)
DESIGN_MUTED = (170, 145, 165)
DESIGN_PANEL = (13, 5, 18)
DESIGN_PANEL_2 = (25, 8, 28)


class GameManager:

    # Values that count as "on" for the mobile / touch controls toggle.
    TOUCH_ON_VALUES = (True, 1, "1", "true", "on", "yes", "enabled")

    def __init__(self, screen, screen_width, screen_height, player_id, player_data=None):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.player_id = player_id
        self.player_data = dict(player_data) if isinstance(player_data, dict) else {}

        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.font = pygame.font.SysFont("Arial", 22, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.medium_font = pygame.font.SysFont("Arial", 28, bold=True)
        self.big_font = pygame.font.SysFont("Arial", 58, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 68, bold=True)
        self.hud_font = pygame.font.SysFont("Arial", 17, bold=True)

        # Journal-style fonts (same hand font as the menu screens)
        self.j_title = hand_font(40, True)
        self.j_banner = hand_font(48, True)
        self.j_big = hand_font(30, True)
        self.j_num = hand_font(28, True)
        self.j_button = hand_font(24, True)
        self.j_text = hand_font(19, True)
        self.j_sub = hand_font(17)
        self.j_small = hand_font(15, True)

        # Background (uses matching menu backgrounds if available)
        self.background = None
        self.background_frames = []
        self.background_frame_durations = []
        self.background_frame_index = 0
        self.background_frame_elapsed = 0
        self.background_is_gif = False
        self.background_cache = {}
        self.load_background()

        self.enemy_image = self.load_image("enemy.png")
        self.tank_image = self.load_image("enemy_tank.png")
        self.fast_image = self.load_image("enemy_fast.png")
        self.boss_image = self.load_image("boss.png")
        self.heart_image = self.load_image("heart.png")
        self.bullet_image = self.load_image("bullet.png")

        self.sprite_cache = {}

        # Pre-rendered effect surfaces, built once and reused every frame.
        self._glow_cache = {}
        self._trail_cache = {}
        self._ebullet_cache = {}
        self._vignette_cache = {}
        self._overlay_cache = {}
        self._bg_tint_cache = {}
        self._shake_layer = None
        self._applied_volume = None

        self.load_sounds()

        self.background_music_path = self.find_sound_file("background_music.mp3")
        self.boss_music_path = self.find_sound_file("boss.mp3")
        self.current_music = None

        self.high_score = self.load_high_score()

        self.refresh_difficulty()
        self.reset_game()

    # ------------------------------------------------------------------
    # Asset loading
    # ------------------------------------------------------------------

    def asset_path(self, filename):
        candidates = [
            os.path.join(self.root, "assets", "images", filename),
            os.path.join(self.root, "assets", "ships", filename),
            os.path.join(self.root, "assets", filename),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        return None

    def load_image_safely(self, path):
        if not path or not os.path.isfile(path):
            return None
        try:
            is_gif = False
            if Image is not None:
                try:
                    with Image.open(path) as img:
                        if img.format == "GIF":
                            is_gif = True
                except Exception:
                    pass
            if is_gif and Image is not None:
                with Image.open(path) as pil_image:
                    converted = pil_image.convert("RGBA")
                    return pygame.image.fromstring(
                        converted.tobytes(), converted.size, "RGBA"
                    ).convert_alpha()
            return pygame.image.load(path).convert_alpha()
        except Exception:
            try:
                return pygame.image.load(path).convert()
            except Exception:
                return None

    def load_image(self, filename):
        path = self.asset_path(filename)
        return self.load_image_safely(path)

    def load_background(self):
        # Prioritize loading the exact same background used in your menu systems
        bg_names = [
            "menu_bg.gif", "menu_bg.png", "menu_bg.jpg",
            "background.gif", "background.png", "background.jpg",
            "fighting_bg.gif", "fighting_bg.png", "fighting_bg.jpg"
        ]

        for name in bg_names:
            path = self.asset_path(name)
            if path is not None:
                if name.endswith(".gif") and Image is not None:
                    frames = self.load_gif_frames(path)
                    if frames:
                        self.background_frames = [f for f, _d in frames]
                        self.background_frame_durations = [d for _f, d in frames]
                        self.background_is_gif = True
                        self.background_frame_index = 0
                        self.background_frame_elapsed = 0
                        self.background = self.background_frames[0]
                        return

                img = self.load_image_safely(path)
                if img is not None:
                    self.background = img
                    return

    def load_gif_frames(self, path):
        frames = []
        try:
            gif = Image.open(path)
            for frame in ImageSequence.Iterator(gif):
                converted = frame.convert("RGBA")
                duration = max(20, int(frame.info.get("duration", 80)))
                surface = pygame.image.fromstring(
                    converted.tobytes(), converted.size, "RGBA"
                ).convert_alpha()
                frames.append((surface, duration))
        except Exception:
            return []
        return frames

    def update_background_animation(self):
        if not self.background_is_gif or len(self.background_frames) <= 1:
            return

        self.background_frame_elapsed += 1000 / 60
        duration = self.background_frame_durations[self.background_frame_index]

        while self.background_frame_elapsed >= duration:
            self.background_frame_elapsed -= duration
            self.background_frame_index = (
                self.background_frame_index + 1
            ) % len(self.background_frames)
            duration = self.background_frame_durations[self.background_frame_index]

        self.background = self.background_frames[self.background_frame_index]

    def find_sound_file(self, filename):
        candidates = [
            os.path.join(self.root, "assets", "sound", filename),
            os.path.join(self.root, "assets", "sounds", filename),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        return None

    def load_sound(self, filename):
        # a freshly loaded sound needs the volume applied again
        self._applied_volume = None
        path = self.find_sound_file(filename)
        if path is None:
            return None
        try:
            if pygame.mixer.get_init():
                return pygame.mixer.Sound(path)
        except Exception:
            pass
        return None

    def load_sounds(self):
        self.bullet_sound = self.load_sound("bullet.mp3")
        self.bullet_hit_sound = self.load_sound("bullet_hit.mp3")
        self.player_hit_sound = self.load_sound("player_hit.mp3")
        self.game_start_sound = self.load_sound("game_start.mp3")
        self.game_over_sound = self.load_sound("game_over.mp3")
        self.powerup_sound = self.load_sound("powerup.mp3")
        self.boss_roar_sound = self.load_sound("boss_roar.mp3")
        self.enemy_shot_sound = self.load_sound("enemy_shot.mp3")
        self.turbo_sound = self.load_sound("turbo.mp3")
        self.apply_sound_volume()

    def apply_sound_volume(self):
        try:
            master = float(PREFERENCES.get("master_volume", 1.0))
        except Exception:
            master = 1.0
        try:
            sfx = float(
                PREFERENCES.get("sfx_volume", PREFERENCES.get("sound_volume", 1.0))
            )
        except Exception:
            sfx = 1.0

        volume = max(0.0, min(1.0, master * sfx))

        if self._applied_volume == volume:
            return
        self._applied_volume = volume

        values = {
            self.bullet_sound: 0.20,
            self.bullet_hit_sound: 0.35,
            self.player_hit_sound: 0.50,
            self.game_start_sound: 0.45,
            self.game_over_sound: 0.50,
            self.powerup_sound: 0.40,
            self.boss_roar_sound: 0.55,
            self.enemy_shot_sound: 0.30,
            self.turbo_sound: 0.32,
        }

        for sound, base in values.items():
            if sound is not None:
                try:
                    sound.set_volume(base * volume)
                except Exception:
                    pass

    def music_volume(self):
        try:
            master = float(PREFERENCES.get("master_volume", 1.0))
            music = float(PREFERENCES.get("music_volume", 1.0))
            return max(0.0, min(1.0, master * music))
        except Exception:
            return 1.0

    def play_sound(self, sound):
        if sound is None:
            return
        try:
            self.apply_sound_volume()
            sound.play()
        except Exception:
            pass

    def start_music(self, boss=False):
        if not pygame.mixer.get_init():
            return

        path = self.boss_music_path if boss else self.background_music_path
        name = "boss" if boss else "background"

        if path is None:
            return

        if self.current_music == name and pygame.mixer.music.get_busy():
            return

        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_volume())
            pygame.mixer.music.play(loops=-1)
            self.current_music = name
        except Exception:
            self.current_music = None

    def stop_music(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self.current_music = None

    def pause_music(self):
        try:
            pygame.mixer.music.pause()
        except Exception:
            pass

    def resume_music(self):
        try:
            pygame.mixer.music.unpause()
        except Exception:
            pass

    def load_high_score(self):
        try:
            player = get_player(self.player_id)
            if isinstance(player, dict):
                return int(player.get("high_score", 0))
        except Exception:
            pass
        return 0

    def refresh_difficulty(self):
        try:
            key = PREFERENCES.get("difficulty", "normal")
            if key not in DIFFICULTIES:
                key = "normal"
            self.difficulty_key = key
            self.difficulty = DIFFICULTIES[key]
        except Exception:
            self.difficulty_key = "normal"
            self.difficulty = {
                "enemy_speed": 1.0,
                "enemy_fire_rate": 1.0,
                "score_multiplier": 1.0,
                "lives": 3,
            }

        self.enemy_speed_multiplier = max(
            0.5, float(self.difficulty.get("enemy_speed", 1.0))
        )
        self.enemy_fire_multiplier = max(
            0.5, float(self.difficulty.get("enemy_fire_rate", 1.0))
        )
        self.score_multiplier = max(
            0.5, float(self.difficulty.get("score_multiplier", 1.0))
        )
        self.max_lives = max(1, int(self.difficulty.get("lives", 3)))

    # ------------------------------------------------------------------
    # Player helpers
    # ------------------------------------------------------------------

    def player_size(self):
        return (
            getattr(self.player, "width", 60),
            getattr(self.player, "height", 70),
        )

    def player_center(self):
        w, h = self.player_size()
        return self.player.x + w * 0.5, self.player.y + h * 0.5

    # ------------------------------------------------------------------
    # Reset / start
    # ------------------------------------------------------------------

    def reset_game(self):
        self.refresh_difficulty()

        self.player = Player(self.screen_width, self.screen_height)
        self.buttons = MobileButtons(self.screen_width, self.screen_height)
        self.init_touch_controls()

        self.player_ship_frames = []
        self.player_ship_frame_index = 0
        self.player_ship_frame_elapsed = 0
        self.player_ship_is_animated = False

        self.refresh_loadout()

        self.game_state = "ready"
        self.previous_game_state = "playing"

        self.score = 0
        self.high_score = max(0, self.high_score)
        self.lives = self.max_lives

        self.wave = 1
        self.combo = 0
        self.combo_timer = 0

        self.wave_timer = 0
        self.wave_clear_timer = 0
        self.wave_intro_timer = 0
        self.shoot_timer = 0
        self.invincible_timer = 0
        self.damage_flash = 0
        self.screen_shake = 0
        self.screen_shake_power = 0

        self.bullets = []
        self.enemies = []
        self.enemy_bullets = []
        self.particles = []
        self.rings = []
        self.powerups = []

        self.formation = {
            "x": 0.0,
            "y": 0.0,
            "dir": 1,
            "entering": False,
            "target_y": 105.0,
        }

        self.boss = None
        self.boss_bullets = []
        self.boss_active = False
        self.boss_timer = 0
        self.boss_attack_timer = 0
        self.boss_phase = 0
        self.boss_flash_timer = 0
        self.boss_escorts = []

        self.rapid_fire = 0
        self.double_shot = 0
        self.shield = 0

        self.fire_level = 1
        self.fire_level_flash_timer = 0
        self.wave_composition_preview = {}

        self.game_time = 0
        self.enemy_count_target = 5
        self.score_saved = False
        self.show_ready = True
        self.damage_direction = 0.0
        self.ship_trail_phase = 0.0
        self.target_lock_pulse = 0.0
        self.ship_velocity_x = 0.0
        self.ship_move_speed = 5.8
        self.turbo_active = False
        self.turbo_energy = 100.0
        self.turbo_max = 100.0
        self.turbo_drain = 1.35
        self.turbo_recharge = 0.42
        self.afterburner_phase = 0.0
        self.turbo_flash = 0
        self.ship_pitch = 0.0
        self.enemy_shot_sound = self.load_sound("enemy_bullet.mp3")
        self.turbo_sound = self.load_sound("turbo.mp3")

        # journal menu state (pause / game over)
        self.new_record = False
        self.menu_selected = 0
        self._menu_prev_hover = None

    # ------------------------------------------------------------------
    # Shop loadout
    # ------------------------------------------------------------------

    def refresh_loadout(self):
        self._load_profile_loadout()

    def _get_shop_equipped_ship(self, player_data):
        candidates = []

        paths = []
        here = os.path.dirname(os.path.abspath(__file__))
        paths.extend([
            os.path.join(here, "ship_loadout.json"),
            os.path.join(os.path.dirname(here), "ship_loadout.json"),
            os.path.join(self.root, "ship_loadout.json"),
            os.path.join(os.getcwd(), "ship_loadout.json"),
        ])

        seen_paths = set()
        for path in paths:
            if path in seen_paths or not os.path.isfile(path):
                continue
            seen_paths.add(path)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                if not isinstance(data, dict):
                    continue
                values = data.get(str(self.player_id))
                if isinstance(values, dict):
                    value = (
                        values.get("equipped_ship")
                        or values.get("selected_ship")
                        or values.get("current_ship")
                        or values.get("active_ship")
                        or values.get("ship")
                        or values.get("ship_id")
                    )
                    if value:
                        candidates.append(value)
                elif isinstance(values, str):
                    candidates.append(values)
                elif len(data) == 1:
                    only_value = next(iter(data.values()))
                    if isinstance(only_value, dict):
                        value = (
                            only_value.get("equipped_ship")
                            or only_value.get("selected_ship")
                            or only_value.get("current_ship")
                            or only_value.get("active_ship")
                            or only_value.get("ship")
                            or only_value.get("ship_id")
                        )
                        if value:
                            candidates.append(value)
            except Exception:
                pass

        database_module = None
        try:
            import database as database_module
        except Exception:
            database_module = None

        if database_module is not None:
            for name in (
                "get_equipped_ship",
                "get_player_ship",
                "get_active_ship",
                "get_selected_ship"
            ):
                fn = getattr(database_module, name, None)
                if not callable(fn) or self.player_id is None:
                    continue
                try:
                    result = fn(self.player_id)
                    if isinstance(result, dict):
                        result = (
                            result.get("equipped_ship")
                            or result.get("selected_ship")
                            or result.get("current_ship")
                            or result.get("active_ship")
                            or result.get("ship")
                            or result.get("ship_id")
                            or result.get("id")
                        )
                    if result:
                        candidates.append(result)
                except Exception:
                    pass

        if isinstance(player_data, dict):
            for key in (
                "equipped_ship",
                "selected_ship",
                "current_ship",
                "active_ship",
                "ship"
            ):
                value = player_data.get(key)
                if value:
                    candidates.append(value)

        aliases = {
            "starter ship": "starter", "ship_starter": "starter", "starter": "starter",
            "falcon ship": "falcon", "ship_falcon": "falcon", "falcon": "falcon",
            "viper ship": "viper", "ship_viper": "viper", "viper": "viper",
            "wraith ship": "wraith", "ship_wraith": "wraith", "wraith": "wraith",
            "dragon ship": "dragon", "ship_dragon": "dragon", "dragon": "dragon"
        }

        valid = {"starter", "falcon", "viper", "wraith", "dragon"}
        normalized = []
        for value in candidates:
            ship_id = aliases.get(str(value).strip().lower(), str(value).strip().lower())
            if ship_id in valid:
                normalized.append(ship_id)

        non_starter = [value for value in normalized if value != "starter"]
        if non_starter:
            return non_starter[0]
        if normalized:
            return normalized[0]
        return None

    def _load_profile_loadout(self):
        player_data = dict(self.player_data) if isinstance(self.player_data, dict) else {}

        try:
            db_player = get_player(self.player_id) or {}
        except Exception:
            db_player = {}

        if not player_data:
            player_data = db_player
        else:
            merged_player = dict(db_player) if isinstance(db_player, dict) else {}
            merged_player.update(player_data)
            player_data = merged_player

        aliases = {
            "starter ship": "starter", "ship_starter": "starter", "starter": "starter",
            "falcon ship": "falcon", "ship_falcon": "falcon", "falcon": "falcon",
            "viper ship": "viper", "ship_viper": "viper", "viper": "viper",
            "wraith ship": "wraith", "ship_wraith": "wraith", "wraith": "wraith",
            "dragon ship": "dragon", "ship_dragon": "dragon", "dragon": "dragon"
        }
        valid = {"starter", "falcon", "viper", "wraith", "dragon"}

        direct_ship = None
        for key in (
            "equipped_ship",
            "selected_ship",
            "current_ship",
            "active_ship",
            "ship"
        ):
            value = player_data.get(key) if isinstance(player_data, dict) else None
            if value:
                normalized = aliases.get(str(value).strip().lower(), str(value).strip().lower())
                if normalized in valid:
                    direct_ship = normalized
                    break

        persisted_ship = self._get_shop_equipped_ship({})
        shop_equipped_ship = persisted_ship or direct_ship
        ship = shop_equipped_ship or "starter"
        color = "ICE"

        if not shop_equipped_ship and callable(get_game_loadout):
            try:
                loadout_result = get_game_loadout(player_data)
                if isinstance(loadout_result, (list, tuple)) and loadout_result:
                    ship = str(loadout_result[0] or ship)
                    if len(loadout_result) > 1 and loadout_result[1]:
                        color = str(loadout_result[1])
            except Exception:
                pass

        settings_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "profile_settings.json"
        )

        if not shop_equipped_ship:
            try:
                with open(settings_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                values = data.get(str(self.player_id), {})
                if isinstance(values, dict):
                    ship = values.get("selected_ship") or values.get("preview_ship") or ship
                    color = values.get("ship_color") or color
            except Exception:
                pass

        aliases = {
            "starter ship": "starter", "ship_starter": "starter", "starter": "starter",
            "falcon ship": "falcon", "ship_falcon": "falcon", "falcon": "falcon",
            "viper ship": "viper", "ship_viper": "viper", "viper": "viper",
            "wraith ship": "wraith", "ship_wraith": "wraith", "wraith": "wraith",
            "dragon ship": "dragon", "ship_dragon": "dragon", "dragon": "dragon"
        }
        self.loadout_ship = aliases.get(str(ship).strip().lower(), str(ship).strip().lower())
        if self.loadout_ship not in {"starter", "falcon", "viper", "wraith", "dragon"}:
            self.loadout_ship = "starter"
        self.loadout_color = str(color).upper()

        frames = self.load_shop_equipped_ship(self.loadout_ship)

        if frames is None and not shop_equipped_ship and callable(load_game_player_ship):
            try:
                img = load_game_player_ship(player_data, 96)
                if img:
                    frames = [(img, 100)]
            except Exception:
                frames = None

        if frames is None:
            frames = self.load_ship_fallback()

        self.player_ship_frames = []
        self.player_ship_frame_index = 0
        self.player_ship_frame_elapsed = 0
        self.player_ship_is_animated = False

        if frames:
            scaled_frames = []
            for surf, duration in frames:
                try:
                    scaled_surf = pygame.transform.smoothscale(surf, (92, 92))
                except Exception:
                    scaled_surf = surf
                scaled_surf = self.tint_ship_image(scaled_surf, self.loadout_color)
                scaled_frames.append((scaled_surf, duration))

            self.player_ship_frames = scaled_frames
            self.player_ship_is_animated = len(scaled_frames) > 1
            self.loadout_image_scaled = scaled_frames[0][0]
        else:
            self.loadout_image_scaled = None

        try:
            self.player.ship_image = self.loadout_image_scaled
        except Exception:
            pass

    def tint_ship_image(self, image, color_name):
        tint = SHIP_COLOR_TINTS.get(str(color_name).upper())

        if tint is None or image is None:
            return image

        try:
            tinted = image.copy()
            overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
            overlay.fill((tint[0], tint[1], tint[2], 255))
            tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            return tinted
        except Exception:
            return image

    def load_ship_gif_or_static(self, path):
        if not path or not os.path.isfile(path):
            return None

        is_gif = False
        if Image is not None:
            try:
                with Image.open(path) as img:
                    if img.format == "GIF":
                        is_gif = True
            except Exception:
                pass

        if is_gif and Image is not None:
            frames = self.load_gif_frames(path)
            if frames:
                return frames

        img = self.load_image_safely(path)
        if img:
            return [(img, 100)]
        return None

    def load_shop_equipped_ship(self, ship_id):
        ship_id = str(ship_id).strip().lower()
        names = [
            f"{ship_id}.png",
            f"ship_{ship_id}.png",
            f"{ship_id}.PNG",
            f"ship_{ship_id}.PNG",
            f"{ship_id}.gif",
            f"ship_{ship_id}.gif",
            os.path.join("ships", f"{ship_id}.png"),
            os.path.join("ships", f"ship_{ship_id}.png"),
            os.path.join("ships", f"{ship_id}.gif"),
            os.path.join("ships", f"ship_{ship_id}.gif"),
        ]

        for name in names:
            path = self.asset_path(name)
            if not path:
                continue

            frames = self.load_ship_gif_or_static(path)
            if frames:
                return frames

        return None

    def load_ship_fallback(self):
        ship_names = [self.loadout_ship]
        if self.loadout_ship == "starter":
            ship_names.append("starter")

        for ship_name in dict.fromkeys(ship_names):
            names = [
                f"ship_{ship_name}.png",
                f"{ship_name}.png",
                f"ship_{ship_name}.PNG",
                os.path.join("ships", f"ship_{ship_name}.png"),
                os.path.join("ships", f"{ship_name}.png"),
            ]

            for name in names:
                path = self.asset_path(name)
                if path:
                    frames = self.load_ship_gif_or_static(path)
                    if frames:
                        return frames

        return None

    def update_player_ship_animation(self):
        if not self.player_ship_is_animated or not self.player_ship_frames:
            return

        self.player_ship_frame_elapsed += 1000 / 60
        duration = self.player_ship_frames[self.player_ship_frame_index][1]

        while self.player_ship_frame_elapsed >= duration:
            self.player_ship_frame_elapsed -= duration
            self.player_ship_frame_index = (
                self.player_ship_frame_index + 1
            ) % len(self.player_ship_frames)
            duration = self.player_ship_frames[self.player_ship_frame_index][1]

    def start_game(self):
        self.reset_game()

        self.game_state = "playing"
        self.show_ready = True
        self.wave = 1
        self.wave_timer = 0
        self.wave_intro_timer = 100

        self.spawn_wave()

        self.play_sound(self.game_start_sound)
        self.start_music(False)

    # ------------------------------------------------------------------
    # Enemy sprites (Graphic Image Assets Only)
    # ------------------------------------------------------------------

    def override_image(self, etype):
        image = {
            "grunt": self.enemy_image,
            "scout": self.fast_image,
            "tank": self.tank_image,
            "boss": self.boss_image,
        }.get(etype)

        if image is None and etype != "boss":
            image = self.enemy_image

        return image

    def build_sprite(self, etype, cell, frame, mode):
        """Builds enemy sprite strictly out of loaded image overrides.

        No blocky procedural invaders are drawn.
        """
        w = 11 * cell
        h = 8 * cell
        override = self.override_image(etype)

        if override is not None:
            try:
                surf = pygame.transform.smoothscale(override, (w, w))
            except Exception:
                surf = override.copy()
        else:
            return None

        if mode == "flash":
            surf.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)
        elif mode == "warn" and override is not None:
            surf.fill((150, 0, 0, 0), special_flags=pygame.BLEND_RGB_ADD)

        return surf

    def get_sprite(self, etype, cell, frame=0, mode="normal"):
        key = (etype, cell, frame % 2, mode)
        sprite = self.sprite_cache.get(key)

        if sprite is None:
            sprite = self.build_sprite(etype, cell, frame % 2, mode)
            if sprite is not None:
                self.sprite_cache[key] = sprite

        return sprite

    # ------------------------------------------------------------------
    # Wave / formation spawning
    # ------------------------------------------------------------------

    def enemy_pool(self):
        pool = ["grunt", "grunt", "scout"]
        if self.wave >= 2:
            pool += ["weaver", "weaver"]
        if self.wave >= 3:
            pool += ["diver"]
        if self.wave >= 4:
            pool += ["bomber"]
        return pool

    def roll_row_types(self, rows):
        pool = self.enemy_pool()
        tank_chance = min(0.22, 0.03 + self.wave * 0.012) if self.wave >= 3 else 0.0

        row_types = []

        for _ in range(rows):
            if random.random() < tank_chance:
                choice = "tank"
            else:
                options = [t for t in pool if not row_types or t != row_types[-1]]
                choice = random.choice(options or pool)
            row_types.append(choice)

        return row_types

    def spawn_wave(self):
        self.enemies = []
        self.enemy_bullets.clear()
        self.wave_timer = 0
        self.wave_clear_timer = 0

        width = self.screen_width

        max_cols = max(3, int((width - 60) // 70))
        cols = max(3, min(max_cols, 5 + self.wave // 4))
        rows = min(5, 2 + self.wave // 3)

        if self.wave >= 10:
            rows = 5

        spacing_x = min(84.0, (width - 60) / cols)
        base = min(64.0, spacing_x * 0.88)
        spacing_y = int(base * 0.95)

        row_types = self.roll_row_types(rows)
        pool = self.enemy_pool()
        composition = {t: 0 for t in ENEMY_STATS if t != "boss"}

        form_x = (width - cols * spacing_x) / 2
        form_y = -(rows * spacing_y) - 20

        self.formation = {
            "x": float(form_x),
            "y": float(form_y),
            "dir": 1,
            "entering": True,
            "target_y": 105.0,
        }

        for row in range(rows):
            for col in range(cols):
                etype = row_types[row]

                if self.wave >= 6 and etype != "tank" and random.random() < 0.25:
                    etype = random.choice(pool)

                composition[etype] += 1

                self.create_enemy(
                    etype, row, col, spacing_x, spacing_y, base
                )

        self.enemy_count_target = rows * cols
        self.wave_composition_preview = composition

    def create_enemy(self, etype, row, col, spacing_x, spacing_y, base):
        stats = ENEMY_STATS[etype]

        cell = max(3, int(base * stats["scale"] / 11))
        w = 11 * cell
        h = 8 * cell

        hp = stats["hp"]
        if etype == "tank":
            hp = 5 + self.wave // 4

        if self.wave >= 8 and etype in ("grunt", "scout", "weaver") and random.random() < 0.10:
            hp += 1
            elite = True
        else:
            elite = False

        sx = col * spacing_x + (spacing_x - w) / 2
        sy = row * spacing_y + (spacing_y - h) / 2

        sway = {"weaver": 22, "scout": 8}.get(etype, 0)

        cracks = []
        if etype == "tank":
            px = random.uniform(w * 0.3, w * 0.7)
            py = 2.0
            for _ in range(6):
                nx = max(2, min(w - 2, px + random.uniform(-w * 0.16, w * 0.16)))
                ny = py + h / 6.5
                cracks.append(((px, py), (nx, ny)))
                px, py = nx, ny

        enemy = {
            "type": etype,
            "x": self.formation["x"] + sx,
            "y": self.formation["y"] + sy,
            "w": w,
            "h": h,
            "cell": cell,
            "sx": sx,
            "sy": sy,
            "sway": sway,
            "row": row,
            "col": col,
            "hp": hp,
            "max_hp": hp,
            "elite": elite,
            "state": "formation",
            "age": random.randint(0, 60),
            "frame": 0,
            "flash": 0,
            "phase": random.uniform(0, math.pi * 2),
            "fire_timer": random.randint(150, 330),
            "warn_timer": 0,
            "dive_x": 0.0,
            "cracks": cracks,
            "dead": False,
        }

        self.enemies.append(enemy)

    def all_enemies_cleared(self):
        return all(enemy["dead"] for enemy in self.enemies)

    def cleanup_enemies(self):
        self.enemies = [e for e in self.enemies if not e["dead"]]

    # ------------------------------------------------------------------
    # Touch / mobile controls (self-contained, no MobileButtons needed)
    # ------------------------------------------------------------------

    def mobile_enabled(self):
        for key in ("mobilecontrols", "mobile_controls", "mobile_buttons",
                    "touch_controls", "mobile"):
            value = PREFERENCES.get(key, False)
            if isinstance(value, str):
                value = value.strip().lower()
            if value in self.TOUCH_ON_VALUES:
                return True
        return False

    def init_touch_controls(self):
        w, h = self.screen_width, self.screen_height
        r = 46
        y = h - r - 60
        self.touch_rects = {
            "left": pygame.Rect(0, 0, r * 2, r * 2),
            "right": pygame.Rect(0, 0, r * 2, r * 2),
            "fire": pygame.Rect(0, 0, r * 2, r * 2),
        }
        self.touch_rects["left"].center = (28 + r, y)
        self.touch_rects["right"].center = (28 + r * 3 + 16, y)
        self.touch_rects["fire"].center = (w - 28 - r, y)
        self.finger_points = {}
        self.touch_held = {"left": False, "right": False, "fire": False}

    def read_touch_controls(self, events):
        w, h = self.screen_width, self.screen_height
        down = getattr(pygame, "FINGERDOWN", None)
        motion = getattr(pygame, "FINGERMOTION", None)
        up = getattr(pygame, "FINGERUP", None)

        for e in events:
            if down is not None and e.type in (down, motion):
                self.finger_points[e.finger_id] = (e.x * w, e.y * h)
            elif up is not None and e.type == up:
                self.finger_points.pop(e.finger_id, None)

        points = list(self.finger_points.values())
        if pygame.mouse.get_pressed()[0]:
            points.append(pygame.mouse.get_pos())

        self.touch_held = {
            name: any(rect.collidepoint(p) for p in points)
            for name, rect in self.touch_rects.items()
        }
        return self.touch_held["left"], self.touch_held["right"], self.touch_held["fire"]

    def draw_touch_controls(self):
        for name, rect in self.touch_rects.items():
            held = self.touch_held.get(name, False)
            color = TAB_ORANGE if name == "fire" else TAB_YELLOW
            r = rect.w // 2

            layer = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.circle(layer, (*color, 215 if held else 120), (r, r), r)
            pygame.draw.circle(layer, (*OUTLINE, 235), (r, r), r, 3)

            if name == "left":
                pts = [(r + 12, r - 18), (r + 12, r + 18), (r - 14, r)]
                pygame.draw.polygon(layer, (*INK, 255), pts)
            elif name == "right":
                pts = [(r - 12, r - 18), (r - 12, r + 18), (r + 14, r)]
                pygame.draw.polygon(layer, (*INK, 255), pts)
            else:
                label = self.j_button.render("FIRE", True, INK)
                layer.blit(label, label.get_rect(center=(r, r)))

            self.screen.blit(layer, rect.topleft)

    # ------------------------------------------------------------------
    # Player update / shooting
    # ------------------------------------------------------------------

    def update_player(self, events):
        keys = pygame.key.get_pressed()

        left = bool(keys[pygame.K_LEFT] or keys[pygame.K_a])
        right = bool(keys[pygame.K_RIGHT] or keys[pygame.K_d])

        fire_mobile = False
        if self.mobile_enabled():
            m_left, m_right, fire_mobile = self.read_touch_controls(events)
            left = left or m_left
            right = right or m_right

        self.turbo_active = False
        self.turbo_energy = min(self.turbo_max, self.turbo_energy + self.turbo_recharge)
        self.turbo_flash = max(0, self.turbo_flash - 1)

        if left and not right:
            self.ship_velocity_x = -self.ship_move_speed
        elif right and not left:
            self.ship_velocity_x = self.ship_move_speed
        else:
            self.ship_velocity_x = 0.0

        self.afterburner_phase += 0.16
        self.player.x += self.ship_velocity_x

        pw, _ph = self.player_size()
        self.player.x = max(8, min(self.screen_width - pw - 8, self.player.x))

        self.ship_pitch = 0.0

        if keys[pygame.K_SPACE] or keys[pygame.K_z] or fire_mobile:
            self.shoot()

        try:
            self.player.keep_inside_screen()
        except Exception:
            pass

        try:
            self.player.update_blink()
        except Exception:
            pass

    def shoot(self):
        if self.shoot_timer > 0:
            return

        if self.game_state not in ("playing", "boss"):
            return

        self.shoot_timer = 4 if self.rapid_fire > 0 else 7

        pw, _ph = self.player_size()
        px = self.player.x + pw * 0.5
        py = self.player.y - 8

        count = 1
        if self.double_shot > 0:
            count = 2
        if self.fire_level >= 3:
            count = 3

        offsets = {1: [0], 2: [-15, 15], 3: [-20, 0, 20]}[count]

        bullet_speed = Bullet.DEFAULT_SPEED
        if self.rapid_fire > 0:
            bullet_speed *= 1.15

        for offset in offsets:
            b = Bullet(px + offset, py, damage=self.fire_level, speed=bullet_speed)

            # Dynamically injection for visual & properties upscaling
            b.damage = self.fire_level

            # Physical bullet size scales with power level up
            if hasattr(b, 'width'):
                b.width = 10 + self.fire_level * 5
            if hasattr(b, 'height'):
                b.height = 20 + self.fire_level * 8

            self.bullets.append(b)

        self.play_sound(self.bullet_sound)
        self.create_muzzle_flash(px, py)

    def create_muzzle_flash(self, x, y):
        # Muzzle flash colors scale with bullet elements
        color = (255, 170, 40)
        if self.fire_level == 2:
            color = (0, 191, 255)
        elif self.fire_level >= 3:
            color = (255, 215, 0)

        for _ in range(5):
            self.particles.append({
                "x": x,
                "y": y,
                "vx": random.uniform(-1.5, 1.5),
                "vy": random.uniform(-4, -1),
                "life": 12,
                "max_life": 12,
                "size": random.randint(2 + self.fire_level, 5 + self.fire_level),
                "color": color,
            })

    def update_fire_level(self):
        thresholds = [(1, 0), (2, 800), (3, 2500)]
        new_level = self.fire_level

        for level, needed in thresholds:
            if self.score >= needed:
                new_level = level

        if new_level > self.fire_level:
            self.fire_level = new_level
            self.fire_level_flash_timer = 90
            self.play_sound(self.powerup_sound)

        if self.fire_level_flash_timer > 0:
            self.fire_level_flash_timer -= 1

    def update_bullets(self):
        for bullet in self.bullets:
            bullet.update(1 / 60)

        self.bullets = [b for b in self.bullets if b.is_active]

    # ------------------------------------------------------------------
    # Formation + enemy behaviour
    # ------------------------------------------------------------------

    def slot_position(self, enemy):
        f = self.formation
        tx = f["x"] + enemy["sx"]
        ty = f["y"] + enemy["sy"]

        if enemy["type"] == "weaver":
            tx += math.sin(enemy["age"] * 0.06 + enemy["phase"]) * 22
            ty += math.cos(enemy["age"] * 0.06 + enemy["phase"]) * 6
        elif enemy["type"] == "scout":
            tx += math.sin(enemy["age"] * 0.10 + enemy["phase"]) * 8

        return tx, ty

    def update_formation(self, alive):
        f = self.formation
        width = self.screen_width

        if f["entering"]:
            f["y"] += 2.4
            if f["y"] >= f["target_y"]:
                f["y"] = f["target_y"]
                f["entering"] = False
            return

        ratio = len(alive) / max(1, self.enemy_count_target)

        speed = (0.6 + self.wave * 0.05) * (1 + (1 - ratio) * 2.0)
        speed = min(4.2, speed * self.enemy_speed_multiplier)

        f["x"] += f["dir"] * speed

        left = min(e["sx"] - e["sway"] for e in alive)
        right = max(e["sx"] + e["w"] + e["sway"] for e in alive)

        step = min(24, 14 + self.wave * 0.5)

        if f["x"] + left < 14:
            f["x"] = 14 - left
            f["dir"] = 1
            f["y"] += step
        elif f["x"] + right > width - 14:
            f["x"] = width - 14 - right
            f["dir"] = -1
            f["y"] += step

    def update_enemies(self):
        alive = [e for e in self.enemies if not e["dead"]]

        if not alive:
            return

        self.update_formation(alive)

        f = self.formation

        front = {}
        for e in alive:
            if e["state"] in ("formation", "warning"):
                if e["col"] not in front or e["row"] > front[e["col"]]:
                    front[e["col"]] = e["row"]

        pcx, _pcy = self.player_center()

        max_divers = 1 + self.wave // 4
        divers_active = sum(
            1 for e in alive if e["state"] in ("warning", "diving")
        )

        frame = (self.game_time // 24) % 2

        for e in alive:
            e["age"] += 1
            e["frame"] = frame

            if e["flash"] > 0:
                e["flash"] -= 1

            state = e["state"]

            if state in ("formation", "warning"):
                e["x"], e["y"] = self.slot_position(e)

                if state == "warning":
                    e["warn_timer"] -= 1
                    if e["warn_timer"] <= 0:
                        e["state"] = "diving"
                elif (
                    e["type"] == "diver"
                    and not f["entering"]
                    and e["age"] > 90
                    and divers_active < max_divers
                    and random.random() < 0.004 + 0.0004 * self.wave
                ):
                    e["state"] = "warning"
                    e["warn_timer"] = 50
                    e["dive_x"] = pcx
                    divers_active += 1

            elif state == "diving":
                dive_speed = (4.0 + self.wave * 0.15) * self.enemy_speed_multiplier
                e["y"] += dive_speed

                pull = (e["dive_x"] - e["w"] * 0.5 - e["x"]) * 0.03
                e["x"] += max(-3.0, min(3.0, pull)) + math.sin(e["age"] * 0.15) * 1.5

                if e["y"] > self.screen_height + 40:
                    e["dead"] = True
                    self.create_explosion(
                        e["x"] + e["w"] * 0.5,
                        self.screen_height - 35,
                        10,
                        [ENEMY_STATS[e["type"]]["color"], (255, 255, 255)],
                    )

            elif state == "returning":
                tx, ty = self.slot_position(e)
                e["x"] += (tx - e["x"]) * 0.05
                e["y"] += min(6.0, max(1.5, (ty - e["y"]) * 0.05))

                if ty - e["y"] < 3 and abs(tx - e["x"]) < 5:
                    e["state"] = "formation"

            e["x"] = max(4.0, min(self.screen_width - e["w"] - 4.0, e["x"]))

            # ---- shooting ----
            e["fire_timer"] -= 1

            eligible = (
                e["state"] == "formation"
                and 30 < e["y"] < self.screen_height * 0.70
                and (
                    front.get(e["col"]) == e["row"]
                    or e["type"] in ("bomber", "tank")
                )
            )

            if e["fire_timer"] <= 0 and eligible:
                self.enemy_shoot(e)

                e["fire_timer"] = int(
                    random.randint(150, 330) / self.enemy_fire_multiplier
                )

        if not f["entering"]:
            low = max(
                (
                    e["y"] + e["h"]
                    for e in alive
                    if e["state"] in ("formation", "warning")
                ),
                default=0,
            )

            if low >= self.player.y - 5:
                f["y"] -= 130
                self.invincible_timer = 0
                self.damage_player()

    def fire_bullet(self, x, y, vx, vy, radius=5, kind="shot"):
        self.enemy_bullets.append({
            "x": x,
            "y": y,
            "px": x,
            "py": y,
            "vx": vx,
            "vy": vy,
            "radius": radius,
            "kind": kind,
            "active": True,
            "age": 0,
        })
        if kind.startswith("enemy") and self.enemy_shot_sound is not None:
            self.play_sound(self.enemy_shot_sound)

    def aim_vector(self, ex, ey, speed):
        pcx, _ = self.player_center()
        dx = pcx - ex
        dy = self.player.y - ey
        dist = max(1.0, math.sqrt(dx * dx + dy * dy))
        return dx / dist * speed, dy / dist * speed

    def enemy_shoot(self, enemy):
        if len(self.enemy_bullets) > 24:
            return

        ex = enemy["x"] + enemy["w"] * 0.5
        ey = enemy["y"] + enemy["h"]
        etype = enemy["type"]

        speed = 4.0 + self.wave * 0.04

        if etype in ("grunt", "weaver"):
            self.fire_bullet(ex, ey, 0, speed, radius=5, kind="enemy_shot")

        elif etype in ("scout", "diver"):
            vx, vy = self.aim_vector(ex, ey, speed)
            self.fire_bullet(ex, ey, vx, vy, radius=5, kind="enemy_guided")

        elif etype == "tank":
            vx, vy = self.aim_vector(ex, ey, speed * 0.85)
            self.fire_bullet(ex, ey, vx, vy, radius=7, kind="enemy_heavy")

        elif etype == "bomber":
            self.fire_bullet(ex, ey, 0, 2.6, radius=9, kind="enemy_bomb")

            if self.wave >= 6:
                for angle in (-0.35, 0.35):
                    self.fire_bullet(
                        ex,
                        ey,
                        math.sin(angle) * 3.4,
                        math.cos(angle) * 3.4,
                    )

    def update_enemy_bullets(self):
        for bullet in self.enemy_bullets:
            bullet["px"] = bullet["x"]
            bullet["py"] = bullet["y"]
            bullet["x"] += bullet["vx"]
            bullet["y"] += bullet["vy"]
            bullet["age"] = bullet.get("age", 0) + 1

            if (
                bullet["x"] < -50
                or bullet["x"] > self.screen_width + 50
                or bullet["y"] > self.screen_height + 50
                or bullet["y"] < -50
            ):
                bullet["active"] = False

        self.enemy_bullets = [b for b in self.enemy_bullets if b["active"]]

    def enemy_rect(self, enemy):
        return pygame.Rect(
            int(enemy["x"] + enemy["w"] * 0.10),
            int(enemy["y"] + enemy["h"] * 0.10),
            int(enemy["w"] * 0.80),
            int(enemy["h"] * 0.80),
        )

    def player_rect(self):
        try:
            return self.player.get_rect().inflate(-12, -10)
        except Exception:
            pw, ph = self.player_size()
            return pygame.Rect(int(self.player.x), int(self.player.y), pw, ph)

    # ------------------------------------------------------------------
    # Collisions / destruction
    # ------------------------------------------------------------------

    def update_collisions(self):
        for bullet in self.bullets:
            if not bullet.is_active:
                continue

            brect = bullet.get_rect()
            hit_x, hit_y = bullet.get_center()

            for enemy in self.enemies:
                if enemy["dead"]:
                    continue

                if brect.colliderect(self.enemy_rect(enemy)):
                    bullet.impact()

                    # Apply leveled up bullet damage
                    enemy["hp"] -= getattr(bullet, 'damage', 1)
                    enemy["flash"] = 4

                    self.create_hit_effect(hit_x, hit_y)
                    self.play_sound(self.bullet_hit_sound)

                    if enemy["hp"] <= 0:
                        self.destroy_enemy(enemy)

                    break

            if not bullet.is_active:
                continue

            for escort in self.boss_escorts:
                if escort["dead"]:
                    continue

                if brect.colliderect(self.enemy_rect(escort)):
                    bullet.impact()

                    escort["hp"] -= getattr(bullet, 'damage', 1)

                    self.create_hit_effect(hit_x, hit_y)
                    self.play_sound(self.bullet_hit_sound)

                    if escort["hp"] <= 0:
                        self.destroy_escort(escort)

                    break

        if self.invincible_timer > 0:
            return

        player_rect = self.player_rect()

        for enemy in self.enemies:
            if enemy["dead"]:
                continue

            if player_rect.colliderect(self.enemy_rect(enemy)):
                enemy["dead"] = True

                self.create_explosion(
                    enemy["x"] + enemy["w"] * 0.5,
                    enemy["y"] + enemy["h"] * 0.5,
                    18,
                    [ENEMY_STATS[enemy["type"]]["color"], (255, 255, 255)],
                )

                self.damage_player()
                break

        for escort in self.boss_escorts:
            if escort["dead"]:
                continue

            if player_rect.colliderect(self.enemy_rect(escort)):
                self.damage_player()
                break

        for bullet in self.enemy_bullets:
            if not bullet["active"]:
                continue

            r = bullet["radius"]
            rect = pygame.Rect(
                int(bullet["x"] - r), int(bullet["y"] - r), r * 2, r * 2
            )

            if player_rect.colliderect(rect):
                bullet["active"] = False
                self.damage_player()
                break

    def add_ring(self, x, y, max_radius, color):
        self.rings.append({
            "x": x,
            "y": y,
            "r": 6.0,
            "max_r": max_radius,
            "life": 18,
            "max_life": 18,
            "color": color,
        })

    def destroy_enemy(self, enemy):
        if enemy["dead"]:
            return

        enemy["dead"] = True

        stats = ENEMY_STATS[enemy["type"]]
        value = stats["score"]

        if enemy["state"] == "diving":
            value = int(value * 1.5)

        self.combo += 1
        self.combo_timer = 150

        multiplier = min(5, 1 + self.combo // 5)

        self.score += int(value * multiplier * self.score_multiplier)

        cx = enemy["x"] + enemy["w"] * 0.5
        cy = enemy["y"] + enemy["h"] * 0.5

        palette = [stats["color"], (255, 255, 255), (255, 215, 70)]

        self.create_explosion(
            cx, cy, 32 if enemy["type"] == "tank" else 22, palette
        )
        self.add_ring(cx, cy, enemy["w"] * 0.9, stats["color"])

        if enemy["type"] == "tank":
            self.screen_shake = 10
            self.screen_shake_power = 6
        else:
            self.screen_shake = 5
            self.screen_shake_power = 3

        drop_chance = 0.35 if enemy["type"] in ("tank", "bomber") else 0.10

        if random.random() < drop_chance:
            self.powerups.append({
                "x": cx,
                "y": cy,
                "type": random.choice(["rapid", "double", "shield"]),
                "life": 600,
            })

    def damage_player(self):
        if self.invincible_timer > 0:
            return

        cx, cy = self.player_center()

        if self.shield > 0:
            self.shield = max(0, self.shield - 90)
            self.invincible_timer = 30
            self.create_hit_effect(cx, cy)
            return

        self.lives -= 1
        self.invincible_timer = 120
        self.damage_flash = 25
        self.screen_shake = 18
        self.screen_shake_power = 10
        self.combo = 0
        self.combo_timer = 0

        self.play_sound(self.player_hit_sound)
        self.create_explosion(cx, cy, 35)

        try:
            self.player.is_blinking = True
        except Exception:
            pass

        if self.lives <= 0:
            self.end_game()

    # ------------------------------------------------------------------
    # Effects
    # ------------------------------------------------------------------

    def create_hit_effect(self, x, y):
        for _ in range(8):
            self.particles.append({
                "x": float(x),
                "y": float(y),
                "vx": random.uniform(-3, 3),
                "vy": random.uniform(-3, 3),
                "life": random.randint(12, 24),
                "max_life": 24,
                "size": random.randint(2, 5),
                "color": random.choice(
                    [(255, 90, 50), (255, 190, 60), (100, 220, 255)]
                ),
            })

    def create_explosion(self, x, y, amount=25, palette=None):
        colors = palette or [
            (255, 45, 45),
            (255, 115, 40),
            (255, 215, 70),
            (100, 210, 255),
        ]

        for _ in range(amount):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 6)

            self.particles.append({
                "x": float(x),
                "y": float(y),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.randint(20, 55),
                "max_life": 55,
                "size": random.randint(2, 7),
                "color": random.choice(colors),
            })

    def update_particles(self):
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.035
            p["life"] -= 1

        self.particles = [p for p in self.particles if p["life"] > 0]

        if len(self.particles) > MAX_PARTICLES:
            self.particles = self.particles[-MAX_PARTICLES:]

        for ring in self.rings:
            ring["life"] -= 1
            t = 1 - ring["life"] / ring["max_life"]
            ring["r"] = 6 + (ring["max_r"] - 6) * t

        self.rings = [r for r in self.rings if r["life"] > 0]

    def update_powerups(self):
        for powerup in self.powerups:
            powerup["y"] += 1.5
            powerup["life"] -= 1

        player_rect = self.player_rect()

        for powerup in self.powerups:
            rect = pygame.Rect(
                int(powerup["x"] - 14), int(powerup["y"] - 14), 28, 28
            )

            if rect.colliderect(player_rect):
                if powerup["type"] == "rapid":
                    self.rapid_fire = 600
                elif powerup["type"] == "double":
                    self.double_shot = 600
                elif powerup["type"] == "shield":
                    self.shield = 600

                powerup["life"] = 0
                self.play_sound(self.powerup_sound)

        self.powerups = [
            p
            for p in self.powerups
            if p["life"] > 0 and p["y"] < self.screen_height + 50
        ]

    # ------------------------------------------------------------------
    # Boss + escorts
    # ------------------------------------------------------------------

    def spawn_boss_escorts(self):
        self.boss_escorts.clear()

        escort_count = min(4, 2 + self.wave // 8)
        cell = 5

        for i in range(escort_count):
            hp = 8 + self.wave // 2

            self.boss_escorts.append({
                "x": float(self.screen_width * 0.5),
                "y": float(-120 - i * 70),
                "w": 11 * cell,
                "h": 8 * cell,
                "cell": cell,
                "type": "escort",
                "hp": hp,
                "max_hp": hp,
                "side": -1 if i % 2 == 0 else 1,
                "orbit_offset": 110 + (i // 2) * 55,
                "phase": random.uniform(0, math.pi * 2),
                "fire_timer": random.randint(50, 120),
                "age": 0,
                "dead": False,
            })

    def update_boss_escorts(self):
        if not self.boss:
            self.boss_escorts = [e for e in self.boss_escorts if not e["dead"]]
            return

        boss_cx = self.boss["x"] + self.boss["w"] * 0.5
        boss_cy = self.boss["y"] + self.boss["h"] * 0.5

        for escort in self.boss_escorts:
            if escort["dead"]:
                continue

            escort["age"] += 1
            escort["phase"] += 0.03

            target_x = (
                boss_cx
                + escort["side"] * escort["orbit_offset"]
                + math.sin(escort["phase"]) * 18
            )
            target_y = boss_cy + 40 + math.cos(escort["phase"] * 0.8) * 14

            escort["x"] += (target_x - escort["w"] * 0.5 - escort["x"]) * 0.08
            escort["y"] += (target_y - escort["h"] * 0.5 - escort["y"]) * 0.08

            escort["fire_timer"] -= 1

            if escort["fire_timer"] <= 0 and escort["y"] > 20:
                self.escort_shoot(escort)

                escort["fire_timer"] = int(
                    random.randint(90, 160) / self.enemy_fire_multiplier
                )

        self.boss_escorts = [e for e in self.boss_escorts if not e["dead"]]

    def escort_shoot(self, escort):
        if len(self.enemy_bullets) > 30:
            return

        ex = escort["x"] + escort["w"] * 0.5
        ey = escort["y"] + escort["h"]

        vx, vy = self.aim_vector(ex, ey, 4.6 + self.wave * 0.03)
        self.fire_bullet(ex, ey, vx, vy)

    def destroy_escort(self, escort):
        if escort["dead"]:
            return

        escort["dead"] = True

        self.combo += 1
        self.combo_timer = 150

        multiplier = min(5, 1 + self.combo // 5)
        self.score += int(35 * multiplier * self.score_multiplier)

        cx = escort["x"] + escort["w"] * 0.5
        cy = escort["y"] + escort["h"] * 0.5

        self.create_explosion(
            cx, cy, 18, [ENEMY_STATS["tank"]["color"], (255, 255, 255)]
        )
        self.add_ring(cx, cy, escort["w"] * 0.9, ENEMY_STATS["tank"]["color"])

        self.screen_shake = max(self.screen_shake, 6)
        self.screen_shake_power = max(self.screen_shake_power, 4)

        if random.random() < 0.20:
            self.powerups.append({
                "x": cx,
                "y": cy,
                "type": random.choice(["rapid", "double", "shield"]),
                "life": 600,
            })

    def update_boss(self):
        if not self.boss:
            return

        self.boss_timer += 1

        self.boss["x"] = (
            self.screen_width * 0.5
            - self.boss["w"] * 0.5
            + math.sin(self.boss_timer * 0.018) * (self.screen_width * 0.28)
        )
        self.boss["y"] = 55 + math.sin(self.boss_timer * 0.025) * 22

        health_ratio = max(0.0, self.boss["hp"] / self.boss["max_hp"])

        new_phase = 0
        if health_ratio <= 0.33:
            new_phase = 2
        elif health_ratio <= 0.66:
            new_phase = 1

        if new_phase != self.boss_phase:
            self.boss_phase = new_phase
            self.boss_flash_timer = 20

            self.screen_shake = max(self.screen_shake, 14)
            self.screen_shake_power = max(self.screen_shake_power, 8)

            self.play_sound(self.boss_roar_sound)

            if self.boss_phase >= 1:
                self.spawn_boss_escorts()

        if self.boss_flash_timer > 0:
            self.boss_flash_timer -= 1

        self.boss_attack_timer -= 1

        if self.boss_attack_timer <= 0:
            self.boss_attack()

            phase_speedup = 1.0 + self.boss_phase * 0.35

            self.boss_attack_timer = max(
                20,
                int(100 / (self.enemy_fire_multiplier * phase_speedup)),
            )

        self.update_boss_escorts()

        boss_rect = pygame.Rect(
            int(self.boss["x"]),
            int(self.boss["y"]),
            int(self.boss["w"]),
            int(self.boss["h"]),
        )

        for bullet in self.bullets:
            if not bullet.is_active:
                continue

            if boss_rect.colliderect(bullet.get_rect()):
                bullet.impact()

                self.boss["hp"] -= getattr(bullet, 'damage', 1)

                hit_x, hit_y = bullet.get_center()
                self.create_hit_effect(hit_x, hit_y)

                self.score += int(5 * self.score_multiplier)

                if self.boss["hp"] <= 0:
                    self.destroy_boss()
                    return

        if self.invincible_timer <= 0:
            if boss_rect.colliderect(self.player_rect()):
                self.damage_player()

    def start_boss(self):
        self.enemies.clear()
        self.enemy_bullets.clear()

        size = min(300, int(self.screen_width * 0.38))
        image = self.boss_image

        if image is not None:
            image = pygame.transform.smoothscale(image, (size, size))
        else:
            image = self.get_sprite("boss", max(3, size // 11), 0, "normal")

        hp = 170 + self.wave * 30

        self.boss = {
            "x": (self.screen_width - size) * 0.5,
            "y": -size,
            "w": size,
            "h": size,
            "image": image,
            "hp": hp,
            "max_hp": hp,
        }

        self.boss_active = True
        self.boss_timer = 0
        self.boss_attack_timer = 80
        self.boss_phase = 0
        self.boss_flash_timer = 0

        self.game_state = "boss"
        self.wave_intro_timer = 130

        self.spawn_boss_escorts()

        self.play_sound(self.boss_roar_sound)
        self.start_music(True)

    def boss_attack(self):
        if not self.boss:
            return

        bx = self.boss["x"] + self.boss["w"] * 0.5
        by = self.boss["y"] + self.boss["h"] * 0.7

        pcx, _ = self.player_center()

        base_angle = math.atan2(self.player.y - by, pcx - bx)

        speed = 5.0 + self.boss_phase * 0.6

        if self.boss_phase >= 2:
            spiral_count = 8

            for i in range(spiral_count):
                angle = (math.pi * 2 / spiral_count) * i + self.boss_timer * 0.05

                self.boss_bullets.append({
                    "x": bx,
                    "y": by,
                    "vx": math.cos(angle) * 3.6,
                    "vy": math.sin(angle) * 3.6,
                    "radius": 6,
                    "kind": "shot",
                    "active": True,
                })

        spread = (
            [-0.24, -0.08, 0.08, 0.24]
            if self.boss_phase >= 1
            else [-0.18, 0, 0.18]
        )

        for offset in spread:
            angle = base_angle + offset

            self.boss_bullets.append({
                "x": bx,
                "y": by,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "radius": 8,
                "kind": "shot",
                "active": True,
            })

    def update_boss_bullets(self):
        for bullet in self.boss_bullets:
            bullet["x"] += bullet["vx"]
            bullet["y"] += bullet["vy"]

            if (
                bullet["x"] < -60
                or bullet["x"] > self.screen_width + 60
                or bullet["y"] < -60
                or bullet["y"] > self.screen_height + 60
            ):
                bullet["active"] = False

        self.boss_bullets = [b for b in self.boss_bullets if b["active"]]

        if self.invincible_timer > 0:
            return

        player_rect = self.player_rect()

        for bullet in self.boss_bullets:
            r = bullet["radius"]
            rect = pygame.Rect(
                int(bullet["x"] - r), int(bullet["y"] - r), int(r * 2), int(r * 2)
            )

            if rect.colliderect(player_rect):
                bullet["active"] = False
                self.damage_player()
                break

    def destroy_boss(self):
        if not self.boss:
            return

        x = self.boss["x"] + self.boss["w"] * 0.5
        y = self.boss["y"] + self.boss["h"] * 0.5

        for _ in range(12):
            self.create_explosion(
                x + random.randint(-70, 70),
                y + random.randint(-70, 70),
                15,
            )

        self.add_ring(x, y, self.boss["w"] * 0.9, ENEMY_STATS["boss"]["color"])

        for escort in self.boss_escorts:
            if not escort["dead"]:
                self.create_explosion(
                    escort["x"] + escort["w"] * 0.5,
                    escort["y"] + escort["h"] * 0.5,
                    12,
                )

        self.boss_escorts.clear()

        self.score += int(1500 * self.score_multiplier)

        self.powerups.append({"x": x, "y": y, "type": "shield", "life": 600})

        self.screen_shake = 40
        self.screen_shake_power = 16

        self.boss = None
        self.boss_active = False
        self.boss_phase = 0
        self.boss_flash_timer = 0
        self.boss_bullets.clear()

        self.wave += 1

        self.start_music(False)
        self.spawn_wave()

        self.wave_intro_timer = 110
        self.game_state = "playing"

    def update_wave(self):
        self.wave_timer += 1

        if not self.all_enemies_cleared():
            self.wave_clear_timer = 0
            return

        self.wave_clear_timer += 1

        if self.wave_clear_timer < 70:
            return

        is_boss_wave = self.wave >= 5 and self.wave % 5 == 0

        if is_boss_wave and not self.boss_active:
            self.start_boss()
            return

        self.wave += 1
        self.spawn_wave()
        self.wave_intro_timer = 90

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------

    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.game_state in ("playing", "boss"):
                    self.previous_game_state = self.game_state
                    self.game_state = "paused"
                    self.menu_selected = 0
                    self._menu_prev_hover = None
                    self._ui_click()
                    self.pause_music()
                    return

                if self.game_state == "paused":
                    self.game_state = self.previous_game_state
                    self.resume_music()
                    return

        if self.game_state == "paused":
            self.draw()
            self.draw_pause(events)
            return

        if self.game_state == "game_over":
            self.draw()
            self.draw_game_over(events)
            return

        if self.game_state == "main_menu":
            self.refresh_loadout()
            return

        if self.shoot_timer > 0:
            self.shoot_timer -= 1

        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        if self.damage_flash > 0:
            self.damage_flash -= 1

        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0

        if self.rapid_fire > 0:
            self.rapid_fire -= 1

        if self.double_shot > 0:
            self.double_shot -= 1

        if self.shield > 0:
            self.shield -= 1

        self.game_time += 1

        self.update_background_animation()
        self.update_player_ship_animation()
        self.update_fire_level()
        self.update_player(events)
        self.update_bullets()
        self.update_enemy_bullets()
        self.update_boss_bullets()
        self.update_particles()
        self.update_powerups()

        if self.game_state == "playing":
            self.update_enemies()
            self.update_collisions()
            self.cleanup_enemies()
            self.update_wave()

        elif self.game_state == "boss":
            self.update_boss()
            self.update_collisions()

        if self.screen_shake > 0:
            self.screen_shake -= 1

        if self.wave_intro_timer > 0:
            self.wave_intro_timer -= 1

        self.draw()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_background(self):
        # Same notebook-desk backdrop the menu screens use.
        if USE_JOURNAL_BACKGROUND and journal_background is not None:
            try:
                journal_background(
                    self.screen,
                    self.screen_width,
                    self.screen_height,
                    self.game_time,
                )
                return
            except Exception:
                pass

        if game_theme is not None:
            local_background = getattr(game_theme, "_local_background", None)
            if callable(local_background):
                try:
                    local_background(
                        self.screen,
                        self.screen_width,
                        self.screen_height,
                        pygame.time.get_ticks(),
                    )
                    return
                except Exception:
                    pass

        if self.background is None:
            self.screen.fill((10, 0, 4))
            return

        image = self.background

        key = id(image)
        cached = self.background_cache.get(key)

        if cached is None:
            target_ratio = self.screen_width / self.screen_height
            source_ratio = image.get_width() / image.get_height()

            if source_ratio > target_ratio:
                new_h = self.screen_height
                new_w = int(new_h * source_ratio)
            else:
                new_w = self.screen_width
                new_h = int(new_w / source_ratio)

            scaled = pygame.transform.smoothscale(image, (new_w, new_h))

            offset_x = (new_w - self.screen_width) // 2
            offset_y = (new_h - self.screen_height) // 2

            cached = (scaled, offset_x, offset_y)

            if len(self.background_cache) < 60:
                self.background_cache[key] = cached

        scaled, offset_x, offset_y = cached

        self.screen.blit(scaled, (-offset_x, -offset_y))

        # tint + letterbox bars are static, so build them once
        size = (self.screen_width, self.screen_height)
        tint = self._bg_tint_cache.get(size)

        if tint is None:
            tint = pygame.Surface(size, pygame.SRCALPHA)
            tint.fill((12, 0, 10, 72))
            pygame.draw.rect(tint, (35, 0, 20, 78), (0, 0, size[0], 54))
            pygame.draw.rect(tint, (18, 0, 12, 96), (0, size[1] - 58, size[0], 58))
            self._bg_tint_cache.clear()
            self._bg_tint_cache[size] = tint

        self.screen.blit(tint, (0, 0))

    def draw_player(self):
        if self.invincible_timer > 0 and (self.invincible_timer // 5) % 2 == 0:
            return

        if self.player_ship_frames:
            image = self.player_ship_frames[self.player_ship_frame_index][0]
        else:
            image = self.loadout_image_scaled

        x, y = self.player_center()

        if image is None:
            try:
                self.player.draw(self.screen)
            except Exception:
                pass
        else:
            render = image
            self.screen.blit(render, render.get_rect(center=(int(x), int(y))))

        # Ship energy field
        if self.shield > 0:
            tint = SHIP_COLOR_TINTS.get(self.loadout_color, (100, 220, 255))
            shield_pulse = 0.5 + 0.5 * math.sin(self.game_time * 0.18)
            pygame.draw.ellipse(
                self.screen, (95, 20, 58),
                pygame.Rect(int(x - 58 - shield_pulse * 5), int(y - 50),
                            int(116 + shield_pulse * 10), 102), 2
            )
            pygame.draw.ellipse(
                self.screen, tint,
                pygame.Rect(int(x - 53 - shield_pulse * 4), int(y - 45),
                            int(106 + shield_pulse * 8), 92), 2
            )

        # Turbo status physically tied to the engine
        if self.turbo_active or self.turbo_energy < 99:
            tint = SHIP_COLOR_TINTS.get(self.loadout_color, (100, 220, 255))
            bar_w = 72
            bar_x = int(x - bar_w / 2)
            bar_y = int(y + 64)
            pygame.draw.rect(self.screen, (8, 12, 18), (bar_x, bar_y, bar_w, 5), border_radius=3)
            fill = int(bar_w * self.turbo_energy / self.turbo_max)
            if fill > 0:
                pygame.draw.rect(self.screen, tint, (bar_x, bar_y, fill, 5), border_radius=3)
            label = self.small_font.render("AFTERBURN", True, (185, 215, 225))
            self.screen.blit(label, (bar_x, bar_y + 7))

    def draw_enemies(self):
        for enemy in self.enemies:
            if enemy["dead"]:
                continue

            stats = ENEMY_STATS[enemy["type"]]
            accent = RARE_ENEMY_ACCENTS.get(enemy["type"], stats["color"])
            state = enemy["state"]
            cx = int(enemy["x"] + enemy["w"] * 0.5)
            cy = int(enemy["y"] + enemy["h"] * 0.5)
            top = int(enemy["y"])

            if state == "warning":
                tx = int(enemy["dive_x"])
                blink = (enemy["warn_timer"] // 4) % 2 == 0
                if blink:
                    for yy in range(int(enemy["y"] + enemy["h"]), self.screen_height, 30):
                        pygame.draw.line(self.screen, (255, 65, 85), (tx, yy), (tx, yy + 13), 1)
                    pygame.draw.polygon(
                        self.screen, (255, 65, 85),
                        [(tx - 10, self.screen_height - 72), (tx + 10, self.screen_height - 72), (tx, self.screen_height - 52)],
                    )
                    mark = self.small_font.render("INCOMING", True, (255, 105, 125))
                    self.screen.blit(mark, mark.get_rect(center=(cx, top - 24)))

            flick = 8 + 5 * math.sin(enemy["age"] * 0.5 + enemy["phase"])
            if state == "diving":
                flick += 20
            half = max(3, enemy["cell"])
            pygame.draw.polygon(
                self.screen,
                tuple(int(c * 0.65) for c in accent),
                [(cx - half, top + 3), (cx + half, top + 3), (cx, top - flick)],
            )

            if enemy["flash"] > 0:
                mode = "flash"
            elif state == "warning" and (enemy["warn_timer"] // 4) % 2 == 0:
                mode = "warn"
            else:
                mode = "normal"

            sprite = self.get_sprite(enemy["type"], enemy["cell"], enemy["frame"], mode)

            self.screen.blit(sprite, sprite.get_rect(center=(cx, cy)))

            if enemy["cracks"] and enemy["hp"] < enemy["max_hp"]:
                damage = 1 - enemy["hp"] / enemy["max_hp"]
                count = 1 + int(damage * (len(enemy["cracks"]) - 1))
                for (ax, ay), (bx, by) in enemy["cracks"][:count]:
                    pygame.draw.line(
                        self.screen, (15, 18, 28),
                        (int(enemy["x"] + ax), int(enemy["y"] + ay)),
                        (int(enemy["x"] + bx), int(enemy["y"] + by)), 2,
                    )

            if enemy.get("elite", False):
                mark_y = max(4, top - 7)
                pygame.draw.rect(
                    self.screen,
                    GOLD,
                    (int(enemy["x"] + enemy["w"] * 0.35), mark_y, int(enemy["w"] * 0.30), 2),
                )

            if enemy["hp"] < enemy["max_hp"] or enemy.get("elite", False):
                bar_w = int(enemy["w"])
                bar_y = int(enemy["y"] - 8)
                pygame.draw.rect(self.screen, (16, 20, 30), (int(enemy["x"]), bar_y, bar_w, 4), border_radius=2)
                pygame.draw.rect(
                    self.screen, accent,
                    (int(enemy["x"]), bar_y, int(bar_w * enemy["hp"] / max(1, enemy["max_hp"])), 4),
                    border_radius=2,
                )

    def draw_boss_escorts(self):
        for escort in self.boss_escorts:
            if escort["dead"]:
                continue

            cx = int(escort["x"] + escort["w"] * 0.5)
            cy = int(escort["y"] + escort["h"] * 0.5)

            frame = (escort["age"] // 24) % 2
            sprite = self.get_sprite("tank", escort["cell"], frame, "normal")

            self.screen.blit(sprite, sprite.get_rect(center=(cx, cy)))

            if escort["hp"] < escort["max_hp"]:
                bar_x = escort["x"]
                bar_y = escort["y"] - 7

                pygame.draw.rect(
                    self.screen,
                    (35, 10, 15),
                    (int(bar_x), int(bar_y), int(escort["w"]), 4),
                )
                pygame.draw.rect(
                    self.screen,
                    GOLD,
                    (
                        int(bar_x),
                        int(bar_y),
                        int(escort["w"] * (escort["hp"] / escort["max_hp"])),
                        4,
                    ),
                )

    def _get_glow(self, level):
        """Plasma aura for powered-up player bullets, built once per tier."""
        tier = 2 if level == 2 else 3
        glow = self._glow_cache.get(tier)

        if glow is None:
            if tier == 2:
                glow = pygame.Surface((32, 32), pygame.SRCALPHA)
                pygame.draw.circle(glow, (0, 180, 255, 60), (16, 16), 12)
                pygame.draw.circle(glow, (180, 240, 255, 120), (16, 16), 6)
            else:
                glow = pygame.Surface((48, 48), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 150, 0, 85), (24, 24), 18)
                pygame.draw.circle(glow, (255, 230, 120, 150), (24, 24), 10)
            self._glow_cache[tier] = glow

        return glow

    def draw_bullets(self):
        for bullet in self.bullets:
            try:
                bullet.draw(self.screen)
            except Exception:
                pygame.draw.rect(self.screen, (255, 255, 255), (bullet.x, bullet.y, 6, 18))

            lvl = getattr(bullet, "damage", 1)
            if lvl < 2:
                continue

            if hasattr(bullet, "get_center"):
                bx, by = bullet.get_center()
            else:
                bx, by = bullet.x, bullet.y

            glow = self._get_glow(lvl)
            half = glow.get_width() // 2
            self.screen.blit(
                glow, (int(bx - half), int(by - half)),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

    def _bullet_style(self, kind):
        if kind in ("enemy_bomb", "bomb"):
            return (255, 145, 45), (255, 95, 25), 1.55
        if kind in ("enemy_heavy", "boss"):
            return (205, 75, 255), (255, 55, 115), 1.45
        if kind == "enemy_guided":
            return (255, 70, 100), (255, 35, 80), 1.20
        return (255, 85, 95), (255, 30, 65), 1.0

    def _trail_glow(self, rr, trail, step):
        key = (rr, trail, step)
        surf = self._trail_cache.get(key)

        if surf is None:
            surf = pygame.Surface((rr * 8, rr * 8), pygame.SRCALPHA)
            pygame.draw.circle(
                surf, (*trail, max(18, 90 - step * 18)), (rr * 4, rr * 4), rr * 2
            )
            self._trail_cache[key] = surf

        return surf

    def _enemy_bullet_sprite(self, kind, radius, vx, vy):
        """Rotated + tinted bullet sprite, cached by kind / size / angle."""
        tint, _trail, scale = self._bullet_style(kind)

        # snap to 10 degrees so the cache stays small
        angle = int(round(math.degrees(math.atan2(vx, -vy)) / 10.0)) * 10 % 360
        key = (kind, radius, angle)

        sprite = self._ebullet_cache.get(key)
        if sprite is not None:
            return sprite

        image = self.bullet_image

        if image is not None:
            try:
                size = max(10, int(radius * 3.0 * scale))
                sprite = pygame.transform.smoothscale(image, (size, size * 2))
                sprite = pygame.transform.rotate(sprite, angle)

                tint_surface = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
                tint_surface.fill((*tint, 255))
                sprite.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            except Exception:
                sprite = None

        if sprite is None:
            sprite = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            c = radius + 1
            pygame.draw.circle(sprite, tint, (c, c), radius)
            pygame.draw.circle(sprite, (255, 235, 235), (c, c), max(2, radius // 2))

        if len(self._ebullet_cache) > 400:
            self._ebullet_cache.clear()
        self._ebullet_cache[key] = sprite

        return sprite

    def draw_enemy_bullets(self):
        bullets = self.enemy_bullets + self.boss_bullets

        # fewer trail segments when the screen is crowded
        segments = 4 if len(bullets) <= 18 else 2

        for bullet in bullets:
            radius = max(4, int(bullet.get("radius", 5)))
            x = int(bullet["x"])
            y = int(bullet["y"])
            vx = float(bullet.get("vx", 0))
            vy = float(bullet.get("vy", 1))
            kind = bullet.get("kind", "enemy_shot")

            _tint, trail, _scale = self._bullet_style(kind)

            speed = max(1.0, math.sqrt(vx * vx + vy * vy))
            nx, ny = vx / speed, vy / speed
            tail = 22 + radius * 2

            for i in range(segments):
                step = i * (4 // segments)
                tx = int(x - nx * (tail * (i + 1) / segments))
                ty = int(y - ny * (tail * (i + 1) / segments))
                rr = max(1, radius - step)
                glow = self._trail_glow(rr, trail, step)
                self.screen.blit(
                    glow, (tx - rr * 4, ty - rr * 4),
                    special_flags=pygame.BLEND_RGBA_ADD,
                )

            sprite = self._enemy_bullet_sprite(kind, radius, vx, vy)
            self.screen.blit(sprite, sprite.get_rect(center=(x, y)))

    def draw_boss(self):
        if not self.boss:
            return

        image = self.boss["image"]

        if image is not None:
            if self.boss_flash_timer > 0 and (self.boss_flash_timer // 3) % 2 == 0:
                render_image = image.copy()

                overlay = pygame.Surface(render_image.get_size(), pygame.SRCALPHA)
                overlay.fill((255, 60, 60, 120))

                render_image.blit(
                    overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD
                )
            else:
                render_image = image

            rect = render_image.get_rect(
                center=(
                    int(self.boss["x"] + self.boss["w"] * 0.5),
                    int(self.boss["y"] + self.boss["h"] * 0.5),
                )
            )

            self.screen.blit(render_image, rect)

        bar_w = max(160, min(int(self.screen_width * 0.50), self.screen_width - 540))
        strip = pygame.Rect(0, 0, bar_w + 24, 48)
        strip.midtop = (self.screen_width // 2, 8)
        self._paper_panel(self.screen, strip, radius=8, edge=2)

        phase_labels = {
            0: "Boss",
            1: "Boss \u00b7 Enraged",
            2: "Boss \u00b7 Final phase",
        }
        put_text(
            self.screen, self.j_small,
            phase_labels.get(self.boss_phase, "Boss"),
            ERROR, (strip.x + 12, strip.y + 5), "topleft",
        )
        put_text(
            self.screen, self.j_small, f"Wave {self.wave}",
            INK_SOFT, (strip.right - 12, strip.y + 5), "topright",
        )

        track = pygame.Rect(strip.x + 12, strip.y + 28, bar_w, 12)
        pygame.draw.rect(self.screen, PAPER_TRACK, track, border_radius=6)

        health_ratio = max(0.0, self.boss["hp"] / self.boss["max_hp"])
        bar_color = (205, 60, 70)
        if self.boss_phase >= 2:
            bar_color = (225, 110, 40)
        elif self.boss_phase >= 1:
            bar_color = (230, 170, 50)

        fill_w = int(bar_w * health_ratio)
        if fill_w > 0:
            pygame.draw.rect(
                self.screen, bar_color,
                (track.x, track.y, fill_w, track.h),
                border_radius=min(6, max(1, fill_w // 2)),
            )
        pygame.draw.rect(self.screen, OUTLINE, track, 2, border_radius=6)

    def draw_particles(self):
        for p in self.particles:
            ratio = max(0, p["life"] / p["max_life"])
            size = max(1, int(p["size"] * ratio))

            pygame.draw.circle(
                self.screen,
                p["color"],
                (int(p["x"]), int(p["y"])),
                size,
            )

    def draw_rings(self):
        for ring in self.rings:
            ratio = ring["life"] / ring["max_life"]
            color = tuple(int(c * ratio) for c in ring["color"])
            width = max(1, int(3 * ratio))

            pygame.draw.circle(
                self.screen,
                color,
                (int(ring["x"]), int(ring["y"])),
                max(2, int(ring["r"])),
                width,
            )

    def draw_powerups(self):
        letters = {"rapid": "R", "double": "D", "shield": "S"}

        colors = {
            "rapid": (255, 185, 40),
            "double": (70, 210, 255),
            "shield": (170, 100, 255),
        }

        for powerup in self.powerups:
            x = int(powerup["x"])
            y = int(powerup["y"])

            pygame.draw.circle(self.screen, colors[powerup["type"]], (x, y), 14)
            pygame.draw.circle(self.screen, WHITE, (x, y), 14, 2)

            text = self.small_font.render(
                letters[powerup["type"]], True, (20, 20, 25)
            )

            self.screen.blit(
                text,
                (x - text.get_width() // 2, y - text.get_height() // 2),
            )

    # ------------------------------------------------------------------
    # Journal helpers
    # ------------------------------------------------------------------

    def _ui_hover(self):
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

    def _ui_click(self):
        if ui_sounds is None:
            return
        try:
            ui_sounds.click()
        except Exception:
            pass

    def _ui_back(self):
        if ui_sounds is None:
            return
        try:
            ui_sounds.back()
            return
        except Exception:
            pass
        self._ui_click()

    def _paper_panel(self, surface, rect, radius=8, edge=2, tape=False):
        pygame.draw.rect(
            surface, PAPER_SHADOW, rect.move(4, 5), border_radius=radius
        )
        pygame.draw.rect(surface, PAPER, rect, border_radius=radius)
        pygame.draw.rect(surface, OUTLINE, rect, edge, border_radius=radius)

        if tape:
            try:
                draw_tape(surface, (rect.centerx, rect.y + 4), 0, (110, 30))
            except Exception:
                pass

    def _journal_button(self, rect, label, color, active):
        r = rect.copy()
        if active:
            r.y -= 3

        pygame.draw.rect(
            self.screen, BUTTON_SHADOW, r.move(0, 3), border_radius=10
        )
        pygame.draw.rect(self.screen, color, r, border_radius=10)
        pygame.draw.rect(
            self.screen, OUTLINE, r, 3 if active else 2, border_radius=10
        )
        put_text(self.screen, self.j_button, label, INK, r.center, "center")

    def _journal_menu_nav(self, events, rects):
        """Hover / arrow-key / click handling shared by pause and game over.

        Returns the activated button index, or None.
        """
        mouse = pygame.mouse.get_pos()

        hover = None
        for i, rect in enumerate(rects):
            if rect.collidepoint(mouse):
                hover = i
                break

        if hover is not None and hover != self._menu_prev_hover:
            self.menu_selected = hover
            self._ui_hover()
        self._menu_prev_hover = hover

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
                    self.menu_selected = (self.menu_selected - 1) % len(rects)
                    self._ui_hover()
                elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
                    self.menu_selected = (self.menu_selected + 1) % len(rects)
                    self._ui_hover()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self._ui_click()
                    return self.menu_selected

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        self.menu_selected = i
                        self._ui_click()
                        return i

        return None

    def _draw_banner(self, lines, center, alpha):
        """Fading taped paper banner. lines = [(text, font, color), ...]."""
        if alpha <= 0 or not lines:
            return

        images = [fnt.render(text, True, color) for text, fnt, color in lines]
        gap = 6
        width = max(img.get_width() for img in images) + 64
        height = sum(img.get_height() for img in images) + gap * (len(images) - 1) + 34

        layer = pygame.Surface((width + 10, height + 12), pygame.SRCALPHA)
        self._paper_panel(layer, pygame.Rect(0, 0, width, height), radius=10, edge=3, tape=True)

        y = 17
        for img in images:
            layer.blit(img, img.get_rect(midtop=(width // 2, y)))
            y += img.get_height() + gap

        layer.set_alpha(max(0, min(255, int(alpha))))
        self.screen.blit(layer, layer.get_rect(center=center))

    def _draw_heart_icon(self, center, alive):
        if self.heart_image is not None:
            cache_key = "_heart_alive" if alive else "_heart_dim"
            image = getattr(self, cache_key, None)

            if image is None:
                try:
                    image = pygame.transform.smoothscale(self.heart_image, (22, 22))
                    if not alive:
                        image.set_alpha(55)
                except Exception:
                    image = None
                setattr(self, cache_key, image)

            if image is not None:
                self.screen.blit(image, image.get_rect(center=center))
                return

        x, y = center
        color = (220, 50, 70) if alive else PAPER_RULE
        pygame.draw.circle(self.screen, color, (x - 4, y - 3), 6)
        pygame.draw.circle(self.screen, color, (x + 4, y - 3), 6)
        pygame.draw.polygon(
            self.screen, color, [(x - 10, y - 1), (x + 10, y - 1), (x, y + 10)]
        )

    # ------------------------------------------------------------------
    # HUD (journal style)
    # ------------------------------------------------------------------

    def draw_hud(self):
        width = self.screen_width
        height = self.screen_height
        center_x = width // 2

        # Score card, top-left
        card = pygame.Rect(12, 8, 232, 84)
        self._paper_panel(self.screen, card, radius=8, edge=2)
        put_text(self.screen, self.j_small, "Score", INK_SOFT,
                 (card.x + 14, card.y + 6), "topleft")
        put_text(self.screen, self.j_num, f"{self.score:,}", INK,
                 (card.x + 14, card.y + 22), "topleft")
        put_text(self.screen, self.j_small, f"Best {self.high_score:,}", GOLD_INK,
                 (card.x + 14, card.y + 58), "topleft")

        # Wave tag, top-centre (the boss bar takes this spot during a boss)
        if not self.boss_active:
            ship_name = str(getattr(self, "loadout_ship", "starter")).title()
            label = f"Wave {self.wave:02d}  \u00b7  {ship_name}"
            tag = pygame.Rect(0, 0, max(190, self.j_text.size(label)[0] + 36), 34)
            tag.midtop = (center_x, 8)
            self._paper_panel(self.screen, tag, radius=8, edge=2)
            put_text(self.screen, self.j_text, label, INK, tag.center, "center")

        if self.game_state == "playing" and not self.boss_active:
            remaining = len([e for e in self.enemies if not e["dead"]])
            total = max(remaining, self.enemy_count_target)
            ratio = remaining / max(1, total)

            strip = pygame.Rect(0, 0, 240, 34)
            strip.midtop = (center_x, 48)
            self._paper_panel(self.screen, strip, radius=8, edge=2)

            status = "Sector clear" if remaining == 0 else f"Hostiles {remaining:02d}"
            put_text(self.screen, self.j_small, status,
                     GREEN_INK if remaining == 0 else INK_SOFT,
                     (strip.centerx, strip.y + 3), "midtop")

            track = pygame.Rect(strip.x + 12, strip.y + 25, strip.w - 24, 5)
            pygame.draw.rect(self.screen, PAPER_TRACK, track, border_radius=3)
            fill = int(track.w * ratio)
            if fill > 0:
                pygame.draw.rect(
                    self.screen,
                    (205, 60, 90) if remaining else (60, 160, 95),
                    (track.x, track.y, fill, track.h),
                    border_radius=3,
                )

        self.draw_lives()

        if self.combo > 1:
            tag = pygame.Rect(0, 0, 130, 28)
            tag.midbottom = (center_x, height - 10)
            self._paper_panel(self.screen, tag, radius=8, edge=2)
            put_text(self.screen, self.j_text, f"Chain x{self.combo}", GOLD_INK,
                     tag.center, "center")

    def draw_lives(self):
        gap = 26
        strip_w = max(92, self.max_lives * gap + 20)
        strip = pygame.Rect(self.screen_width - 12 - strip_w, 8, strip_w, 58)
        self._paper_panel(self.screen, strip, radius=8, edge=2)

        put_text(self.screen, self.j_small, "Lives", INK_SOFT,
                 (strip.centerx, strip.y + 4), "midtop")

        first_x = strip.centerx - (self.max_lives * gap) // 2 + gap // 2
        for i in range(self.max_lives):
            self._draw_heart_icon((first_x + i * gap, strip.y + 39), i < self.lives)

    def draw_status_effects(self):
        parts = [(f"Power Lv.{self.fire_level}", GOLD_INK)]

        if self.rapid_fire > 0:
            parts.append((f"Rapid {self.rapid_fire // 60 + 1}s", BLUE_INK))
        if self.double_shot > 0:
            parts.append((f"Double {self.double_shot // 60 + 1}s", BLUE_INK))
        if self.shield > 0:
            parts.append((f"Shield {self.shield // 60 + 1}s", BLUE_INK))

        spacing = 16
        total = sum(self.j_small.size(text)[0] for text, _c in parts)
        total += spacing * (len(parts) - 1)

        strip = pygame.Rect(10, self.screen_height - 38, total + 24, 28)
        self._paper_panel(self.screen, strip, radius=8, edge=2)

        x = strip.x + 12
        for text, color in parts:
            rect = put_text(self.screen, self.j_small, text, color,
                            (x, strip.centery), "midleft")
            x += rect.width + spacing

    def draw_vignette(self):
        alpha = min(130, self.damage_flash * 5) if self.damage_flash > 0 else 0
        key = (self.screen_width, self.screen_height, alpha)

        surface = self._vignette_cache.get(key)

        if surface is None:
            surface = pygame.Surface(
                (self.screen_width, self.screen_height), pygame.SRCALPHA
            )

            pygame.draw.rect(
                surface,
                (0, 0, 0, 28),
                (0, 0, self.screen_width, self.screen_height),
                20,
            )

            if alpha > 0:
                pygame.draw.rect(
                    surface,
                    (255, 0, 20, alpha),
                    (0, 0, self.screen_width, self.screen_height),
                    15,
                )

            if len(self._vignette_cache) > 40:
                self._vignette_cache.clear()
            self._vignette_cache[key] = surface

        self.screen.blit(surface, (0, 0))

    def draw_wave_message(self):
        if self.wave_intro_timer <= 0:
            return

        message = (
            f"Boss wave {self.wave}" if self.boss_active else f"Wave {self.wave}"
        )

        lines = [(message, self.j_banner, ERROR if self.boss_active else INK)]

        if not self.boss_active and self.wave_composition_preview:
            labels = {
                "grunt": "Grunt",
                "scout": "Scout",
                "weaver": "Weaver",
                "diver": "Diver",
                "bomber": "Bomber",
                "tank": "Tank",
            }

            parts = [
                f"{labels[key]} x{self.wave_composition_preview.get(key, 0)}"
                for key in labels
                if self.wave_composition_preview.get(key, 0) > 0
            ]

            if parts:
                lines.append(("Incoming:  " + "   ".join(parts), self.j_text, BLUE_INK))

        self._draw_banner(
            lines,
            (self.screen_width // 2, int(self.screen_height * 0.26)),
            min(255, self.wave_intro_timer * 4),
        )

    def draw_fire_level_flash(self):
        if self.fire_level_flash_timer <= 0:
            return

        self._draw_banner(
            [(f"Firepower up! Lv.{self.fire_level}", self.j_big, GOLD_INK)],
            (self.screen_width // 2, int(self.screen_height * 0.40)),
            min(255, self.fire_level_flash_timer * 6),
        )

    def draw_world(self):
        self.draw_enemies()
        self.draw_bullets()
        self.draw_enemy_bullets()
        self.draw_boss()
        self.draw_boss_escorts()
        self.draw_player()
        self.draw_particles()
        self.draw_rings()
        self.draw_powerups()

    def draw(self):
        self.draw_background()

        shake_x = 0
        shake_y = 0

        if self.screen_shake > 0:
            power = self.screen_shake_power
            shake_x = random.randint(-power, power)
            shake_y = random.randint(-power, power)

        if shake_x or shake_y:
            game = self._shake_layer

            if game is None or game.get_size() != (self.screen_width, self.screen_height):
                game = pygame.Surface(
                    (self.screen_width, self.screen_height), pygame.SRCALPHA
                )
                self._shake_layer = game

            game.fill((0, 0, 0, 0))

            old_screen = self.screen
            self.screen = game

            self.draw_world()

            self.screen = old_screen
            self.screen.blit(game, (shake_x, shake_y))
        else:
            self.draw_world()

        self.draw_hud()
        self.draw_status_effects()

        if self.mobile_enabled() and self.game_state in ("playing", "boss"):
            self.draw_touch_controls()

        self.draw_wave_message()
        self.draw_fire_level_flash()
        self.draw_vignette()

    # ------------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------------

    def _pause_action(self, index):
        if index == 0:
            self.game_state = self.previous_game_state
            self.resume_music()
        elif index == 1:
            self.start_game()
        else:
            self.stop_music()
            self.game_state = "main_menu"

    def draw_pause(self, events):
        self.draw_overlay(150)

        width, height = self.screen_width, self.screen_height
        card = pygame.Rect(0, 0, min(500, width - 60), min(410, height - 60))
        card.center = (width // 2, height // 2)
        self._paper_panel(self.screen, card, radius=10, edge=3, tape=True)

        put_text(self.screen, self.j_title, "Paused", INK,
                 (card.centerx, card.y + 58), "center")
        pygame.draw.line(self.screen, INK_SOFT,
                         (card.centerx - 70, card.y + 88),
                         (card.centerx + 70, card.y + 88), 2)
        put_text(self.screen, self.j_sub, "The battle awaits", INK_SOFT,
                 (card.centerx, card.y + 108), "center")

        entries = (
            ("Resume", TAB_YELLOW),
            ("Restart", TAB_ORANGE),
            ("Main menu", TAB_PINK),
        )

        button_w = min(300, card.w - 80)
        button_h = 48
        gap = 14
        start_y = card.y + 140

        rects = []
        for i in range(len(entries)):
            rect = pygame.Rect(0, 0, button_w, button_h)
            rect.centerx = card.centerx
            rect.y = start_y + i * (button_h + gap)
            rects.append(rect)

        chosen = self._journal_menu_nav(events, rects)

        for i, (label, color) in enumerate(entries):
            self._journal_button(rects[i], label, color, i == self.menu_selected)

        put_text(self.screen, self.j_sub, "Esc resume  \u00b7  R restart  \u00b7  M menu",
                 INK_SOFT, (card.centerx, card.bottom - 28), "center")

        if chosen is not None:
            self._pause_action(chosen)
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    self._ui_back()
                    self._pause_action(0)
                    return
                if event.key == pygame.K_r:
                    self._ui_click()
                    self._pause_action(1)
                    return
                if event.key == pygame.K_m:
                    self._ui_back()
                    self._pause_action(2)
                    return

    def draw_game_over(self, events):
        self.draw_overlay(160)

        width, height = self.screen_width, self.screen_height
        card = pygame.Rect(0, 0, min(540, width - 60), min(470, height - 50))
        card.center = (width // 2, height // 2)
        self._paper_panel(self.screen, card, radius=10, edge=3, tape=True)

        put_text(self.screen, self.j_title, "Game over", ERROR,
                 (card.centerx, card.y + 56), "center")
        pygame.draw.line(self.screen, INK_SOFT,
                         (card.centerx - 80, card.y + 86),
                         (card.centerx + 80, card.y + 86), 2)

        if journal_rank is not None:
            try:
                rank_name, rank_color = journal_rank(self.high_score)[:2]
            except Exception:
                rank_name, rank_color = "ROOKIE", INK_SOFT
        else:
            rank_name, rank_color = "ROOKIE", INK_SOFT

        x0 = card.x + 48
        right_edge = card.right - 48

        rows = (
            ("Score", f"{self.score:,}", INK),
            ("Best", f"{self.high_score:,}", GOLD_INK),
            ("Wave", str(self.wave), BLUE_INK),
            ("Rank", rank_name.title(), INK),
        )

        for i, (label, value, color) in enumerate(rows):
            line_y = card.y + 126 + i * 38
            put_text(self.screen, self.j_text, label, INK_SOFT,
                     (x0, line_y - 6), "bottomleft")
            value_rect = put_text(self.screen, self.j_num if i == 0 else self.j_text,
                                  value, color, (right_edge, line_y - 6), "bottomright")

            if label == "Rank":
                badge = (value_rect.left - 20, value_rect.centery)
                pygame.draw.circle(self.screen, rank_color, badge, 9)
                pygame.draw.circle(self.screen, OUTLINE, badge, 9, 2)

            pygame.draw.line(self.screen, PAPER_RULE,
                             (x0 - 6, line_y), (right_edge + 6, line_y), 1)

        if self.new_record:
            note = pygame.Rect(0, 0, 190, 30)
            note.center = (card.centerx, card.y + 126 + 4 * 38 + 18)
            alpha_rect(self.screen, (*HIGHLIGHT, 150), note, 8)
            put_text(self.screen, self.j_text, "New record!", GOLD_INK,
                     note.center, "center")

        entries = (("Play again", TAB_YELLOW), ("Main menu", TAB_PINK))

        button_w = min(300, card.w - 80)
        button_h = 48
        menu_rect = pygame.Rect(0, 0, button_w, button_h)
        menu_rect.midbottom = (card.centerx, card.bottom - 28)
        play_rect = pygame.Rect(0, 0, button_w, button_h)
        play_rect.midbottom = (card.centerx, menu_rect.top - 12)
        rects = [play_rect, menu_rect]

        chosen = self._journal_menu_nav(events, rects)

        for i, (label, color) in enumerate(entries):
            self._journal_button(rects[i], label, color, i == self.menu_selected)

        if chosen is not None:
            if chosen == 0:
                self.start_game()
            else:
                self.stop_music()
                self.game_state = "main_menu"
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self._ui_click()
                    self.start_game()
                    return
                if event.key in (pygame.K_ESCAPE, pygame.K_m):
                    self._ui_back()
                    self.stop_music()
                    self.game_state = "main_menu"
                    return

    def draw_button(self, rect, label):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        self._journal_button(rect, label, TAB_YELLOW, hovered)

    def draw_overlay(self, alpha):
        key = (self.screen_width, self.screen_height, alpha)
        overlay = self._overlay_cache.get(key)

        if overlay is None:
            overlay = pygame.Surface(
                (self.screen_width, self.screen_height), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, alpha))
            self._overlay_cache[key] = overlay

        self.screen.blit(overlay, (0, 0))

    def draw_centered(self, text, y_ratio):
        self.screen.blit(
            text,
            (
                self.screen_width // 2 - text.get_width() // 2,
                int(self.screen_height * y_ratio),
            ),
        )

    def end_game(self):
        if self.game_state == "game_over":
            return

        self.game_state = "game_over"
        self.menu_selected = 0
        self._menu_prev_hover = None

        self.stop_music()

        # must be computed before high_score is updated below
        self.new_record = self.score > self.high_score

        if self.score > self.high_score:
            self.high_score = self.score

        if self.player_id is not None and not self.score_saved:
            try:
                save_score(self.player_id, self.score)
                self.score_saved = True
            except Exception:
                pass

        self.play_sound(self.game_over_sound)

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    def is_playing(self):
        return self.game_state in ("playing", "boss")

    def is_paused(self):
        return self.game_state == "paused"

    def is_game_over(self):
        return self.game_state == "game_over"

    def is_main_menu(self):
        return self.game_state == "main_menu"