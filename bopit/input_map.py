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
