import os
import math
import json
import random

import pygame

try:
    from PIL import Image, ImageSequence
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

try:
    from managers.ui_sounds import ui_sounds
except Exception:
    ui_sounds = None

try:
    import database
except Exception:
    database = None

# Shared notebook-style helpers
from screens.login import (
    INK,
    INK_SOFT,
    ERROR,
    SUCCESS,
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
    draw_ruled_lines,
    draw_space_picture,
)
from screens.menu import (
    book_layout,
    draw_book,
    polaroid_layout,
    draw_polaroid,
    draw_desc_box,
    draw_actions,
    fit_text,
    wrap_text,
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
SHIP_DIR = os.path.join(ASSET_DIR, "ships")
IMAGE_DIR = os.path.join(ASSET_DIR, "images")
LOADOUT_PATH = os.path.join(BASE_DIR, "ship_loadout.json")

# Bright colors are used for the glow inside the dark polaroid picture.
WHITE = (245, 248, 255)
CYAN = (0, 220, 255)
GREEN = (70, 255, 145)
RED = (255, 24, 52)
GOLD = (255, 210, 90)
PURPLE = (180, 90, 255)

GOLD_INK = (170, 110, 20)
GREEN_INK = (40, 130, 70)

FONT_CACHE = {}
SHIP_ANIM_CACHE = {}
_SCALED_CACHE = {}

SHIP_DATA = [
    {
        "id": "starter", "name": "STARTER", "rank": "ROOKIE",
        "power": 35, "armor": 40, "speed": 55, "fire_rate": 45, "shield": 30,
        "unlock_level": 1, "ship_class": "TRAINER CLASS",
        "description": "Reliable starter craft for new pilots.",
        "special": "Balanced", "color": CYAN,
        "files": ["starter.png", "ship_starter.png", "starter_ship.png"],
    },
    {
        "id": "falcon", "name": "FALCON", "rank": "ELITE",
        "power": 55, "armor": 45, "speed": 85, "fire_rate": 75, "shield": 40,
        "unlock_level": 5, "ship_class": "LIGHT INTERCEPTOR",
        "description": "Fast interceptor built for aggressive pilots.",
        "special": "Rapid Fire", "color": RED,
        "files": ["falcon.png", "falcon.gif", "ship_falcon.png", "falcon_ship.png"],
    },
    {
        "id": "viper", "name": "VIPER", "rank": "MASTER",
        "power": 75, "armor": 60, "speed": 70, "fire_rate": 80, "shield": 65,
        "unlock_level": 10, "ship_class": "ASSAULT FIGHTER",
        "description": "Heavy assault fighter with strong offensive power.",
        "special": "Poison Strike", "color": GREEN,
        "files": ["viper.png", "viper.gif", "ship_viper.png", "viper_ship.png"],
    },
    {
        "id": "wraith", "name": "WRAITH", "rank": "GRANDMASTER",
        "power": 85, "armor": 90, "speed": 50, "fire_rate": 65, "shield": 95,
        "unlock_level": 20, "ship_class": "HEAVY WARSHIP",
        "description": "Armored warship designed to survive intense battles.",
        "special": "Energy Shield", "color": PURPLE,
        "files": ["wraith.png", "wraith.gif", "ship_wraith.png", "wraith_ship.png"],
    },
    {
        "id": "dragon", "name": "DRAGON", "rank": "MYTHIC",
        "power": 100, "armor": 95, "speed": 95, "fire_rate": 100, "shield": 98,
        "unlock_level": 30, "ship_class": "LEGENDARY FLAGSHIP",
        "description": "Mythic flagship built for the strongest pilots.",
        "special": "Dragon Blast", "color": GOLD,
        "files": ["dragon.png", "dragon.gif", "ship_dragon.png", "ship_dragon.gif"],
    },
]

# Ink-friendly colors for the stat bars on paper.
STAT_COLORS = {
    "power": (200, 60, 70),
    "armor": (50, 150, 180),
    "speed": (60, 150, 90),
    "fire_rate": (130, 80, 190),
    "shield": (200, 150, 40),
}

STAT_LABELS = {
    "power": "Power",
    "armor": "Armor",
    "speed": "Speed",
    "fire_rate": "Fire rate",
    "shield": "Shield",
}

STAT_ORDER = ("power", "armor", "speed", "fire_rate", "shield")


# ---------------------------------------------------------------
# Fonts / small helpers (kept for other screens that import them)
# ---------------------------------------------------------------
def font(size, bold=False):
    return hand_font(size, bold)


def draw_text(surface, text, fnt, color, x, y, align="left"):
    image = fnt.render(str(text), True, color)
    rect = image.get_rect()
    if align == "center":
        rect.center = (int(x), int(y))
    elif align == "right":
        rect.midright = (int(x), int(y))
    else:
        rect.midleft = (int(x), int(y))
    surface.blit(image, rect)
    return rect


def get_value(player, *keys, default=0):
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


def format_number(value):
    return f"{safe_int(value):,}"


# ---------------------------------------------------------------
# Sounds
# ---------------------------------------------------------------
def play_hover():
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


def play_click():
    if ui_sounds:
        try:
            ui_sounds.click()
        except Exception:
            pass


def play_back():
    if ui_sounds is None:
        return
    try:
        ui_sounds.back()
        return
    except Exception:
        pass
    try:
        ui_sounds.click()
    except Exception:
        pass


def play_success():
    if ui_sounds:
        try:
            ui_sounds.success()
            return
        except Exception:
            pass
    play_click()


def play_error():
    if ui_sounds:
        try:
            ui_sounds.error()
        except Exception:
            pass


# ---------------------------------------------------------------
# Ship images
# ---------------------------------------------------------------
def find_asset(names):
    for folder in (SHIP_DIR, IMAGE_DIR, ASSET_DIR):
        if not os.path.isdir(folder):
            continue
        for name in names:
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                return path
    return None


def _load_gif_frames(path):
    if not PIL_AVAILABLE:
        return None, None
    try:
        image = Image.open(path)
        frames = []
        durations = []
        for frame in ImageSequence.Iterator(image):
            rgba = frame.convert("RGBA")
            surface = pygame.image.fromstring(
                rgba.tobytes(), rgba.size, "RGBA"
            ).convert_alpha()
            frames.append(surface)
            durations.append(max(0.02, frame.info.get("duration", 90) / 1000.0))
        if not frames:
            return None, None
        return frames, durations
    except Exception:
        return None, None


def load_ship_animation(ship_id):
    if ship_id in SHIP_ANIM_CACHE:
        return SHIP_ANIM_CACHE[ship_id]

    data = next((s for s in SHIP_DATA if s["id"] == ship_id), None)
    result = {"frames": None, "durations": None, "total": 0.0, "static": None}

    if data:
        gif_names = [n for n in data["files"] if n.lower().endswith(".gif")]
        png_names = [n for n in data["files"] if not n.lower().endswith(".gif")]

        gif_path = find_asset(gif_names) if gif_names else None
        if gif_path:
            frames, durations = _load_gif_frames(gif_path)
            if frames:
                result["frames"] = frames
                result["durations"] = durations
                result["total"] = sum(durations)

        if result["frames"] is None:
            static_path = find_asset(png_names) if png_names else find_asset(data["files"])
            if static_path:
                try:
                    result["static"] = pygame.image.load(static_path).convert_alpha()
                except Exception:
                    result["static"] = None

    SHIP_ANIM_CACHE[ship_id] = result
    return result


def get_current_frame(ship_id, time_value):
    anim = load_ship_animation(ship_id)

    if anim["frames"]:
        total = anim["total"]
        t = time_value % total if total > 0 else 0.0
        elapsed = 0.0
        for frame, duration in zip(anim["frames"], anim["durations"]):
            elapsed += duration
            if t < elapsed:
                return frame
        return anim["frames"][-1]

    return anim["static"]


def get_cached_scaled(frame, width, height):
    key = (id(frame), width, height)
    if key in _SCALED_CACHE:
        return _SCALED_CACHE[key]
    try:
        scaled = pygame.transform.smoothscale(frame, (width, height))
    except Exception:
        scaled = pygame.transform.scale(frame, (width, height))
    if len(_SCALED_CACHE) > 300:
        _SCALED_CACHE.clear()
    _SCALED_CACHE[key] = scaled
    return scaled


# ---------------------------------------------------------------
# Player / ship data
# ---------------------------------------------------------------
def player_id(player):
    return get_value(player, "id", "player_id", "user_id", default=None)


def player_score(player):
    return safe_int(get_value(player, "score", "high_score", "total_score", default=0))


def normalize_ship_id(value):
    if isinstance(value, dict):
        value = value.get("ship_id", value.get("id", value.get("name", "")))

    text = str(value or "").strip().lower()

    aliases = {}
    for ship in SHIP_DATA:
        sid = ship["id"]
        for alias in (sid, sid + " ship", sid + "_ship", "ship_" + sid):
            aliases[alias] = sid

    return aliases.get(text, text)


def player_rank(score):
    score = safe_int(score)
    for minimum, name in (
        (30000, "MYTHIC IMMORTAL"),
        (15000, "MYTHIC"),
        (7000, "LEGEND"),
        (3500, "GRANDMASTER"),
        (1500, "MASTER"),
        (500, "ELITE"),
    ):
        if score >= minimum:
            return name
    return "ROOKIE"


def rank_order(rank):
    ranks = ["ROOKIE", "ELITE", "MASTER", "GRANDMASTER", "LEGEND", "MYTHIC", "MYTHIC IMMORTAL"]
    try:
        return ranks.index(rank)
    except ValueError:
        return 0


def player_level(player):
    value = get_value(
        player, "level", "player_level", "user_level", "current_level", default=None
    )
    if value is not None:
        return max(1, safe_int(value, 1))

    # Same score -> level fallback as the Profile screen, so both agree.
    score = player_score(player)
    for minimum, level in (
        (30000, 50), (15000, 40), (7000, 30),
        (3500, 20), (1500, 10), (500, 5),
    ):
        if score >= minimum:
            return level
    return 1


def player_username(player):
    return get_value(player, "username", "user_name", "account_name", default=None)


def _call_database_function(name, player, ship_id=None):
    if not database:
        return None

    fn = getattr(database, name, None)
    if not fn:
        return None

    candidates = []
    pid = player_id(player)
    username = player_username(player)

    if pid is not None:
        candidates.append(pid)
    if username and username != pid:
        candidates.append(username)

    for value in candidates:
        try:
            if ship_id is None:
                return fn(value)
            return fn(value, ship_id)
        except Exception:
            continue

    return None


def get_database_owned_ids(player):
    result = _call_database_function("get_owned_ships", player)
    if result is None:
        return set()

    if isinstance(result, dict):
        result = result.get("ships", result.get("owned_ships", result.get("data", [])))

    if not isinstance(result, (list, tuple, set)):
        result = [result]

    owned = set()
    valid_ids = {ship["id"] for ship in SHIP_DATA}

    for item in result:
        if isinstance(item, dict):
            value = item.get(
                "ship_id",
                item.get("id", item.get("ship_name", item.get("name", ""))),
            )
        else:
            value = item

        ship_id = normalize_ship_id(value)
        if ship_id in valid_ids:
            owned.add(ship_id)

    return owned


def save_owned_ship(player, ship_id):
    if not isinstance(player, dict):
        return False

    ship_id = normalize_ship_id(ship_id)
    owned = player.setdefault("owned_ships", [])

    if ship_id not in [normalize_ship_id(v) for v in owned]:
        owned.append(ship_id)

    if database:
        for fn_name in ("buy_ship", "add_owned_ship", "save_owned_ship"):
            result = _call_database_function(fn_name, player, ship_id)
            if result is not None and result is not False:
                break

    return True


def get_owned_ids(player):
    level = player_level(player)
    owned = get_database_owned_ids(player)

    local_owned = get_value(player, "owned_ships", "ownedShips", "ships", default=[])
    if isinstance(local_owned, dict):
        local_owned = list(local_owned.keys())

    if isinstance(local_owned, (list, tuple, set)):
        for value in local_owned:
            ship_id = normalize_ship_id(value)
            if ship_id:
                owned.add(ship_id)

    owned.add("starter")

    for ship in SHIP_DATA:
        if level >= ship["unlock_level"]:
            owned.add(ship["id"])

    ordered = [ship["id"] for ship in SHIP_DATA if ship["id"] in owned]

    if isinstance(player, dict):
        player["owned_ships"] = ordered

    return ordered


def can_unlock(ship, player):
    return player_level(player) >= ship["unlock_level"]


def get_unlocked_ids(player):
    return [ship["id"] for ship in SHIP_DATA if can_unlock(ship, player)]


def load_saved_equipped_ship(player):
    pid = player_id(player)
    keys = []
    if pid is not None:
        keys.append(str(pid))
    keys.append("local")

    try:
        if not os.path.isfile(LOADOUT_PATH):
            return None

        with open(LOADOUT_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return None

        for key in keys:
            saved = data.get(key)
            if not isinstance(saved, dict):
                continue

            for field in (
                "equipped_ship", "selected_ship", "current_ship",
                "active_ship", "ship", "ship_id",
            ):
                value = normalize_ship_id(saved.get(field, ""))
                if value:
                    return value
    except Exception:
        pass

    return None


def equip_ship(player, ship_id):
    ship_id = normalize_ship_id(ship_id)
    pid = player_id(player)

    if isinstance(player, dict):
        for field in (
            "equipped_ship", "selected_ship", "current_ship", "active_ship", "ship",
        ):
            player[field] = ship_id

    saved = False

    try:
        data = {}
        if os.path.isfile(LOADOUT_PATH):
            try:
                with open(LOADOUT_PATH, "r", encoding="utf-8") as file:
                    loaded = json.load(file)
                if isinstance(loaded, dict):
                    data = loaded
            except Exception:
                data = {}

        key = str(pid) if pid is not None else "local"
        data[key] = {
            "equipped_ship": ship_id,
            "selected_ship": ship_id,
            "current_ship": ship_id,
            "active_ship": ship_id,
            "ship": ship_id,
            "ship_id": ship_id,
        }

        with open(LOADOUT_PATH, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        saved = True
    except Exception:
        pass

    if pid is not None and database:
        for name in (
            "equip_ship", "set_equipped_ship", "set_player_ship",
            "set_active_ship", "set_selected_ship",
        ):
            fn = getattr(database, name, None)
            if not callable(fn):
                continue
            try:
                if fn(pid, ship_id) is not False:
                    saved = True
                    break
            except Exception:
                pass

    return saved or isinstance(player, dict)


def get_equipped(player, unlocked_ids):
    value = normalize_ship_id(
        get_value(
            player, "equipped_ship", "selected_ship", "current_ship",
            "active_ship", "ship", "ship_id", default=None,
        )
    )

    saved_value = load_saved_equipped_ship(player)
    if saved_value:
        value = saved_value
        if isinstance(player, dict):
            for field in (
                "equipped_ship", "selected_ship", "current_ship",
                "active_ship", "ship", "ship_id",
            ):
                player[field] = value

    # A ship above the player's level can never be equipped.
    if value and value in unlocked_ids:
        return value

    return "starter"


# ---------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------
def draw_ship_fallback(surface, center, size, accent, time_value=0.0):
    cx, cy = center
    cy += math.sin(time_value * 1.6) * (size * 0.05)

    body = [
        (cx, cy - size // 2), (cx + size // 7, cy - size // 6),
        (cx + size // 2, cy + size // 3), (cx + size // 6, cy + size // 4),
        (cx, cy + size // 8), (cx - size // 6, cy + size // 4),
        (cx - size // 2, cy + size // 3), (cx - size // 7, cy - size // 6),
    ]
    pygame.draw.polygon(surface, (170, 190, 210), body)
    pygame.draw.polygon(surface, WHITE, body, 2)

    cockpit = [
        (cx, cy - size // 3), (cx + size // 8, cy),
        (cx, cy + size // 6), (cx - size // 8, cy),
    ]
    pygame.draw.polygon(surface, accent, cockpit)
    pygame.draw.polygon(surface, (210, 245, 255), cockpit, 2)

    flame_y = cy + size // 3
    flicker = 1.0 + math.sin(time_value * 12) * 0.15
    pygame.draw.polygon(
        surface, CYAN,
        [
            (cx - size // 10, flame_y),
            (cx, flame_y + (size // 4) * flicker),
            (cx + size // 10, flame_y),
        ],
    )


def draw_ship_into(pic, ship, time_value, owned):
    """Draws the animated ship on top of the polaroid backdrop."""
    w, h = pic.get_size()
    cx, cy = w // 2, h // 2

    # soft colored glow behind the ship
    glow = pygame.Surface((w, h), pygame.SRCALPHA)
    pulse = (math.sin(time_value * 2.2) + 1) * 0.5
    radius = int(min(w, h) * 0.42)
    pygame.draw.circle(glow, (*ship["color"], 26 + int(pulse * 14)), (cx, cy), radius)
    pygame.draw.circle(glow, (*ship["color"], 20), (cx, cy), int(radius * 0.7))
    pic.blit(glow, (0, 0))

    frame = get_current_frame(ship["id"], time_value)
    bob = int(math.sin(time_value * 2.4) * 4)

    if frame is not None and frame.get_width() > 0 and frame.get_height() > 0:
        pad = 14
        ratio = min(
            (w - pad * 2) / float(frame.get_width()),
            (h - pad * 2) / float(frame.get_height()),
        )
        sw = max(1, int(frame.get_width() * ratio))
        sh = max(1, int(frame.get_height() * ratio))
        scaled = get_cached_scaled(frame, sw, sh)
        pic.blit(scaled, scaled.get_rect(center=(cx, cy + bob)))
    else:
        draw_ship_fallback(pic, (cx, cy), int(h * 0.68), ship["color"], time_value)

    if not owned:
        alpha_rect(pic, (0, 0, 0, 140), pygame.Rect(0, 0, w, h))
        put_text(pic, hand_font(30, True), "LOCKED", (255, 110, 110), (cx, cy - 12), "center")
        put_text(pic, hand_font(20, True), f"Level {ship['unlock_level']}",
                 (235, 225, 210), (cx, cy + 20), "center")


def draw_arrow(screen, center, direction, enabled, hovered):
    cx, cy = center
    color = INK if (enabled and hovered) else (INK_SOFT if enabled else (200, 190, 170))
    for off in (-10, 8):
        if direction < 0:
            pts = [(cx + off, cy), (cx + off + 14, cy - 12), (cx + off + 14, cy + 12)]
        else:
            pts = [(cx + off, cy - 12), (cx + off + 14, cy), (cx + off, cy + 12)]
        pygame.draw.polygon(screen, color, pts, 2)


def draw_stat_bar(screen, x, y, width, label, value, color, label_font, value_font):
    put_text(screen, label_font, label, INK_SOFT, (x, y), "midleft")

    bar = pygame.Rect(x + 92, y - 6, max(40, width - 92 - 40), 12)
    pygame.draw.rect(screen, (232, 224, 204), bar, border_radius=6)

    fill_w = int(bar.w * max(0, min(100, value)) / 100)
    if fill_w > 0:
        pygame.draw.rect(screen, color, pygame.Rect(bar.x, bar.y, fill_w, bar.h), border_radius=6)
    pygame.draw.rect(screen, OUTLINE, bar, 2, border_radius=6)

    put_text(screen, value_font, str(value), INK, (x + width, y), "midright")


# ---------------------------------------------------------------
# Shop screen
# ---------------------------------------------------------------
def shop_screen(screen, clock, player=None):
    """Journal-style ship shop. Returns "back" or "quit"."""
    if player is None:
        player = {}

    heading_font = hand_font(26, True)
    item_font = hand_font(22, True)
    body_font = hand_font(17)
    small_font = hand_font(15)
    small_bold = hand_font(15, True)
    stat_font = hand_font(16)
    stat_value_font = hand_font(16, True)
    caption_font = hand_font(26, True)
    big_font = hand_font(28, True)
    action_font = hand_font(40, True)
    tab_font = hand_font(15, True)

    rng = random.Random(77)
    stars = [(rng.random(), rng.random(), rng.choice((1, 1, 2))) for _ in range(45)]

    existing_owned = set(get_database_owned_ids(player))
    local_owned = get_value(player, "owned_ships", "ownedShips", "ships", default=[])
    if isinstance(local_owned, (list, tuple, set)):
        existing_owned.update(normalize_ship_id(v) for v in local_owned)
    existing_owned.add("starter")

    owned_ids = []
    level = 1
    equipped_id = "starter"

    def refresh_state():
        """Database lookups are slow, so this only runs about once a second."""
        nonlocal owned_ids, level, equipped_id
        level = player_level(player)
        for ship_id in get_unlocked_ids(player):
            if ship_id not in existing_owned:
                save_owned_ship(player, ship_id)
                existing_owned.add(ship_id)
        owned_ids = get_owned_ids(player)
        equipped_id = get_equipped(player, get_unlocked_ids(player))

    refresh_state()

    ids = [s["id"] for s in SHIP_DATA]
    viewed = ids.index(equipped_id) if equipped_id in ids else 0

    notification = ""
    notification_color = SUCCESS
    notification_until = 0

    time_value = 0.0
    tick = 0
    previous_hover = None

    def notify(message, color, ms=1800):
        nonlocal notification, notification_color, notification_until
        notification = message
        notification_color = color
        notification_until = pygame.time.get_ticks() + ms

    def move(delta):
        nonlocal viewed
        viewed = (viewed + delta) % len(SHIP_DATA)
        play_hover()

    def try_equip():
        nonlocal equipped_id
        ship = SHIP_DATA[viewed]

        if ship["id"] not in owned_ids:
            play_error()
            notify(f"Requires level {ship['unlock_level']}.", ERROR, 2000)
            return

        if ship["id"] == equipped_id:
            notify(f"{ship['name'].title()} is already equipped.", INK_SOFT, 1400)
            return

        if equip_ship(player, ship["id"]):
            equipped_id = ship["id"]
            play_success()
            notify(f"{ship['name'].title()} equipped.", SUCCESS)
        else:
            play_error()
            notify("Could not equip ship.", ERROR, 2000)

    while True:
        dt = clock.tick(60) / 1000.0
        time_value += dt
        tick += 1

        if tick % 60 == 0:
            refresh_state()

        width, height = screen.get_size()
        mouse = pygame.mouse.get_pos()

        ship = SHIP_DATA[viewed]
        ship_owned = ship["id"] in owned_ids
        ship_equipped = ship["id"] == equipped_id

        # ---------- layout ----------
        book, lp, rp = book_layout(width, height)
        polaroid, picture, controls_center, desc_box = polaroid_layout(rp)

        x0 = lp.x + 34
        right_edge = lp.right - 36
        content_x = lp.x + 44
        content_w = lp.w - 90

        list_y = lp.y + 88
        step = max(28, min(40, (lp.h - 88 - 40 - 5 * 24 - 24) // len(SHIP_DATA)))
        rows = [
            pygame.Rect(content_x - 8, list_y + i * step, content_w + 8, step - 4)
            for i in range(len(SHIP_DATA))
        ]

        note_rect = pygame.Rect(book.right - 34, book.y + 18, 150, 230)
        side_back = pygame.Rect(book.x - 58, book.y + 60, 78, 30)

        top_tabs = [
            (pygame.Rect(lp.x + 30, book.y - 36, 72, 48), TAB_PINK),
            (pygame.Rect(lp.x + 108, book.y - 36, 72, 48), TAB_ORANGE),
            (pygame.Rect(lp.x + 186, book.y - 36, 72, 48), TAB_YELLOW),
            (pygame.Rect(rp.x + 30, book.y - 36, 72, 48), TAB_PURPLE),
            (pygame.Rect(rp.x + 108, book.y - 36, 72, 48), TAB_PURPLE),
            (pygame.Rect(rp.x + 186, book.y - 36, 72, 48), TAB_BLUE),
        ]

        return_rect = pygame.Rect(30, height - 78, 190, 56)
        done_rect = pygame.Rect(width - 220, height - 78, 190, 56)

        prev_rect = pygame.Rect(0, 0, 56, 40)
        prev_rect.center = (controls_center[0] - 62, controls_center[1])
        next_rect = pygame.Rect(0, 0, 56, 40)
        next_rect.center = (controls_center[0] + 62, controls_center[1])

        # hover selects, like the menu
        current_hover = None
        for i, r in enumerate(rows):
            if r.collidepoint(mouse):
                current_hover = i
                break
        if current_hover is not None and current_hover != previous_hover:
            viewed = current_hover
            play_hover()
            ship = SHIP_DATA[viewed]
            ship_owned = ship["id"] in owned_ids
            ship_equipped = ship["id"] == equipped_id
        previous_hover = current_hover

        # ---------- draw ----------
        draw_background(screen, width, height, tick)
        draw_notepad(screen, note_rect, big_font, tab_font, False, footer=f"Level {level}")

        draw_tab(screen, side_back, SIDE_PINK, "Menu", tab_font,
                 side_back.collidepoint(mouse), vertical=True)
        for r, col in top_tabs:
            draw_tab(screen, r, col, "", tab_font, r.collidepoint(mouse))

        draw_book(screen, book, lp, rp)
        draw_ruled_lines(screen, lp, list_y, step)

        put_text(screen, heading_font, "Ship Shop", INK, (lp.centerx, lp.y + 28), "midtop")
        pygame.draw.line(screen, INK_SOFT,
                         (lp.centerx - 70, lp.y + 64), (lp.centerx + 70, lp.y + 64), 2)
        put_text(screen, small_font,
                 f"Level {level}  \u00b7  Owned {len(owned_ids)}/{len(SHIP_DATA)}",
                 INK_SOFT, (lp.centerx, lp.y + 68), "midtop")

        # ship list
        for i, (r, s) in enumerate(zip(rows, SHIP_DATA)):
            is_sel = i == viewed
            s_owned = s["id"] in owned_ids
            s_equipped = s["id"] == equipped_id

            if is_sel:
                alpha_rect(screen, (*HIGHLIGHT, 130), r, 8)

            put_text(screen, item_font, "\u2022", ERROR if is_sel else INK_SOFT,
                     (r.x + 8, r.centery), "midleft")

            name_color = INK if (is_sel and s_owned) else INK_SOFT
            put_text(screen, item_font, s["name"].title(), name_color,
                     (r.x + 30, r.centery), "midleft")

            if s_equipped:
                put_text(screen, small_bold, "\u2713 Equipped", GREEN_INK,
                         (r.right - 6, r.centery), "midright")
            elif s_owned:
                put_text(screen, small_font, "Owned", INK_SOFT,
                         (r.right - 6, r.centery), "midright")
            else:
                put_text(screen, small_bold, f"Lv {s['unlock_level']}", ERROR,
                         (r.right - 6, r.centery), "midright")

        # stats for the viewed ship
        stats_y = list_y + len(SHIP_DATA) * step + 10
        put_text(screen, small_bold, f"{ship['name'].title()} stats", INK, (x0, stats_y), "midleft")
        pygame.draw.line(screen, (205, 196, 176),
                         (x0 - 6, stats_y + 12), (right_edge + 6, stats_y + 12), 1)

        for i, key in enumerate(STAT_ORDER):
            draw_stat_bar(
                screen, x0, stats_y + 32 + i * 24, right_edge - x0,
                STAT_LABELS[key], ship[key], STAT_COLORS[key],
                stat_font, stat_value_font,
            )

        # right page: polaroid with the animated ship
        pic = draw_space_picture(picture.size, tick, stars)
        draw_ship_into(pic, ship, time_value, ship_owned)
        draw_polaroid(screen, polaroid, picture, pic, ship["name"].title(), caption_font)

        draw_arrow(screen, prev_rect.center, -1, True, prev_rect.collidepoint(mouse))
        draw_arrow(screen, next_rect.center, 1, True, next_rect.collidepoint(mouse))

        draw_desc_box(screen, desc_box)
        desc_lines = []
        for line in wrap_text(small_font, ship["description"], desc_box.w - 24)[:2]:
            desc_lines.append((line, small_font, INK))
        desc_lines.append((f"{ship['ship_class'].title()}  \u00b7  {ship['rank'].title()}",
                           small_font, GOLD_INK))
        desc_lines.append((f"Special: {ship['special']}", small_font, INK_SOFT))

        line_h = small_font.get_linesize()
        ty = desc_box.centery - (line_h * len(desc_lines)) // 2 + 4
        for text_value, fnt, color in desc_lines:
            put_text(screen, fnt, fit_text(fnt, text_value, desc_box.w - 24),
                     color, (desc_box.centerx, ty), "midtop")
            ty += line_h

        if ship_equipped:
            done_label = "Equipped"
        elif ship_owned:
            done_label = "Equip"
        else:
            done_label = "Locked"
        draw_actions(screen, action_font, return_rect, done_rect, mouse, done_label)

        # toast
        if notification and pygame.time.get_ticks() < notification_until:
            img = body_font.render(notification, True, INK)
            toast = pygame.Rect(0, 0, img.get_width() + 40, 40)
            toast.center = (width // 2, height - 40)
            pygame.draw.rect(screen, (60, 40, 36), toast.move(3, 4), border_radius=8)
            pygame.draw.rect(screen, PAPER, toast, border_radius=8)
            pygame.draw.rect(screen, notification_color, toast, 3, border_radius=8)
            screen.blit(img, img.get_rect(center=toast.center))

        pygame.display.flip()

        # ---------- events ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    play_back()
                    return "back"
                elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
                    move(-1)
                elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
                    move(1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    try_equip()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                if return_rect.collidepoint(pos) or side_back.collidepoint(pos):
                    play_back()
                    return "back"

                if done_rect.collidepoint(pos):
                    try_equip()
                elif prev_rect.collidepoint(pos):
                    move(-1)
                elif next_rect.collidepoint(pos):
                    move(1)
                else:
                    for i, r in enumerate(rows):
                        if r.collidepoint(pos):
                            if i != viewed:
                                viewed = i
                                play_click()
                            break