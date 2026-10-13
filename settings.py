import json
import os


# =========================================================
# GAME SETTINGS
# =========================================================
#
# This file is split into two parts:
#
#   1) STATIC CONSTANTS   — things that never change at runtime
#      (screen size, palette, difficulty presets, fonts...)
#
#   2) USER PREFERENCES   — things the player can change from the
#      in-game Settings screen (volume, difficulty, fullscreen...).
#      These are loaded from / saved to a small JSON file so they
#      persist between sessions.
#
# =========================================================


# =========================================================
# DISPLAY
# =========================================================

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700

FPS = 60

GAME_TITLE = "Space Invaders - Patalinghog"


# =========================================================
# COLOR PALETTE
# =========================================================
# Grouped by purpose so it reads like a real design system
# instead of a flat list of tuples.

# --- Core neutrals ---
BLACK = (5, 5, 20)
WHITE = (255, 255, 255)
MUTED = (150, 155, 175)          # secondary text / hints
PANEL_BG = (18, 20, 38)          # cards / panels
PANEL_BORDER = (60, 65, 100)

# --- Brand accents ---
CYAN = (0, 220, 255)
BLUE = (50, 100, 255)

RED = (255, 60, 60)
GREEN = (50, 255, 100)
YELLOW = (255, 220, 50)

PURPLE = (180, 70, 255)
ORANGE = (255, 130, 30)
GOLD = (255, 215, 0)

# --- Semantic aliases (use these in UI code so re-theming is a one-line change) ---
COLOR_PRIMARY = CYAN
COLOR_SECONDARY = BLUE
COLOR_SUCCESS = GREEN
COLOR_DANGER = RED
COLOR_WARNING = YELLOW
COLOR_ACCENT = PURPLE

# --- UI element states ---
BUTTON_IDLE = (30, 70, 160)
BUTTON_HOVER = (45, 100, 210)
BUTTON_PRESSED = (20, 50, 120)
BUTTON_DISABLED = (60, 60, 70)

SLIDER_TRACK = (40, 44, 70)
SLIDER_FILL = CYAN
SLIDER_KNOB = WHITE

TOGGLE_ON = GREEN
TOGGLE_OFF = (80, 84, 100)


# =========================================================
# TYPOGRAPHY SCALE
# =========================================================
# Relative sizes as a fraction of screen width — matches the
# `int(width * X)` pattern already used across your screens.

FONT_SCALE_TITLE = 0.05
FONT_SCALE_HEADING = 0.032
FONT_SCALE_BODY = 0.022
FONT_SCALE_HINT = 0.014


# =========================================================
# UI MOTION / JUICE CONSTANTS
# =========================================================
# Centralizing these means every screen (menu, game over,
# settings...) feels consistent instead of hand-tuned per file.

ENTRANCE_FADE_FRAMES = 28
ENTRANCE_SHAKE_FRAMES = 14
ENTRANCE_SHAKE_STRENGTH = 10

BUTTON_HOVER_GROW = 0.05
BUTTON_HOVER_LERP_SPEED = 0.25

PARTICLE_BURST_COUNT = 40
PARTICLE_BURST_COUNT_CELEBRATION = 90


# =========================================================
# DIFFICULTY PRESETS
# =========================================================

DIFFICULTIES = {
    "EASY": {
        "label": "EASY",
        "color": GREEN,
        "enemy_speed_mult": 0.75,
        "enemy_fire_rate_mult": 0.7,
        "player_lives": 5,
        "score_mult": 0.8,
    },
    "NORMAL": {
        "label": "NORMAL",
        "color": CYAN,
        "enemy_speed_mult": 1.0,
        "enemy_fire_rate_mult": 1.0,
        "player_lives": 3,
        "score_mult": 1.0,
    },
    "HARD": {
        "label": "HARD",
        "color": ORANGE,
        "enemy_speed_mult": 1.3,
        "enemy_fire_rate_mult": 1.4,
        "player_lives": 2,
        "score_mult": 1.3,
    },
    "INSANE": {
        "label": "INSANE",
        "color": RED,
        "enemy_speed_mult": 1.6,
        "enemy_fire_rate_mult": 1.8,
        "player_lives": 1,
        "score_mult": 1.6,
    },
}

DIFFICULTY_ORDER = ["EASY", "NORMAL", "HARD", "INSANE"]


# =========================================================
# KEY BINDINGS (defaults — could be remapped later)
# =========================================================

import pygame  # noqa: E402  (kept below settings for readability above)

DEFAULT_KEYBINDS = {
    "move_left": pygame.K_a,
    "move_right": pygame.K_d,
    "shoot": pygame.K_SPACE,
    "pause": pygame.K_ESCAPE,
    "fullscreen_toggle": pygame.K_F11,
}


# =========================================================
# USER PREFERENCES (persisted)
# =========================================================

SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "user_settings.json"
)

DEFAULT_PREFERENCES = {
    "master_volume": 0.8,     # 0.0 - 1.0
    "music_volume": 0.6,      # 0.0 - 1.0
    "sfx_volume": 1.0,        # 0.0 - 1.0
    "fullscreen": True,
    "screen_shake": True,
    "difficulty": "NORMAL",
    "mobilecontrols": False,  # on-screen move/shoot buttons
}


def load_preferences():
    """
    Loads saved player preferences from disk, falling back to
    defaults for any missing/corrupt fields so the game never
    crashes on a bad or partial settings file.
    """

    prefs = dict(DEFAULT_PREFERENCES)

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                saved = json.load(f)

            for key in DEFAULT_PREFERENCES:
                if key in saved:
                    prefs[key] = saved[key]

        except (json.JSONDecodeError, OSError):
            # Corrupt or unreadable file — silently fall back to defaults
            pass

    return prefs


def save_preferences(prefs):
    """Writes the given preferences dict to disk as JSON."""

    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(prefs, f, indent=2)
        return True

    except OSError:
        return False


# Loaded once at import time; screens can mutate this dict directly
# and call save_preferences(PREFERENCES) to persist changes.
PREFERENCES = load_preferences()


# =========================================================
# LIVE VOLUME APPLICATION
# =========================================================
#
# Call this any time master_volume / music_volume / sfx_volume
# change (e.g. while dragging a slider on the Settings screen)
# so the change is heard immediately instead of only on next
# sound load. Safe to call even if the mixer isn't initialized
# yet or ui_sounds doesn't expose set_volume (checked defensively).

def apply_volume_settings():

    master = max(0.0, min(1.0, float(PREFERENCES.get("master_volume", 1.0))))
    music = max(0.0, min(1.0, float(PREFERENCES.get("music_volume", 1.0))))
    sfx = max(0.0, min(1.0, float(PREFERENCES.get("sfx_volume", 1.0))))

    # --- background music ---
    try:
        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.set_volume(master * music)
    except pygame.error:
        pass

    # --- UI click/hover sounds ---
    try:
        from managers.ui_sounds import ui_sounds

        if hasattr(ui_sounds, "set_volume"):
            ui_sounds.set_volume(master * sfx)

    except Exception:
        # ui_sounds not importable yet, or has no set_volume method.
        # Gameplay SFX in GameManager already recompute their own
        # volume from PREFERENCES right before playing, so this
        # only affects menu click/hover sounds.
        pass