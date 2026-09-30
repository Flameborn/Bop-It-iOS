"""The pygame window, event loop and screen stack."""

import logging
import time
from typing import Protocol

import pygame

from bopit import screens
from bopit.audio import Audio, Voice
from bopit.config import Settings, save_settings
from bopit.engine.game import BASIC, BLITZ, CLASSIC, EXTREME, ModeRules
from bopit.game_screen import GameScreen
from bopit.input_map import menu_nav_for
from bopit.menu import Menu
from bopit.microphone import Microphone
from bopit.progress import Progress
from bopit.savegame import SavedGame
from bopit.scores import Scores
from bopit.speech import Speech
from bopit.themes import themed

log = logging.getLogger(__name__)

# Keys are timestamped when the loop sees them, so a faster loop means fairer timing.
FRAMES_PER_SECOND = 120
MODES: dict[str, ModeRules] = {"Classic": CLASSIC, "Basic": BASIC, "Extreme": EXTREME,
                               "Blitz": BLITZ}


class Screen(Protocol):
    title: str

    def enter(self, now: float) -> None: ...

    def key(self, key: int, now: float) -> None: ...

    def update(self, now: float) -> None: ...


class MenuScreen:
    """Runs a speech menu as a screen."""

    def __init__(self, app: "App", menu: Menu) -> None:
        self.title = menu.title
        self._app = app
        self._menu = menu

    def enter(self, now: float) -> None:
        self._menu.enter(self._app.speech)

    def key(self, key: int, now: float) -> None:
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.handle(nav, self._app.speech, self._app.play_themed, now)

    def key_up(self, key: int, now: float) -> None:
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.release(nav, self._app.play_themed, now)

    def update(self, now: float) -> None:
        self._menu.update(now)


class App:
    def __init__(self, speech: Speech, audio: Audio, settings: Settings) -> None:
        self.speech = speech
        self.audio = audio
        self.settings = settings
        self.scores = Scores()
        self.progress = Progress()
        self.microphone = Microphone()
        self.saved_game = SavedGame()
        self.announced_no_microphone = False
        self._stack: list[Screen] = []
        self._running = False
        self._menu_music: Voice | None = None
        # How often each command has been called. The original kept this on its Command
        # objects, which lived across games until the command list was rebuilt.
        self.times_called: dict[str, int] = {}
        self._commands_key = (settings.theme, settings.shout_it)

    # Navigation

    def push(self, screen: Menu | Screen) -> None:
        self._stack.append(self._as_screen(screen))
        self._enter_top()

    def replace(self, screen: Menu | Screen) -> None:
        self._stack[-1] = self._as_screen(screen)
        self._enter_top()

    def pop(self) -> None:
        if len(self._stack) <= 1:
            return
        self._stack.pop()
        self._enter_top()

    def return_to_menu(self) -> None:
        """GameController::returnToMenu: back to the main menu with the menu music."""
        del self._stack[1:]
        # Rebuilt so the Play item shows Quick Play or Resume Game correctly.
        self._stack[0] = self._as_screen(screens.main_menu(self))
        self.start_menu_music()
        self._enter_top()

    def first_time(self, flag: str) -> bool:
        return self.progress.first_time(flag)

    def has_saved_game(self) -> bool:
        return self.saved_game.exists()

    def play_pressed(self) -> None:
        """LandingPage::executePlayButtonPressed: resume a saved game, else Quick Play."""
        saved = self.saved_game.take()
        if saved is not None and saved.get("mode") in MODES:
            self.stop_menu_music()
            self.push(GameScreen(self, MODES[saved["mode"]], saved=saved))
            return
        self.start_mode(self.settings.quick_play)

    def quit(self) -> None:
        log.info("Quit from main menu")
        self._running = False

    def not_built(self, what: str) -> None:
        self.speech.speak(f"{what} is not built yet.", interrupt=True)

    def start_mode(self, name: str) -> None:
        rules = MODES.get(name)
        if rules is None:
            self.not_built(name)
            return
        # Choosing a mode stops the menu music (GameController::init).
        self.stop_menu_music()
        self.push(screens.intro_menu(self, rules.name, self.scores.best(rules.name),
                                     lambda: self.replace(GameScreen(self, rules))))

    # Settings and sound

    def settings_changed(self) -> None:
        self.audio.set_mix(self.settings.sfx_volume / 100, self.settings.music_volume / 100)
        # The original rebuilt its commands (GameSettings::createCommands) on a theme or
        # Shout It change, which reset their call counts.
        key = (self.settings.theme, self.settings.shout_it)
        if key != self._commands_key:
            self._commands_key = key
            self.times_called.clear()
        save_settings(self.settings)

    def play(self, name: str) -> None:
        self.audio.play(name)

    def speak(self, text: str) -> None:
        self.speech.speak(text, interrupt=True)

    def play_themed(self, name: str) -> None:
        """For sounds the original passed through GetSkinFilename, like menu buttons."""
        self.audio.play(themed(name, self.settings.theme))

    def start_menu_music(self) -> None:
        if self._menu_music is not None and self._menu_music.playing:
            return
        self._menu_music = self.audio.play(
            themed("MUSIC_MenuMusic", self.settings.theme), loop=True, music=True)

    def stop_menu_music(self) -> None:
        if self._menu_music is not None:
            self._menu_music.stop()
            self._menu_music = None

    # Loop

    def run(self) -> None:
        pygame.init()
        pygame.display.set_mode((320, 480))
        pygame.display.set_caption("Bop It")
        clock = pygame.time.Clock()
        self.settings_changed()
        # The original starts the menu music at launch whatever the Commands setting.
        self.start_menu_music()
        self.push(screens.main_menu(self))
        if self.saved_game.exists():
            # Bop_ItAppDelegate::doFinishLaunching: a saved game resumes at launch, paused.
            self.play_pressed()
        self._running = True
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    self._key_down(event, time.perf_counter())
                elif event.type == pygame.KEYUP:
                    key_up = getattr(self._stack[-1], "key_up", None)
                    if key_up is not None:
                        key_up(event.key, time.perf_counter())
            self._stack[-1].update(time.perf_counter())
            self.audio.update()
            clock.tick(FRAMES_PER_SECOND)
        self.microphone.close()
        pygame.quit()

    def _key_down(self, event: pygame.event.Event, now: float) -> None:
        if event.key == pygame.K_F4 and event.mod & pygame.KMOD_ALT:
            self._running = False
            return
        self._stack[-1].key(event.key, now)

    def _as_screen(self, screen: Menu | Screen) -> Screen:
        return MenuScreen(self, screen) if isinstance(screen, Menu) else screen

    def _enter_top(self) -> None:
        screen = self._stack[-1]
        log.info("Screen: %s", screen.title)
        screen.enter(time.perf_counter())
