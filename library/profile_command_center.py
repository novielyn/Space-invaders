import os
import json
import time
import math
import random
import pygame

try:
    import tkinter
    from tkinter import filedialog
except Exception:
    tkinter = None
    filedialog = None

import theme

from theme import (
    menu_font,
    draw_background,
    draw_panel,
    draw_title,
    draw_input,
    draw_button,
    draw_cursor,
    draw_eye_icon,
    draw_person_icon,
    TITLE_RED,
    TITLE_SHADOW,
    MENU_BLUE,
    MENU_WHITE,
    MUTED,
    CURSOR_RED,
    ERROR_RED,
    SUCCESS_GREEN,
    FIELD_FILL,
    FIELD_EDGE,
)

try:
    import database
except Exception:
    database = None

# The shop keeps a local economy cache, while signed-in players may also have
# their balance and fleet in MySQL.  Keep both sources available so the profile
# still works offline and never crashes when the database is unavailable.
try:
    from economy import (
        get_coins as get_cached_coins,
        get_owned_ships as get_cached_ships,
        delete_player_data,
    )
except Exception:
    def get_cached_coins(player_id, default=0):
        return default

    def get_cached_ships(player_id):
        return []

    def delete_player_data(player_id):
        return False

DEFAULT_WIDTH = 900
DEFAULT_HEIGHT = 600

MAX_USERNAME_LENGTH = 40
MAX_EMAIL_LENGTH = 60
MAX_PASSWORD_LENGTH = 40
MAX_GAMER_TAG_LENGTH = 24
MAX_BIO_LENGTH = 90

AVATAR_KINDS = (
    "hood",
    "ninja",
    "cat",
    "wizard",
    "robot",
    "mohawk",
    "cap",
    "visor",
)

LINK_PROVIDERS = (
    "FACEBOOK",
    "GOOGLE",
    "DISCORD",
)

VISIBILITY_OPTIONS = (
    "online",
    "offline",
    "private",
)

ASSET_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ),
    "assets"
)

_avatar_cache = {}
_ship_cache = {}
_preset_cache = {}


def get_value(player, *keys, default=""):
    if not isinstance(player, dict):
        return default

    for key in keys:
        if key in player and player[key] is not None:
            return player[key]

    return default


def safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def number(value):
    try:
        return f"{int(float(value)):,}"
    except Exception:
        return str(value)


def get_profile_coins(player_id, player):
    """Return the most current usable coin balance without assuming a DB."""
    value = get_value(player, "coins", "credits", "money", default=None)
    if value is not None:
        return max(0, safe_int(value))

    try:
        return max(0, safe_int(get_cached_coins(player_id, 0)))
    except Exception:
        return 0


def get_profile_ships(player_id):
    """Read database fleet records first, then the shop's offline cache."""
    ships = []

    if database is not None:
        getter = getattr(database, "get_owned_ships", None)
        if callable(getter):
            try:
                records = getter(player_id) or []
                for record in records:
                    name = (
                        record.get("ship_name")
                        if isinstance(record, dict)
                        else record
                    )
                    if name:
                        ships.append(str(name))
            except Exception:
                ships = []

    if not ships:
        try:
            ships = list(get_cached_ships(player_id) or [])
        except Exception:
            ships = []

    return list(dict.fromkeys(str(ship) for ship in ships if str(ship).strip()))


def get_gamer_rank(high_score):
    tiers = (
        (30000, "MYTHIC"),
        (15000, "LEGEND"),
        (7000, "GRANDMASTER"),
        (3500, "MASTER"),
        (1500, "ELITE"),
        (500, "VETERAN"),
        (0, "ROOKIE"),
    )
    for threshold, title in tiers:
        if high_score >= threshold:
            return title
    return "ROOKIE"


def fit_text(font, text, width):
    text = str(text or "")

    if font.size(text)[0] <= width:
        return text

    while text and font.size(
        text + "..."
    )[0] > width:
        text = text[:-1]

    return text + "..."


def cache_file():
    return os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "profile_settings.json"
    )


def load_settings(player_id):
    if player_id is None:
        return {}

    try:
        path = cache_file()

        if not os.path.isfile(path):
            return {}

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {}

        result = data.get(
            str(player_id),
            {}
        )

        return (
            result
            if isinstance(result, dict)
            else {}
        )

    except Exception:
        return {}


def save_settings(player_id, settings):
    if player_id is None:
        return

    try:
        path = cache_file()
        data = {}

        if os.path.isfile(path):
            try:
                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as file:
                    old_data = json.load(file)

                if isinstance(old_data, dict):
                    data = old_data

            except Exception:
                data = {}

        data[str(player_id)] = settings

        temp_path = path + ".tmp"

        with open(
            temp_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                indent=2
            )

        os.replace(
            temp_path,
            path
        )

    except Exception:
        pass


def load_custom_avatar(path, size):
    if not path:
        return None

    key = (
        path,
        int(size)
    )

    if key in _avatar_cache:
        return _avatar_cache[key]

    image = None

    try:
        image = pygame.image.load(
            path
        ).convert_alpha()

        image = pygame.transform.smoothscale(
            image,
            (
                int(size),
                int(size)
            )
        )

    except Exception:
        image = None

    _avatar_cache[key] = image

    return image


def load_preset_avatar(kind, size):
    key = (
        kind,
        int(size)
    )

    if key in _preset_cache:
        return _preset_cache[key]

    candidates = [
        os.path.join(
            ASSET_DIR,
            f"avatar_{kind}.png"
        ),
        os.path.join(
            ASSET_DIR,
            "avatars",
            f"{kind}.png"
        ),
        os.path.join(
            ASSET_DIR,
            f"{kind}.png"
        ),
    ]

    image = None

    for path in candidates:

        if not os.path.isfile(path):
            continue

        try:
            image = pygame.image.load(
                path
            ).convert_alpha()

            image = pygame.transform.smoothscale(
                image,
                (
                    int(size),
                    int(size)
                )
            )

            break

        except Exception:
            image = None

    _preset_cache[key] = image

    return image


def circular_image(surface):
    if surface is None:
        return None

    width, height = surface.get_size()
    size = min(
        width,
        height
    )

    result = pygame.Surface(
        (
            size,
            size
        ),
        pygame.SRCALPHA
    )

    source = pygame.transform.smoothscale(
        surface,
        (
            size,
            size
        )
    )

    mask = pygame.Surface(
        (
            size,
            size
        ),
        pygame.SRCALPHA
    )

    pygame.draw.circle(
        mask,
        (255, 255, 255, 255),
        (
            size // 2,
            size // 2
        ),
        size // 2
    )

    result.blit(
        source,
        (0, 0)
    )

    result.blit(
        mask,
        (0, 0),
        special_flags=pygame.BLEND_RGBA_MULT
    )

    return result


def choose_avatar():
    if tkinter is None or filedialog is None:
        return None

    path = None

    try:
        root = tkinter.Tk()
        root.withdraw()
        root.attributes(
            "-topmost",
            True
        )

        path = filedialog.askopenfilename(
            title="Choose Profile Picture",
            filetypes=[
                (
                    "Image Files",
                    "*.png *.jpg *.jpeg *.bmp *.gif"
                ),
                (
                    "All Files",
                    "*.*"
                ),
            ]
        )

        root.destroy()

    except Exception:
        path = None

    return path


def get_ship_path(ship):
    candidates = [
        os.path.join(
            ASSET_DIR,
            f"ship_{ship}.png"
        ),
        os.path.join(
            ASSET_DIR,
            "ships",
            f"{ship}.png"
        ),
        os.path.join(
            ASSET_DIR,
            "ships",
            f"ship_{ship}.png"
        ),
        os.path.join(
            ASSET_DIR,
            f"{ship}.png"
        ),
        os.path.join(
            ASSET_DIR,
            "images",
            "ship.png"
        ),
    ]

    for path in candidates:

        if os.path.isfile(path):
            return path

    return None


def load_ship(ship, size):
    if not ship:
        return None

    key = (
        str(ship),
        int(size)
    )

    if key in _ship_cache:
        return _ship_cache[key]

    path = get_ship_path(
        str(ship)
    )

    image = None

    if path:

        try:
            image = pygame.image.load(
                path
            ).convert_alpha()

            image = pygame.transform.smoothscale(
                image,
                (
                    int(size),
                    int(size)
                )
            )

            # The bundled yellow ship has a black matte.  Removing it makes
            # the ship float naturally over the animated profile background.
            image.set_colorkey((0, 0, 0))

        except Exception:
            image = None

    _ship_cache[key] = image

    return image


SHIP_COLORS = {
    "ICE": {"primary": (206, 229, 255), "secondary": (82, 154, 255), "dark": (24, 47, 78), "accent": (120, 194, 255)},
    "CRIMSON": {"primary": (238, 74, 88), "secondary": (164, 22, 40), "dark": (66, 14, 24), "accent": (255, 100, 112)},
    "CYAN": {"primary": (78, 224, 244), "secondary": (18, 146, 191), "dark": (16, 58, 72), "accent": (124, 245, 255)},
    "GOLD": {"primary": (255, 215, 100), "secondary": (182, 101, 16), "dark": (76, 46, 14), "accent": (255, 237, 154)},
    "VIOLET": {"primary": (193, 126, 255), "secondary": (105, 49, 178), "dark": (54, 27, 82), "accent": (224, 173, 255)},
    "LIME": {"primary": (161, 235, 107), "secondary": (58, 158, 59), "dark": (28, 67, 27), "accent": (205, 255, 157)},
    "STEEL": {"primary": (193, 199, 215), "secondary": (88, 104, 129), "dark": (39, 46, 58), "accent": (230, 236, 250)},
    "OBSIDIAN": {"primary": (105, 117, 142), "secondary": (41, 49, 67), "dark": (15, 19, 29), "accent": (148, 162, 188)},
}

SHIP_CATALOG_PRICES = {
    "starter": 0,
    "falcon": 0,
    "viper": 2500,
    "phantom": 5000,
    "titan": 8500,
    "nova": 12000,
    "specter": 16000,
    "raven": 22000,
}

SHIP_STATS = {
    "starter": (7, 5, 6),
    "falcon": (8, 7, 6),
    "viper": (9, 6, 5),
    "phantom": (8, 8, 5),
    "titan": (5, 9, 10),
    "nova": (10, 8, 6),
    "specter": (9, 9, 4),
    "raven": (7, 10, 9),
}

_ship_tinted_cache = {}


def _ship_display_name(name):
    return str(name or "STARTER").replace("_", " ").replace("-", " ").upper()


def _discover_ship_names():
    found = []
    folders = [
        os.path.join(ASSET_DIR, "ships"),
        ASSET_DIR,
    ]
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        try:
            for filename in os.listdir(folder):
                lower = filename.lower()
                if not lower.endswith(".png"):
                    continue
                stem = filename[:-4]
                if stem.lower().startswith("ship_"):
                    stem = stem[5:]
                if stem.lower() == "ship":
                    continue
                if stem.strip():
                    found.append(stem)
        except Exception:
            pass
    return list(dict.fromkeys(found))


def get_ship_catalog(player_id=None):
    owned = set(x.lower() for x in get_profile_ships(player_id))
    names = ["starter", "falcon", "viper", "phantom", "titan", "nova", "specter", "raven"]
    names.extend(_discover_ship_names())
    names.extend(owned)
    return list(dict.fromkeys(str(x).lower() for x in names if str(x).strip()))


def _warm_pixel(r, g, b):
    return r > 120 and r > g * 1.34 and g > b * 1.15


def recolor_ship_body(surface, color_name="ICE"):
    if surface is None:
        return None
    color_name = str(color_name or "ICE").upper()
    palette = SHIP_COLORS.get(color_name, SHIP_COLORS["ICE"])
    key = (id(surface), color_name, surface.get_size())
    cached = _ship_tinted_cache.get(key)
    if cached is not None:
        return cached.copy()
    source = surface.convert_alpha()
    output = pygame.Surface(source.get_size(), pygame.SRCALPHA)
    sw, sh = source.get_size()
    for y in range(sh):
        for x in range(sw):
            r, g, b, a = source.get_at((x, y))
            if a == 0:
                continue
            if r < 38 and g < 38 and b < 42:
                output.set_at((x, y), (r, g, b, a))
                continue
            if _warm_pixel(r, g, b) and r > 150:
                output.set_at((x, y), (r, g, b, a))
                continue
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
            if lum < 0.22:
                tint = palette["dark"]
                mix = 0.65
            elif lum < 0.52:
                t = (lum - 0.22) / 0.30
                tint = tuple(int(palette["dark"][i] + (palette["secondary"][i] - palette["dark"][i]) * t) for i in range(3))
                mix = 0.82
            elif lum < 0.84:
                t = (lum - 0.52) / 0.32
                tint = tuple(int(palette["secondary"][i] + (palette["primary"][i] - palette["secondary"][i]) * t) for i in range(3))
                mix = 0.88
            else:
                t = min(1.0, (lum - 0.84) / 0.16)
                tint = tuple(int(palette["primary"][i] + (245 - palette["primary"][i]) * t) for i in range(3))
                mix = 0.64
            nr = int(r * (1 - mix) + tint[0] * mix)
            ng = int(g * (1 - mix) + tint[1] * mix)
            nb = int(b * (1 - mix) + tint[2] * mix)
            output.set_at((x, y), (max(0, min(255, nr)), max(0, min(255, ng)), max(0, min(255, nb)), a))
    _ship_tinted_cache[key] = output.copy()
    return output


def load_ship_variant(ship, color_name="ICE", size=220):
    base = load_ship(ship, size)
    if base is None:
        return None
    return recolor_ship_body(base, color_name)


def save_ship_loadout(player_id, player, ship_name, color_name, rotation=0.0):
    color_name = str(color_name or "ICE").upper()
    ship_name = str(ship_name or "starter")
    settings = load_settings(player_id)
    settings.update({
        "selected_ship": ship_name,
        "preview_ship": ship_name,
        "ship_color": color_name,
        "ship_rotation": float(rotation) % 360,
        "ship_preview_rotation": float(rotation) % 360,
    })
    save_settings(player_id, settings)
    if isinstance(player, dict):
        player.update({
            "selected_ship": ship_name,
            "current_ship": ship_name,
            "equipped_ship": ship_name,
            "ship": ship_name,
            "ship_color": color_name,
            "ship_rotation": float(rotation) % 360,
        })
    if database is not None and player_id is not None:
        for function_name in (
            "set_active_ship", "set_selected_ship", "set_equipped_ship",
            "equip_ship", "update_selected_ship", "update_active_ship",
        ):
            fn = getattr(database, function_name, None)
            if not callable(fn):
                continue
            for args, kwargs in (
                ((player_id, ship_name), {}),
                ((), {"player_id": player_id, "ship_name": ship_name}),
                ((), {"player_id": player_id, "selected_ship": ship_name}),
                ((), {"player_id": player_id, "ship": ship_name}),
            ):
                try:
                    fn(*args, **kwargs)
                    raise StopIteration
                except StopIteration:
                    break
                except Exception:
                    continue
    return settings


def get_game_loadout(player=None):
    player = player if isinstance(player, dict) else {}
    player_id = get_value(player, "id", "player_id", "user_id", default=None)
    settings = load_settings(player_id)
    ship = get_value(player, "selected_ship", "current_ship", "equipped_ship", "ship", default=None)
    if not ship:
        ship = settings.get("selected_ship") or settings.get("preview_ship") or "starter"
    color = get_value(player, "ship_color", default=None) or settings.get("ship_color") or "ICE"
    return str(ship), str(color).upper()


def load_game_player_ship(player, size=72):
    ship, color = get_game_loadout(player)
    return load_ship_variant(ship, color, size)


def ship_is_owned(player_id, ship_name):
    name = str(ship_name or "").lower()
    return name in set(x.lower() for x in get_profile_ships(player_id)) or name in {"starter", "falcon"}


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(a, b, t):
    return tuple(int(lerp(a[i], b[i], t)) for i in range(3))


def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - pow(1 - t, 3)


# =========================================================
# PSEUDO-3D SHIP RENDERING
#
# pygame has no real 3D pipeline, but a handful of cheap 2D tricks read
# as "3D" when layered together: squashing width to fake a turntable
# spin, flipping to the mirrored sprite past the 90/270 degree mark,
# darkening the far side, a moving specular sweep, a stamped-silhouette
# rim glow, a floating bob + idle bank, a soft contact shadow, a
# holographic scan pad, and a real particle thruster trail instead of
# a static flame polygon. None of this needs new assets.
# =========================================================

class ThrusterParticle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size")

    def __init__(self, x, y, vx, vy, life, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size


def spawn_thruster_particles(particles, engine_pos, direction, intensity=1.0, count=2):
    ex, ey = engine_pos
    dx, dy = direction
    for _ in range(count):
        spread = random.uniform(-0.4, 0.4)
        speed = random.uniform(1.4, 3.0) * max(0.25, intensity)
        jx = dx * math.cos(spread) - dy * math.sin(spread)
        jy = dx * math.sin(spread) + dy * math.cos(spread)
        particles.append(
            ThrusterParticle(
                ex + random.uniform(-2, 2),
                ey + random.uniform(-2, 2),
                jx * speed,
                jy * speed,
                life=random.uniform(0.32, 0.6),
                size=random.uniform(3.0, 6.0) * max(0.35, intensity),
            )
        )
    # occasional bright spark for extra shimmer
    if random.random() < 0.12:
        particles.append(
            ThrusterParticle(
                ex, ey,
                dx * random.uniform(2.5, 4.0),
                dy * random.uniform(2.5, 4.0),
                life=0.25,
                size=2.0,
            )
        )


def update_thruster_particles(particles, dt):
    dt = min(0.05, max(0.0, dt))
    alive = []
    for p in particles:
        p.life -= dt
        if p.life <= 0:
            continue
        p.x += p.vx
        p.y += p.vy
        p.vx *= 0.94
        p.vy *= 0.94
        alive.append(p)
    particles[:] = alive


def draw_thruster_particles(screen, particles):
    for p in particles:
        t = max(0.0, min(1.0, p.life / p.max_life))
        radius = max(1, int(p.size * t))
        color = lerp_color((255, 90, 15), (255, 232, 150), 1 - t)
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color, int(190 * t)), (radius, radius), radius)
        screen.blit(surf, (p.x - radius, p.y - radius), special_flags=pygame.BLEND_RGBA_ADD)


def draw_holo_pad(screen, center, radius, tick, color=TITLE_RED):
    """An animated scanner-ring platform under the ship."""
    cx, cy = center
    pad_h = max(8, int(radius * 0.30))

    glow = pygame.Surface((radius * 2 + 50, pad_h * 2 + 50), pygame.SRCALPHA)
    gcx, gcy = glow.get_width() // 2, glow.get_height() // 2
    pulse = 0.75 + math.sin(tick / 260.0) * 0.25
    for i, mul in enumerate((1.0, 0.7, 0.42)):
        alpha = max(0, int((70 - i * 20) * pulse))
        rect = pygame.Rect(0, 0, int(radius * 2 * mul), int(pad_h * 2 * mul))
        rect.center = (gcx, gcy)
        pygame.draw.ellipse(glow, (*color, alpha), rect)
    screen.blit(glow, (cx - glow.get_width() // 2, cy - glow.get_height() // 2), special_flags=pygame.BLEND_RGBA_ADD)

    pygame.draw.ellipse(screen, color, pygame.Rect(cx - radius, cy - pad_h, radius * 2, pad_h * 2), 2)

    for mul, speed, segments in ((0.72, 1.0, 22), (0.5, -1.6, 16)):
        rw, rh = max(2, int(radius * mul)), max(2, int(pad_h * mul))
        base = (tick / 14.0) * speed
        rect = pygame.Rect(cx - rw, cy - rh, rw * 2, rh * 2)
        for s in range(segments):
            if s % 2 == 0:
                continue
            a0 = math.radians(base + s * (360 / segments))
            a1 = math.radians(base + s * (360 / segments) + (360 / segments) * 0.6)
            try:
                pygame.draw.arc(screen, color, rect, a0, a1, 2)
            except Exception:
                pass


def render_hangar_ship(screen, particles, base_image, center, rotation_y, tick, dt,
                        bob_phase=0.0, accent=TITLE_RED, label_drag=False):
    """
    Draws a ship as a floating, spinning holographic display:
    holo pad -> contact shadow -> rim glow -> thruster trail -> shaded,
    specular-swept, turntable-squashed sprite with idle bob/bank.

    rotation_y is the drag-controlled "turntable" heading in degrees.
    Returns the on-screen center actually used (useful for click/drag hit-testing).
    """
    if base_image is None:
        update_thruster_particles(particles, dt)
        draw_thruster_particles(screen, particles)
        return center

    bw, bh = base_image.get_size()

    facing = math.cos(math.radians(rotation_y))
    width_scale = 0.30 + 0.70 * abs(facing)
    is_back = facing < 0

    working = pygame.transform.smoothscale(base_image, (max(2, int(bw * width_scale)), bh))
    if is_back:
        working = pygame.transform.flip(working, True, False)

    # darken the far side of the turntable to sell depth
    shade_level = int(140 * (1 - abs(facing)))
    if shade_level > 3:
        shade = pygame.Surface(working.get_size())
        shade.fill((shade_level, shade_level, shade_level))
        working.blit(shade, (0, 0), special_flags=pygame.BLEND_RGB_SUB)

    # a soft diagonal highlight sweeping across the hull, RGB-only so it
    # never bleeds into the transparent background
    diag = working.get_width() + working.get_height()
    band = max(6, int(diag * 0.14))
    off = (tick * 0.10) % (diag + band * 2) - band
    sweep = pygame.Surface(working.get_size())
    pts = [
        (off, 0),
        (off + band, 0),
        (off + band - working.get_height(), working.get_height()),
        (off - working.get_height(), working.get_height()),
    ]
    pygame.draw.polygon(sweep, (55, 55, 55), pts)
    working.blit(sweep, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    # idle bank (roll) + float, so it feels alive even at rest
    roll = math.sin(tick / 650.0 + bob_phase) * (2.0 if label_drag else 3.5)
    working = pygame.transform.rotozoom(working, roll, 1.0)

    bob = math.sin(tick / 420.0 + bob_phase) * 7
    ship_center = (center[0], center[1] + bob)

    pad_center = (center[0], int(center[1] + bh * 0.42))
    pad_radius = max(28, int(bw * 0.62))
    draw_holo_pad(screen, pad_center, pad_radius, tick, accent)

    shadow_scale = max(0.5, 0.85 - bob / 14.0)
    shadow_w = max(10, int(bw * 0.5 * shadow_scale))
    shadow_h = max(4, int(bh * 0.11 * shadow_scale))
    shadow = pygame.Surface((shadow_w * 2, shadow_h * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 120), shadow.get_rect())
    screen.blit(shadow, shadow.get_rect(center=pad_center))

    try:
        mask = pygame.mask.from_surface(working)
        silhouette = mask.to_surface(setcolor=(*accent, 110), unsetcolor=(0, 0, 0, 0))
        spread = 5
        glow_layer = pygame.Surface(
            (working.get_width() + spread * 2, working.get_height() + spread * 2),
            pygame.SRCALPHA,
        )
        offsets = ((spread, 0), (-spread, 0), (0, spread), (0, -spread),
                   (4, 4), (-4, 4), (4, -4), (-4, -4))
        for ox, oy in offsets:
            glow_layer.blit(silhouette, (spread + ox, spread + oy), special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(glow_layer, glow_layer.get_rect(center=ship_center), special_flags=pygame.BLEND_RGBA_ADD)
    except Exception:
        pass

    angle_rad = math.radians(roll)
    engine_local = working.get_height() * 0.46
    ex = ship_center[0] + engine_local * math.sin(angle_rad)
    ey = ship_center[1] + engine_local * math.cos(angle_rad)
    direction = (math.sin(angle_rad), math.cos(angle_rad))
    intensity = 0.55 + 0.45 * abs(facing)
    spawn_thruster_particles(particles, (ex, ey), direction, intensity)
    update_thruster_particles(particles, dt)
    draw_thruster_particles(screen, particles)

    screen.blit(working, working.get_rect(center=ship_center))

    return ship_center

def crop_transparent_image(image):
    if image is None:
        return None

    try:
        image = image.convert_alpha()
    except Exception:
        return image

    try:
        alpha = image.get_masks()[3]

        if alpha is None:
            return image

        bbox = alpha.get_bounding_rect()

        if bbox.width <= 0 or bbox.height <= 0:
            return image

        padding = 2

        bbox.x = max(
            0,
            bbox.x - padding
        )

        bbox.y = max(
            0,
            bbox.y - padding
        )

        bbox.width = min(
            image.get_width() - bbox.x,
            bbox.width + padding * 2
        )

        bbox.height = min(
            image.get_height() - bbox.y,
            bbox.height + padding * 2
        )

        return image.subsurface(
            bbox
        ).copy()

    except Exception:
        return image


def fit_ship_image(
    image,
    target_rect,
    padding=6
):
    if image is None:
        return None

    if (
        image.get_width() <= 0
        or image.get_height() <= 0
    ):
        return None

    image = crop_transparent_image(
        image
    )

    if image is None:
        return None

    available_width = max(
        1,
        target_rect.width - padding * 2
    )

    available_height = max(
        1,
        target_rect.height - padding * 2
    )

    image_width = image.get_width()
    image_height = image.get_height()

    scale_x = (
        available_width
        / float(image_width)
    )

    scale_y = (
        available_height
        / float(image_height)
    )

    scale = min(
        scale_x,
        scale_y
    )

    new_width = max(
        1,
        int(image_width * scale)
    )

    new_height = max(
        1,
        int(image_height * scale)
    )

    scaled = pygame.transform.smoothscale(
        image,
        (
            new_width,
            new_height
        )
    )

    return scaled


def draw_ship_engine_effect(screen, center, rotation, size, tick):
    """Draw a gentle yellow-orange thruster glow behind the floating ship."""
    pulse = 0.82 + math.sin(tick / 95) * 0.18
    angle = math.radians(rotation)
    offset = max(16, int(size * 0.36))
    flame_x = int(center[0] + math.sin(angle) * offset)
    flame_y = int(center[1] + math.cos(angle) * offset)
    glow_size = max(20, int(size * 0.62 * pulse))

    glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
    glow_center = (glow_size, glow_size)
    pygame.draw.circle(glow, (255, 75, 10, 28), glow_center, glow_size)
    pygame.draw.circle(glow, (255, 170, 20, 65), glow_center, int(glow_size * 0.64))
    pygame.draw.circle(glow, (255, 240, 120, 170), glow_center, int(glow_size * 0.32))
    screen.blit(glow, glow.get_rect(center=(flame_x, flame_y)))

    flame_length = max(10, int(size * 0.28 * pulse))
    side = max(5, int(size * 0.09))
    direction = (math.sin(angle), math.cos(angle))
    perpendicular = (direction[1], -direction[0])
    tip = (flame_x + int(direction[0] * flame_length), flame_y + int(direction[1] * flame_length))
    left = (flame_x + int(perpendicular[0] * side), flame_y + int(perpendicular[1] * side))
    right = (flame_x - int(perpendicular[0] * side), flame_y - int(perpendicular[1] * side))
    pygame.draw.polygon(screen, (255, 174, 25), (tip, left, right))


def draw_icon(
    screen,
    center,
    icon,
    size=20,
    color=TITLE_RED
):
    x, y = center
    size = max(
        10,
        int(size)
    )

    width = max(
        2,
        size // 7
    )

    if icon == "person":

        head = max(
            3,
            size // 5
        )

        pygame.draw.circle(
            screen,
            color,
            (
                x,
                y - size // 4
            ),
            head
        )

        body = pygame.Rect(
            x - size // 3,
            y,
            size * 2 // 3,
            size // 2
        )

        pygame.draw.arc(
            screen,
            color,
            body,
            math.pi,
            math.pi * 2,
            width
        )

    elif icon == "mail":

        rect = pygame.Rect(
            x - size // 2,
            y - size // 3,
            size,
            size * 2 // 3
        )

        pygame.draw.rect(
            screen,
            color,
            rect,
            width,
            border_radius=2
        )

        pygame.draw.line(
            screen,
            color,
            rect.topleft,
            rect.center,
            width
        )

        pygame.draw.line(
            screen,
            color,
            rect.topright,
            rect.center,
            width
        )

    elif icon == "lock":

        body = pygame.Rect(
            x - size // 3,
            y - size // 8,
            size * 2 // 3,
            size // 2
        )

        pygame.draw.rect(
            screen,
            color,
            body,
            width,
            border_radius=3
        )

        shackle = pygame.Rect(
            x - size // 4,
            y - size // 2,
            size // 2,
            size // 2
        )

        pygame.draw.arc(
            screen,
            color,
            shackle,
            math.pi,
            math.pi * 2,
            width
        )

        pygame.draw.circle(
            screen,
            color,
            (
                x,
                y + size // 8
            ),
            max(
                2,
                size // 12
            )
        )

    elif icon == "shield":

        points = [
            (
                x,
                y - size // 2
            ),
            (
                x + size // 2,
                y - size // 3
            ),
            (
                x + size // 3,
                y + size // 3
            ),
            (
                x,
                y + size // 2
            ),
            (
                x - size // 3,
                y + size // 3
            ),
            (
                x - size // 2,
                y - size // 3
            ),
        ]

        pygame.draw.polygon(
            screen,
            color,
            points,
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x - size // 5,
                y
            ),
            (
                x - size // 16,
                y + size // 5
            ),
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x - size // 16,
                y + size // 5
            ),
            (
                x + size // 4,
                y - size // 5
            ),
            width
        )

    elif icon == "bell":

        bell = pygame.Rect(
            x - size // 3,
            y - size // 4,
            size * 2 // 3,
            size // 2
        )

        pygame.draw.arc(
            screen,
            color,
            bell,
            math.pi,
            math.pi * 2,
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x - size // 3,
                y
            ),
            (
                x - size // 3,
                y + size // 5
            ),
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x + size // 3,
                y
            ),
            (
                x + size // 3,
                y + size // 5
            ),
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x - size // 2,
                y + size // 5
            ),
            (
                x + size // 2,
                y + size // 5
            ),
            width
        )

        pygame.draw.circle(
            screen,
            color,
            (
                x,
                y + size // 3
            ),
            max(
                2,
                width
            )
        )

    elif icon == "user_plus":

        draw_icon(
            screen,
            (
                x - size // 5,
                y
            ),
            "person",
            int(size * 0.72),
            color
        )

        pygame.draw.line(
            screen,
            color,
            (
                x + size // 5,
                y
            ),
            (
                x + size // 2,
                y
            ),
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x + size * 7 // 20,
                y - size // 5
            ),
            (
                x + size * 7 // 20,
                y + size // 5
            ),
            width
        )

    elif icon == "key":

        pygame.draw.circle(
            screen,
            color,
            (
                x - size // 4,
                y
            ),
            size // 5,
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x - size // 8,
                y
            ),
            (
                x + size // 2,
                y
            ),
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x + size // 4,
                y
            ),
            (
                x + size // 4,
                y + size // 5
            ),
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x + size * 2 // 5,
                y
            ),
            (
                x + size * 2 // 5,
                y + size // 5
            ),
            width
        )

    elif icon == "trash":

        rect = pygame.Rect(
            x - size // 3,
            y - size // 4,
            size * 2 // 3,
            size * 2 // 3
        )

        pygame.draw.rect(
            screen,
            color,
            rect,
            width,
            border_radius=2
        )

        pygame.draw.line(
            screen,
            color,
            (
                x - size // 2,
                y - size // 3
            ),
            (
                x + size // 2,
                y - size // 3
            ),
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x - size // 5,
                y - size // 2
            ),
            (
                x + size // 5,
                y - size // 2
            ),
            width
        )

    elif icon == "download":

        pygame.draw.line(
            screen,
            color,
            (
                x,
                y - size // 2
            ),
            (
                x,
                y + size // 5
            ),
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x - size // 5,
                y
            ),
            (
                x,
                y + size // 5
            ),
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x + size // 5,
                y
            ),
            (
                x,
                y + size // 5
            ),
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x - size // 2,
                y + size // 2
            ),
            (
                x + size // 2,
                y + size // 2
            ),
            width
        )

    elif icon == "star":

        points = []

        for i in range(10):

            angle = (
                -math.pi / 2
                + i * math.pi / 5
            )

            radius = (
                size // 2
                if i % 2 == 0
                else size // 5
            )

            points.append(
                (
                    x + math.cos(angle) * radius,
                    y + math.sin(angle) * radius
                )
            )

        pygame.draw.polygon(
            screen,
            color,
            points
        )

    elif icon == "coin":

        pygame.draw.circle(
            screen,
            color,
            center,
            size // 2
        )

        pygame.draw.circle(
            screen,
            FIELD_FILL,
            center,
            max(
                2,
                size // 2 - width
            ),
            width
        )

        font = menu_font(
            max(
                8,
                size // 2
            ),
            True
        )

        text = font.render(
            "C",
            True,
            color
        )

        screen.blit(
            text,
            text.get_rect(
                center=center
            )
        )

    elif icon == "ship":

        points = [
            (
                x,
                y - size // 2
            ),
            (
                x + size // 2,
                y + size // 2
            ),
            (
                x,
                y + size // 5
            ),
            (
                x - size // 2,
                y + size // 2
            ),
        ]

        pygame.draw.polygon(
            screen,
            color,
            points
        )

    elif icon == "game":

        rect = pygame.Rect(
            x - size // 2,
            y - size // 3,
            size,
            size * 2 // 3
        )

        pygame.draw.rect(
            screen,
            color,
            rect,
            width,
            border_radius=4
        )

        pygame.draw.line(
            screen,
            color,
            (
                x - size // 4,
                y
            ),
            (
                x + size // 4,
                y
            ),
            width
        )

        pygame.draw.line(
            screen,
            color,
            (
                x,
                y - size // 4
            ),
            (
                x,
                y + size // 4
            ),
            width
        )

    elif icon == "rank":

        points = [
            (
                x,
                y - size // 2
            ),
            (
                x + size // 3,
                y - size // 4
            ),
            (
                x + size // 4,
                y + size // 2
            ),
            (
                x,
                y + size // 4
            ),
            (
                x - size // 4,
                y + size // 2
            ),
            (
                x - size // 3,
                y - size // 4
            ),
        ]

        pygame.draw.polygon(
            screen,
            color,
            points
        )

    elif icon == "facebook":

        font = pygame.font.SysFont(
            "Arial",
            size,
            bold=True
        )

        text = font.render(
            "f",
            True,
            color
        )

        screen.blit(
            text,
            text.get_rect(
                center=center
            )
        )

    elif icon == "google":

        font = pygame.font.SysFont(
            "Arial",
            size,
            bold=True
        )

        text = font.render(
            "G",
            True,
            color
        )

        screen.blit(
            text,
            text.get_rect(
                center=center
            )
        )

    elif icon == "discord":

        rect = pygame.Rect(
            x - size // 2,
            y - size // 3,
            size,
            size * 2 // 3
        )

        pygame.draw.arc(
            screen,
            color,
            rect,
            0,
            math.pi,
            width
        )

        pygame.draw.circle(
            screen,
            color,
            (
                x - size // 5,
                y
            ),
            max(
                2,
                size // 12
            )
        )

        pygame.draw.circle(
            screen,
            color,
            (
                x + size // 5,
                y
            ),
            max(
                2,
                size // 12
            )
        )


def section_header(
    screen,
    rect,
    title,
    icon,
    color=TITLE_RED
):
    pygame.draw.rect(
        screen,
        (24, 29, 45),
        rect,
        border_radius=6
    )

    pygame.draw.rect(
        screen,
        color,
        rect,
        1,
        border_radius=6
    )

    pygame.draw.rect(
        screen,
        color,
        pygame.Rect(
            rect.x,
            rect.y,
            4,
            rect.height
        ),
        border_radius=3
    )

    draw_icon(
        screen,
        (
            rect.x + 19,
            rect.centery
        ),
        icon,
        20,
        color
    )

    font = menu_font(
        13,
        True
    )

    text = font.render(
        title,
        True,
        MENU_WHITE
    )

    screen.blit(
        text,
        (
            rect.x + 37,
            rect.centery
            - text.get_height() // 2
        )
    )


def stat_card(
    screen,
    rect,
    title,
    value,
    icon,
    color=TITLE_RED
):
    pygame.draw.rect(
        screen,
        (19, 25, 40),
        rect,
        border_radius=7
    )

    pygame.draw.rect(
        screen,
        color,
        rect,
        1,
        border_radius=7
    )

    draw_icon(
        screen,
        (
            rect.x + 18,
            rect.centery
        ),
        icon,
        20,
        color
    )

    label_font = menu_font(
        8,
        True
    )

    value_font = menu_font(
        13,
        True
    )

    label = label_font.render(
        title,
        True,
        MUTED
    )

    value_text = fit_text(
        value_font,
        value,
        rect.width - 42
    )

    value_surface = value_font.render(
        value_text,
        True,
        MENU_WHITE
    )

    screen.blit(
        label,
        (
            rect.x + 34,
            rect.y + 7
        )
    )

    screen.blit(
        value_surface,
        (
            rect.x + 34,
            rect.y + 21
        )
    )


def setting_card(
    screen,
    rect,
    title,
    subtitle,
    icon,
    enabled,
    color=TITLE_RED
):
    pygame.draw.rect(
        screen,
        (19, 25, 40),
        rect,
        border_radius=7
    )

    pygame.draw.rect(
        screen,
        FIELD_EDGE,
        rect,
        1,
        border_radius=7
    )

    draw_icon(
        screen,
        (
            rect.x + 20,
            rect.centery
        ),
        icon,
        20,
        color
    )

    title_font = menu_font(
        10,
        True
    )

    subtitle_font = menu_font(
        8,
        True
    )

    title_surface = title_font.render(
        title,
        True,
        MENU_WHITE
    )

    subtitle_surface = subtitle_font.render(
        subtitle,
        True,
        MUTED
    )

    screen.blit(
        title_surface,
        (
            rect.x + 39,
            rect.y + 7
        )
    )

    screen.blit(
        subtitle_surface,
        (
            rect.x + 39,
            rect.y + 23
        )
    )

    switch = pygame.Rect(
        rect.right - 43,
        rect.centery - 9,
        35,
        18
    )

    pygame.draw.rect(
        screen,
        SUCCESS_GREEN
        if enabled
        else (48, 52, 64),
        switch,
        border_radius=9
    )

    pygame.draw.circle(
        screen,
        MENU_WHITE,
        (
            switch.right - 9
            if enabled
            else switch.left + 9,
            switch.centery
        ),
        6
    )

    return switch


def status_card(
    screen,
    rect,
    title,
    subtitle,
    icon,
    selected,
    color
):
    pygame.draw.rect(
        screen,
        (19, 25, 40),
        rect,
        border_radius=7
    )

    pygame.draw.rect(
        screen,
        color if selected else FIELD_EDGE,
        rect,
        2 if selected else 1,
        border_radius=7
    )

    draw_icon(
        screen,
        (
            rect.x + 22,
            rect.centery
        ),
        icon,
        20,
        color
    )

    title_font = menu_font(
        11,
        True
    )

    subtitle_font = menu_font(
        8,
        True
    )

    title_surface = title_font.render(
        title,
        True,
        MENU_WHITE
    )

    subtitle_surface = subtitle_font.render(
        subtitle,
        True,
        MUTED
    )

    screen.blit(
        title_surface,
        (
            rect.x + 42,
            rect.y + 8
        )
    )

    screen.blit(
        subtitle_surface,
        (
            rect.x + 42,
            rect.y + 26
        )
    )

    if selected:

        pygame.draw.circle(
            screen,
            SUCCESS_GREEN,
            (
                rect.right - 15,
                rect.centery
            ),
            5
        )

    return rect


def update_database_settings(
    player_id,
    settings
):
    if database is None:
        return

    function = getattr(
        database,
        "update_profile_settings",
        None
    )

    if not callable(function):
        return

    try:
        function(
            player_id,
            settings
        )

    except TypeError:

        try:
            function(
                player_id,
                **settings
            )

        except Exception:
            pass

    except Exception:
        pass


def save_profile_to_database(
    player_id,
    username,
    email
):
    if database is None:
        return True, None

    function = getattr(
        database,
        "update_profile",
        None
    )

    if not callable(function):
        return True, None

    try:
        result = function(
            player_id,
            username,
            email
        )

        if result is False:
            return (
                False,
                "USERNAME OR EMAIL ALREADY IN USE"
            )

        return True, None

    except TypeError:

        try:
            result = function(
                player_id,
                username=username,
                email=email
            )

            if result is False:
                return (
                    False,
                    "USERNAME OR EMAIL ALREADY IN USE"
                )

            return True, None

        except Exception:
            return (
                False,
                "COULD NOT SAVE PROFILE"
            )

    except Exception:
        return (
            False,
            "COULD NOT SAVE PROFILE"
        )


def read_player(player_id, fallback):
    if database is not None:

        function = getattr(
            database,
            "get_player",
            None
        )

        if callable(function):

            try:
                result = function(
                    player_id
                )

                if isinstance(result, dict):
                    return result

            except Exception:
                pass

    return fallback


def delete_account(player_id):
    if database is None:
        return False

    function = getattr(
        database,
        "delete_player",
        None
    )

    if not callable(function):
        return False

    try:
        result = function(
            player_id
        )

    except Exception:
        return False

    if result:

        try:
            delete_player_data(
                player_id
            )
        except Exception:
            pass

        return True

    return False


def export_data(
    player_id,
    player,
    settings
):
    try:
        directory = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            "exports"
        )

        os.makedirs(
            directory,
            exist_ok=True
        )

        path = os.path.join(
            directory,
            f"profile_{player_id}.json"
        )

        data = {
            "profile": player,
            "settings": settings
        }

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                default=str
            )

        return path

    except Exception:
        return None


def advanced_profile_screen(
    screen,
    clock,
    player=None
):
    if not isinstance(player, dict):
        player = {}

    player_id = get_value(
        player,
        "id",
        "player_id",
        "user_id",
        default=None
    )

    settings = load_settings(
        player_id
    )

    username = str(
        get_value(
            player,
            "username",
            "display_name",
            default="PLAYER"
        )
        or "PLAYER"
    )

    email = str(
        get_value(
            player,
            "email",
            default=""
        )
        or ""
    )

    gamer_tag = str(
        settings.get("gamer_tag", "")
        or ""
    )[:MAX_GAMER_TAG_LENGTH]

    bio = str(
        settings.get("bio", "")
        or ""
    )[:MAX_BIO_LENGTH]

    avatar_kind = player.get(
        "avatar",
        settings.get(
            "avatar",
            "hood"
        )
    )

    if avatar_kind not in AVATAR_KINDS:
        avatar_kind = "hood"

    avatar_path = get_value(
        player,
        "profile_picture",
        "avatar_path",
        default=None
    ) or settings.get(
        "avatar_path"
    )

    visibility = player.get(
        "visibility",
        settings.get(
            "visibility",
            "online"
        )
    )

    if visibility not in VISIBILITY_OPTIONS:
        visibility = "online"

    allow_friend_requests = bool(
        player.get(
            "allow_friend_requests",
            settings.get(
                "allow_friend_requests",
                True
            )
        )
    )

    login_alerts = bool(
        player.get(
            "login_alerts",
            settings.get(
                "login_alerts",
                True
            )
        )
    )

    two_factor = bool(
        player.get(
            "two_factor",
            settings.get(
                "two_factor",
                False
            )
        )
    )

    connected_accounts = dict(
        settings.get(
            "connected_accounts",
            {}
        )
    )

    preview_ship = str(settings.get("preview_ship", "") or "")
    ship_rotation = safe_float(settings.get("ship_preview_rotation", 0)) % 360

    active = None
    mode = "profile"
    pending_provider = None
    card_draft = None
    ship_drag_start = None
    ship_drag_rotation = 0.0
    ship_spin_velocity = 0.0
    ship_particles = []
    ship_bob_phase = random.uniform(0, math.tau)

    cursor_visible = True
    cursor_timer = time.time()

    message = ""
    message_color = ERROR_RED

    password_values = {
        "current": "",
        "new": "",
        "confirm": ""
    }

    password_reveal = {
        "current": False,
        "new": False,
        "confirm": False
    }

    delete_text = ""
    link_text = ""

    original = {
        "username": username,
        "email": email,
        "gamer_tag": gamer_tag,
        "bio": bio,
        "avatar": avatar_kind,
        "avatar_path": avatar_path,
        "visibility": visibility,
        "allow_friend_requests": allow_friend_requests,
        "login_alerts": login_alerts,
        "two_factor": two_factor,
        "connected_accounts": dict(
            connected_accounts
        ),
        "preview_ship": preview_ship,
        "ship_preview_rotation": ship_rotation,
    }

    is_fullscreen = (
        screen.get_flags()
        & pygame.FULLSCREEN
    ) != 0

    def message_show(
        text,
        color=ERROR_RED
    ):
        nonlocal message
        nonlocal message_color

        message = text
        message_color = color

        if color == SUCCESS_GREEN:
            theme.sound_success()
        else:
            theme.sound_error()

    def start_text(name):
        nonlocal active

        active = name

        try:
            pygame.key.start_text_input()
        except Exception:
            pass

        theme.sound_click()

    def stop_text():
        nonlocal active

        active = None

        try:
            pygame.key.stop_text_input()
        except Exception:
            pass

    def toggle_fullscreen():
        nonlocal screen
        nonlocal is_fullscreen

        is_fullscreen = not is_fullscreen

        if is_fullscreen:

            screen = pygame.display.set_mode(
                (
                    0,
                    0
                ),
                pygame.FULLSCREEN
            )

        else:

            screen = pygame.display.set_mode(
                (
                    DEFAULT_WIDTH,
                    DEFAULT_HEIGHT
                )
            )

    def save_changes():
        nonlocal original

        clean_username = username.strip()
        clean_email = email.strip()

        if len(clean_username) < 2:

            message_show(
                "USERNAME TOO SHORT"
            )

            return False

        if clean_email and (
            "@" not in clean_email
            or "." not in clean_email
        ):

            message_show(
                "INVALID EMAIL ADDRESS"
            )

            return False

        success, error = save_profile_to_database(
            player_id,
            clean_username,
            clean_email
        )

        if not success:

            message_show(
                error or "COULD NOT SAVE PROFILE"
            )

            return False

        new_settings = {
            "gamer_tag": gamer_tag.strip(),
            "bio": bio.strip(),
            "avatar": avatar_kind,
            "avatar_path": avatar_path,
            "visibility": visibility,
            "show_online": visibility != "offline",
            "allow_friend_requests": allow_friend_requests,
            "login_alerts": login_alerts,
            "two_factor": two_factor,
            "connected_accounts": {
                key: value
                for key, value in connected_accounts.items()
                if not key.startswith("__")
            },
            "preview_ship": preview_ship,
            "ship_preview_rotation": ship_rotation,
        }

        save_settings(
            player_id,
            new_settings
        )

        update_database_settings(
            player_id,
            new_settings
        )

        player.update(
            {
                "username": clean_username,
                "display_name": clean_username,
                "email": clean_email,
                "gamer_tag": gamer_tag.strip(),
                "bio": bio.strip(),
                "avatar": avatar_kind,
                "avatar_path": avatar_path,
                "profile_picture": avatar_path,
                "visibility": visibility,
                "show_online": visibility != "offline",
                "allow_friend_requests": allow_friend_requests,
                "login_alerts": login_alerts,
                "two_factor": two_factor
            }
        )

        original = {
            "username": clean_username,
            "email": clean_email,
            "gamer_tag": gamer_tag.strip(),
            "bio": bio.strip(),
            "avatar": avatar_kind,
            "avatar_path": avatar_path,
            "visibility": visibility,
            "allow_friend_requests": allow_friend_requests,
            "login_alerts": login_alerts,
            "two_factor": two_factor,
            "connected_accounts": dict(
                connected_accounts
            ),
            "preview_ship": preview_ship,
            "ship_preview_rotation": ship_rotation,
        }

        stop_text()

        message_show(
            "PROFILE SAVED",
            SUCCESS_GREEN
        )

        return True

    def reset_changes():
        nonlocal username
        nonlocal email
        nonlocal gamer_tag
        nonlocal bio
        nonlocal avatar_kind
        nonlocal avatar_path
        nonlocal visibility
        nonlocal allow_friend_requests
        nonlocal login_alerts
        nonlocal two_factor
        nonlocal connected_accounts
        nonlocal preview_ship
        nonlocal ship_rotation
        nonlocal message

        username = original["username"]
        email = original["email"]
        gamer_tag = original["gamer_tag"]
        bio = original["bio"]
        avatar_kind = original["avatar"]
        avatar_path = original["avatar_path"]
        visibility = original["visibility"]
        allow_friend_requests = original[
            "allow_friend_requests"
        ]
        login_alerts = original[
            "login_alerts"
        ]
        two_factor = original[
            "two_factor"
        ]
        connected_accounts = dict(
            original[
                "connected_accounts"
            ]
        )

        message = ""

        stop_text()

    running = True

    while running:

        width, height = screen.get_size()

        mouse_pos = pygame.mouse.get_pos()

        tick = pygame.time.get_ticks()

        frame_dt = clock.get_time() / 1000.0

        if ship_drag_start is None:
            if abs(ship_spin_velocity) > 0.015:
                ship_rotation = (ship_rotation + ship_spin_velocity) % 360
                ship_spin_velocity *= 0.93
            else:
                ship_spin_velocity = 0.0

        if (
            time.time()
            - cursor_timer
            > 0.5
        ):

            cursor_visible = not cursor_visible
            cursor_timer = time.time()

        draw_background(
            screen,
            width,
            height,
            tick
        )

        compact = (
            width < 1000
            or height < 650
        )

        margin = max(
            18,
            int(width * 0.035)
        )

        back_rect = pygame.Rect(
            margin,
            18,
            105,
            42
        )

        draw_button(
            screen,
            back_rect,
            "BACK",
            mouse_pos,
            tick,
            primary=False
        )

        title_size = (
            36
            if not compact
            else 29
        )

        draw_title(
            screen,
            "PROFILE SETTINGS",
            width // 2,
            28,
            title_size,
            underline_width=240
            if not compact
            else 190
        )

        subtitle_font = menu_font(
            13
            if not compact
            else 11,
            True
        )

        subtitle = subtitle_font.render(
            "Manage your player identity and account",
            True,
            MENU_BLUE
        )

        screen.blit(
            subtitle,
            (
                width // 2
                - subtitle.get_width() // 2,
                70
            )
        )

        footer_height = 56
        panel_top = 103
        panel_bottom = (
            height
            - footer_height
            - 15
        )

        panel_height = max(
            350,
            panel_bottom - panel_top
        )

        usable_width = (
            width
            - margin * 2
        )

        gap = 12

        left_width = int(
            usable_width * 0.31
        )

        middle_width = int(
            usable_width * 0.40
        )

        right_width = (
            usable_width
            - left_width
            - middle_width
            - gap * 2
        )

        if right_width < 185:

            right_width = 185

            middle_width = (
                usable_width
                - left_width
                - right_width
                - gap * 2
            )

        left = pygame.Rect(
            margin,
            panel_top,
            left_width,
            panel_height
        )

        middle = pygame.Rect(
            left.right + gap,
            panel_top,
            middle_width,
            panel_height
        )

        right = pygame.Rect(
            middle.right + gap,
            panel_top,
            right_width,
            panel_height
        )

        draw_panel(
            screen,
            left,
            tick
        )

        draw_panel(
            screen,
            middle,
            tick
        )

        draw_panel(
            screen,
            right,
            tick
        )

        inner = 10

        lx = left.x + inner
        mx = middle.x + inner
        rx = right.x + inner

        lw = left.width - inner * 2
        mw = middle.width - inner * 2
        rw = right.width - inner * 2

        header_height = 34

        identity_header = pygame.Rect(
            lx,
            left.y + 10,
            lw,
            header_height
        )

        account_header = pygame.Rect(
            mx,
            middle.y + 10,
            mw,
            header_height
        )

        status_header = pygame.Rect(
            rx,
            right.y + 10,
            rw,
            header_height
        )

        section_header(
            screen,
            identity_header,
            "PLAYER IDENTITY",
            "person",
            TITLE_RED
        )

        section_header(
            screen,
            account_header,
            "ACCOUNT INFORMATION",
            "person",
            TITLE_RED
        )

        section_header(
            screen,
            status_header,
            "PLAYER STATUS",
            "shield",
            TITLE_RED
        )

        avatar_size = min(
            105,
            max(
                78,
                panel_height // 4
            )
        )

        avatar_rect = pygame.Rect(
            0,
            0,
            avatar_size,
            avatar_size
        )

        avatar_rect.center = (
            left.centerx,
            identity_header.bottom + 75
        )

        pygame.draw.rect(
            screen,
            TITLE_RED,
            avatar_rect.inflate(
                12,
                12
            ),
            2,
            border_radius=10
        )

        avatar_image = None

        if avatar_path:
            avatar_image = load_custom_avatar(
                avatar_path,
                avatar_size
            )

        if avatar_image is None:

            avatar_image = load_preset_avatar(
                avatar_kind,
                avatar_size
            )

        if avatar_image is not None:

            avatar_image = circular_image(
                avatar_image
            )

            screen.blit(
                avatar_image,
                avatar_image.get_rect(
                    center=avatar_rect.center
                )
            )

        else:

            pygame.draw.circle(
                screen,
                (19, 25, 40),
                avatar_rect.center,
                avatar_size // 2
            )

            draw_icon(
                screen,
                avatar_rect.center,
                "person",
                48,
                TITLE_RED
            )

        upload_rect = pygame.Rect(
            avatar_rect.centerx - 43,
            avatar_rect.bottom + 10,
            86,
            29
        )

        draw_button(
            screen,
            upload_rect,
            "UPLOAD",
            mouse_pos,
            tick,
            primary=False
        )

        name_font = menu_font(
            20
            if not compact
            else 17,
            True
        )

        name_surface = name_font.render(
            fit_text(
                name_font,
                username,
                lw - 10
            ),
            True,
            MENU_WHITE
        )

        name_y = (
            upload_rect.bottom
            + 10
        )

        screen.blit(
            name_surface,
            (
                left.centerx
                - name_surface.get_width() // 2,
                name_y
            )
        )

        level = max(
            1,
            safe_int(
                get_value(
                    player,
                    "level",
                    default=1
                ),
                1
            )
        )

        level_font = menu_font(
            11,
            True
        )

        level_surface = level_font.render(
            f"LEVEL {level}",
            True,
            TITLE_RED
        )

        screen.blit(
            level_surface,
            (
                left.centerx
                - level_surface.get_width() // 2,
                name_y
                + name_surface.get_height()
                + 4
            )
        )

        id_font = menu_font(
            9,
            True
        )

        id_value = (
            f"#{player_id}"
            if player_id is not None
            else "#—"
        )

        callsign = gamer_tag.strip() or "ROOKIE PILOT"
        id_surface = id_font.render(
            fit_text(
                id_font,
                f"{id_value}  |  {callsign.upper()}",
                lw - 12
            ),
            True,
            MUTED
        )

        screen.blit(
            id_surface,
            (
                left.centerx
                - id_surface.get_width() // 2,
                name_y
                + name_surface.get_height()
                + 21
            )
        )

        card_edit_rect = pygame.Rect(
            identity_header.right - 70,
            identity_header.y + 5,
            64,
            24
        )
        draw_button(screen, card_edit_rect, "CARD", mouse_pos, tick, primary=False)

        score = max(
            0,
            safe_int(
                get_value(
                    player,
                    "score",
                    "total_score",
                    "high_score",
                    default=0
                )
            )
        )

        coins = get_profile_coins(player_id, player)

        kills = max(
            0,
            safe_int(
                get_value(
                    player,
                    "kills",
                    "ships_destroyed",
                    default=0
                )
            )
        )

        games = max(
            0,
            safe_int(
                get_value(
                    player,
                    "games_played",
                    "games",
                    "total_games",
                    default=0
                )
            )
        )

        accuracy = max(
            0,
            min(
                100,
                safe_float(
                    get_value(
                        player,
                        "accuracy",
                        "hit_accuracy",
                        default=0
                    )
                )
            )
        )

        high_score = max(
            0,
            safe_int(get_value(player, "high_score", "score", default=0))
        )

        rank = str(
            get_value(player, "rank", "arena_rank", default="")
            or get_gamer_rank(high_score)
        )

        owned_ships = get_profile_ships(player_id)

        ship_count = len(
            owned_ships
        )

        stats_top = (
            left.bottom
            - 155
        )

        stat_gap = 6

        stat_width = (
            lw
            - stat_gap * 2
        ) // 3

        stat_height = 48

        stat_data = [
            (
                "SCORE",
                number(score),
                "star"
            ),
            (
                "COINS",
                number(coins),
                "coin"
            ),
            (
                "SHIPS",
                number(ship_count),
                "ship"
            ),
        ]

        for index, data in enumerate(
            stat_data
        ):

            rect = pygame.Rect(
                lx
                + index * (
                    stat_width
                    + stat_gap
                ),
                stats_top,
                stat_width,
                stat_height
            )

            stat_card(
                screen,
                rect,
                data[0],
                data[1],
                data[2],
                TITLE_RED
            )

        bottom_stat_y = (
            stats_top
            + stat_height
            + 6
        )

        bottom_stat_width = (
            lw
            - stat_gap
        ) // 2

        stat_card(
            screen,
            pygame.Rect(
                lx,
                bottom_stat_y,
                bottom_stat_width,
                stat_height
            ),
            "GAMES",
            number(games),
            "game",
            TITLE_RED
        )

        stat_card(
            screen,
            pygame.Rect(
                lx
                + bottom_stat_width
                + stat_gap,
                bottom_stat_y,
                bottom_stat_width,
                stat_height
            ),
            "RANK",
            fit_text(
                menu_font(
                    12,
                    True
                ),
                rank,
                bottom_stat_width - 42
            ),
            "rank",
            TITLE_RED
        )

        performance_font = menu_font(
            9,
            True
        )

        performance = performance_font.render(
            f"ACCURACY {accuracy:.1f}%   •   KILLS {number(kills)}",
            True,
            MUTED
        )

        screen.blit(
            performance,
            (
                left.centerx
                - performance.get_width() // 2,
                left.bottom - 34
            )
        )

        input_font = menu_font(
            13,
            True
        )

        field_height = 44

        username_rect = pygame.Rect(
            mx,
            account_header.bottom + 10,
            mw,
            field_height
        )

        email_rect = pygame.Rect(
            mx,
            username_rect.bottom + 7,
            mw,
            field_height
        )

        draw_input(
            screen,
            username_rect,
            "person",
            username,
            active == "username",
            "Username",
            input_font,
            cursor_visible,
            tick=tick
        )

        draw_input(
            screen,
            email_rect,
            "mail",
            email,
            active == "email",
            "Email Address",
            input_font,
            cursor_visible,
            tick=tick
        )

        if active == "username":

            draw_cursor(
                screen,
                username_rect.left - 12,
                username_rect.centery,
                tick,
                6
            )

        elif active == "email":

            draw_cursor(
                screen,
                email_rect.left - 12,
                email_rect.centery,
                tick,
                6
            )

        linked_header = pygame.Rect(
            mx,
            email_rect.bottom + 8,
            mw,
            29
        )

        section_header(
            screen,
            linked_header,
            "CONNECTED ACCOUNTS",
            "user_plus",
            TITLE_RED
        )

        provider_gap = 6

        provider_width = (
            mw
            - provider_gap
        ) // 2

        provider_height = 37

        provider_rects = {}

        provider_icons = {
            "FACEBOOK": "facebook",
            "GOOGLE": "google",
            "DISCORD": "discord"
        }

        provider_colors = {
            "FACEBOOK": (
                74,
                111,
                190
            ),
            "GOOGLE": (
                220,
                80,
                65
            ),
            "DISCORD": (
                90,
                102,
                235
            )
        }

        for index, provider in enumerate(
            LINK_PROVIDERS
        ):

            row = index // 2
            col = index % 2

            rect = pygame.Rect(
                mx
                + col * (
                    provider_width
                    + provider_gap
                ),
                linked_header.bottom
                + 5
                + row * (
                    provider_height
                    + 5
                ),
                provider_width,
                provider_height
            )

            provider_rects[
                provider
            ] = rect

            linked = provider in connected_accounts

            color = provider_colors.get(
                provider,
                TITLE_RED
            )

            pygame.draw.rect(
                screen,
                (19, 25, 40),
                rect,
                border_radius=6
            )

            pygame.draw.rect(
                screen,
                color if linked else FIELD_EDGE,
                rect,
                1,
                border_radius=6
            )

            draw_icon(
                screen,
                (
                    rect.x + 17,
                    rect.centery
                ),
                provider_icons[
                    provider
                ],
                18,
                color
            )

            provider_font = menu_font(
                10,
                True
            )

            provider_text = provider_font.render(
                provider.title(),
                True,
                MENU_WHITE
            )

            screen.blit(
                provider_text,
                (
                    rect.x + 32,
                    rect.y + 6
                )
            )

            status_font = menu_font(
                8,
                True
            )

            status_text = status_font.render(
                "Connected"
                if linked
                else "Not linked",
                True,
                SUCCESS_GREEN
                if linked
                else MUTED
            )

            screen.blit(
                status_text,
                (
                    rect.x + 32,
                    rect.y + 22
                )
            )

        privacy_header = pygame.Rect(
            mx,
            linked_header.bottom
            + 2 * (
                provider_height + 5
            )
            + 8,
            mw,
            29
        )

        section_header(
            screen,
            privacy_header,
            "PRIVACY & SECURITY",
            "shield",
            TITLE_RED
        )

        setting_gap = 5

        setting_width = (
            mw
            - setting_gap
        ) // 2

        setting_height = 41

        setting_rects = {}

        setting_data = [
            (
                "friends",
                "Friend Requests",
                "Allow player requests",
                "user_plus",
                allow_friend_requests
            ),
            (
                "alerts",
                "Login Alerts",
                "Notify about new logins",
                "bell",
                login_alerts
            ),
            (
                "twofa",
                "Two-Factor",
                "Extra account security",
                "lock",
                two_factor
            ),
            (
                "online",
                "Online Visibility",
                "Show your online status",
                "shield",
                visibility == "online"
            ),
        ]

        for index, data in enumerate(
            setting_data
        ):

            row = index // 2
            col = index % 2

            rect = pygame.Rect(
                mx
                + col * (
                    setting_width
                    + setting_gap
                ),
                privacy_header.bottom
                + 5
                + row * (
                    setting_height
                    + setting_gap
                ),
                setting_width,
                setting_height
            )

            setting_rects[
                data[0]
            ] = rect

            setting_card(
                screen,
                rect,
                data[1],
                data[2],
                data[3],
                data[4],
                TITLE_RED
            )

        security_header = pygame.Rect(
            mx,
            privacy_header.bottom
            + 5
            + 2 * (
                setting_height
                + setting_gap
            )
            + 7,
            mw,
            29
        )

        section_header(
            screen,
            security_header,
            "SECURITY ACCOUNT",
            "lock",
            TITLE_RED
        )

        action_gap = 5

        action_width = (
            mw
            - action_gap * 3
        ) // 4

        action_height = max(
            46,
            middle.bottom
            - security_header.bottom
            - 16
        )

        actions = [
            (
                "PASSWORD",
                "key"
            ),
            (
                "RESET",
                "lock"
            ),
            (
                "DELETE",
                "trash"
            ),
            (
                "EXPORT",
                "download"
            ),
        ]

        action_rects = {}

        for index, action in enumerate(
            actions
        ):

            rect = pygame.Rect(
                mx
                + index * (
                    action_width
                    + action_gap
                ),
                security_header.bottom + 5,
                action_width,
                action_height
            )

            action_rects[
                action[0]
            ] = rect

            pygame.draw.rect(
                screen,
                (19, 25, 40),
                rect,
                border_radius=6
            )

            pygame.draw.rect(
                screen,
                TITLE_RED,
                rect,
                1,
                border_radius=6
            )

            draw_icon(
                screen,
                (
                    rect.centerx,
                    rect.y + min(
                        32,
                        max(22, rect.height // 3)
                    )
                ),
                action[1],
                min(
                    32,
                    max(22, rect.width - 18)
                ),
                TITLE_RED
            )

            action_font = menu_font(
                8,
                True
            )

            action_surface = action_font.render(
                action[0],
                True,
                MENU_WHITE
            )

            screen.blit(
                action_surface,
                (
                    rect.centerx
                    - action_surface.get_width() // 2,
                    rect.bottom
                    - action_surface.get_height()
                    - 7
                )
            )

        current_rect = pygame.Rect(
            rx,
            status_header.bottom + 10,
            rw,
            43
        )

        current_color = {
            "online": SUCCESS_GREEN,
            "offline": MUTED,
            "private": MENU_BLUE
        }.get(
            visibility,
            SUCCESS_GREEN
        )

        pygame.draw.rect(
            screen,
            (19, 25, 40),
            current_rect,
            border_radius=6
        )

        pygame.draw.rect(
            screen,
            TITLE_RED,
            current_rect,
            1,
            border_radius=6
        )

        draw_icon(
            screen,
            (
                current_rect.x + 18,
                current_rect.centery
            ),
            "shield",
            19,
            TITLE_RED
        )

        current_font = menu_font(
            11,
            True
        )

        current_surface = current_font.render(
            f"CURRENT: {visibility.upper()}",
            True,
            MENU_WHITE
        )

        screen.blit(
            current_surface,
            (
                current_rect.x + 36,
                current_rect.centery
                - current_surface.get_height() // 2
            )
        )

        status_font = menu_font(
            10,
            True
        )

        status_y = (
            current_rect.bottom
            + 8
        )

        status_rects = {}

        status_data = [
            (
                "online",
                "ONLINE",
                "Visible to players",
                "person",
                SUCCESS_GREEN
            ),
            (
                "offline",
                "OFFLINE",
                "Appear offline",
                "person",
                MUTED
            ),
            (
                "private",
                "PRIVATE",
                "Limited visibility",
                "lock",
                MENU_BLUE
            ),
        ]

        for data in status_data:

            rect = pygame.Rect(
                rx,
                status_y,
                rw,
                52
            )

            status_card(
                screen,
                rect,
                data[1],
                data[2],
                data[3],
                visibility == data[0],
                data[4]
            )

            status_rects[
                data[0]
            ] = rect

            status_y = (
                rect.bottom
                + 6
            )

        ship_rect = pygame.Rect(
            rx,
            right.bottom - 148,
            rw,
            132
        )

        pygame.draw.rect(
            screen,
            (19, 25, 40),
            ship_rect,
            border_radius=7
        )

        pygame.draw.rect(
            screen,
            TITLE_RED,
            ship_rect,
            1,
            border_radius=7
        )

        selected_ship = (
            get_value(
                player,
                "selected_ship",
                "current_ship",
                "equipped_ship",
                default=None
            )
        )

        if not selected_ship and database is not None:
            active_ship_getter = getattr(database, "get_active_ship", None)
            if callable(active_ship_getter):
                try:
                    selected_ship = active_ship_getter(player_id)
                except Exception:
                    selected_ship = None

        if not selected_ship and owned_ships:
            selected_ship = owned_ships[0]

        if preview_ship not in owned_ships:
            preview_ship = str(selected_ship or "")

        displayed_ship = preview_ship or selected_ship
        ship_center = (
            ship_rect.x + ship_rect.width // 2,
            ship_rect.y + 53
        )

        ship_image = load_ship(
            displayed_ship,
            min(86, ship_rect.height - 44)
        )

        if ship_image is not None:

            render_hangar_ship(
                screen,
                ship_particles,
                ship_image,
                ship_center,
                ship_rotation,
                tick,
                frame_dt,
                bob_phase=ship_bob_phase,
                accent=TITLE_RED,
                label_drag=ship_drag_start is not None,
            )

        else:

            draw_icon(
                screen,
                (
                    ship_center
                ),
                "ship", 48,
                TITLE_RED
            )

        ship_title_font = menu_font(
            10,
            True
        )

        ship_sub_font = menu_font(
            8,
            True
        )

        ship_title = ship_title_font.render(
            "SHIP HANGAR",
            True,
            MENU_WHITE
        )

        ship_subtitle = ship_sub_font.render(
            fit_text(
                ship_sub_font,
                f"{str(displayed_ship or 'starter').upper()}  |  DRAG TO SPIN",
                ship_rect.width - 18
            ),
            True,
            MUTED
        )

        screen.blit(
            ship_title,
            (
                ship_rect.centerx - ship_title.get_width() // 2,
                ship_rect.y + 6
            )
        )

        screen.blit(
            ship_subtitle,
            (
                ship_rect.centerx - ship_subtitle.get_width() // 2,
                ship_rect.y + 22
            )
        )

        ship_controls = {
            "previous": pygame.Rect(ship_rect.x + 8, ship_rect.bottom - 31, 29, 23),
            "rotate_left": pygame.Rect(ship_rect.centerx - 48, ship_rect.bottom - 31, 29, 23),
            "rotate_right": pygame.Rect(ship_rect.centerx - 15, ship_rect.bottom - 31, 29, 23),
            "next": pygame.Rect(ship_rect.right - 37, ship_rect.bottom - 31, 29, 23),
        }

        for label, control in (("<", ship_controls["previous"]), ("↶", ship_controls["rotate_left"]), ("↷", ship_controls["rotate_right"]), (">", ship_controls["next"])):
            draw_button(screen, control, label, mouse_pos, tick, primary=False)

        refresh_rect = pygame.Rect(
            width
            - margin
            - 125
            - 8
            - 170,
            height - 53,
            125,
            43
        )

        save_rect = pygame.Rect(
            width
            - margin
            - 170,
            height - 53,
            170,
            43
        )

        draw_button(
            screen,
            refresh_rect,
            "REFRESH",
            mouse_pos,
            tick,
            primary=False
        )

        draw_button(
            screen,
            save_rect,
            "SAVE CHANGES",
            mouse_pos,
            tick,
            primary=True
        )

        hint_font = menu_font(
            8,
            True
        )

        hint = hint_font.render(
            "L-CLICK AVATAR TO UPLOAD  •  R-CLICK AVATAR TO CHANGE PRESET  •  ESC BACK",
            True,
            MUTED
        )

        available_hint_width = (
            refresh_rect.x
            - margin
            - 10
        )

        hint_text = fit_text(
            hint_font,
            "L-CLICK AVATAR TO UPLOAD  |  R-CLICK AVATAR TO CHANGE PRESET  |  ESC BACK",
            available_hint_width
        )


        hint = hint_font.render(
            hint_text,
            True,
            MUTED
        )

        screen.blit(
            hint,
            (
                margin,
                height - 37
            )
        )

        if message:

            message_font = menu_font(
                11,
                True
            )

            message_surface = message_font.render(
                message,
                True,
                message_color
            )

            message_shadow = message_font.render(
                message,
                True,
                TITLE_SHADOW
            )

            message_shadow.set_alpha(
                130
            )

            message_rect = message_surface.get_rect(
                center=(
                    width // 2,
                    height - 65
                )
            )

            screen.blit(
                message_shadow,
                (
                    message_rect.x + 2,
                    message_rect.y + 2
                )
            )

            screen.blit(
                message_surface,
                message_rect
            )

        hover_targets = {
            "back": back_rect,
            "avatar": avatar_rect,
            "upload": upload_rect,
            "edit_card": card_edit_rect,
            "username": username_rect,
            "email": email_rect,
            "password": action_rects["PASSWORD"],
            "reset": action_rects["RESET"],
            "delete": action_rects["DELETE"],
            "export": action_rects["EXPORT"],
            "refresh": refresh_rect,
            "save": save_rect,
        }

        for key, rect in provider_rects.items():

            hover_targets[
                "provider_" + key.lower()
            ] = rect

        for key, rect in setting_rects.items():

            hover_targets[
                "setting_" + key
            ] = rect

        for key, rect in status_rects.items():

            hover_targets[
                "status_" + key
            ] = rect

        for key, rect in ship_controls.items():

            hover_targets["ship_" + key] = rect

        try:
            theme.update_hover(
                hover_targets,
                mouse_pos,
                scope="profile_screen"
            )
        except Exception:
            pass

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                stop_text()

                return (
                    "quit",
                    player
                )

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F11:

                    toggle_fullscreen()

                elif event.key == pygame.K_ESCAPE:

                    if mode != "profile":

                        if mode == "card" and card_draft is not None:
                            gamer_tag, bio = card_draft
                            card_draft = None

                        mode = "profile"
                        pending_provider = None
                        connected_accounts.pop(
                            "__pending__",
                            None
                        )
                        stop_text()

                    else:

                        stop_text()
                        theme.sound_back()

                        return (
                            "menu",
                            player
                        )

                elif (
                    event.key == pygame.K_s
                    and event.mod & pygame.KMOD_CTRL
                    and mode == "profile"
                ):

                    save_changes()

                elif active:

                    if event.key == pygame.K_BACKSPACE:

                        if active == "username":
                            username = username[:-1]

                        elif active == "email":
                            email = email[:-1]

                        elif active in password_values:

                            password_values[
                                active
                            ] = password_values[
                                active
                            ][:-1]

                        elif active == "delete":
                            delete_text = delete_text[:-1]

                        elif active == "link":

                            link_text = link_text[:-1]

                        elif active == "gamer_tag":

                            gamer_tag = gamer_tag[:-1]

                        elif active == "bio":

                            bio = bio[:-1]

                    elif event.key == pygame.K_TAB:

                        if mode == "profile":

                            if active == "username":
                                start_text(
                                    "email"
                                )
                            else:
                                start_text(
                                    "username"
                                )

                    elif event.key == pygame.K_RETURN:

                        if mode == "profile":

                            if active == "username":

                                start_text(
                                    "email"
                                )

                            else:

                                stop_text()

                    elif event.key == pygame.K_F11:

                        toggle_fullscreen()

            if event.type == pygame.TEXTINPUT:

                if not active:
                    continue

                text = event.text

                if active == "username":

                    username = (
                        username
                        + text
                    )[:MAX_USERNAME_LENGTH]

                elif active == "email":

                    email = (
                        email
                        + text
                    )[:MAX_EMAIL_LENGTH]

                elif active in password_values:

                    password_values[
                        active
                    ] = (
                        password_values[
                            active
                        ]
                        + text
                    )[:MAX_PASSWORD_LENGTH]

                elif active == "delete":

                    delete_text = (
                        delete_text
                        + text
                    )[:10]

                elif active == "link":

                    link_text = (
                        link_text
                        + text
                    )[:60]

                elif active == "gamer_tag":

                    gamer_tag = (gamer_tag + text)[:MAX_GAMER_TAG_LENGTH]

                elif active == "bio":

                    bio = (bio + text)[:MAX_BIO_LENGTH]

            if event.type == pygame.MOUSEMOTION:

                if mode == "profile" and ship_drag_start is not None:
                    ship_rotation = (
                        ship_drag_rotation
                        - (event.pos[0] - ship_drag_start[0])
                    ) % 360
                    ship_spin_velocity = -event.rel[0] * 0.9

            if event.type == pygame.MOUSEBUTTONUP:

                if event.button == 1:
                    ship_drag_start = None

            if event.type == pygame.MOUSEBUTTONDOWN:

                pos = event.pos

                if mode == "profile":

                    if (
                        event.button == 1
                        and back_rect.collidepoint(pos)
                    ):

                        stop_text()
                        theme.sound_back()

                        return (
                            "menu",
                            player
                        )

                    if (
                        avatar_rect.collidepoint(pos)
                        or upload_rect.collidepoint(pos)
                    ):

                        if event.button == 3:

                            try:
                                index = AVATAR_KINDS.index(
                                    avatar_kind
                                )
                            except ValueError:
                                index = 0

                            avatar_kind = AVATAR_KINDS[
                                (
                                    index + 1
                                ) % len(
                                    AVATAR_KINDS
                                )
                            ]

                            avatar_path = None

                            theme.sound_click()

                            message_show(
                                f"AVATAR {avatar_kind.upper()}",
                                SUCCESS_GREEN
                            )

                        elif event.button == 1:

                            theme.sound_click()

                            selected = choose_avatar()

                            if selected:

                                avatar_path = selected

                                message_show(
                                    "AVATAR UPDATED",
                                    SUCCESS_GREEN
                                )

                        continue

                    if (
                        event.button == 1
                        and card_edit_rect.collidepoint(pos)
                    ):

                        mode = "card"
                        card_draft = (gamer_tag, bio)
                        stop_text()
                        theme.sound_click()

                        continue

                    if (
                        event.button == 1
                        and username_rect.collidepoint(pos)
                    ):

                        start_text(
                            "username"
                        )

                        continue

                    if (
                        event.button == 1
                        and email_rect.collidepoint(pos)
                    ):

                        start_text(
                            "email"
                        )

                        continue

                    provider_clicked = False

                    for provider, rect in provider_rects.items():

                        if rect.collidepoint(pos):

                            provider_clicked = True
                            theme.sound_click()

                            if provider in connected_accounts:

                                connected_accounts.pop(
                                    provider,
                                    None
                                )

                                message_show(
                                    f"{provider.title()} DISCONNECTED",
                                    SUCCESS_GREEN
                                )

                            else:

                                pending_provider = provider
                                link_text = ""
                                mode = "link"
                                stop_text()

                            break

                    if provider_clicked:
                        continue

                    setting_clicked = False

                    for key, rect in setting_rects.items():

                        if rect.collidepoint(pos):

                            setting_clicked = True
                            theme.sound_click()

                            if key == "friends":

                                allow_friend_requests = not allow_friend_requests

                            elif key == "alerts":

                                login_alerts = not login_alerts

                            elif key == "twofa":

                                two_factor = not two_factor

                            elif key == "online":

                                if visibility == "online":
                                    visibility = "offline"
                                else:
                                    visibility = "online"

                            break

                    if setting_clicked:
                        continue

                    status_clicked = False

                    for key, rect in status_rects.items():

                        if rect.collidepoint(pos):

                            status_clicked = True

                            visibility = key

                            theme.sound_click()

                            break

                    if status_clicked:
                        continue

                    if (
                        event.button == 1
                        and ship_rect.collidepoint(pos)
                        and not any(
                            rect.collidepoint(pos)
                            for rect in ship_controls.values()
                        )
                    ):
                        ship_drag_start = pos
                        ship_drag_rotation = ship_rotation
                        theme.sound_click()
                        continue

                    for key, rect in ship_controls.items():

                        if not rect.collidepoint(pos):
                            continue

                        theme.sound_click()

                        if key == "rotate_left":
                            ship_spin_velocity += 7.0

                        elif key == "rotate_right":
                            ship_spin_velocity -= 7.0

                        elif owned_ships:
                            current_index = (
                                owned_ships.index(preview_ship)
                                if preview_ship in owned_ships
                                else 0
                            )
                            offset = -1 if key == "previous" else 1
                            preview_ship = owned_ships[(current_index + offset) % len(owned_ships)]

                        message_show("HANGAR VIEW UPDATED — SAVE CHANGES", SUCCESS_GREEN)
                        break
                    else:
                        key = None

                    if key is not None:
                        continue

                    if action_rects[
                        "PASSWORD"
                    ].collidepoint(pos):

                        mode = "password"

                        password_values = {
                            "current": "",
                            "new": "",
                            "confirm": ""
                        }

                        password_reveal = {
                            "current": False,
                            "new": False,
                            "confirm": False
                        }

                        stop_text()
                        theme.sound_click()

                        continue

                    if action_rects[
                        "RESET"
                    ].collidepoint(pos):

                        theme.sound_click()

                        reset_function = None

                        if database is not None:

                            reset_function = getattr(
                                database,
                                "request_password_reset",
                                None
                            )

                        result = None

                        if callable(reset_function):

                            try:
                                result = reset_function(
                                    player_id
                                )
                            except Exception:
                                result = False

                        if result is False:

                            message_show(
                                "RESET REQUEST FAILED"
                            )

                        else:

                            message_show(
                                "PASSWORD RESET REQUESTED",
                                SUCCESS_GREEN
                            )

                        continue

                    if action_rects[
                        "DELETE"
                    ].collidepoint(pos):

                        delete_text = ""
                        mode = "delete"
                        stop_text()
                        theme.sound_click()

                        continue

                    if action_rects[
                        "EXPORT"
                    ].collidepoint(pos):

                        theme.sound_click()

                        export_settings = {
                            "avatar": avatar_kind,
                            "avatar_path": avatar_path,
                            "visibility": visibility,
                            "allow_friend_requests": allow_friend_requests,
                            "login_alerts": login_alerts,
                            "two_factor": two_factor,
                            "connected_accounts": connected_accounts,
                            "preview_ship": preview_ship,
                            "ship_preview_rotation": ship_rotation,
                        }

                        result = export_data(
                            player_id,
                            player,
                            export_settings
                        )

                        if result:

                            message_show(
                                "PROFILE DATA EXPORTED",
                                SUCCESS_GREEN
                            )

                        else:

                            message_show(
                                "EXPORT FAILED"
                            )

                        continue

                    if refresh_rect.collidepoint(pos):

                        theme.sound_click()

                        refreshed = read_player(
                            player_id,
                            player
                        )

                        if isinstance(
                            refreshed,
                            dict
                        ):

                            player.clear()
                            player.update(
                                refreshed
                            )

                            refreshed_settings = load_settings(
                                player_id
                            )

                            username = str(
                                get_value(
                                    player,
                                    "username",
                                    "display_name",
                                    default=username
                                )
                                or username
                            )

                            email = str(
                                get_value(
                                    player,
                                    "email",
                                    default=email
                                )
                                or email
                            )

                            avatar_kind = player.get(
                                "avatar",
                                refreshed_settings.get(
                                    "avatar",
                                    avatar_kind
                                )
                            )

                            avatar_path = get_value(
                                player,
                                "profile_picture",
                                "avatar_path",
                                default=None
                            ) or refreshed_settings.get(
                                "avatar_path",
                                avatar_path
                            )

                            visibility = player.get(
                                "visibility",
                                refreshed_settings.get(
                                    "visibility",
                                    visibility
                                )
                            )

                            allow_friend_requests = bool(
                                player.get(
                                    "allow_friend_requests",
                                    refreshed_settings.get(
                                        "allow_friend_requests",
                                        allow_friend_requests
                                    )
                                )
                            )

                            login_alerts = bool(
                                player.get(
                                    "login_alerts",
                                    refreshed_settings.get(
                                        "login_alerts",
                                        login_alerts
                                    )
                                )
                            )

                            two_factor = bool(
                                player.get(
                                    "two_factor",
                                    refreshed_settings.get(
                                        "two_factor",
                                        two_factor
                                    )
                                )
                            )

                            connected_accounts = dict(
                                refreshed_settings.get(
                                    "connected_accounts",
                                    connected_accounts
                                )
                            )

                            preview_ship = str(
                                refreshed_settings.get(
                                    "preview_ship",
                                    preview_ship
                                ) or ""
                            )
                            ship_rotation = safe_float(
                                refreshed_settings.get(
                                    "ship_preview_rotation",
                                    ship_rotation
                                )
                            ) % 360

                            message_show(
                                "PROFILE REFRESHED",
                                SUCCESS_GREEN
                            )

                        else:

                            message_show(
                                "REFRESH FAILED"
                            )

                        continue

                    if save_rect.collidepoint(pos):

                        theme.sound_click()

                        save_changes()

                        continue

                elif mode == "card":

                    modal = pygame.Rect(0, 0, min(480, width - 60), 280)
                    modal.center = (width // 2, height // 2)
                    tag_rect = pygame.Rect(modal.x + 22, modal.y + 76, modal.width - 44, 43)
                    bio_rect = pygame.Rect(modal.x + 22, modal.y + 128, modal.width - 44, 43)
                    save_card_rect = pygame.Rect(modal.x + 22, modal.bottom - 51, (modal.width - 53) // 2, 40)
                    cancel_rect = pygame.Rect(modal.centerx + 5, modal.bottom - 51, (modal.width - 53) // 2, 40)

                    if tag_rect.collidepoint(pos):
                        start_text("gamer_tag")
                    elif bio_rect.collidepoint(pos):
                        start_text("bio")
                    elif save_card_rect.collidepoint(pos):
                        mode = "profile"
                        card_draft = None
                        stop_text()
                        message_show("CARD READY — SAVE CHANGES", SUCCESS_GREEN)
                    elif cancel_rect.collidepoint(pos):
                        if card_draft is not None:
                            gamer_tag, bio = card_draft
                            card_draft = None
                        mode = "profile"
                        stop_text()
                        theme.sound_back()

                elif mode == "link":

                    modal_w = min(
                        460,
                        width - 60
                    )

                    modal_h = 225

                    modal = pygame.Rect(
                        0,
                        0,
                        modal_w,
                        modal_h
                    )

                    modal.center = (
                        width // 2,
                        height // 2
                    )

                    input_rect = pygame.Rect(
                        modal.x + 22,
                        modal.y + 80,
                        modal.width - 44,
                        44
                    )

                    connect_rect = pygame.Rect(
                        modal.x + 22,
                        modal.bottom - 51,
                        (
                            modal.width - 52
                        ) // 2,
                        40
                    )

                    cancel_rect = pygame.Rect(
                        modal.centerx + 4,
                        modal.bottom - 51,
                        (
                            modal.width - 52
                        ) // 2,
                        40
                    )

                    if input_rect.collidepoint(pos):

                        start_text(
                            "link"
                        )

                    elif connect_rect.collidepoint(pos):

                        if len(
                            link_text.strip()
                        ) < 2:

                            message_show(
                                "ENTER AN ACCOUNT ID"
                            )

                        else:

                            connected_accounts[
                                pending_provider
                            ] = link_text.strip()

                            mode = "profile"
                            pending_provider = None
                            stop_text()

                            message_show(
                                "ACCOUNT CONNECTED",
                                SUCCESS_GREEN
                            )

                    elif cancel_rect.collidepoint(pos):

                        mode = "profile"
                        pending_provider = None
                        stop_text()
                        theme.sound_back()

                elif mode == "password":

                    modal_w = min(
                        470,
                        width - 60
                    )

                    modal_h = 350

                    modal = pygame.Rect(
                        0,
                        0,
                        modal_w,
                        modal_h
                    )

                    modal.center = (
                        width // 2,
                        height // 2
                    )

                    current_rect = pygame.Rect(
                        modal.x + 22,
                        modal.y + 70,
                        modal.width - 44,
                        43
                    )

                    new_rect = pygame.Rect(
                        modal.x + 22,
                        modal.y + 122,
                        modal.width - 44,
                        43
                    )

                    confirm_rect = pygame.Rect(
                        modal.x + 22,
                        modal.y + 174,
                        modal.width - 44,
                        43
                    )

                    current_eye = pygame.Rect(
                        current_rect.right - 44,
                        current_rect.y + 3,
                        38,
                        37
                    )

                    new_eye = pygame.Rect(
                        new_rect.right - 44,
                        new_rect.y + 3,
                        38,
                        37
                    )

                    confirm_eye = pygame.Rect(
                        confirm_rect.right - 44,
                        confirm_rect.y + 3,
                        38,
                        37
                    )

                    update_rect = pygame.Rect(
                        modal.x + 22,
                        modal.bottom - 50,
                        (
                            modal.width - 53
                        ) // 2,
                        40
                    )

                    cancel_rect = pygame.Rect(
                        modal.centerx + 5,
                        modal.bottom - 50,
                        (
                            modal.width - 53
                        ) // 2,
                        40
                    )

                    if current_rect.collidepoint(pos):

                        start_text(
                            "current"
                        )

                    elif new_rect.collidepoint(pos):

                        start_text(
                            "new"
                        )

                    elif confirm_rect.collidepoint(pos):

                        start_text(
                            "confirm"
                        )

                    elif current_eye.collidepoint(pos):

                        password_reveal[
                            "current"
                        ] = not password_reveal[
                            "current"
                        ]

                        theme.sound_click()

                    elif new_eye.collidepoint(pos):

                        password_reveal[
                            "new"
                        ] = not password_reveal[
                            "new"
                        ]

                        theme.sound_click()

                    elif confirm_eye.collidepoint(pos):

                        password_reveal[
                            "confirm"
                        ] = not password_reveal[
                            "confirm"
                        ]

                        theme.sound_click()

                    elif update_rect.collidepoint(pos):

                        current_password = password_values[
                            "current"
                        ]

                        new_password = password_values[
                            "new"
                        ]

                        confirm_password = password_values[
                            "confirm"
                        ]

                        if len(new_password) < 6:

                            message_show(
                                "NEW PASSWORD MUST BE 6+ CHARACTERS"
                            )

                            continue

                        if new_password != confirm_password:

                            message_show(
                                "PASSWORDS DO NOT MATCH"
                            )

                            continue

                        if database is None:

                            message_show(
                                "DATABASE UNAVAILABLE"
                            )

                            continue

                        verified = None

                        try:

                            verified = database.login_player(
                                username,
                                current_password
                            )

                        except Exception:
                            verified = None

                        if not verified:

                            message_show(
                                "CURRENT PASSWORD INCORRECT"
                            )

                            continue

                        update_function = getattr(
                            database,
                            "update_password",
                            None
                        )

                        if not callable(
                            update_function
                        ):

                            message_show(
                                "PASSWORD UPDATE NOT AVAILABLE"
                            )

                            continue

                        try:

                            changed = update_function(
                                player_id,
                                new_password
                            )

                        except Exception:

                            changed = False

                        if changed:

                            mode = "profile"
                            stop_text()

                            message_show(
                                "PASSWORD UPDATED",
                                SUCCESS_GREEN
                            )

                        else:

                            message_show(
                                "PASSWORD UPDATE FAILED"
                            )

                    elif cancel_rect.collidepoint(pos):

                        mode = "profile"
                        stop_text()
                        theme.sound_back()

                elif mode == "delete":

                    modal_w = min(
                        430,
                        width - 60
                    )

                    modal_h = 245

                    modal = pygame.Rect(
                        0,
                        0,
                        modal_w,
                        modal_h
                    )

                    modal.center = (
                        width // 2,
                        height // 2
                    )

                    input_rect = pygame.Rect(
                        modal.x + 22,
                        modal.y + 84,
                        modal.width - 44,
                        44
                    )

                    confirm_rect = pygame.Rect(
                        modal.x + 22,
                        modal.bottom - 50,
                        (
                            modal.width - 53
                        ) // 2,
                        40
                    )

                    cancel_rect = pygame.Rect(
                        modal.centerx + 5,
                        modal.bottom - 50,
                        (
                            modal.width - 53
                        ) // 2,
                        40
                    )

                    if input_rect.collidepoint(pos):

                        start_text(
                            "delete"
                        )

                    elif confirm_rect.collidepoint(pos):

                        if (
                            delete_text
                            .strip()
                            .upper()
                            != "DELETE"
                        ):

                            message_show(
                                "TYPE DELETE TO CONFIRM"
                            )

                            continue

                        if delete_account(
                            player_id
                        ):

                            stop_text()
                            theme.sound_success()

                            return (
                                "login",
                                None
                            )

                        message_show(
                            "COULD NOT DELETE ACCOUNT"
                        )

                    elif cancel_rect.collidepoint(pos):

                        mode = "profile"
                        stop_text()
                        theme.sound_back()

        if mode == "card":

            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))
            screen.blit(overlay, (0, 0))

            modal = pygame.Rect(0, 0, min(480, width - 60), 280)
            modal.center = (width // 2, height // 2)
            draw_panel(screen, modal, tick)
            draw_title(screen, "PLAYER CARD", modal.centerx, modal.y + 16, 25, underline_width=155)

            info_font = menu_font(9, True)
            info = info_font.render("Create the identity other pilots see in the arena.", True, MUTED)
            screen.blit(info, (modal.centerx - info.get_width() // 2, modal.y + 52))

            tag_rect = pygame.Rect(modal.x + 22, modal.y + 76, modal.width - 44, 43)
            bio_rect = pygame.Rect(modal.x + 22, modal.y + 128, modal.width - 44, 43)
            card_font = menu_font(12, True)
            draw_input(screen, tag_rect, "person", gamer_tag, active == "gamer_tag", "Callsign / gamer tag", card_font, cursor_visible, tick=tick)
            draw_input(screen, bio_rect, "star", bio, active == "bio", "Bio (your play style or squad motto)", card_font, cursor_visible, tick=tick)

            save_card_rect = pygame.Rect(modal.x + 22, modal.bottom - 51, (modal.width - 53) // 2, 40)
            cancel_rect = pygame.Rect(modal.centerx + 5, modal.bottom - 51, (modal.width - 53) // 2, 40)
            draw_button(screen, save_card_rect, "DONE", mouse_pos, tick, primary=True)
            draw_button(screen, cancel_rect, "CANCEL", mouse_pos, tick, primary=False)

        elif mode == "link":

            overlay = pygame.Surface(
                screen.get_size(),
                pygame.SRCALPHA
            )

            overlay.fill(
                (
                    0,
                    0,
                    0,
                    175
                )
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            modal_w = min(
                460,
                width - 60
            )

            modal_h = 225

            modal = pygame.Rect(
                0,
                0,
                modal_w,
                modal_h
            )

            modal.center = (
                width // 2,
                height // 2
            )

            draw_panel(
                screen,
                modal,
                tick
            )

            draw_title(
                screen,
                f"LINK {pending_provider}",
                modal.centerx,
                modal.y + 16,
                25,
                underline_width=175
            )

            info_font = menu_font(
                10,
                True
            )

            info = info_font.render(
                "Enter the account email, username, or ID.",
                True,
                MUTED
            )

            screen.blit(
                info,
                (
                    modal.centerx
                    - info.get_width() // 2,
                    modal.y + 52
                )
            )

            input_rect = pygame.Rect(
                modal.x + 22,
                modal.y + 80,
                modal.width - 44,
                44
            )

            draw_input(
                screen,
                input_rect,
                "person",
                link_text,
                active == "link",
                "Account identifier",
                menu_font(
                    13,
                    True
                ),
                cursor_visible,
                tick=tick
            )

            connect_rect = pygame.Rect(
                modal.x + 22,
                modal.bottom - 51,
                (
                    modal.width - 52
                ) // 2,
                40
            )

            cancel_rect = pygame.Rect(
                modal.centerx + 4,
                modal.bottom - 51,
                (
                    modal.width - 52
                ) // 2,
                40
            )

            draw_button(
                screen,
                connect_rect,
                "CONNECT",
                mouse_pos,
                tick,
                primary=True
            )

            draw_button(
                screen,
                cancel_rect,
                "CANCEL",
                mouse_pos,
                tick,
                primary=False
            )

        elif mode == "password":

            overlay = pygame.Surface(
                screen.get_size(),
                pygame.SRCALPHA
            )

            overlay.fill(
                (
                    0,
                    0,
                    0,
                    175
                )
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            modal_w = min(
                470,
                width - 60
            )

            modal_h = 350

            modal = pygame.Rect(
                0,
                0,
                modal_w,
                modal_h
            )

            modal.center = (
                width // 2,
                height // 2
            )

            draw_panel(
                screen,
                modal,
                tick
            )

            draw_title(
                screen,
                "CHANGE PASSWORD",
                modal.centerx,
                modal.y + 16,
                25,
                underline_width=190
            )

            current_rect = pygame.Rect(
                modal.x + 22,
                modal.y + 70,
                modal.width - 44,
                43
            )

            new_rect = pygame.Rect(
                modal.x + 22,
                modal.y + 122,
                modal.width - 44,
                43
            )

            confirm_rect = pygame.Rect(
                modal.x + 22,
                modal.y + 174,
                modal.width - 44,
                43
            )

            password_font = menu_font(
                13,
                True
            )

            draw_input(
                screen,
                current_rect,
                "lock",
                password_values["current"],
                active == "current",
                "Current password",
                password_font,
                cursor_visible,
                masked=not password_reveal["current"],
                tick=tick
            )

            draw_input(
                screen,
                new_rect,
                "lock",
                password_values["new"],
                active == "new",
                "New password",
                password_font,
                cursor_visible,
                masked=not password_reveal["new"],
                tick=tick
            )

            draw_input(
                screen,
                confirm_rect,
                "lock",
                password_values["confirm"],
                active == "confirm",
                "Confirm new password",
                password_font,
                cursor_visible,
                masked=not password_reveal["confirm"],
                tick=tick
            )

            current_eye = pygame.Rect(
                current_rect.right - 44,
                current_rect.y + 3,
                38,
                37
            )

            new_eye = pygame.Rect(
                new_rect.right - 44,
                new_rect.y + 3,
                38,
                37
            )

            confirm_eye = pygame.Rect(
                confirm_rect.right - 44,
                confirm_rect.y + 3,
                38,
                37
            )

            draw_eye_icon(
                screen,
                current_eye.center,
                9,
                TITLE_RED,
                password_reveal["current"]
            )

            draw_eye_icon(
                screen,
                new_eye.center,
                9,
                TITLE_RED,
                password_reveal["new"]
            )

            draw_eye_icon(
                screen,
                confirm_eye.center,
                9,
                TITLE_RED,
                password_reveal["confirm"]
            )

            update_rect = pygame.Rect(
                modal.x + 22,
                modal.bottom - 50,
                (
                    modal.width - 53
                ) // 2,
                40
            )

            cancel_rect = pygame.Rect(
                modal.centerx + 5,
                modal.bottom - 50,
                (
                    modal.width - 53
                ) // 2,
                40
            )

            draw_button(
                screen,
                update_rect,
                "UPDATE",
                mouse_pos,
                tick,
                primary=True
            )

            draw_button(
                screen,
                cancel_rect,
                "CANCEL",
                mouse_pos,
                tick,
                primary=False
            )

        elif mode == "delete":

            overlay = pygame.Surface(
                screen.get_size(),
                pygame.SRCALPHA
            )

            overlay.fill(
                (
                    0,
                    0,
                    0,
                    180
                )
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            modal_w = min(
                430,
                width - 60
            )

            modal_h = 245

            modal = pygame.Rect(
                0,
                0,
                modal_w,
                modal_h
            )

            modal.center = (
                width // 2,
                height // 2
            )

            draw_panel(
                screen,
                modal,
                tick
            )

            draw_title(
                screen,
                "DELETE ACCOUNT",
                modal.centerx,
                modal.y + 16,
                25,
                underline_width=180
            )

            draw_icon(
                screen,
                (
                    modal.centerx,
                    modal.y + 59
                ),
                "trash",
                24,
                TITLE_RED
            )

            warning_font = menu_font(
                10,
                True
            )

            warning = warning_font.render(
                "This permanently deletes your account data.",
                True,
                MUTED
            )

            screen.blit(
                warning,
                (
                    modal.centerx
                    - warning.get_width() // 2,
                    modal.y + 72
                )
            )

            input_rect = pygame.Rect(
                modal.x + 22,
                modal.y + 84,
                modal.width - 44,
                44
            )

            draw_input(
                screen,
                input_rect,
                "lock",
                delete_text,
                active == "delete",
                "Type DELETE to confirm",
                menu_font(
                    13,
                    True
                ),
                cursor_visible,
                tick=tick
            )

            confirm_rect = pygame.Rect(
                modal.x + 22,
                modal.bottom - 50,
                (
                    modal.width - 53
                ) // 2,
                40
            )

            cancel_rect = pygame.Rect(
                modal.centerx + 5,
                modal.bottom - 50,
                (
                    modal.width - 53
                ) // 2,
                40
            )

            draw_button(
                screen,
                confirm_rect,
                "DELETE",
                mouse_pos,
                tick,
                primary=True
            )

            draw_button(
                screen,
                cancel_rect,
                "CANCEL",
                mouse_pos,
                tick,
                primary=False
            )

        pygame.display.flip()

        clock.tick(60)

    stop_text()

    return (
        "quit",
        player
    )


def profile_screen(screen, clock, player=None):
    player = player if isinstance(player, dict) else {}
    player_id = get_value(player, "id", "player_id", "user_id", default=None)
    settings = load_settings(player_id)

    username = str(
        get_value(player, "username", "display_name", default="SPACE ACE")
        or "SPACE ACE"
    ).upper()
    avatar_kind = player.get("avatar", settings.get("avatar", "hood"))
    avatar_path = (
        get_value(player, "profile_picture", "avatar_path", default=None)
        or settings.get("avatar_path")
    )

    catalog = get_ship_catalog(player_id)
    if not catalog:
        catalog = ["starter", "falcon", "viper", "phantom", "titan", "nova", "specter", "raven"]

    selected_ship = str(
        get_value(
            player,
            "selected_ship",
            "current_ship",
            "equipped_ship",
            "ship",
            default=settings.get("selected_ship") or settings.get("preview_ship") or "starter",
        )
        or "starter"
    ).lower()

    if selected_ship not in catalog:
        catalog.insert(0, selected_ship)

    color_name = str(
        get_value(player, "ship_color", default=None)
        or settings.get("ship_color")
        or "CRIMSON"
    ).upper()
    if color_name not in SHIP_COLORS:
        color_name = "CRIMSON"

    rotation = safe_float(
        settings.get("ship_rotation", settings.get("ship_preview_rotation", 0)),
        0.0,
    ) % 360
    index = catalog.index(selected_ship) if selected_ship in catalog else 0
    drag_start = None
    drag_rotation = rotation
    message = ""
    message_until = 0

    def toast(text, ok=False):
        nonlocal message, message_until
        message = str(text)
        message_until = pygame.time.get_ticks() + 1900
        try:
            theme.sound_click()
        except Exception:
            pass

    def save_current():
        if not ship_is_owned(player_id, selected_ship):
            toast("LOCKED SHIP — CANNOT EQUIP", False)
            return
        save_ship_loadout(player_id, player, selected_ship, color_name, rotation)
        toast("LOADOUT SAVED — READY FOR COMBAT", True)

    def panel(rect, accent=MENU_BLUE, fill=(3, 9, 18), radius=12):
        pygame.draw.rect(screen, fill, rect, border_radius=radius)
        pygame.draw.rect(screen, (19, 53, 83), rect, 1, border_radius=radius)
        pygame.draw.line(
            screen,
            accent,
            (rect.x + 12, rect.y + 1),
            (rect.right - 12, rect.y + 1),
            2,
        )

    def panel_title(rect, title, accent=MENU_BLUE):
        f = menu_font(11, True)
        s = f.render(title.upper(), True, accent)
        screen.blit(s, (rect.x + 12, rect.y + 9))

    def stat_box(rect, label, value, icon, accent):
        panel(rect, accent=accent, fill=(5, 12, 22), radius=9)
        try:
            draw_icon(screen, (rect.x + 19, rect.centery), icon, 15, accent)
        except Exception:
            pass
        lf = menu_font(8, True)
        vf = menu_font(14, True)
        l = lf.render(label, True, MUTED)
        v = vf.render(value, True, MENU_WHITE)
        screen.blit(l, (rect.x + 34, rect.y + 7))
        screen.blit(v, (rect.x + 34, rect.y + 21))

    def progress_bar(rect, ratio, fill_color=MENU_BLUE):
        ratio = max(0.0, min(1.0, float(ratio)))
        pygame.draw.rect(screen, (6, 15, 28), rect, border_radius=6)
        pygame.draw.rect(screen, (29, 67, 99), rect, 1, border_radius=6)
        if ratio > 0:
            inner = rect.inflate(-4, -4)
            inner.width = max(4, int(inner.width * ratio))
            pygame.draw.rect(screen, fill_color, inner, border_radius=4)
            glow = pygame.Surface((inner.width + 18, inner.height + 12), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*fill_color, 55), glow.get_rect(), border_radius=5)
            screen.blit(glow, (inner.x - 9, inner.y - 6), special_flags=pygame.BLEND_RGBA_ADD)

    running = True
    while running:
        width, height = screen.get_size()
        tick = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        draw_background(screen, width, height, tick)

        margin = max(18, int(width * 0.028))
        header_h = 54
        content_top = header_h + 18
        bottom = height - 18

        back_rect = pygame.Rect(margin, 12, 90, 34)
        ready_rect = pygame.Rect(width - margin - 132, 12, 132, 34)
        draw_button(screen, back_rect, "BACK", mouse_pos, tick, primary=False)
        draw_title(screen, "PILOT PROFILE", width // 2, 15, 30, underline_width=190)
        draw_button(screen, ready_rect, "COMBAT READY", mouse_pos, tick, primary=False)

        left_w = max(306, int(width * 0.34))
        gap = 14
        left = pygame.Rect(margin, content_top, left_w, bottom - content_top)
        right = pygame.Rect(left.right + gap, content_top, width - margin - left.right - gap, bottom - content_top)

        panel(left, accent=MENU_BLUE, fill=(2, 7, 14), radius=14)
        panel(right, accent=MENU_BLUE, fill=(2, 7, 14), radius=14)

        small = menu_font(9, True)
        body = menu_font(11, True)
        title_font = menu_font(18, True)
        big = menu_font(21, True)

        # PILOT IDENTITY
        identity_h = 202
        identity = pygame.Rect(left.x + 12, left.y + 12, left.width - 24, identity_h)
        panel(identity, accent=MENU_BLUE, fill=(4, 11, 20), radius=11)
        panel_title(identity, "PILOT IDENTITY")

        avatar_size = min(88, max(68, identity.width // 4))
        avatar_center = (identity.x + 62, identity.y + 103)
        pygame.draw.circle(screen, (7, 22, 35), avatar_center, avatar_size // 2 + 8)
        pygame.draw.circle(screen, MENU_BLUE, avatar_center, avatar_size // 2 + 8, 2)
        avatar_image = None
        if avatar_path:
            avatar_image = load_custom_avatar(avatar_path, avatar_size)
        if avatar_image is None:
            avatar_image = load_preset_avatar(avatar_kind, avatar_size)
        if avatar_image is not None:
            ci = circular_image(avatar_image)
            screen.blit(ci, ci.get_rect(center=avatar_center))
        else:
            try:
                draw_person_icon(screen, avatar_center, avatar_size // 2, MENU_BLUE)
            except Exception:
                try:
                    draw_icon(screen, avatar_center, "person", 42, MENU_BLUE)
                except Exception:
                    pass

        info_x = avatar_center[0] + avatar_size // 2 + 22
        name_font = menu_font(17, True)
        name_s = name_font.render(fit_text(name_font, username, identity.right - info_x - 12), True, MENU_WHITE)
        screen.blit(name_s, (info_x, identity.y + 48))

        high_score = max(0, safe_int(get_value(player, "high_score", "score", default=0)))
        level = max(1, safe_int(get_value(player, "level", default=1), 1))
        rank = get_gamer_rank(high_score)
        rank_s = small.render(f"LV. {level}  •  {rank}", True, MENU_BLUE)
        screen.blit(rank_s, (info_x, identity.y + 74))

        callsign = str(settings.get("gamer_tag") or get_value(player, "gamer_tag", default="SPACE ACE") or "SPACE ACE").upper()
        call_s = small.render(fit_text(small, callsign, identity.right - info_x - 12), True, MUTED)
        screen.blit(call_s, (info_x, identity.y + 94))

        # compact pilot telemetry
        total_xp = max(1, safe_int(get_value(player, "xp_to_next", "next_xp", default=2000), 2000))
        xp = max(0, safe_int(get_value(player, "xp", "experience", default=1820), 1820))
        xp_ratio = min(1.0, xp / total_xp)
        xp_label = small.render(f"{number(xp)} / {number(total_xp)} XP", True, MUTED)
        screen.blit(xp_label, (info_x, identity.y + 122))
        progress_bar(pygame.Rect(info_x, identity.y + 140, identity.right - info_x - 12, 10), xp_ratio, MENU_BLUE)

        status_y = identity.bottom - 28
        pygame.draw.circle(screen, SUCCESS_GREEN, (identity.x + 15, status_y), 4)
        st = small.render("ONLINE  •  ACTIVE  •  READY", True, SUCCESS_GREEN)
        screen.blit(st, (identity.x + 26, status_y - 6))

        # CORE STATS
        stats_y = identity.bottom + 10
        stat_gap = 8
        stat_w = (left.width - 24 - stat_gap * 2) // 3
        stats = [
            ("SCORE", number(max(0, safe_int(get_value(player, "total_score", "score", "high_score", default=high_score)))), "star"),
            ("COINS", number(get_profile_coins(player_id, player)), "coin"),
            ("GAMES", number(max(0, safe_int(get_value(player, "total_games", "games_played", "games", default=0)))), "game"),
        ]
        for i, (label, value, icon) in enumerate(stats):
            r = pygame.Rect(left.x + 12 + i * (stat_w + stat_gap), stats_y, stat_w, 52)
            stat_box(r, label, value, icon, MENU_BLUE)

        # CURRENT LOADOUT
        loadout = pygame.Rect(left.x + 12, stats_y + 64, left.width - 24, 108)
        panel(loadout, accent=SHIP_COLORS[color_name]["accent"], fill=(4, 12, 22), radius=10)
        panel_title(loadout, "CURRENT LOADOUT", SHIP_COLORS[color_name]["accent"])

        thumb_rect = pygame.Rect(loadout.x + 11, loadout.y + 34, 86, 61)
        pygame.draw.rect(screen, (2, 8, 16), thumb_rect, border_radius=8)
        pygame.draw.rect(screen, (17, 49, 73), thumb_rect, 1, border_radius=8)
        thumb = load_ship_variant(selected_ship, color_name, 62)
        if thumb is not None:
            bob = math.sin(tick / 420.0) * 2
            rt = pygame.transform.rotozoom(thumb, rotation * 0.15, 1.0)
            screen.blit(rt, rt.get_rect(center=(thumb_rect.centerx, thumb_rect.centery + int(bob))))
        else:
            draw_icon(screen, thumb_rect.center, "ship", 35, MENU_BLUE)

        load_name = title_font.render(_ship_display_name(selected_ship), True, MENU_WHITE)
        screen.blit(load_name, (loadout.x + 110, loadout.y + 37))
        class_name = "INTERCEPTOR" if selected_ship in ("starter", "falcon", "nova") else "COMBAT FRAME"
        class_s = small.render(f"MK-II  •  {class_name}", True, MENU_BLUE)
        screen.blit(class_s, (loadout.x + 110, loadout.y + 60))
        owned = ship_is_owned(player_id, selected_ship)
        state_txt = "EQUIPPED" if owned else "LOCKED"
        state_col = SUCCESS_GREEN if owned else ERROR_RED
        state_s = small.render(("✓ " if owned else "LOCKED  •  ") + state_txt, True, state_col)
        screen.blit(state_s, (loadout.x + 110, loadout.y + 81))

        # HULL FINISH
        finish = pygame.Rect(left.x + 12, loadout.bottom + 10, left.width - 24, 133)
        panel(finish, accent=SHIP_COLORS[color_name]["accent"], fill=(4, 12, 22), radius=10)
        panel_title(finish, "HULL FINISH", SHIP_COLORS[color_name]["accent"])
        color_names = list(SHIP_COLORS.keys())
        sw = (finish.width - 32) // 4
        sh = 42
        color_rects = {}
        for i, cname in enumerate(color_names):
            row, col = divmod(i, 4)
            r = pygame.Rect(finish.x + 7 + col * (sw + 5), finish.y + 30 + row * (sh + 7), sw, sh)
            color_rects[cname] = r
            pal = SHIP_COLORS[cname]
            is_sel = cname == color_name
            pygame.draw.rect(screen, (7, 17, 30), r, border_radius=8)
            pygame.draw.rect(screen, pal["accent"] if is_sel else (25, 47, 67), r, 2 if is_sel else 1, border_radius=8)
            swatch = pygame.Rect(r.x + 8, r.y + 8, 28, 26)
            pygame.draw.rect(screen, pal["dark"], swatch, border_radius=6)
            pygame.draw.rect(screen, pal["secondary"], swatch.inflate(-4, -4), border_radius=5)
            pygame.draw.line(screen, pal["primary"], (swatch.x + 7, swatch.bottom - 6), (swatch.right - 7, swatch.y + 7), 2)
            ct = small.render(cname, True, MENU_WHITE if is_sel else MUTED)
            screen.blit(ct, (r.x + 42, r.y + 12))

        # SAVE LOADOUT
        save_rect = pygame.Rect(left.x + 12, left.bottom - 46, left.width - 24, 35)
        draw_button(screen, save_rect, "SAVE LOADOUT", mouse_pos, tick, primary=True)

        # RIGHT / HANGAR
        panel_title(right, "COMBAT HANGAR")
        status = "OWNED" if owned else "LOCKED"
        status_col = SUCCESS_GREEN if owned else ERROR_RED
        slot_s = small.render(f"SHIP {index + 1:02d} / {len(catalog):02d}   •   {status}", True, status_col)
        screen.blit(slot_s, slot_s.get_rect(topright=(right.right - 14, right.y + 9)))

        ship_name = title_font.render(_ship_display_name(selected_ship), True, MENU_WHITE)
        screen.blit(ship_name, ship_name.get_rect(center=(right.centerx, right.y + 28)))
        subtitle = small.render("INTERCEPTOR / FRONTLINE COMBAT FRAME", True, MENU_BLUE)
        screen.blit(subtitle, subtitle.get_rect(center=(right.centerx, right.y + 49)))

        preview = pygame.Rect(right.x + 14, right.y + 68, right.width - 28, 292)
        pygame.draw.rect(screen, (1, 6, 12), preview, border_radius=12)
        pygame.draw.rect(screen, (18, 52, 81), preview, 1, border_radius=12)

        # Hangar grid and scan lines
        for gx in range(preview.x + 20, preview.right, 44):
            pygame.draw.line(screen, (5, 24, 40), (gx, preview.y + 10), (gx, preview.bottom - 10), 1)
        for gy in range(preview.y + 18, preview.bottom, 34):
            pygame.draw.line(screen, (5, 24, 40), (preview.x + 10, gy), (preview.right - 10, gy), 1)
        scan_y = preview.y + int((tick % 2600) / 2600 * preview.height)
        pygame.draw.line(screen, (12, 72, 110), (preview.x + 8, scan_y), (preview.right - 8, scan_y), 1)

        center = (preview.centerx, preview.centery + 7)
        ship_size = max(110, min(preview.width - 90, preview.height - 72))
        ship_img = load_ship_variant(selected_ship, color_name, ship_size)

        if ship_img is not None:
            bob = math.sin(tick / 390.0) * 5
            ship_center = (center[0], int(center[1] + bob))
            shadow = pygame.Surface((max(130, ship_size // 2), 30), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 140), shadow.get_rect())
            screen.blit(shadow, shadow.get_rect(center=(ship_center[0], preview.bottom - 30)))

            # Engine plume
            plume = pygame.Surface((260, 120), pygame.SRCALPHA)
            pulse = 0.85 + 0.15 * math.sin(tick / 85.0)
            for rr, aa in ((62, 16), (46, 24), (32, 42)):
                pygame.draw.ellipse(plume, (56, 174, 255, int(aa * pulse)), (130 - rr, 60 - rr // 3, rr * 2, rr))
            screen.blit(plume, plume.get_rect(center=(ship_center[0], preview.bottom - 60)), special_flags=pygame.BLEND_RGBA_ADD)

            rotated = pygame.transform.rotozoom(ship_img, rotation * 0.45, 1.0)
            screen.blit(rotated, rotated.get_rect(center=ship_center))
        else:
            # Future asset slot: intentionally clean and easy to replace with a PNG later.
            silhouette = pygame.Surface((170, 170), pygame.SRCALPHA)
            pygame.draw.polygon(
                silhouette,
                (24, 49, 70, 190),
                [(85, 12), (146, 124), (106, 112), (85, 148), (64, 112), (24, 124)],
            )
            pygame.draw.polygon(
                silhouette,
                (70, 119, 155, 150),
                [(85, 28), (128, 108), (95, 96), (85, 120), (75, 96), (42, 108)],
            )
            screen.blit(silhouette, silhouette.get_rect(center=center))

        if not owned:
            overlay = pygame.Surface(preview.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 86))
            screen.blit(overlay, preview.topleft)
            lock_label = big.render("LOCKED", True, ERROR_RED)
            screen.blit(lock_label, lock_label.get_rect(center=(preview.centerx, preview.centery - 13)))
            price = SHIP_CATALOG_PRICES.get(selected_ship, 5000)
            if ship_img is None:
                sublock = small.render("ADD SHIP PNG TO ACTIVATE THIS SLOT", True, MUTED)
            else:
                sublock = small.render(f"UNLOCK COST  {number(price)} COINS", True, MENU_WHITE)
            screen.blit(sublock, sublock.get_rect(center=(preview.centerx, preview.centery + 14)))

        # Controls
        prev_rect = pygame.Rect(preview.x + 14, preview.bottom + 10, 58, 34)
        next_rect = pygame.Rect(preview.right - 72, preview.bottom + 10, 58, 34)
        draw_button(screen, prev_rect, "<", mouse_pos, tick, primary=False)
        draw_button(screen, next_rect, ">", mouse_pos, tick, primary=False)
        drag_text = small.render("DRAG SHIP TO ROTATE", True, MUTED)
        screen.blit(drag_text, drag_text.get_rect(center=(preview.centerx, preview.bottom + 27)))

        # Ship stats
        stats_panel = pygame.Rect(right.x + 14, preview.bottom + 50, right.width - 28, 112)
        panel(stats_panel, accent=SHIP_COLORS[color_name]["accent"], fill=(4, 12, 22), radius=10)
        panel_title(stats_panel, "SHIP STATS", SHIP_COLORS[color_name]["accent"])
        stat_values = SHIP_STATS.get(selected_ship, (7, 7, 7))
        stat_labels = ("SPEED", "DAMAGE", "ARMOR")
        for i, label in enumerate(stat_labels):
            y = stats_panel.y + 32 + i * 23
            lab = small.render(label, True, MUTED)
            screen.blit(lab, (stats_panel.x + 11, y))
            bar = pygame.Rect(stats_panel.x + 72, y + 1, stats_panel.width - 92, 11)
            progress_bar(bar, stat_values[i] / 10.0, SHIP_COLORS[color_name]["accent"])
            val = small.render(f"{stat_values[i]}/10", True, MENU_WHITE)
            screen.blit(val, (bar.right + 7, y - 1))

        # combat status strip
        ready = pygame.Rect(right.x + 14, right.bottom - 43, right.width - 28, 31)
        pygame.draw.rect(screen, (3, 15, 23), ready, border_radius=8)
        ready_col = SUCCESS_GREEN if owned else ERROR_RED
        pygame.draw.rect(screen, ready_col, ready, 1, border_radius=8)
        ready_text = "EQUIPPED  •  YOUR SHIP WILL APPEAR IN COMBAT" if owned else "LOCKED  •  PREVIEW ONLY  •  ADD PNG / UNLOCK LATER"
        rs = small.render(ready_text, True, ready_col)
        screen.blit(rs, rs.get_rect(center=ready.center))

        if message and tick < message_until:
            note_col = SUCCESS_GREEN if "SAVED" in message or "READY" in message else ERROR_RED
            note = body.render(message, True, note_col)
            screen.blit(note, note.get_rect(center=(width // 2, height - 8)))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", player

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu", player
                if event.key == pygame.K_LEFT:
                    index = (index - 1) % len(catalog)
                    selected_ship = catalog[index]
                    try:
                        theme.sound_click()
                    except Exception:
                        pass
                elif event.key == pygame.K_RIGHT:
                    index = (index + 1) % len(catalog)
                    selected_ship = catalog[index]
                    try:
                        theme.sound_click()
                    except Exception:
                        pass
                elif event.key == pygame.K_RETURN:
                    save_current()

            elif event.type == pygame.MOUSEMOTION and drag_start is not None:
                rotation = (drag_rotation - (event.pos[0] - drag_start[0])) % 360

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                drag_start = None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                if back_rect.collidepoint(pos):
                    return "menu", player

                if save_rect.collidepoint(pos):
                    save_current()
                    continue

                if prev_rect.collidepoint(pos):
                    index = (index - 1) % len(catalog)
                    selected_ship = catalog[index]
                    try:
                        theme.sound_click()
                    except Exception:
                        pass
                    continue

                if next_rect.collidepoint(pos):
                    index = (index + 1) % len(catalog)
                    selected_ship = catalog[index]
                    try:
                        theme.sound_click()
                    except Exception:
                        pass
                    continue

                clicked_color = False
                for cname, r in color_rects.items():
                    if r.collidepoint(pos):
                        color_name = cname
                        clicked_color = True
                        try:
                            theme.sound_click()
                        except Exception:
                            pass
                        break
                if clicked_color:
                    continue

                if preview.collidepoint(pos):
                    drag_start = pos
                    drag_rotation = rotation

        pygame.display.flip()
        clock.tick(60)


show_profile = profile_screen
show_profile_settings = advanced_profile_screen
