import os
import math
import random
import importlib

import pygame


# ---------------------------------------------------------------- palette

WHITE = (248, 246, 244)
GRAY = (145, 153, 178)
MUTED = (94, 106, 137)

CYAN = (0, 220, 255)
GREEN = (70, 255, 145)
RED = (255, 24, 52)
GOLD = (255, 210, 90)
PURPLE = (180, 90, 255)

TITLE_RED = (245, 20, 62)
TITLE_SHADOW = (92, 2, 22)

MENU_BLUE = (145, 164, 207)
MENU_WHITE = (250, 247, 244)

CURSOR_RED = (242, 17, 52)
GOLD_STAR = (255, 215, 105)

BG_TOP = (3, 0, 3)
BG_BOTTOM = (12, 1, 5)

PANEL_FILL = (5, 2, 7)
PANEL_EDGE = (75, 18, 38)

FIELD_FILL = (7, 3, 9)
FIELD_EDGE = (68, 16, 34)

ERROR_RED = (255, 72, 82)
SUCCESS_GREEN = (70, 255, 145)

BG_IMAGE = os.path.join(
    "assets",
    "images",
    "bg.png"
)


# ------------------------------------------------------ optional menu link

MENU_MODULES = (
    "menu",
    "screens.menu",
    "ui.menu",
    "menu_screen",
    "screens.menu_screen",
    "scenes.menu",
)

_MENU = None

for _name in MENU_MODULES:

    try:
        _candidate = importlib.import_module(_name)

    except Exception:
        continue

    if hasattr(_candidate, "draw_menu_background"):
        _MENU = _candidate
        break


try:
    from managers.ui_sounds import ui_sounds

except Exception:
    ui_sounds = None


# ------------------------------------------------------------------ fonts

_FONT_CACHE = {}
_FONT_FILE = None


def _find_font_file():
    folders = [
        os.path.join("assets", "fonts"),
        "assets",
    ]

    preferred = [
        "gothic.ttf",
        "Gothic.ttf",
        "medieval.ttf",
        "Medieval.ttf",
        "cinzel.ttf",
        "Cinzel.ttf",
        "menu.ttf",
        "font.ttf",
    ]

    for folder in folders:

        if not os.path.isdir(folder):
            continue

        for name in preferred:

            path = os.path.join(
                folder,
                name
            )

            if os.path.isfile(path):
                return path

    for folder in folders:

        if not os.path.isdir(folder):
            continue

        try:

            for name in os.listdir(folder):

                if name.lower().endswith(
                    (
                        ".ttf",
                        ".otf"
                    )
                ):
                    return os.path.join(
                        folder,
                        name
                    )

        except Exception:
            pass

    return None


def _local_menu_font(size, bold=False):
    global _FONT_FILE

    size = max(
        8,
        int(size)
    )

    key = (
        size,
        bold
    )

    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    if _FONT_FILE is None:
        _FONT_FILE = _find_font_file()

    try:

        if (
            _FONT_FILE
            and os.path.isfile(_FONT_FILE)
        ):
            font = pygame.font.Font(
                _FONT_FILE,
                size
            )

        else:

            font_path = pygame.font.match_font(
                "Georgia",
                bold=bold
            )

            if font_path:
                font = pygame.font.Font(
                    font_path,
                    size
                )
            else:
                font = pygame.font.SysFont(
                    "Arial",
                    size,
                    bold=bold
                )

    except Exception:

        font = pygame.font.SysFont(
            "Arial",
            size,
            bold=bold
        )

    _FONT_CACHE[key] = font

    return font


menu_font = getattr(
    _MENU,
    "menu_font",
    _local_menu_font
)


def get_font(size, bold=False):
    return menu_font(
        size,
        bold
    )


def fit_text(font, text, width):
    text = str(text)

    if font.size(text)[0] <= width:
        return text

    value = text

    while value:

        candidate = value + "..."

        if font.size(candidate)[0] <= width:
            return candidate

        value = value[:-1]

    return "..."


# ------------------------------------------------------- fallback weather

_BG_IMAGE = None

_RAIN = []
_FINE_RAIN = []
_HEAVY_RAIN = []
_CLOUDS = []

_LIGHTNING_POINTS = []
_LIGHTNING_LIFE = 0
_LIGHTNING_COOLDOWN = 0
_LIGHTNING_FLASH = 0

_LAST_SIZE = None


def lerp_color(a, b, t):
    t = max(
        0.0,
        min(
            1.0,
            t
        )
    )

    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t)
    )


def _draw_gradient(screen, width, height):
    height = max(
        1,
        height
    )

    for y in range(height):

        color = lerp_color(
            BG_TOP,
            BG_BOTTOM,
            y / max(
                1,
                height - 1
            )
        )

        pygame.draw.line(
            screen,
            color,
            (
                0,
                y
            ),
            (
                width,
                y
            )
        )


def _load_background():
    global _BG_IMAGE

    if _BG_IMAGE is not None:
        return True

    if not os.path.isfile(BG_IMAGE):
        return False

    try:
        _BG_IMAGE = pygame.image.load(
            BG_IMAGE
        ).convert()

        return True

    except Exception:
        _BG_IMAGE = None

        return False


def _draw_scaled_background(screen, width, height):

    if not _load_background():

        _draw_gradient(
            screen,
            width,
            height
        )

        return

    source_width = _BG_IMAGE.get_width()
    source_height = _BG_IMAGE.get_height()

    source_ratio = (
        source_width
        / max(
            1,
            source_height
        )
    )

    target_ratio = (
        width
        / max(
            1,
            height
        )
    )

    if source_ratio > target_ratio:

        new_height = height

        new_width = int(
            height * source_ratio
        )

    else:

        new_width = width

        new_height = int(
            width / source_ratio
        )

    scaled = pygame.transform.smoothscale(
        _BG_IMAGE,
        (
            new_width,
            new_height
        )
    )

    screen.blit(
        scaled,
        (
            -(new_width - width) // 2,
            -(new_height - height) // 2
        )
    )


def _initialize_weather(width, height):
    global _RAIN
    global _FINE_RAIN
    global _HEAVY_RAIN
    global _CLOUDS

    rng = random.Random(913742)

    _RAIN = []
    _FINE_RAIN = []
    _HEAVY_RAIN = []
    _CLOUDS = []

    for _ in range(155):

        _RAIN.append({
            "x": rng.uniform(-width, width),
            "y": rng.uniform(-height, height),
            "length": rng.uniform(16, 34),
            "speed": rng.uniform(7, 14),
            "alpha": rng.randint(28, 72),
            "thickness": rng.choice([1, 1, 1, 2])
        })

    for _ in range(240):

        _FINE_RAIN.append({
            "x": rng.uniform(-width, width),
            "y": rng.uniform(-height, height),
            "length": rng.uniform(4, 12),
            "speed": rng.uniform(3, 8),
            "alpha": rng.randint(7, 26)
        })

    for _ in range(30):

        _HEAVY_RAIN.append({
            "x": rng.uniform(-width, width),
            "y": rng.uniform(-height, height),
            "length": rng.uniform(30, 58),
            "speed": rng.uniform(12, 20),
            "alpha": rng.randint(35, 75)
        })

    for _ in range(18):

        _CLOUDS.append({
            "x": rng.uniform(-width * 0.20, width * 1.10),
            "y": rng.uniform(-height * 0.08, height * 0.52),
            "w": rng.uniform(width * 0.18, width * 0.42),
            "h": rng.uniform(height * 0.04, height * 0.14),
            "speed": rng.uniform(0.05, 0.16),
            "alpha": rng.randint(5, 16)
        })


def _draw_clouds(screen, width, height, tick):

    if not _CLOUDS:
        return

    surface = pygame.Surface(
        (
            width,
            height
        ),
        pygame.SRCALPHA
    )

    for cloud in _CLOUDS:

        cloud["x"] += cloud["speed"]

        if cloud["x"] > width + cloud["w"]:
            cloud["x"] = -cloud["w"]

        y = (
            cloud["y"]
            + math.sin(
                tick * 0.002
                + cloud["x"] * 0.001
            ) * 4
        )

        pygame.draw.ellipse(
            surface,
            (
                0,
                0,
                0,
                cloud["alpha"]
            ),
            (
                int(cloud["x"]),
                int(y),
                int(cloud["w"]),
                int(cloud["h"])
            )
        )

    screen.blit(
        surface,
        (
            0,
            0
        )
    )


def _draw_red_atmosphere(screen, width, height, tick):
    surface = pygame.Surface(
        (
            width,
            height
        ),
        pygame.SRCALPHA
    )

    pulse = (
        math.sin(tick * 0.004)
        + 1
    ) * 0.5

    center_x = int(width * 0.84)
    center_y = int(height * 0.27)

    maximum = int(
        max(
            width,
            height
        ) * 0.65
    )

    for radius in range(
        maximum,
        10,
        -20
    ):

        progress = (
            1
            - radius / max(
                1,
                maximum
            )
        )

        alpha = int(
            1
            + progress * (
                7
                + pulse * 5
            )
        )

        pygame.draw.circle(
            surface,
            (
                180,
                0,
                18,
                alpha
            ),
            (
                center_x,
                center_y
            ),
            radius
        )

    screen.blit(
        surface,
        (
            0,
            0
        )
    )


def _draw_dark_overlay(screen, width, height, tick):
    surface = pygame.Surface(
        (
            width,
            height
        ),
        pygame.SRCALPHA
    )

    pulse = (
        math.sin(tick * 0.003)
        + 1
    ) * 0.5

    pygame.draw.rect(
        surface,
        (
            0,
            0,
            0,
            int(148 + pulse * 6)
        ),
        surface.get_rect()
    )

    screen.blit(
        surface,
        (
            0,
            0
        )
    )


def _draw_vignette(screen, width, height):
    surface = pygame.Surface(
        (
            width,
            height
        ),
        pygame.SRCALPHA
    )

    for i in range(20):

        pygame.draw.rect(
            surface,
            (
                0,
                0,
                0,
                int(2 + i * 1.5)
            ),
            (
                i * 2,
                i * 2,
                width - i * 4,
                height - i * 4
            ),
            max(
                1,
                int(2 + i * 0.55)
            )
        )

    screen.blit(
        surface,
        (
            0,
            0
        )
    )


def _draw_starfield(screen, width, height, tick):
    rng = random.Random(82631)

    surface = pygame.Surface(
        (
            width,
            height
        ),
        pygame.SRCALPHA
    )

    for _ in range(55):

        x = rng.randrange(
            max(
                1,
                width
            )
        )

        y = rng.randrange(
            max(
                1,
                int(height * 0.80)
            )
        )

        phase = rng.random() * math.tau

        alpha = int(
            4
            + (
                (
                    math.sin(
                        tick * 0.009
                        + phase
                    )
                    + 1
                ) * 0.5
            ) * 16
        )

        pygame.draw.circle(
            surface,
            (
                205,
                210,
                225,
                alpha
            ),
            (
                x,
                y
            ),
            rng.choice([1, 1, 1, 2])
        )

    screen.blit(
        surface,
        (
            0,
            0
        )
    )


def _create_lightning(width, height):
    global _LIGHTNING_POINTS
    global _LIGHTNING_LIFE
    global _LIGHTNING_FLASH

    start_x = random.randint(
        int(width * 0.55),
        int(width * 0.94)
    )

    points = [
        (
            start_x,
            -20
        )
    ]

    x = start_x
    y = -20

    while y < height * 0.60:

        x += random.randint(-45, 45)
        y += random.randint(35, 72)

        points.append(
            (
                x,
                y
            )
        )

    _LIGHTNING_POINTS = points
    _LIGHTNING_LIFE = 7
    _LIGHTNING_FLASH = 4


def _draw_lightning(screen, width, height, tick):
    global _LIGHTNING_LIFE
    global _LIGHTNING_COOLDOWN
    global _LIGHTNING_FLASH

    if _LIGHTNING_COOLDOWN > 0:
        _LIGHTNING_COOLDOWN -= 1

    if (
        _LIGHTNING_LIFE <= 0
        and _LIGHTNING_COOLDOWN <= 0
        and random.random() < 0.0016
    ):

        _create_lightning(
            width,
            height
        )

        _LIGHTNING_COOLDOWN = 220

    if _LIGHTNING_LIFE <= 0:
        return

    _LIGHTNING_LIFE -= 1

    surface = pygame.Surface(
        (
            width,
            height
        ),
        pygame.SRCALPHA
    )

    alpha = int(
        165 * (
            _LIGHTNING_LIFE / 7
        )
    )

    pygame.draw.lines(
        surface,
        (
            255,
            0,
            25,
            alpha // 4
        ),
        False,
        _LIGHTNING_POINTS,
        8
    )

    pygame.draw.lines(
        surface,
        (
            255,
            80,
            95,
            alpha
        ),
        False,
        _LIGHTNING_POINTS,
        2
    )

    screen.blit(
        surface,
        (
            0,
            0
        )
    )

    if _LIGHTNING_FLASH > 0:

        flash = pygame.Surface(
            (
                width,
                height
            ),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            flash,
            (
                255,
                15,
                30,
                int(20 * (_LIGHTNING_FLASH / 4))
            ),
            flash.get_rect()
        )

        screen.blit(
            flash,
            (
                0,
                0
            )
        )

        _LIGHTNING_FLASH -= 1


def _draw_rain(screen, width, height, tick):
    surface = pygame.Surface(
        (
            width,
            height
        ),
        pygame.SRCALPHA
    )

    for drop in _FINE_RAIN:

        drop["y"] += drop["speed"]
        drop["x"] -= drop["speed"] * 0.10

        if drop["y"] > height + 20:
            drop["y"] = random.uniform(-100, -5)
            drop["x"] = random.uniform(0, width)

        pygame.draw.line(
            surface,
            (
                180,
                185,
                198,
                drop["alpha"]
            ),
            (
                int(drop["x"]),
                int(drop["y"])
            ),
            (
                int(drop["x"] - 1),
                int(drop["y"] - drop["length"])
            ),
            1
        )

    for drop in _RAIN:

        drop["y"] += drop["speed"]
        drop["x"] -= drop["speed"] * 0.18

        if drop["y"] > height + 35:
            drop["y"] = random.uniform(-130, -10)
            drop["x"] = random.uniform(0, width)

        pygame.draw.line(
            surface,
            (
                210,
                50,
                68,
                drop["alpha"]
            ),
            (
                int(drop["x"]),
                int(drop["y"])
            ),
            (
                int(drop["x"] - drop["length"] * 0.18),
                int(drop["y"] - drop["length"])
            ),
            drop["thickness"]
        )

    for drop in _HEAVY_RAIN:

        drop["y"] += drop["speed"]
        drop["x"] -= drop["speed"] * 0.22

        if drop["y"] > height + 65:
            drop["y"] = random.uniform(-180, -15)
            drop["x"] = random.uniform(0, width)

        pygame.draw.line(
            surface,
            (
                230,
                50,
                65,
                drop["alpha"]
            ),
            (
                int(drop["x"]),
                int(drop["y"])
            ),
            (
                int(drop["x"] - drop["length"] * 0.24),
                int(drop["y"] - drop["length"])
            ),
            2
        )

    screen.blit(
        surface,
        (
            0,
            0
        )
    )


def _local_background(screen, width, height, tick):
    global _LAST_SIZE

    if _LAST_SIZE != (width, height):

        _initialize_weather(
            width,
            height
        )

        _LAST_SIZE = (
            width,
            height
        )

    _draw_scaled_background(
        screen,
        width,
        height
    )

    _draw_clouds(
        screen,
        width,
        height,
        tick
    )

    _draw_red_atmosphere(
        screen,
        width,
        height,
        tick
    )

    _draw_dark_overlay(
        screen,
        width,
        height,
        tick
    )

    _draw_vignette(
        screen,
        width,
        height
    )

    _draw_starfield(
        screen,
        width,
        height,
        tick
    )

    _draw_lightning(
        screen,
        width,
        height,
        tick
    )

    _draw_rain(
        screen,
        width,
        height,
        tick
    )


draw_background = getattr(
    _MENU,
    "draw_menu_background",
    _local_background
)


# ----------------------------------------------------------------- cursor

def _local_cursor(screen, x, y, tick, size=8):
    pulse = (
        math.sin(tick * 0.08)
        + 1
    ) * 0.5

    surface_size = size * 5

    surface = pygame.Surface(
        (
            surface_size,
            surface_size
        ),
        pygame.SRCALPHA
    )

    center = surface_size // 2

    outer = int(
        size * (
            1.40
            + pulse * 0.12
        )
    )

    pygame.draw.polygon(
        surface,
        (
            255,
            5,
            35,
            40
        ),
        [
            (center, center - outer),
            (center + outer, center),
            (center, center + outer),
            (center - outer, center)
        ]
    )

    inner = max(
        4,
        int(size * 0.70)
    )

    pygame.draw.polygon(
        surface,
        CURSOR_RED,
        [
            (center, center - inner),
            (center + inner, center),
            (center, center + inner),
            (center - inner, center)
        ]
    )

    screen.blit(
        surface,
        (
            int(x - center),
            int(y - center)
        )
    )


draw_cursor = getattr(
    _MENU,
    "draw_menu_cursor",
    _local_cursor
)


# ------------------------------------------------------------------ icons

def draw_person_icon(screen, center, size, color):
    cx, cy = center

    pygame.draw.circle(
        screen,
        color,
        (
            cx,
            cy - int(size * 0.26)
        ),
        max(
            3,
            int(size * 0.26)
        ),
        2
    )

    pygame.draw.arc(
        screen,
        color,
        pygame.Rect(
            cx - int(size * 0.48),
            cy - int(size * 0.02),
            int(size * 0.96),
            int(size * 0.86)
        ),
        math.radians(0),
        math.radians(180),
        2
    )


def draw_lock_icon(screen, center, size, color):
    cx, cy = center

    body_width = int(size * 0.72)
    body_height = int(size * 0.56)

    pygame.draw.rect(
        screen,
        color,
        pygame.Rect(
            cx - body_width // 2,
            cy - int(size * 0.02),
            body_width,
            body_height
        ),
        2
    )

    pygame.draw.arc(
        screen,
        color,
        pygame.Rect(
            cx - int(size * 0.28),
            cy - int(size * 0.46),
            int(size * 0.56),
            int(size * 0.60)
        ),
        math.radians(180),
        math.radians(360),
        2
    )

    pygame.draw.line(
        screen,
        color,
        (
            cx,
            cy + int(size * 0.14)
        ),
        (
            cx,
            cy + int(size * 0.34)
        ),
        2
    )


def draw_mail_icon(screen, center, size, color):
    cx, cy = center

    width = int(size * 1.35)
    height = int(size * 0.95)

    rect = pygame.Rect(
        cx - width // 2,
        cy - height // 2,
        width,
        height
    )

    pygame.draw.rect(
        screen,
        color,
        rect,
        2
    )

    pygame.draw.line(
        screen,
        color,
        (
            rect.left + 3,
            rect.top + 3
        ),
        (
            cx,
            cy + 1
        ),
        2
    )

    pygame.draw.line(
        screen,
        color,
        (
            rect.right - 3,
            rect.top + 3
        ),
        (
            cx,
            cy + 1
        ),
        2
    )


def draw_eye_icon(screen, center, size, color, visible):
    cx, cy = center

    points = [
        (cx - size, cy),
        (cx - int(size * 0.55), cy - int(size * 0.52)),
        (cx, cy - int(size * 0.65)),
        (cx + int(size * 0.55), cy - int(size * 0.52)),
        (cx + size, cy),
        (cx + int(size * 0.55), cy + int(size * 0.52)),
        (cx, cy + int(size * 0.65)),
        (cx - int(size * 0.55), cy + int(size * 0.52))
    ]

    pygame.draw.polygon(
        screen,
        color,
        points,
        2
    )

    if visible:

        pygame.draw.circle(
            screen,
            color,
            (
                cx,
                cy
            ),
            max(
                3,
                int(size * 0.30)
            )
        )

    else:

        pygame.draw.line(
            screen,
            color,
            (
                cx - size - 2,
                cy - size - 2
            ),
            (
                cx + size + 2,
                cy + size + 2
            ),
            3
        )


# ----------------------------------------------------------------- panels

def draw_panel(screen, rect, tick=0, accent=True):
    surface = pygame.Surface(
        rect.size,
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        surface,
        (
            PANEL_FILL[0],
            PANEL_FILL[1],
            PANEL_FILL[2],
            218
        ),
        surface.get_rect()
    )

    screen.blit(
        surface,
        rect.topleft
    )

    pygame.draw.rect(
        screen,
        TITLE_RED if accent else PANEL_EDGE,
        rect,
        2
    )

    corner = 14

    for x, y, dx, dy in (
        (rect.left, rect.top, 1, 1),
        (rect.right - 1, rect.top, -1, 1),
        (rect.left, rect.bottom - 1, 1, -1),
        (rect.right - 1, rect.bottom - 1, -1, -1)
    ):

        pygame.draw.line(
            screen,
            TITLE_SHADOW,
            (
                x + dx * 3,
                y + dy * 3
            ),
            (
                x + dx * corner,
                y + dy * 3
            ),
            2
        )

        pygame.draw.line(
            screen,
            TITLE_SHADOW,
            (
                x + dx * 3,
                y + dy * 3
            ),
            (
                x + dx * 3,
                y + dy * corner
            ),
            2
        )


def draw_title(
    screen,
    text,
    center_x,
    top_y,
    size,
    underline_width=0
):
    font = menu_font(
        size,
        True
    )

    shadow = font.render(
        text,
        True,
        TITLE_SHADOW
    )

    label = font.render(
        text,
        True,
        TITLE_RED
    )

    x = center_x - label.get_width() // 2

    screen.blit(
        shadow,
        (
            x + 4,
            top_y + 5
        )
    )

    screen.blit(
        label,
        (
            x,
            top_y
        )
    )

    if underline_width > 0:

        line_y = (
            top_y
            + label.get_height()
            + 6
        )

        pygame.draw.line(
            screen,
            TITLE_RED,
            (
                center_x - underline_width // 2,
                line_y
            ),
            (
                center_x + underline_width // 2,
                line_y
            ),
            3
        )

        pygame.draw.line(
            screen,
            TITLE_SHADOW,
            (
                center_x - underline_width // 2 + 26,
                line_y + 7
            ),
            (
                center_x + underline_width // 2 - 26,
                line_y + 7
            ),
            1
        )

    return label.get_height()


def draw_input(
    screen,
    rect,
    icon_type,
    value,
    active_state,
    placeholder,
    font,
    cursor_visible,
    masked=False,
    tick=0
):
    surface = pygame.Surface(
        rect.size,
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        surface,
        (
            FIELD_FILL[0],
            FIELD_FILL[1],
            FIELD_FILL[2],
            230
        ),
        surface.get_rect()
    )

    screen.blit(
        surface,
        rect.topleft
    )

    if active_state:

        glow = pygame.Surface(
            rect.inflate(16, 16).size,
            pygame.SRCALPHA
        )

        pulse = (
            math.sin(tick * 0.09)
            + 1
        ) * 0.5

        pygame.draw.rect(
            glow,
            (
                CURSOR_RED[0],
                CURSOR_RED[1],
                CURSOR_RED[2],
                int(14 + pulse * 20)
            ),
            glow.get_rect()
        )

        screen.blit(
            glow,
            rect.inflate(16, 16).topleft
        )

    pygame.draw.rect(
        screen,
        TITLE_RED if active_state else FIELD_EDGE,
        rect,
        2
    )

    icon_color = (
        TITLE_RED
        if active_state
        else MENU_BLUE
    )

    icon_center = (
        rect.x + 28,
        rect.centery
    )

    if icon_type == "person":
        draw_person_icon(
            screen,
            icon_center,
            20,
            icon_color
        )

    elif icon_type == "lock":
        draw_lock_icon(
            screen,
            icon_center,
            22,
            icon_color
        )

    elif icon_type == "mail":
        draw_mail_icon(
            screen,
            icon_center,
            20,
            icon_color
        )

    pygame.draw.line(
        screen,
        FIELD_EDGE,
        (
            rect.x + 52,
            rect.y + 8
        ),
        (
            rect.x + 52,
            rect.bottom - 8
        ),
        1
    )

    text_x = rect.x + 64

    display_text = (
        "*" * len(value)
        if masked
        else value
    )

    if display_text:

        text_surface = font.render(
            display_text,
            True,
            MENU_WHITE
        )

        max_width = rect.width - 115

        while (
            text_surface.get_width() > max_width
            and len(display_text) > 1
        ):

            display_text = display_text[1:]

            text_surface = font.render(
                display_text,
                True,
                MENU_WHITE
            )

        screen.blit(
            text_surface,
            (
                text_x,
                rect.centery
                - text_surface.get_height() // 2
            )
        )

        cursor_x = (
            text_x
            + text_surface.get_width()
            + 3
        )

    else:

        placeholder_surface = font.render(
            placeholder,
            True,
            MUTED
        )

        screen.blit(
            placeholder_surface,
            (
                text_x,
                rect.centery
                - placeholder_surface.get_height() // 2
            )
        )

        cursor_x = text_x

    if active_state and cursor_visible:

        pygame.draw.line(
            screen,
            CURSOR_RED,
            (
                cursor_x,
                rect.centery - 11
            ),
            (
                cursor_x,
                rect.centery + 11
            ),
            2
        )


def draw_button(
    screen,
    rect,
    text,
    mouse_pos,
    tick,
    primary=True,
    focused=False
):
    hovered = rect.collidepoint(mouse_pos)

    active = hovered or focused

    if active:

        glow = pygame.Surface(
            rect.inflate(22, 22).size,
            pygame.SRCALPHA
        )

        pulse = (
            math.sin(tick * 0.12)
            + 1
        ) * 0.5

        pygame.draw.rect(
            glow,
            (
                CURSOR_RED[0],
                CURSOR_RED[1],
                CURSOR_RED[2],
                int(25 + pulse * 35)
            ),
            glow.get_rect()
        )

        screen.blit(
            glow,
            rect.inflate(22, 22).topleft
        )

    surface = pygame.Surface(
        rect.size,
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        surface,
        (
            PANEL_FILL[0],
            PANEL_FILL[1],
            PANEL_FILL[2],
            235
        ),
        surface.get_rect()
    )

    screen.blit(
        surface,
        rect.topleft
    )

    if primary:
        border = TITLE_RED
    else:
        border = (
            TITLE_RED
            if active
            else FIELD_EDGE
        )

    pygame.draw.rect(
        screen,
        border,
        rect,
        2
    )

    font = menu_font(
        max(
            18,
            min(
                28,
                rect.height - 24
            )
        ),
        True
    )

    color = (
        MENU_WHITE
        if active
        else (
            TITLE_RED
            if primary
            else MENU_BLUE
        )
    )

    label = font.render(
        fit_text(
            font,
            text,
            rect.width - 40
        ),
        True,
        color
    )

    if active:

        shadow = font.render(
            fit_text(
                font,
                text,
                rect.width - 40
            ),
            True,
            TITLE_RED
        )

        shadow.set_alpha(70)

        screen.blit(
            shadow,
            (
                rect.centerx - shadow.get_width() // 2 + 2,
                rect.centery - shadow.get_height() // 2 + 2
            )
        )

    screen.blit(
        label,
        (
            rect.centerx - label.get_width() // 2,
            rect.centery - label.get_height() // 2
        )
    )

    if active:

        draw_cursor(
            screen,
            rect.left - 18,
            rect.centery,
            tick,
            max(
                6,
                rect.height // 7
            )
        )

    return hovered


# ------------------------------------------------------------------ sound

def sound_hover():
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


def sound_click():
    if ui_sounds is None:
        return

    try:
        ui_sounds.click()
        return
    except Exception:
        pass

    try:
        ui_sounds.play("click")
    except Exception:
        pass


def sound_back():
    if ui_sounds is None:
        return

    try:
        ui_sounds.back()
    except Exception:
        pass


def sound_error():
    if ui_sounds is None:
        return

    try:
        ui_sounds.error()
    except Exception:
        pass


def sound_success():
    if ui_sounds is None:
        return

    try:
        ui_sounds.success()
    except Exception:
        pass


def update_hover(rects, mouse_pos, scope):
    if ui_sounds is None:
        return

    try:
        ui_sounds.update_hover(
            rects,
            mouse_pos,
            scope=scope
        )
    except Exception:
        pass