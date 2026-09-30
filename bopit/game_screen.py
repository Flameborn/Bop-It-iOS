"""The in-game screen and the solo end screen. They connect the engine to audio and speech."""

import logging
import random
from typing import Protocol

import pygame

from bopit.audio import Audio, Voice
from bopit.config import Settings
from bopit.engine import events as ev
from bopit.engine.game import Game, ModeRules, Options
from bopit.input_map import GAME_SCORE_KEY, game_command_for, key_name_for, menu_nav_for
from bopit.menu import Button, Menu
from bopit.scores import Scores
from bopit.speech import Speech
from bopit.themes import themed

log = logging.getLogger(__name__)

END_HIGH_SCORE_DELAY = 1.0  # SoloEndGame: the high score check comes a second after the scores.


class Host(Protocol):
    speech: Speech
    audio: Audio
    settings: Settings
    scores: Scores

    def replace(self, screen: object) -> None: ...

    def return_to_menu(self) -> None: ...

    def play_themed(self, name: str) -> None: ...


class GameScreen:
    def __init__(self, host: Host, rules: ModeRules, start_now: bool = False,
                 seed: int | None = None) -> None:
        self.title = rules.name
        self._host = host
        self._rules = rules
        s = host.settings
        self._game = Game(rules, Options(s.commands, s.banter, s.theme), random.Random(seed))
        self._music: Voice | None = None
        self._start_now = start_now

    def enter(self, now: float) -> None:
        self._game.prepare(now)
        if self._start_now:
            # Play Again goes straight into the game, as in the original.
            self._game.press("Bop", now)
        self._dispatch()

    def key(self, key: int, now: float) -> None:
        if key == pygame.K_ESCAPE:
            # Temporary until the pause menu is built.
            self._stop_music()
            self._host.return_to_menu()
            return
        if key == GAME_SCORE_KEY:
            # The original showed the score on screen during play.
            g = self._game
            self._host.speech.speak(f"Moves {g.moves}. Points {_grouped(g.total)}.", interrupt=True)
            return
        if self._game.state.name == "HELP":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._game.dismiss_help(now)
                self._dispatch()
            return
        command = game_command_for(key)
        if command is not None:
            log.info("key %s -> %s at %.3f", pygame.key.name(key), command, now)
            self._game.press(command, now)
            self._dispatch()

    def update(self, now: float) -> None:
        self._game.update(now)
        self._dispatch()

    def _dispatch(self) -> None:
        for event in self._game.pop_events():
            log.info("game %s", event)
            self._handle(event)

    def _handle(self, event: ev.Event) -> None:
        audio = self._host.audio
        speech = self._host.speech
        match event:
            case ev.PlaySound(name, pitch):
                audio.play(name, pitch=pitch)
            case ev.MusicStart(name, pitch, position):
                self._stop_music()
                self._music = audio.play(name, pitch=pitch, loop=True, music=True)
                if self._music is not None:
                    self._music.seek(position)
            case ev.MusicSegment(name, pitch):
                audio.play(name, pitch=pitch, music=True)
            case ev.MusicSeek(position):
                if self._music is not None:
                    self._music.seek(position)
            case ev.MusicPitch(pitch):
                if self._music is not None:
                    self._music.set_pitch(pitch)
            case ev.MusicStop():
                self._stop_music()
            case ev.WaitingToStart():
                # The original showed "Bop It to start" on screen.
                speech.speak("Bop it to start.", interrupt=True)
            case ev.HelpNeeded(command):
                # Replaces the original's touch instructions (see docs/DEVIATIONS.md).
                key = key_name_for(command) or "no key"
                speech.speak(f"{command} it. Key: {key}. Press Enter to continue.", interrupt=True)
            case ev.GameOver():
                self._host.replace(EndScreen(self._host, self._rules, event))
            case _:
                pass

    def _stop_music(self) -> None:
        if self._music is not None:
            self._music.stop()
            self._music = None


def _grouped(number: int) -> str:
    return f"{number:,}"


class EndScreen:
    """SoloEndGame for Classic: scores appear with SFX_BonusScore, then a second later
    SFX_HighScore if the previous best was beaten. Then Play Again or Menu."""

    def __init__(self, host: Host, rules: ModeRules, result: ev.GameOver) -> None:
        self.title = "Game over"
        self._host = host
        self._rules = rules
        self._result = result
        self._previous_best = host.scores.add(rules.name, result.total, result.moves)
        self._high_score_due: float | None = None
        self._menu = Menu("Game over", [
            Button("Play again", self._play_again, "SFX_Select"),
            Button("Menu", host.return_to_menu, "SFX_Select"),
        ])

    def enter(self, now: float) -> None:
        r = self._result
        self._host.audio.play("SFX_BonusScore")
        # Classic shows moves and points; its bonus line is blank.
        self._host.speech.speak(
            f"Game over. Moves {r.moves}. Points {_grouped(r.total)}. {self._menu.describe()}",
            interrupt=True, protect=True)
        self._high_score_due = now + END_HIGH_SCORE_DELAY

    def key(self, key: int, now: float) -> None:
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.handle(nav, self._host.speech, self._host.play_themed)

    def update(self, now: float) -> None:
        if self._high_score_due is not None and now >= self._high_score_due:
            self._high_score_due = None
            if self._result.total > self._previous_best:
                self._host.audio.play("SFX_HighScore")
                self._host.speech.speak("New high score.", protect=True)

    def _play_again(self) -> None:
        self._host.replace(GameScreen(self._host, self._rules, start_now=True))
