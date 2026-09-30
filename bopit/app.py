"""The pygame window, event loop and screen stack."""

import logging

import pygame

from bopit import screens
from bopit.audio import Audio, Voice
from bopit.config import Settings, save_settings
from bopit.input_map import menu_nav_for
from bopit.menu import Menu
from bopit.speech import Speech
from bopit.themes import themed

log = logging.getLogger(__name__)

FRAMES_PER_SECOND = 60


class App:
    def __init__(self, speech: Speech, audio: Audio, settings: Settings) -> None:
        self.speech = speech
        self.audio = audio
        self.settings = settings
        self._stack: list[Menu] = []
        self._running = False
        self._menu_music: Voice | None = None

    # Navigator

    def push(self, menu: Menu) -> None:
        self._stack.append(menu)
        log.info("Screen: %s", menu.title)
        menu.enter(self.speech)

    def pop(self) -> None:
        if len(self._stack) <= 1:
            return
        self._stack.pop()
        menu = self._stack[-1]
        log.info("Screen: %s", menu.title)
        menu.enter(self.speech)

    def quit(self) -> None:
        log.info("Quit from main menu")
        self._running = False

    def not_built(self, what: str) -> None:
        self.speech.speak(f"{what} is not built yet.", interrupt=True)

    def settings_changed(self) -> None:
        self.audio.set_mix(self.settings.sfx_volume / 100, self.settings.music_volume / 100)
        save_settings(self.settings)

    def play(self, name: str) -> None:
        self.audio.play(name)

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
        self._running = True
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    self._key_down(event)
            self.audio.update()
            clock.tick(FRAMES_PER_SECOND)
        pygame.quit()

    def _key_down(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_F4 and event.mod & pygame.KMOD_ALT:
            self._running = False
            return
        nav = menu_nav_for(event.key)
        if nav is not None:
            self._stack[-1].handle(nav, self.speech, self.play_themed)
