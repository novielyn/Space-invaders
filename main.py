import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    GAME_TITLE,
    PREFERENCES,
)

from database import get_player

from screens.login import login_screen
from screens.register import register_screen
from screens.leaderboard import leaderboard_screen
from screens.menu import menu_screen
from screens.settings import settings_screen
from screens.shop import shop_screen
from screens.profile import profile_screen
from screens.game_over import game_over_screen

from managers.game_manager import GameManager
from managers.ui_sounds import ui_sounds


pygame.init()

try:
    pygame.mixer.init()
except pygame.error:
    pass

ui_sounds.load()

WINDOWED_WIDTH = SCREEN_WIDTH
WINDOWED_HEIGHT = SCREEN_HEIGHT

FULLSCREEN = PREFERENCES.get("fullscreen", True)


def create_screen():
    global FULLSCREEN

    if FULLSCREEN:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WINDOWED_WIDTH, WINDOWED_HEIGHT))

    pygame.display.set_caption
    ("Space Invaders by Patalinghog Jannel B.")

    return screen


screen = create_screen()
clock = pygame.time.Clock()


def get_screen_size():
    return (screen.get_width(), screen.get_height())


def toggle_fullscreen():
    global FULLSCREEN
    global screen

    FULLSCREEN = not FULLSCREEN

    if FULLSCREEN:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode(
            (WINDOWED_WIDTH, WINDOWED_HEIGHT),
            pygame.RESIZABLE,
        )

    PREFERENCES["fullscreen"] = FULLSCREEN

    pygame.display.set_caption(GAME_TITLE)

    return screen


def refresh_player():
    global player

    if not isinstance(player, dict):
        return player

    player_id = player.get("id")

    if not player_id:
        return player

    try:
        fresh_player = get_player(player_id)

        if isinstance(fresh_player, dict):
            player = fresh_player

    except Exception:
        pass

    return player


screen_state = "login"

player = None
game = None
running = True


def create_game():
    global player

    refresh_player()

    if not isinstance(player, dict) or not player.get("id"):
        return None

    return GameManager(
        screen,
        screen.get_width(),
        screen.get_height(),
        player["id"],
        player,
    )


while running:

    # ---------------------------------------------------------- login
    if screen_state == "login":

        result = login_screen(screen, clock)

        state = result[0]

        if state == "quit":
            running = False

        elif state == "menu":
            player = result[1]
            refresh_player()
            screen_state = "menu"

        elif state == "register":
            screen_state = "register"

    # ------------------------------------------------------- register
    elif screen_state == "register":

        result = register_screen(screen, clock)

        state = result[0] if isinstance(result, tuple) else result

        if state == "quit":
            running = False

        elif state == "login":
            screen_state = "login"

    # ----------------------------------------------------------- menu
    elif screen_state == "menu":

        refresh_player()

        next_state, menu_player = menu_screen(screen, clock, player)

        if isinstance(menu_player, dict):
            player = menu_player

        refresh_player()

        if next_state == "quit":
            running = False

        elif next_state == "play":
            game = create_game()

            if game is not None:
                game.start_game()
                screen_state = "game"
            else:
                screen_state = "menu"

        elif next_state == "shop":
            screen_state = "shop"

        elif next_state == "leaderboard":
            screen_state = "leaderboard"

        elif next_state == "profile":
            screen_state = "profile"

        elif next_state == "settings":
            screen_state = "settings"

        elif next_state == "login":
            player = None
            game = None
            screen_state = "login"

    # ----------------------------------------------------------- shop
    elif screen_state == "shop":

        refresh_player()

        result = shop_screen(screen, clock, player)

        if isinstance(result, tuple):
            state = result[0]

            if len(result) > 1 and isinstance(result[1], dict):
                player = result[1]
        else:
            state = result

        refresh_player()

        if state == "quit":
            running = False

        elif state in ("back", "menu"):
            screen_state = "menu"

    # ------------------------------------------------------- settings
    elif screen_state == "settings":

        result, screen = settings_screen(screen, clock, toggle_fullscreen)

        if result == "quit":
            running = False

        elif result == "menu":
            screen_state = "menu"

    # ----------------------------------------------------------- game
    elif screen_state == "game":

        if game is None:
            screen_state = "menu"
            continue

        events = pygame.event.get()

        quit_requested = False

        for event in events:

            if event.type == pygame.QUIT:
                quit_requested = True

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:

                screen = toggle_fullscreen()

                if hasattr(game, "screen"):
                    game.screen = screen

                if hasattr(game, "screen_width"):
                    game.screen_width = screen.get_width()

                if hasattr(game, "screen_height"):
                    game.screen_height = screen.get_height()

        if quit_requested:
            running = False
            continue

        game.update(events)

        pygame.display.flip()

        clock.tick(FPS)

        if game.game_state == "game_over":
            refresh_player()
            screen_state = "game_over"

        elif game.game_state == "main_menu":
            refresh_player()
            screen_state = "menu"

    # ------------------------------------------------------ game over
    elif screen_state == "game_over":

        refresh_player()

        result, screen = game_over_screen(
            screen,
            clock,
            game.score,
            game.high_score,
            player,
            toggle_fullscreen,
        )

        if result == "quit":
            running = False

        elif result == "retry":
            game = create_game()

            if game is not None:
                game.start_game()
                screen_state = "game"
            else:
                screen_state = "menu"

        elif result == "menu":
            screen_state = "menu"

    # ---------------------------------------------------- leaderboard
    elif screen_state == "leaderboard":

        refresh_player()

        result = leaderboard_screen(screen, clock, player)

        if result == "quit":
            running = False

        elif result in ("back", "menu"):
            screen_state = "menu"

    # --------------------------------------------------------- profile
    elif screen_state == "profile":

        refresh_player()

        next_state, profile_player = profile_screen(screen, clock, player)

        if isinstance(profile_player, dict):
            player = profile_player

        refresh_player()

        if next_state == "quit":
            running = False

        elif next_state == "menu":
            screen_state = "menu"

        elif next_state == "login":
            player = None
            game = None
            screen_state = "login"


pygame.quit()