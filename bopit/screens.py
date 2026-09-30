"""The menu screens, in the original's structure. Items are ordered top to bottom by their
on-screen position in the original (see docs/DEVIATIONS.md). Back is on the back key.

Sounds match the original's button handlers: SFX_Select for navigation, SFX_SelectGame
for Play and game modes, SFX_Back for back, SFX_SettingsSelect for Banter and Shout It.
"""

from collections.abc import Callable, Sequence
from typing import Protocol

from bopit import texts
from bopit.config import SELECTABLE_COMMAND_MODES, Settings
from bopit.menu import Button, Choice, Menu, Slider
from bopit.scores import Entry
from bopit.themes import THEMES

ON_OFF = ("On", "Off")
SELECT = "SFX_Select"
SELECT_GAME = "SFX_SelectGame"
BACK = "SFX_Back"
SETTINGS_SELECT = "SFX_SettingsSelect"


class Navigator(Protocol):
    settings: Settings

    def push(self, menu: Menu) -> None: ...

    def pop(self) -> None: ...

    def quit(self) -> None: ...

    def not_built(self, what: str) -> None: ...

    def start_mode(self, name: str) -> None: ...

    def return_to_menu(self) -> None: ...

    def settings_changed(self) -> None: ...

    def play(self, name: str) -> None:
        """Play a sound as named, with no theme variant."""
        ...

    def start_menu_music(self) -> None: ...

    def stop_menu_music(self) -> None: ...


def submenu(nav: Navigator, title: str, items: list[Button | Choice | Slider]) -> Menu:
    return Menu(title, items, on_back=nav.pop, back_sound=BACK)


def text_screen(nav: Navigator, title: str, lines: Sequence[str]) -> Menu:
    """Read-only text, one line per item, so it can be arrowed through."""
    return submenu(nav, title, [Button(line, lambda: None) for line in lines])


def main_menu(nav: Navigator) -> Menu:
    s = nav.settings

    def set_theme(index: int) -> None:
        # The original swapped skins by swiping the main menu, then restarted the menu music.
        s.theme = index
        nav.settings_changed()
        nav.stop_menu_music()
        nav.start_menu_music()

    return Menu("Bop It", [
        Button("Play", lambda: nav.not_built("Quick Play"), SELECT_GAME),
        Button("Games", lambda: nav.push(games_menu(nav)), SELECT),
        Button("Options", lambda: nav.push(options_menu(nav)), SELECT),
        Choice("Theme", THEMES, lambda: s.theme, set_theme),
    ], on_back=nav.quit)


def games_menu(nav: Navigator) -> Menu:
    return submenu(nav, "Games", [
        Button("Solo", lambda: nav.push(solo_menu(nav)), SELECT),
        Button("Multiplayer", lambda: nav.push(multiplayer_menu(nav)), SELECT),
        Button("Trophies", lambda: nav.not_built("Trophies"), SELECT),
        Button("Scores", lambda: nav.not_built("Scores"), SELECT),
    ])


# Verbatim from English.lproj/Localizable.strings.
MODE_DESCRIPTIONS = {
    "Classic": "The original game of Bop, Twist and Pull. Just do what it says to stay alive "
               "as it gets faster and faster.",
    "Basic": "The Rhythm Challenge! Get Rhythm Bonus points for completing moves on the beat - "
             "a PERFECT awards the most points. Use X-Moves for additional bonus points.",
    "Extreme": "With as many 6 BopJects on screen at once, even a Bop Master will think this is "
               "Extreme! Get Rhythm Bonus points for completing moves on the beat. Use X-Moves "
               "for additional bonus points.",
    "Blitz": "Complete 20 moves as fast as you can. Just do what it says...only faster!",
}


def intro_menu(nav: Navigator, mode: str, best: Entry, on_start: Callable[[], None]) -> Menu:
    """GameModeIntro, top to bottom: description, high score, Start. Back returns to the
    main menu without a sound, as in the original."""
    return Menu(mode, [
        Button(MODE_DESCRIPTIONS.get(mode, ""), lambda: None),
        Button(f"High Score: {best.moves} moves, {best.score:,} points", lambda: None),
        Button("Start", on_start, SELECT),
    ], on_back=nav.return_to_menu)


def _modes(nav: Navigator, names: Sequence[str]) -> list[Button | Choice | Slider]:
    def starter(name: str) -> Callable[[], None]:
        return lambda: nav.start_mode(name)

    return [Button(name, starter(name), SELECT_GAME) for name in names]


def solo_menu(nav: Navigator) -> Menu:
    return submenu(nav, "Solo", _modes(nav, ["Classic", "Basic", "Blitz", "Extreme"]))


def multiplayer_menu(nav: Navigator) -> Menu:
    names = ["Pass It Basic", "Blitz Challenge", "Pass It Extreme", "Head 2 Head"]
    return submenu(nav, "Multiplayer", _modes(nav, names))


def options_menu(nav: Navigator) -> Menu:
    return submenu(nav, "Options", [
        Button("Help", lambda: nav.push(help_menu(nav)), SELECT),
        Button("Settings", lambda: nav.push(settings_menu(nav)), SELECT),
        Button("Credits", lambda: nav.push(text_screen(nav, "Credits", texts.CREDITS)), SELECT),
        Button("About", lambda: nav.push(text_screen(nav, "About", texts.ABOUT)), SELECT),
    ])


def help_menu(nav: Navigator) -> Menu:
    # The original's Overview and Tutorials tabs played no sound.
    return submenu(nav, "Help", [
        Button("Overview", lambda: nav.push(text_screen(nav, "Overview", texts.HELP_OVERVIEW))),
        Button("Tutorials", lambda: nav.not_built("Tutorials")),
    ])


def settings_menu(nav: Navigator) -> Menu:
    s = nav.settings

    def set_commands(i: int) -> None:
        # Settings::commandsBtnPressed: a preview of the chosen kind of command, then the
        # menu music restarts. Silent stopped the menu music instead; it is kept here
        # for reference but is not currently selectable.
        s.commands = SELECTABLE_COMMAND_MODES[i]
        nav.settings_changed()
        if s.commands == "Silent":
            nav.stop_menu_music()
            return
        nav.play("VO_Bop" if s.commands == "VOX" else "SFX_Bop_R")
        nav.start_menu_music()

    def set_banter(i: int) -> None:
        s.banter = i == 0
        nav.settings_changed()
        nav.play(SETTINGS_SELECT)

    def set_shout_it(i: int) -> None:
        s.shout_it = i == 0
        nav.settings_changed()
        nav.play(SETTINGS_SELECT)

    def set_music(v: int) -> None:
        # The live volume change is the only feedback, as in the original.
        s.music_volume = v
        nav.settings_changed()

    def set_sfx(v: int) -> None:
        # Settings::sfxValueChange previews with SFX_Bop_R, except in Silent.
        s.sfx_volume = v
        nav.settings_changed()
        if s.commands != "Silent":
            nav.play("SFX_Bop_R")

    return submenu(nav, "Settings", [
        Choice("Commands", SELECTABLE_COMMAND_MODES,
               lambda: SELECTABLE_COMMAND_MODES.index(s.commands), set_commands),
        Choice("Banter", ON_OFF, lambda: 0 if s.banter else 1, set_banter),
        Choice("Shout It", ON_OFF, lambda: 0 if s.shout_it else 1, set_shout_it),
        Slider("Music", lambda: s.music_volume, set_music),
        Slider("SFX", lambda: s.sfx_volume, set_sfx),
    ])
