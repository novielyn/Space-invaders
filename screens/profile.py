import os
import math
import time
import hashlib

import pygame

try:
    import tkinter as tk
    from tkinter import filedialog
    TK_AVAILABLE = True
except Exception:
    TK_AVAILABLE = False

try:
    from PIL import Image, ImageSequence
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

try:
    import database
except Exception:
    database = None

try:
    import economy
    from economy import get_owned_ships as eco_get_owned_ships
except Exception:
    economy = None
    eco_get_owned_ships = None

try:
    from managers.ui_sounds import ui_sounds
except Exception:
    ui_sounds = None

# Shared notebook-style helpers
from screens.login import (
    INK,
    INK_SOFT,
    ERROR,
    SUCCESS,
    INFO,
    OUTLINE,
    PAPER,
    HIGHLIGHT,
    TAB_PINK,
    TAB_ORANGE,
    TAB_YELLOW,
    TAB_PURPLE,
    TAB_BLUE,
    SIDE_PINK,
    hand_font,
    put_text,
    alpha_rect,
    draw_background,
    draw_tab,
    draw_notepad,
    draw_field,
)
from screens.menu import (
    book_layout,
    draw_book,
    polaroid_layout,
    draw_polaroid,
    draw_desc_box,
    draw_actions,
)

PROFILE_DIR = os.path.join("assets", "profiles")
os.makedirs(PROFILE_DIR, exist_ok=True)

GOLD_INK = (170, 110, 20)
GREEN_INK = (40, 130, 70)
BLUE_INK = (60, 100, 170)

# Legacy color constants (main.py and other screens still import these)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
GOLD = (255, 215, 0)
RED = (220, 60, 60)
GREEN = (60, 200, 100)
BLUE = (80, 140, 255)
CYAN = (0, 220, 255)

RANKS = (
    (30000, "MYTHIC IMMORTAL"),
    (15000, "MYTHIC"),
    (7000, "LEGEND"),
    (3500, "GRANDMASTER"),
    (1500, "MASTER"),
    (500, "ELITE"),
    (0, "ROOKIE"),
)

SHIP_DATA = [
    {"id": "starter", "name": "STARTER", "rank": "ROOKIE", "unlock_level": 1},
    {"id": "falcon", "name": "FALCON", "rank": "ELITE", "unlock_level": 5},
    {"id": "viper", "name": "VIPER", "rank": "MASTER", "unlock_level": 10},
    {"id": "wraith", "name": "WRAITH", "rank": "GRANDMASTER", "unlock_level": 20},
    {"id": "dragon", "name": "DRAGON", "rank": "MYTHIC", "unlock_level": 30},
]

SHIP_ORDER = tuple(s["id"] for s in SHIP_DATA)
SHIP_NAMES = {s["id"]: s["name"] for s in SHIP_DATA}
SHIP_UNLOCK_LEVELS = {s["id"]: s["unlock_level"] for s in SHIP_DATA}

SHIP_FILES = {
    sid: (
        sid + ".gif",
        sid + ".png",
        "ship_" + sid + ".png",
        sid + "_ship.png",
        "ship_" + sid + ".gif",
    )
    for sid in SHIP_ORDER
}

SHIP_ALIASES = {}
for _sid in SHIP_ORDER:
    for _alias in (_sid, _sid + " ship", _sid + "_ship", "ship_" + _sid):
        SHIP_ALIASES[_alias] = _sid

_SHIP_GIF_CACHE = {}
_SCALED_FRAME_CACHE = {}
_AVATAR_CACHE = {}


# ---------------------------------------------------------------
# Fonts / drawing helpers (kept for other screens that import them)
# ---------------------------------------------------------------
def font(size, bold=False):
    return hand_font(size, bold)


def get_font(name_or_size, size=None):
    value = name_or_size if size is None else size
    try:
        return font(int(value))
    except Exception:
        return font(14)


def text(surface, value, pos, fnt, color=INK):
    image = fnt.render(str(value), True, color)
    surface.blit(image, pos)
    return image.get_rect(topleft=pos)


def center_text(surface, value, center, fnt, color=INK):
    image = fnt.render(str(value), True, color)
    rect = image.get_rect(center=center)
    surface.blit(image, rect)
    return rect


def rounded_rect(surface, rect, color, radius=10, width=0):
    pygame.draw.rect(surface, color, rect, width, border_radius=radius)


def fit_text(fnt, value, width):
    value = str(value)
    if fnt.size(value)[0] <= width:
        return value
    while value:
        if fnt.size(value + "...")[0] <= width:
            return value + "..."
        value = value[:-1]
    return "..."


def draw_gradient_background(surface, top_color=(10, 2, 15), bottom_color=(2, 0, 5)):
    width, height = surface.get_size()
    grad = pygame.Surface((2, 2))
    grad.set_at((0, 0), top_color[:3])
    grad.set_at((1, 0), top_color[:3])
    grad.set_at((0, 1), bottom_color[:3])
    grad.set_at((1, 1), bottom_color[:3])
    surface.blit(pygame.transform.smoothscale(grad, (width, height)), (0, 0))


# ---------------------------------------------------------------
# Sounds
# ---------------------------------------------------------------
def play_hover():
    try:
        if ui_sounds and hasattr(ui_sounds, "update_hover"):
            ui_sounds.update_hover(True)
    except Exception:
        pass


def play_click():
    try:
        if ui_sounds:
            if hasattr(ui_sounds, "click"):
                ui_sounds.click()
                return
            if hasattr(ui_sounds, "play_click"):
                ui_sounds.play_click()
                return
    except Exception:
        pass
    try:
        path = os.path.join("assets", "sounds", "button_click.wav")
        if os.path.exists(path):
            sound = pygame.mixer.Sound(path)
            sound.set_volume(0.7)
            sound.play()
    except Exception:
        pass


# ---------------------------------------------------------------
# Player data helpers
# ---------------------------------------------------------------
def get_value(player, key, default=None):
    if player is None:
        return default
    if isinstance(player, dict):
        return player.get(key, default)
    return getattr(player, key, default)


def set_value(player, key, value):
    if player is None:
        return
    if isinstance(player, dict):
        player[key] = value
        return
    try:
        setattr(player, key, value)
    except Exception:
        pass


def get_username(player):
    value = (
        get_value(player, "username", None)
        or get_value(player, "name", None)
        or get_value(player, "user_name", None)
        or "Player"
    )
    return str(value)


def get_email(player):
    value = (
        get_value(player, "email", None)
        or get_value(player, "user_email", None)
        or "No email connected"
    )
    return str(value)


def _first_int(player, keys, fallback=0):
    for key in keys:
        try:
            return int(get_value(player, key, 0) or 0)
        except Exception:
            pass
    return fallback


def get_score(player):
    return _first_int(player, ("score", "current_score", "points"))


def get_high_score(player):
    return _first_int(
        player,
        ("high_score", "highest_score", "best_score"),
        get_score(player),
    )


def get_rank(player):
    score = max(get_high_score(player), get_score(player))
    for minimum, rank in RANKS:
        if score >= minimum:
            return rank
    return "ROOKIE"


def get_player_level(player):
    for key in ("level", "player_level", "user_level"):
        try:
            return max(1, int(get_value(player, key, None)))
        except Exception:
            pass

    score = max(get_high_score(player), get_score(player))
    for minimum, level in (
        (30000, 50), (15000, 40), (7000, 30),
        (3500, 20), (1500, 10), (500, 5),
    ):
        if score >= minimum:
            return level
    return 1


def safe_balance(player):
    if database:
        fn = getattr(database, "get_balance", None)
        if callable(fn):
            try:
                return int(fn(get_username(player)) or 0)
            except Exception:
                pass

    value = (
        get_value(player, "balance", None)
        or get_value(player, "coins", None)
        or get_value(player, "credits", None)
    )
    try:
        return int(value or 0)
    except Exception:
        return 0


def get_online_status(player):
    for key in ("online", "is_online", "session_active"):
        value = get_value(player, key, None)
        if value is not None:
            if isinstance(value, str):
                return value.strip().lower() in (
                    "online", "active", "true", "1", "connected",
                )
            return bool(value)
    return True


def get_game_loadout(player_data=None):
    if isinstance(player_data, dict):
        ship = (
            player_data.get("equipped_ship")
            or player_data.get("selected_ship")
            or player_data.get("ship")
            or "starter"
        )
        color = player_data.get("ship_color") or player_data.get("color") or "ICE"
        return (ship, color)
    return ("starter", "ICE")


def load_game_player_ship(player_data=None, size=96):
    ship_id = "starter"
    if isinstance(player_data, dict):
        ship_id = (
            player_data.get("equipped_ship")
            or player_data.get("selected_ship")
            or player_data.get("ship")
            or "starter"
        )
    ship_id = normalize_ship_id(ship_id) or "starter"
    img = load_ship_image(ship_id)
    if img:
        try:
            return pygame.transform.smoothscale(img, (size, size))
        except Exception:
            return img
    return None


# ---------------------------------------------------------------
# Ships
# ---------------------------------------------------------------
def normalize_ship_id(value):
    if isinstance(value, dict):
        value = (
            value.get("ship_id")
            or value.get("id")
            or value.get("ship")
            or value.get("ship_name")
            or value.get("name")
            or ""
        )
    if value is None:
        return ""
    return SHIP_ALIASES.get(str(value).strip().lower(), "")


def normalize_owned_ids(source):
    result = []

    if source is None:
        return result

    if isinstance(source, dict):
        for key in ("owned_ships", "ownedShips", "ships", "ship_ids", "items", "data"):
            if key in source:
                result.extend(normalize_owned_ids(source[key]))
        if not result:
            ship_id = normalize_ship_id(source)
            if ship_id:
                result.append(ship_id)
        return result

    if isinstance(source, (list, tuple, set)):
        for item in source:
            result.extend(normalize_owned_ids(item))
        return result

    ship_id = normalize_ship_id(source)
    if ship_id:
        result.append(ship_id)
    return result


def validate_ship_ownership(player, ship_id):
    """Ships unlock by level, so a ship above the player's level is never owned."""
    if ship_id == "starter":
        return True
    return get_player_level(player) >= SHIP_UNLOCK_LEVELS.get(ship_id, 999)


def get_shop_owned_ids(player):
    owned = []
    username = get_username(player)
    player_id = get_value(player, "id", None)
    names = ("get_owned_ships", "get_owned_ship_ids", "get_player_ships")

    if economy and eco_get_owned_ships:
        try:
            owned.extend(normalize_owned_ids(eco_get_owned_ships(username or player_id)))
        except Exception:
            pass

        if not owned:
            for name in names:
                fn = getattr(economy, name, None)
                if not callable(fn):
                    continue
                for value in (username, player_id):
                    if value is None or value == "":
                        continue
                    try:
                        owned.extend(normalize_owned_ids(fn(value)))
                        break
                    except Exception:
                        pass

    if database and not owned:
        for name in names:
            fn = getattr(database, name, None)
            if not callable(fn):
                continue
            for value in (username, player_id):
                if value is None or value == "":
                    continue
                try:
                    owned.extend(normalize_owned_ids(fn(value)))
                except Exception:
                    pass

    if not owned:
        for key in ("owned_ships", "ownedShips", "ships", "unlocked_ships"):
            owned.extend(normalize_owned_ids(get_value(player, key, None)))

    level = get_player_level(player)
    for ship_id, required in SHIP_UNLOCK_LEVELS.items():
        if level >= required:
            owned.append(ship_id)

    owned.append("starter")
    owned_set = set(owned)

    return [
        ship_id
        for ship_id in SHIP_ORDER
        if ship_id in owned_set and validate_ship_ownership(player, ship_id)
    ]


def safe_ships(player):
    ships = [
        {"id": ship_id, "name": SHIP_NAMES.get(ship_id, ship_id.upper()), "owned": True}
        for ship_id in get_shop_owned_ids(player)
    ]
    if not ships:
        ships.append({"id": "starter", "name": "STARTER", "owned": True})
    return ships


def load_image_safely(path):
    """Loads an image; GIF content hiding behind a .png name is parsed with PIL."""
    if not path or not os.path.isfile(path):
        return None
    try:
        is_gif = False
        if PIL_AVAILABLE:
            try:
                with Image.open(path) as img:
                    is_gif = img.format == "GIF"
            except Exception:
                pass
        if is_gif and PIL_AVAILABLE:
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


def get_ship_image_path(ship_id, prefer_gif=True):
    ship_id = normalize_ship_id(ship_id)
    if not ship_id:
        return None

    bases = [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ]
    folders = []
    for base in bases:
        folders.extend([
            os.path.join(base, "assets", "ships"),
            os.path.join(base, "assets", "images", "ships"),
            os.path.join(base, "assets", "images"),
            os.path.join(base, "ships"),
        ])

    filenames = list(SHIP_FILES.get(ship_id, ()))
    if prefer_gif:
        filenames.sort(key=lambda n: 0 if n.lower().endswith(".gif") else 1)

    for folder in folders:
        if not os.path.isdir(folder):
            continue
        for filename in filenames:
            path = os.path.join(folder, filename)
            if os.path.isfile(path):
                return path
    return None


def load_ship_image(ship_id):
    path = get_ship_image_path(ship_id, prefer_gif=False)
    if not path:
        return None
    try:
        return load_image_safely(path)
    except Exception:
        return None


def load_gif_frames(path):
    if not PIL_AVAILABLE:
        return None
    try:
        pil_image = Image.open(path)
        frames = []
        for frame in ImageSequence.Iterator(pil_image):
            rgba = frame.convert("RGBA")
            surface = pygame.image.fromstring(
                rgba.tobytes(), rgba.size, "RGBA"
            ).convert_alpha()
            duration = frame.info.get("duration", 100)
            if duration <= 0:
                duration = 100
            frames.append((surface, duration))
        return frames or None
    except Exception:
        return None


def get_ship_frames(ship_id):
    ship_id = normalize_ship_id(ship_id)
    if not ship_id:
        return None
    if ship_id in _SHIP_GIF_CACHE:
        return _SHIP_GIF_CACHE[ship_id]

    path = get_ship_image_path(ship_id, prefer_gif=PIL_AVAILABLE)
    if not path:
        return None

    if os.path.splitext(path)[1].lower() == ".gif" and PIL_AVAILABLE:
        frames = load_gif_frames(path)
        if frames:
            _SHIP_GIF_CACHE[ship_id] = frames
            return frames

    static_img = load_ship_image(ship_id)
    if static_img:
        frames = [(static_img, 100)]
        _SHIP_GIF_CACHE[ship_id] = frames
        return frames
    return None


def get_cached_scaled(frame_surf, width, height):
    key = (id(frame_surf), width, height)
    if key in _SCALED_FRAME_CACHE:
        return _SCALED_FRAME_CACHE[key]
    try:
        scaled = pygame.transform.smoothscale(frame_surf, (width, height))
    except Exception:
        scaled = pygame.transform.scale(frame_surf, (width, height))
    if len(_SCALED_FRAME_CACHE) > 300:
        _SCALED_FRAME_CACHE.clear()
    _SCALED_FRAME_CACHE[key] = scaled
    return scaled


def current_ship_frame(ship_id):
    frames = get_ship_frames(ship_id)
    if not frames:
        return None
    if len(frames) == 1:
        return frames[0][0]
    total = sum(f[1] for f in frames)
    if total <= 0:
        return frames[0][0]
    play_time = pygame.time.get_ticks() % total
    elapsed = 0
    for surface, duration in frames:
        elapsed += duration
        if play_time < elapsed:
            return surface
    return frames[0][0]


# ---------------------------------------------------------------
# Accounts, avatar, passwords, deletion
# ---------------------------------------------------------------
def get_connected_accounts(player):
    data = get_value(player, "connected_accounts", None)
    if isinstance(data, dict):
        return {k: bool(data.get(k, False)) for k in ("facebook", "google", "discord")}
    return {
        k: bool(get_value(player, k + "_connected", False))
        for k in ("facebook", "google", "discord")
    }


def save_connected_accounts(player, accounts):
    set_value(player, "connected_accounts", dict(accounts))
    for key in ("facebook", "google", "discord"):
        set_value(player, key + "_connected", bool(accounts.get(key)))

    if database:
        for name in (
            "update_connected_accounts",
            "save_connected_accounts",
            "set_connected_accounts",
        ):
            fn = getattr(database, name, None)
            if not callable(fn):
                continue
            try:
                fn(get_username(player), dict(accounts))
                break
            except Exception:
                pass


def get_profile_image(player, size=80):
    path = get_value(player, "profile_image", None)
    if not path or not os.path.exists(path):
        return None

    key = (path, size)
    if key in _AVATAR_CACHE:
        return _AVATAR_CACHE[key]

    try:
        image = load_image_safely(path)
        if image is None:
            return None
        image = pygame.transform.smoothscale(image, (size, size)).convert_alpha()
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (size // 2, size // 2), size // 2)
        image.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        _AVATAR_CACHE[key] = image
        return image
    except Exception:
        return None


def choose_profile_image(player):
    if not TK_AVAILABLE:
        return False

    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        path = filedialog.askopenfilename(
            title="Choose Profile Image",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.webp"),
                ("PNG Files", "*.png"),
                ("JPEG Files", "*.jpg *.jpeg"),
                ("All Files", "*.*"),
            ],
        )
        if not path:
            return False

        extension = os.path.splitext(path)[1].lower()
        if extension not in (".png", ".jpg", ".jpeg", ".webp"):
            extension = ".png"

        safe_name = "".join(
            c if c.isalnum() or c in "_-" else "_" for c in get_username(player)
        )
        save_path = os.path.join(PROFILE_DIR, safe_name + extension)

        image = load_image_safely(path)
        if image is None:
            return False

        image = pygame.transform.smoothscale(image, (256, 256))
        pygame.image.save(image, save_path)

        _AVATAR_CACHE.clear()
        set_value(player, "profile_image", save_path)

        if database:
            for name in ("update_profile_image", "set_profile_image", "save_profile_image"):
                fn = getattr(database, name, None)
                if not callable(fn):
                    continue
                try:
                    fn(get_username(player), save_path)
                    break
                except Exception:
                    pass
        return True

    except Exception:
        return False

    finally:
        try:
            if root:
                root.destroy()
        except Exception:
            pass


def get_stored_password(player):
    return (
        get_value(player, "password", None),
        get_value(player, "password_hash", None),
    )


def password_matches(player, supplied):
    plain, hashed = get_stored_password(player)

    if plain is not None:
        return str(plain) == supplied

    if hashed is not None:
        hashed = str(hashed)
        if len(hashed) == 64:
            return hashlib.sha256(supplied.encode()).hexdigest() == hashed
        return supplied == hashed

    return True


def format_password(player, new_password):
    _, hashed = get_stored_password(player)
    if hashed is not None and len(str(hashed)) == 64:
        return hashlib.sha256(new_password.encode()).hexdigest()
    return new_password


def persist_password(player, new_password):
    formatted = format_password(player, new_password)

    if get_value(player, "password_hash", None) is not None:
        set_value(player, "password_hash", formatted)
    else:
        set_value(player, "password", new_password)

    if database:
        for name in (
            "update_password",
            "update_player_password",
            "change_password",
            "set_password",
        ):
            fn = getattr(database, name, None)
            if not callable(fn):
                continue
            try:
                fn(get_username(player), formatted)
                break
            except Exception:
                try:
                    player_id = get_value(player, "id", None)
                    if player_id is not None:
                        fn(player_id, formatted)
                        break
                except Exception:
                    pass


def save_new_password(player, fields):
    current, new, confirm = fields

    if not password_matches(player, current):
        return False, "Current password is incorrect."
    if len(new) < 4:
        return False, "New password must be at least 4 characters."
    if new != confirm:
        return False, "Passwords do not match."
    if new == current:
        return False, "New password must be different."

    persist_password(player, new)
    return True, ""


def delete_account_action(player):
    if database:
        fn = getattr(database, "delete_player", None)
        if callable(fn):
            try:
                return fn(get_username(player)) is not False
            except Exception:
                return False

    set_value(player, "deleted", True)
    return True


def refresh_profile_player(player):
    """Refresh database player data when Profile opens."""
    if player is None or not database:
        return player

    username = get_username(player)
    if not username or username == "Player":
        return player

    for function_name in ("get_player", "get_player_by_username", "load_player", "get_user"):
        fn = getattr(database, function_name, None)
        if not callable(fn):
            continue

        try:
            fresh = fn(username)
        except Exception:
            continue

        if not fresh:
            continue

        if isinstance(player, dict) and isinstance(fresh, dict):
            old_local = dict(player)
            player.clear()
            player.update(fresh)

            for key in (
                "profile_image",
                "connected_accounts",
                "facebook_connected",
                "google_connected",
                "discord_connected",
                "online",
                "is_online",
                "session_active",
            ):
                if key in old_local and key not in player:
                    player[key] = old_local[key]

            # Never let a stale database read regress progress that was
            # just applied locally (e.g. right after Game Over).
            for key in (
                "score", "current_score", "points",
                "high_score", "highest_score", "best_score",
                "level", "player_level", "user_level",
            ):
                if key not in old_local:
                    continue
                try:
                    old_num = int(old_local[key])
                except Exception:
                    continue
                try:
                    new_num = int(player.get(key, 0))
                except Exception:
                    new_num = 0
                if old_num > new_num:
                    player[key] = old_num

            merged = normalize_owned_ids(old_local.get("owned_ships"))
            merged += normalize_owned_ids(player.get("owned_ships"))
            if merged:
                seen = []
                for ship_id in merged:
                    if ship_id not in seen:
                        seen.append(ship_id)
                player["owned_ships"] = seen

            return player

        return fresh

    return player


# ---------------------------------------------------------------
# Journal-style widgets
# ---------------------------------------------------------------
def tag_button(screen, rect, label, fnt, hovered, color=TAB_YELLOW):
    r = rect.copy()
    if hovered:
        r.y -= 2
    pygame.draw.rect(screen, (150, 130, 100), r.move(0, 3), border_radius=8)
    pygame.draw.rect(screen, color, r, border_radius=8)
    pygame.draw.rect(screen, OUTLINE, r, 2, border_radius=8)
    put_text(screen, fnt, label, INK, r.center, "center")


def form_dialog(screen, title, subtitle, labels, submit_label, action):
    """Journal-style popup. Returns "saved", "cancel" or "quit"."""
    snapshot = screen.copy()
    clock = pygame.time.Clock()

    heading_font = hand_font(30, True)
    body_font = hand_font(16)
    input_font = hand_font(22)
    label_font = hand_font(17)
    button_font = hand_font(21, True)
    error_font = hand_font(15, True)

    values = ["" for _ in labels]
    active = 0
    error = ""
    cursor_visible = True
    cursor_timer = time.time()

    def submit():
        nonlocal error
        ok, err = action(values)
        if ok:
            return True
        error = err
        return False

    while True:
        width, height = screen.get_size()
        mouse = pygame.mouse.get_pos()

        if time.time() - cursor_timer > 0.5:
            cursor_visible = not cursor_visible
            cursor_timer = time.time()

        screen.blit(snapshot, (0, 0))
        alpha_rect(screen, (0, 0, 0, 170), pygame.Rect(0, 0, width, height))

        card = pygame.Rect(0, 0, min(520, width - 60), min(height - 30, 190 + 76 * len(labels)))
        card.center = (width // 2, height // 2)
        pygame.draw.rect(screen, (60, 40, 36), card.move(6, 8), border_radius=10)
        pygame.draw.rect(screen, PAPER, card, border_radius=10)
        pygame.draw.rect(screen, OUTLINE, card, 3, border_radius=10)

        put_text(screen, heading_font, title, INK, (card.centerx, card.y + 42), "center")
        put_text(screen, body_font, subtitle, INK_SOFT, (card.centerx, card.y + 80), "center")

        boxes = []
        y = card.y + 134
        for i, label in enumerate(labels):
            box = pygame.Rect(card.x + 40, y, card.w - 80, 46)
            draw_field(screen, box, label, values[i], active == i, True,
                       input_font, label_font, cursor_visible, "\u2022 \u2022 \u2022 \u2022")
            boxes.append(box)
            y += 76

        if error:
            put_text(screen, error_font, error, ERROR, (card.centerx, y - 18), "center")

        submit_rect = pygame.Rect(card.centerx - 165, card.bottom - 68, 160, 44)
        cancel_rect = pygame.Rect(card.centerx + 5, card.bottom - 68, 160, 44)
        tag_button(screen, submit_rect, submit_label, button_font,
                   submit_rect.collidepoint(mouse), TAB_PINK)
        tag_button(screen, cancel_rect, "Cancel", button_font,
                   cancel_rect.collidepoint(mouse), TAB_YELLOW)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "cancel"

                if event.key == pygame.K_TAB and labels:
                    active = (active + 1) % len(labels)

                elif event.key == pygame.K_BACKSPACE and labels:
                    values[active] = values[active][:-1]

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if labels and active < len(labels) - 1:
                        active += 1
                    elif submit():
                        play_click()
                        return "saved"

                elif labels and event.unicode and event.unicode.isprintable():
                    if len(values[active]) < 64:
                        values[active] += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                for i, box in enumerate(boxes):
                    if box.collidepoint(pos):
                        active = i
                        play_click()

                if submit_rect.collidepoint(pos):
                    play_click()
                    if submit():
                        return "saved"
                elif cancel_rect.collidepoint(pos):
                    play_click()
                    return "cancel"

        pygame.display.flip()
        clock.tick(60)


def change_password_dialog(screen, player):
    return form_dialog(
        screen,
        "Change Password",
        "Update your account password",
        ["Current password", "New password", "Confirm password"],
        "Save",
        lambda values: save_new_password(player, values),
    )


def reset_password_dialog(screen, player):
    def action(values):
        if len(values[0]) < 4:
            return False, "Password must be at least 4 characters."
        persist_password(player, values[0])
        return True, ""

    return form_dialog(
        screen,
        "Reset Password",
        "Create a new password for your account",
        ["New password"],
        "Reset",
        action,
    )


def confirm_dialog(screen, title, message):
    result = form_dialog(screen, title, message, [], "Confirm", lambda values: (True, ""))
    return "confirm" if result == "saved" else result


# ---------------------------------------------------------------
# Drawing bits for the profile screen
# ---------------------------------------------------------------
def draw_avatar(screen, player, center, radius, initial_font):
    x, y = center
    image = get_profile_image(player, radius * 2)

    pygame.draw.circle(screen, (150, 130, 100), (x + 3, y + 4), radius + 3)

    if image:
        screen.blit(image, (x - radius, y - radius))
    else:
        pygame.draw.circle(screen, (240, 226, 196), (x, y), radius)
        put_text(screen, initial_font, get_username(player)[:1].upper(), INK, (x, y), "center")

    pygame.draw.circle(screen, OUTLINE, (x, y), radius + 2, 3)


def draw_account_icon(screen, key, center, fnt):
    x, y = center
    if key == "facebook":
        pygame.draw.circle(screen, (55, 95, 180), (x, y), 18)
        put_text(screen, fnt, "f", (255, 255, 255), (x + 1, y + 1), "center")
    elif key == "google":
        pygame.draw.circle(screen, (255, 255, 255), (x, y), 18)
        pygame.draw.circle(screen, OUTLINE, (x, y), 18, 2)
        put_text(screen, fnt, "G", (60, 100, 210), (x, y + 1), "center")
    else:
        rect = pygame.Rect(x - 18, y - 18, 36, 36)
        pygame.draw.rect(screen, (105, 80, 190), rect, border_radius=9)
        pygame.draw.circle(screen, (255, 255, 255), (x - 7, y - 2), 3)
        pygame.draw.circle(screen, (255, 255, 255), (x + 7, y - 2), 3)


def draw_ship_backdrop(size, tick, stars):
    pic = pygame.Surface(size)
    w, h = size
    for y in range(h):
        t = y / max(1, h)
        pygame.draw.line(
            pic,
            (int(18 + 40 * t), int(14 + 18 * t), int(48 + 60 * t)),
            (0, y), (w, y),
        )
    for i, (sx, sy, sr) in enumerate(stars):
        tw = 150 + int(90 * math.sin(tick * 0.05 + i))
        pygame.draw.circle(pic, (tw, tw, min(255, tw + 30)), (int(sx * w), int(sy * h)), sr)
    return pic


def draw_ship_into(pic, ship_id, tick):
    w, h = pic.get_size()
    frame = current_ship_frame(ship_id)
    bob = int(math.sin(tick * 0.05) * 4)

    if frame is not None and frame.get_width() > 0 and frame.get_height() > 0:
        pad = 12
        ratio = min(
            (w - pad * 2) / float(frame.get_width()),
            (h - pad * 2) / float(frame.get_height()),
        )
        sw = max(1, int(frame.get_width() * ratio))
        sh = max(1, int(frame.get_height() * ratio))
        scaled = get_cached_scaled(frame, sw, sh)
        pic.blit(scaled, scaled.get_rect(center=(w // 2, h // 2 + bob)))
        return

    # vector fallback when no image file exists
    cx, cy = w // 2, h // 2 + bob
    fw, fh = int(w * 0.42), int(h * 0.62)
    points = [
        (cx, cy - fh // 2), (cx + fw // 2, cy + fh // 3), (cx + fw // 5, cy + fh // 4),
        (cx, cy + fh // 2), (cx - fw // 5, cy + fh // 4), (cx - fw // 2, cy + fh // 3),
    ]
    pygame.draw.polygon(pic, (60, 50, 90), points)
    pygame.draw.polygon(pic, (230, 80, 90), points, 2)


def draw_arrow(screen, center, direction, enabled, hovered):
    cx, cy = center
    color = INK if (enabled and hovered) else (INK_SOFT if enabled else (200, 190, 170))
    for off in (-10, 8):
        if direction < 0:
            pts = [(cx + off, cy), (cx + off + 14, cy - 12), (cx + off + 14, cy + 12)]
        else:
            pts = [(cx + off, cy - 12), (cx + off + 14, cy), (cx + off, cy + 12)]
        pygame.draw.polygon(screen, color, pts, 2)


# ---------------------------------------------------------------
# Profile screen
# ---------------------------------------------------------------
def profile_screen(screen, clock, player):
    if player is None:
        return "login", None

    player = refresh_profile_player(player)

    set_value(player, "online", True)
    set_value(player, "is_online", True)
    set_value(player, "session_active", True)

    heading_font = hand_font(26, True)
    name_font = hand_font(24, True)
    body_font = hand_font(17)
    small_font = hand_font(15)
    row_font = hand_font(19)
    value_font = hand_font(21, True)
    caption_font = hand_font(26, True)
    big_font = hand_font(28, True)
    action_font = hand_font(40, True)
    tab_font = hand_font(15, True)
    tag_font = hand_font(16, True)
    icon_font = hand_font(22, True)
    avatar_font = hand_font(36, True)

    import random
    rng = random.Random(33)
    stars = [(rng.random(), rng.random(), rng.choice((1, 1, 2))) for _ in range(45)]

    tab_names = ("Profile", "Accounts", "Security")
    tab_colors = (TAB_PINK, TAB_ORANGE, TAB_YELLOW)
    tab = 0
    ship_index = 0

    notification = ""
    notification_color = SUCCESS
    notification_until = 0

    ships = safe_ships(player)
    balance = safe_balance(player)
    tick = 0
    previous_hover = None

    def refresh_cache():
        nonlocal ships, balance
        ships = safe_ships(player)
        balance = safe_balance(player)

    def notify(message, color, ms=1800):
        nonlocal notification, notification_color, notification_until
        notification = message
        notification_color = color
        notification_until = pygame.time.get_ticks() + ms

    while True:
        tick += 1

        # database/economy lookups are slow, so refresh about once a second
        if tick % 60 == 0:
            refresh_cache()

        width, height = screen.get_size()
        mouse = pygame.mouse.get_pos()

        # ---------- layout ----------
        book, lp, rp = book_layout(width, height)
        polaroid, picture, controls_center, desc_box = polaroid_layout(rp)

        x0 = lp.x + 34
        right_edge = lp.right - 36

        note_rect = pygame.Rect(book.right - 34, book.y + 18, 150, 230)
        side_back = pygame.Rect(book.x - 58, book.y + 60, 78, 30)

        top_tabs = [
            (pygame.Rect(lp.x + 30 + i * 90, book.y - 36, 82, 48), tab_colors[i], tab_names[i])
            for i in range(3)
        ]
        deco_tabs = [
            (pygame.Rect(rp.x + 30, book.y - 36, 72, 48), TAB_PURPLE),
            (pygame.Rect(rp.x + 108, book.y - 36, 72, 48), TAB_PURPLE),
            (pygame.Rect(rp.x + 186, book.y - 36, 72, 48), TAB_BLUE),
        ]

        return_rect = pygame.Rect(30, height - 78, 190, 56)
        done_rect = pygame.Rect(width - 220, height - 78, 190, 56)

        # Ship arrows sit on the left/right edges of the ship picture,
        # so they never cover the polaroid caption underneath.
        prev_rect = pygame.Rect(0, 0, 56, 40)
        prev_rect.center = (picture.left + 38, picture.centery)
        next_rect = pygame.Rect(0, 0, 56, 40)
        next_rect.center = (picture.right - 38, picture.centery)

        hits = []  # (rect, action)

        # ---------- draw ----------
        draw_background(screen, width, height, tick)
        draw_notepad(screen, note_rect, big_font, tab_font, False, footer=get_rank(player).title())

        draw_tab(screen, side_back, SIDE_PINK, "Menu", tab_font,
                 side_back.collidepoint(mouse), vertical=True)
        hits.append((side_back, "back"))

        for i, (r, col, label) in enumerate(top_tabs):
            draw_tab(screen, r, col, label, tab_font, i == tab or r.collidepoint(mouse))
            hits.append((r, ("tab", i)))
        for r, col in deco_tabs:
            draw_tab(screen, r, col, "", tab_font, r.collidepoint(mouse))

        draw_book(screen, book, lp, rp)

        titles = ("Pilot Profile", "Accounts", "Security")
        put_text(screen, heading_font, titles[tab], INK, (lp.centerx, lp.y + 28), "midtop")
        pygame.draw.line(screen, INK_SOFT,
                         (lp.centerx - 70, lp.y + 64), (lp.centerx + 70, lp.y + 64), 2)

        def rule(y):
            pygame.draw.line(screen, (205, 196, 176), (x0 - 6, y), (right_edge + 6, y), 1)

        if tab == 0:
            # identity
            avatar_center = (x0 + 40, lp.y + 122)
            draw_avatar(screen, player, avatar_center, 40, avatar_font)

            tx = x0 + 100
            max_w = right_edge - tx
            put_text(screen, name_font, fit_text(name_font, get_username(player), max_w),
                     INK, (tx, lp.y + 92))
            put_text(screen, small_font, fit_text(small_font, get_email(player), max_w),
                     INK_SOFT, (tx, lp.y + 124))
            put_text(screen, body_font, get_rank(player), GOLD_INK, (tx, lp.y + 148))

            upload_rect = pygame.Rect(x0, lp.y + 176, 104, 28)
            tag_button(screen, upload_rect, "Upload", tag_font,
                       upload_rect.collidepoint(mouse), TAB_YELLOW)
            hits.append((upload_rect, "upload"))

            stats = (
                ("Current score", f"{get_score(player):,}", INK),
                ("High score", f"{get_high_score(player):,}", GOLD_INK),
                ("Credits", f"{balance:,}", BLUE_INK),
                ("Level", str(get_player_level(player)), INK),
                ("Ships owned", str(len(ships)), GREEN_INK),
            )
            for i, (label, value, color) in enumerate(stats):
                line_y = lp.y + 250 + i * 34
                put_text(screen, row_font, label, INK_SOFT, (x0, line_y - 6), "bottomleft")
                put_text(screen, value_font, value, color, (right_edge, line_y - 6), "bottomright")
                rule(line_y)

        elif tab == 1:
            accounts = get_connected_accounts(player)
            for i, (key, name) in enumerate((("facebook", "Facebook"),
                                             ("google", "Google"),
                                             ("discord", "Discord"))):
                ry = lp.y + 96 + i * 76
                draw_account_icon(screen, key, (x0 + 20, ry + 30), icon_font)
                put_text(screen, hand_font(21, True), name, INK, (x0 + 56, ry + 16), "midleft")

                connected = accounts.get(key, False)
                put_text(screen, small_font,
                         "connected" if connected else "not connected",
                         GREEN_INK if connected else INK_SOFT, (x0 + 56, ry + 42), "midleft")

                btn = pygame.Rect(right_edge - 108, ry + 14, 108, 32)
                tag_button(screen, btn, "Disconnect" if connected else "Connect", tag_font,
                           btn.collidepoint(mouse), TAB_PINK if connected else TAB_BLUE)
                hits.append((btn, ("account", key)))
                rule(ry + 66)

        else:
            online = get_online_status(player)
            privacy = str(get_value(player, "privacy",
                                    get_value(player, "account_privacy", "PRIVATE"))).title()
            info = (
                ("Account status", "Online" if online else "Offline",
                 GREEN_INK if online else INK_SOFT),
                ("Session", "Active", BLUE_INK),
                ("Profile visibility", privacy, GOLD_INK),
            )
            for i, (label, value, color) in enumerate(info):
                line_y = lp.y + 134 + i * 34
                put_text(screen, row_font, label, INK_SOFT, (x0, line_y - 6), "bottomleft")
                put_text(screen, value_font, value, color, (right_edge, line_y - 6), "bottomright")
                rule(line_y)

            for i, (label, action, color) in enumerate((
                ("Change password", "change", TAB_YELLOW),
                ("Reset password", "reset", TAB_ORANGE),
                ("Delete account", "delete", TAB_PINK),
            )):
                btn = pygame.Rect(x0, lp.y + 250 + i * 50, right_edge - x0, 40)
                tag_button(screen, btn, label, hand_font(19, True),
                           btn.collidepoint(mouse), color)
                hits.append((btn, action))

        # right page: ship viewer
        ship_index = max(0, min(ship_index, len(ships) - 1))
        ship = ships[ship_index]
        ship_id = ship["id"]
        ship_name = ship.get("name") or SHIP_NAMES.get(ship_id, ship_id.upper())

        pic = draw_ship_backdrop(picture.size, tick, stars)
        draw_ship_into(pic, ship_id, tick)
        draw_polaroid(screen, polaroid, picture, pic, ship_name.title(), caption_font)

        multi = len(ships) > 1
        draw_arrow(screen, prev_rect.center, -1, multi, prev_rect.collidepoint(mouse))
        draw_arrow(screen, next_rect.center, 1, multi, next_rect.collidepoint(mouse))
        if multi:
            hits.append((prev_rect, "ship_prev"))
            hits.append((next_rect, "ship_next"))

        draw_desc_box(screen, desc_box)
        put_text(screen, body_font, f"Owned ship {ship_index + 1} of {len(ships)}", INK,
                 (desc_box.centerx, desc_box.centery - 4), "midbottom")
        put_text(screen, small_font,
                 f"Unlocks at level {SHIP_UNLOCK_LEVELS.get(ship_id, 1)}", INK_SOFT,
                 (desc_box.centerx, desc_box.centery + 2), "midtop")

        draw_actions(screen, action_font, return_rect, done_rect, mouse)
        hits.append((return_rect, "back"))
        hits.append((done_rect, "back"))

        # toast
        if notification and pygame.time.get_ticks() < notification_until:
            img = body_font.render(notification, True, INK)
            toast = pygame.Rect(0, 0, img.get_width() + 40, 40)
            toast.center = (width // 2, height - 40)
            pygame.draw.rect(screen, (60, 40, 36), toast.move(3, 4), border_radius=8)
            pygame.draw.rect(screen, PAPER, toast, border_radius=8)
            pygame.draw.rect(screen, notification_color, toast, 3, border_radius=8)
            screen.blit(img, img.get_rect(center=toast.center))

        # hover sound when the hovered control changes
        hover_key = next((str(a) for r, a in hits if r.collidepoint(mouse)), None)
        if hover_key is not None and hover_key != previous_hover:
            play_hover()
        previous_hover = hover_key

        pygame.display.flip()

        # ---------- events ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                set_value(player, "session_active", False)
                return "quit", player

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    play_click()
                    return "menu", player
                elif event.key in (pygame.K_LEFT, pygame.K_a) and len(ships) > 1:
                    ship_index = (ship_index - 1) % len(ships)
                elif event.key in (pygame.K_RIGHT, pygame.K_d) and len(ships) > 1:
                    ship_index = (ship_index + 1) % len(ships)
                elif event.key == pygame.K_TAB:
                    tab = (tab + 1) % 3

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = next((a for r, a in hits if r.collidepoint(event.pos)), None)
                if action is None:
                    continue

                play_click()

                if action == "back":
                    return "menu", player

                elif isinstance(action, tuple) and action[0] == "tab":
                    tab = action[1]

                elif action == "ship_prev":
                    ship_index = (ship_index - 1) % len(ships)

                elif action == "ship_next":
                    ship_index = (ship_index + 1) % len(ships)

                elif action == "upload":
                    if choose_profile_image(player):
                        notify("Profile image updated.", SUCCESS)
                    else:
                        notify("Profile image was not changed.", INK_SOFT)

                elif isinstance(action, tuple) and action[0] == "account":
                    key = action[1]
                    accounts = get_connected_accounts(player)
                    accounts[key] = not accounts[key]
                    save_connected_accounts(player, accounts)
                    notify(key.title() + (" connected." if accounts[key] else " disconnected."),
                           SUCCESS if accounts[key] else INK_SOFT, 1500)

                elif action == "change":
                    result = change_password_dialog(screen, player)
                    if result == "quit":
                        return "quit", player
                    if result == "saved":
                        notify("Password changed successfully.", SUCCESS)

                elif action == "reset":
                    result = reset_password_dialog(screen, player)
                    if result == "quit":
                        return "quit", player
                    if result == "saved":
                        notify("Password reset successfully.", SUCCESS)

                elif action == "delete":
                    result = confirm_dialog(
                        screen,
                        "Delete Account?",
                        "This action cannot be easily undone.",
                    )
                    if result == "quit":
                        return "quit", player
                    if result == "confirm":
                        if delete_account_action(player):
                            return "login", None
                        notify("Unable to delete account.", ERROR, 2000)

                break  # hits are stale after any action

        clock.tick(60)