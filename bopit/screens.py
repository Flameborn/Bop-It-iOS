"""The menu screens, in the original's structure. Items are ordered top to bottom by their
on-screen position in the original (see docs/DEVIATIONS.md). Back is on the back key.

Sounds match the original's button handlers: SFX_Select for navigation, SFX_SelectGame
for Play and game modes, SFX_Back for back, SFX_SettingsSelect for Banter and Shout It.
"""

from collections.abc import Callable, Sequence
from typing import Protocol

from bopit import i18n, input_map, port_texts, texts
from bopit.config import (SELECTABLE_COMMAND_MODES, TEXT_SIZE_MAX, TEXT_SIZE_MIN,
                          TEXT_SIZE_STEP, Settings)
from bopit.menu import Button, Choice, Menu, Slider
from bopit.progress import Progress
from bopit.scores import Entry, Scores
from bopit.trophies import all_trophies
from bopit.themes import THEMES
from bopit.tutorials import TUTORIAL_ORDER

ON_OFF = ("On", "Off")
SELECT = "SFX_Select"
SELECT_GAME = "SFX_SelectGame"
BACK = "SFX_Back"
SETTINGS_SELECT = "SFX_SettingsSelect"


class Navigator(Protocol):
    settings: Settings
    scores: Scores
    progress: Progress
    # Blitz Challenge players. The original kept it for the session, starting at 2.
    blitz_players: int

    def push(self, menu: Menu) -> None: ...

    def pop(self) -> None: ...

    def quit(self) -> None: ...

    def not_built(self, what: str) -> None: ...

    def start_mode(self, name: str) -> None: ...

    def play_pressed(self) -> None: ...

    def first_time(self, flag: str) -> bool: ...

    def has_saved_game(self) -> bool: ...

    def return_to_menu(self) -> None: ...

    def leave_game(self) -> None: ...

    def open_tutorial(self, command: str) -> None: ...

    def settings_changed(self) -> None: ...

    def language_changed(self) -> None: ...

    def play(self, name: str) -> None:
        """Play a sound as named, with no theme variant."""
        ...

    def play_themed(self, name: str) -> None: ...

    def speak(self, text: str) -> None: ...

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
        # The original's Play button read "Quick Play", or "Resume Game" with a saved game.
        Button("Resume Game" if nav.has_saved_game() else "Quick Play", nav.play_pressed,
               SELECT_GAME),
        Button("Games", lambda: nav.push(games_menu(nav)), SELECT),
        Button("Options", lambda: nav.push(options_menu(nav)), SELECT),
        Choice("Theme", THEMES, lambda: s.theme, set_theme),
    ], on_back=nav.quit)


def games_menu(nav: Navigator) -> Menu:
    return submenu(nav, "Games", [
        Button("Solo", lambda: open_solo(nav), SELECT),
        Button("Multiplayer", lambda: open_multiplayer(nav), SELECT),
        Button("Trophies", lambda: nav.push(trophies_menu(nav)), SELECT),
        Button("Scores", lambda: nav.push(scores_menu(nav)), SELECT),
    ])


# From English.lproj/Localizable.strings, verbatim except Head 2 Head.
MODE_DESCRIPTIONS = {
    "Classic": "The original game of Bop, Twist and Pull. Just do what it says to stay alive "
               "as it gets faster and faster.",
    "Basic": "The Rhythm Challenge! Get Rhythm Bonus points for completing moves on the beat - "
             "a PERFECT awards the most points. Use X-Moves for additional bonus points.",
    "Extreme": "With as many 6 BopJects on screen at once, even a Bop Master will think this is "
               "Extreme! Get Rhythm Bonus points for completing moves on the beat. Use X-Moves "
               "for additional bonus points.",
    "Blitz": "Complete 20 moves as fast as you can. Just do what it says...only faster!",
    "Pass It Basic": "Play the Basic game with friends. Do what it says, then pass it to the "
                     "next player. See how long the group can stay alive OR play a "
                     "competition, where the last player standing wins!",
    "Pass It Extreme": "Play the Extreme game with friends. Do what it says, then pass it to "
                       "the next player. See how long the group can stay alive OR play a "
                       "competition, where the last player standing wins!",
    # Reworded for keys; the original said "your half of the screen" and "Tap your half of
    # the Bop" (docs/DEVIATIONS.md).
    "Head 2 Head": "Complete the moves on your side of the keyboard. Press your Bop key first "
                   "on the \u201cBop It\u201d command to score a point. Also score when your "
                   "opponent blows it. First player to 7 wins!",
    "Blitz Challenge": "Challenge your friends to a game of Blitz. Take turns to see who can "
                       "handle the pressure and get the fastest time!",
}

# CommandPicker: buttons in the order its createCommands added them to the game.
PICKER_ORDER = ("Twist", "Pull", "Spin", "Flick", "Shout", "Squeeze", "Crank", "Shake",
                "Poke", "Nail", "Brush")
# Commands that must be unlocked (in Basic or Extreme) before they can be picked.
UNLOCKABLE = {"Spin", "Flick", "Shout", "Squeeze", "Crank", "Shake", "Poke", "Nail", "Brush"}
PICKER_HINT = "Add 2-4 BopJects to Bop It"
MAX_PICKED = 4


def picker_menu(nav: Navigator, mode: str, on_go: Callable[[tuple[str, ...]], None]) -> Menu:
    """CommandPicker ("customize game"), top to bottom: GO (top left), the Bop It button,
    which is always on, the eleven commands in rows, then the hint. Toggling on plays
    SFX_SettingsSelect, off SFX_BackButtonOLD; GO plays SFX_Select and needs two picks."""
    s = nav.settings

    def available(command: str) -> bool:
        if command == "Shout" and not s.shout_it:
            return False
        if command == "Poke" and mode == "Head 2 Head":
            return False
        return command not in UNLOCKABLE or command in nav.progress.unlocked

    stored = [c for c in s.picked if available(c)]
    if len(stored) >= 2:
        picked = stored[:MAX_PICKED]
    else:
        # CommandPicker::defaultCommands: Twist and Pull, plus Spin and Flick if unlocked.
        picked = ["Twist", "Pull"] + [c for c in ("Spin", "Flick") if available(c)]

    def toggle(command: str) -> Callable[[], None]:
        def pressed() -> None:
            if not available(command):
                return
            if command in picked:
                picked.remove(command)
                nav.play("SFX_BackButtonOLD")
            elif len(picked) < MAX_PICKED:
                picked.append(command)
                nav.play(SETTINGS_SELECT)
            else:
                # The original did nothing; see docs/DEVIATIONS.md.
                nav.speak(f"{MAX_PICKED} already chosen.")
                return
            nav.speak("on" if command in picked else "off")
        return pressed

    def state(command: str) -> Callable[[], str | None]:
        def current() -> str:
            if not available(command):
                return "locked"
            return "on" if command in picked else "off"
        return current

    def go() -> None:
        if len(picked) < 2:
            return
        nav.play_themed(SELECT)
        order = tuple(c for c in PICKER_ORDER if c in picked)
        s.picked = list(order)
        nav.settings_changed()
        on_go(order)

    items: list[Button | Choice | Slider] = [
        Button("GO", go, get_state=lambda: None if len(picked) >= 2 else "unavailable"),
        Button("Bop It", lambda: None, get_state=lambda: "always on"),
    ]
    # On screen in rows of three, read left to right: Bop It, Twist, Pull; Spin, Flick, Shout;
    # Squeeze, Crank, Shake; Nail, Brush, Poke.
    for command in ("Twist", "Pull", "Spin", "Flick", "Shout", "Squeeze", "Crank", "Shake",
                    "Nail", "Brush", "Poke"):
        items.append(Button(command, toggle(command), get_state=state(command)))
    items.append(Button(PICKER_HINT, lambda: None))
    return Menu("customize game", items, on_back=nav.pop, back_sound=BACK)


MIN_PLAYERS = 2
MAX_PLAYERS = 10


def player_select_menu(nav: Navigator, on_go: Callable[[], None]) -> Menu:
    """mpBlitzPlayerSelect, top to bottom: the player counts 2 to 10 (choosing one made no
    sound), then Back and GO. GO plays SFX_Select, Back SFX_Back."""
    counts = [str(n) for n in range(MIN_PLAYERS, MAX_PLAYERS + 1)]

    def set_players(index: int) -> None:
        nav.blitz_players = MIN_PLAYERS + index

    def go() -> None:
        nav.play_themed(SELECT)
        on_go()

    return Menu("Blitz Challenge players", [
        Choice("Players", counts, lambda: nav.blitz_players - MIN_PLAYERS, set_players),
        Button("GO", go),
    ], on_back=nav.pop, back_sound=BACK)


def high_score_text(mode: str, best: Entry) -> str:
    """As GameModeIntro showed it: moves and points, or for Blitz a time to 4 places."""
    if mode == "Blitz":
        return f"{i18n.tr('High Score')}: {best.score:.4f} seconds"
    return f"{i18n.tr('High Score')}: {best.moves} moves, {int(best.score):,} points"


def intro_menu(nav: Navigator, mode: str, best: Entry | None, on_start: Callable[[], None]) -> Menu:
    """GameModeIntro, top to bottom: description, high score, Start. Multiplayer modes hid
    the high score. Back returns to the main menu without a sound, as in the original."""
    items: list[Button | Choice | Slider] = [Button(MODE_DESCRIPTIONS.get(mode, ""), lambda: None)]
    if best is not None:
        items.append(Button(high_score_text(mode, best), lambda: None))
    items.append(Button("Start", on_start, SELECT))
    # GameModeIntro::backButtonPressed also forgot the mode to return to from a tutorial.
    return Menu(mode, items, on_back=nav.leave_game)


def _modes(nav: Navigator, names: Sequence[str]) -> list[Button | Choice | Slider]:
    """Mode buttons. A tap starts the mode; holding Enter makes it the Quick Play mode."""
    s = nav.settings

    def starter(name: str) -> Callable[[], None]:
        return lambda: nav.start_mode(name)

    def make_default(name: str) -> Callable[[], None]:
        def hold() -> None:
            # SoloGameOptions::setNewDefaultButton plays SFX_SelectGame and saves the mode.
            s.quick_play = name
            nav.settings_changed()
            nav.play_themed(SELECT_GAME)
            # The original marked the button; here the change is spoken.
            nav.speak(f"{name} is now your Quick Play game.")
        return hold

    def state(name: str) -> Callable[[], str | None]:
        return lambda: "Quick Play" if s.quick_play == name else None

    return [Button(name, starter(name), SELECT_GAME, hold=make_default(name), get_state=state(name))
            for name in names]


def _quick_play_hint(nav: Navigator) -> None:
    # The first visit to Solo or Multiplayer, whichever comes first, shows the Quick Play
    # hint (popupForDefaultButton, shared by both screens). Its close button made no sound.
    if nav.first_time("quick_play_hint"):
        nav.push(Menu(QUICK_PLAY_HINT, [Button("Close", nav.pop)], on_back=nav.pop))


def open_solo(nav: Navigator) -> None:
    nav.push(solo_menu(nav))
    _quick_play_hint(nav)


def open_multiplayer(nav: Navigator) -> None:
    nav.push(multiplayer_menu(nav))
    _quick_play_hint(nav)


# The original's popup said "press and hold any game mode button to make it your Quick Play
# game"; the keyboard wording is recorded in docs/DEVIATIONS.md.
QUICK_PLAY_HINT = "Press and hold Enter on any game mode to make it your Quick Play game"



def solo_menu(nav: Navigator) -> Menu:
    return submenu(nav, "Solo", _modes(nav, ["Classic", "Basic", "Blitz", "Extreme"]))


def multiplayer_menu(nav: Navigator) -> Menu:
    names = ["Pass It Basic", "Blitz Challenge", "Pass It Extreme", "Head 2 Head"]
    return submenu(nav, "Multiplayer", _modes(nav, names))


SOLO_MODES = ("Classic", "Basic", "Extreme", "Blitz")
RESET_QUESTION = "Whoa! Are you sure you want to reset your local scores?"


def score_rows(mode: str, entries: Sequence[Entry]) -> list[Button | Choice | Slider]:
    """Scores::localTableView: one row per entry with a nonzero score. The name column
    always read "Me"."""
    rows: list[Button | Choice | Slider] = []
    for entry in entries:
        if int(entry.score) == 0:
            continue
        if mode == "Blitz":
            text = f"Me, {entry.score:.3f} seconds"
        else:
            text = f"Me, {entry.moves} moves, {int(entry.score):,} points"
        rows.append(Button(text, lambda: None))
    if not rows:
        # The original showed an empty table; see docs/DEVIATIONS.md.
        rows.append(Button("No scores", lambda: None))
    return rows


def scores_menu(nav: Navigator) -> Menu:
    """Scores, top to bottom: mode tabs (Classic first), the local list, Reset. The mode
    tabs and Reset made no sound; the online Local, Friends and Global tabs are left out."""
    mode = [0]

    def rebuild() -> None:
        name = SOLO_MODES[mode[0]]
        menu.items = [tabs] + score_rows(name, nav.scores.entries(name)) + [reset]

    def set_mode(index: int) -> None:
        mode[0] = index
        rebuild()

    def confirm_reset() -> None:
        def ok() -> None:
            nav.scores.reset(SOLO_MODES)
            nav.pop()
            rebuild()
        # A UIAlertView with Cancel and OK, in that order.
        nav.push(Menu(RESET_QUESTION, [Button("Cancel", nav.pop), Button("OK", ok)],
                      on_back=nav.pop))

    tabs = Choice("Mode", SOLO_MODES, lambda: mode[0], set_mode)
    reset = Button("Reset", confirm_reset)
    menu = submenu(nav, "Scores", [])
    rebuild()
    return menu


def trophies_menu(nav: Navigator) -> Menu:
    """TrophiesPage: every trophy in the original's order. Earned ones showed their medal;
    the others were drawn locked."""
    earned = nav.progress.trophies

    def row(title: str, medal: str) -> Button:
        state = f"{medal} trophy" if title in earned else "locked"
        return Button(title, lambda: None, get_state=lambda: state)

    items: list[Button | Choice | Slider] = [
        row(t.title, t.medal) for t in all_trophies(nav.settings.shout_it)]
    return submenu(nav, "Trophies", items)


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
        Button("Overview", lambda: nav.push(text_screen(nav, "Overview", port_texts.HELP_OVERVIEW))),
        Button("Tutorials", lambda: nav.push(tutorials_menu(nav))),
        # Our addition: the keys, as this port is played on a keyboard (docs/DEVIATIONS.md).
        Button("Keys", lambda: nav.push(text_screen(nav, "Keys", input_map.describe_bindings()))),
    ])


def tutorials_menu(nav: Navigator) -> Menu:
    """Help's Tutorials tab: all twelve commands, locked or not, row by row as on screen.
    The buttons made no sound."""
    def opener(command: str) -> Callable[[], None]:
        return lambda: nav.open_tutorial(command)
    return Menu("Tutorials", [Button(c, opener(c)) for c in TUTORIAL_ORDER], on_back=nav.pop)


TUTORIAL_POPUP_QUESTION = "Would you like to see the tutorials and try the moves before playing?"
TUTORIAL_POPUP_NOTE = "access tutorials any time in options>help"


def tutorial_popup(nav: Navigator, on_no: Callable[[], None],
                   on_yes: Callable[[], None]) -> Menu:
    """TutorialPopUp, shown once instead of the first game's intro: the question, No (left)
    and Yes (right), then the note. No starts the game at once; Yes opens Help's tutorials.
    Neither made a sound."""
    return Menu(TUTORIAL_POPUP_QUESTION, [
        Button("No", on_no),
        Button("Yes", on_yes),
        Button(TUTORIAL_POPUP_NOTE, lambda: None),
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

    def set_microphone(i: int) -> None:
        # Our addition; it uses the same sound as the original's other toggles.
        s.microphone = i == 0
        nav.settings_changed()
        nav.play(SETTINGS_SELECT)

    codes = tuple(i18n.LANGUAGES)

    def set_language(i: int) -> None:
        # Our addition. Each language is named in its own language.
        s.language = codes[i]
        nav.language_changed()
        nav.play(SETTINGS_SELECT)

    def set_text_size(v: int) -> None:
        # Our addition. Only the picture changes, so there is no sound but the new size spoken.
        s.text_size = v
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
        Choice("Microphone", ON_OFF, lambda: 0 if s.microphone else 1, set_microphone),
        Choice("Language", tuple(i18n.LANGUAGES.values()),
               lambda: codes.index(s.language) if s.language in codes else 0, set_language),
        Slider("Text size", lambda: s.text_size, set_text_size, TEXT_SIZE_STEP, TEXT_SIZE_MIN,
               TEXT_SIZE_MAX, "points"),
    ])
