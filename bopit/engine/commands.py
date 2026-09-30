"""The original's commands and their sounds (GameSettings::createCommands, Command_*::init)."""

from bopit.themes import themed

# Master list order. Commands unlock in this order.
COMMAND_ORDER = ("Bop", "Twist", "Pull", "Spin", "Flick", "Shout",
                 "Squeeze", "Crank", "Shake", "Nail", "Brush", "Poke")

# Crank and Brush use differently named sound effect files.
_SFX_STEMS = {"Crank": "Turn", "Brush": "Pet"}
# Only Shout's sound effects go through the theme filter.
_THEMED_SFX = {"Shout"}


def all_commands(shout_it: bool) -> tuple[str, ...]:
    """The master list. Shout is left out entirely when Shout It is off."""
    return tuple(c for c in COMMAND_ORDER if shout_it or c != "Shout")


def _sfx(command: str, suffix: str, theme: int) -> str:
    name = f"SFX_{_SFX_STEMS.get(command, command)}_{suffix}"
    return themed(name, theme) if command in _THEMED_SFX else name


def callout_sound(command: str, commands_mode: str, theme: int) -> str:
    """VO_<Name> in VOX mode, the command sound effect otherwise."""
    if commands_mode == "VOX":
        return f"VO_{command}"
    return _sfx(command, "C", theme)


def response_sound(command: str, theme: int) -> str:
    return _sfx(command, "R", theme)
