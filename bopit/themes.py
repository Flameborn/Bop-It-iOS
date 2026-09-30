"""The original's skins. Index order matches its skinMode values: 0 Original, 1 Halloween, 2 Christmas."""

THEMES = ("Original", "Halloween", "Christmas")
_SUFFIXES = ("", "_HLWN", "_XMAS")


def themed(name: str, theme: int) -> str:
    """The theme's variant of a sound, as the original's GetSkinFilename did.

    Only call this for sounds the original passed through GetSkinFilename.
    """
    return name + _SUFFIXES[theme]


def next_theme(theme: int) -> int:
    return (theme + 1) % len(THEMES)
