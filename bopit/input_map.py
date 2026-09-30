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


# Temporary game keys for testing. The real scheme is proposed at stage 6.
GAME_KEYS: dict[int, str] = {
    pygame.K_SPACE: "Bop",
    pygame.K_LEFT: "Twist",
    pygame.K_DOWN: "Pull",
    pygame.K_RIGHT: "Spin",
    pygame.K_UP: "Flick",
    pygame.K_y: "Shout",
    pygame.K_q: "Squeeze",
    pygame.K_c: "Crank",
    pygame.K_k: "Shake",
    pygame.K_n: "Nail",
    pygame.K_b: "Brush",
    pygame.K_p: "Poke",
}


# Speaks the current score during a game. Never counts as a move.
GAME_SCORE_KEY = pygame.K_s


# Temporary Head 2 Head keys, by position: each player's Bop, then their commands in the
# order they were picked. Green (player 0) is on the left, Blue (player 1) on the right.
H2H_KEYS: dict[int, tuple[int, int | None]] = {
    pygame.K_f: (0, None), pygame.K_d: (0, 0), pygame.K_s: (0, 1),
    pygame.K_j: (1, None), pygame.K_k: (1, 0), pygame.K_l: (1, 1),
}
# S is Green's, so Head 2 Head speaks the score on Tab.
H2H_SCORE_KEY = pygame.K_TAB


def h2h_slot_for(key: int) -> tuple[int, int | None] | None:
    """(player, slot) for a Head 2 Head key; slot None is that player's Bop."""
    return H2H_KEYS.get(key)


def h2h_key_name(player: int, slot: int | None) -> str:
    for key, bound in H2H_KEYS.items():
        if bound == (player, slot):
            return pygame.key.name(key).upper()
    return "no key"


def game_command_for(key: int) -> str | None:
    return GAME_KEYS.get(key)


def key_name_for(command: str) -> str | None:
    """The key currently bound to a command, as a spoken name."""
    for key, bound in GAME_KEYS.items():
        if bound == command:
            return pygame.key.name(key)
    return None
