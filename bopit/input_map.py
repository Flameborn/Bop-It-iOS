"""Every key binding lives here. Nothing else refers to pygame key codes.

These are interim defaults. The final scheme is proposed and approved at build stage 6.
"""

import pygame

from bopit.menu import Nav

MENU_KEYS: dict[int, Nav] = {
    pygame.K_UP: Nav.UP,
    pygame.K_DOWN: Nav.DOWN,
    pygame.K_LEFT: Nav.LEFT,
    pygame.K_RIGHT: Nav.RIGHT,
    pygame.K_HOME: Nav.FIRST,
    pygame.K_END: Nav.LAST,
    pygame.K_RETURN: Nav.SELECT,
    pygame.K_KP_ENTER: Nav.SELECT,
    pygame.K_SPACE: Nav.SELECT,
    pygame.K_ESCAPE: Nav.BACK,
    pygame.K_BACKSPACE: Nav.BACK,
}


def menu_nav_for(key: int) -> Nav | None:
    return MENU_KEYS.get(key)


# Temporary game keys for testing Classic. The real scheme is proposed at stage 6.
GAME_KEYS: dict[int, str] = {
    pygame.K_SPACE: "Bop",
    pygame.K_LEFT: "Twist",
    pygame.K_DOWN: "Pull",
}


# Speaks the current score during a game. Never counts as a move.
GAME_SCORE_KEY = pygame.K_s


def game_command_for(key: int) -> str | None:
    return GAME_KEYS.get(key)


def key_name_for(command: str) -> str | None:
    """The key currently bound to a command, as a spoken name."""
    for key, bound in GAME_KEYS.items():
        if bound == command:
            return pygame.key.name(key)
    return None
