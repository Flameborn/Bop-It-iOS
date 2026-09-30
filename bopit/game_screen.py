"""The in-game screen and the solo end screen. They connect the engine to audio and speech."""

import logging
import math
import random
from collections.abc import Callable
from typing import Protocol

import pygame

from bopit.audio import Audio, Voice
from bopit.config import Settings
from bopit.engine import events as ev
from bopit.engine.game import Game, ModeRules, Options
from bopit.input_map import GAME_SCORE_KEY, game_command_for, key_name_for, menu_nav_for
from bopit.menu import Button, Menu
from bopit.microphone import Microphone
from bopit.progress import Progress
from bopit.savegame import SavedGame
from bopit.scores import Scores
from bopit.speech import Speech
from bopit.themes import themed

log = logging.getLogger(__name__)

# SoloEndGame timing. The screen animates in (0.5 delay plus UIKit's default 0.2 second
# animation), then waits 0.5 before showing scores.
END_SHOW_DELAY = 1.2
END_BONUS_DELAY = 1.0       # Scores to bonus (or, in Classic, to the feedback wait).
END_TOTAL_DELAY = 0.5       # Bonus to the total's count up.
END_FEEDBACK_DELAY = 1.0    # Count up finished to the high score check.
TALLY_INTERVAL = 1 / 60
# SoloBlitzEndGame: payoff music as the screen finishes sliding in, the time a second
# later, and the high score sound half a second after that.
BLITZ_PAYOFF_DELAY = 0.7
BLITZ_TIME_DELAY = 1.0
BLITZ_HIGH_SCORE_DELAY = 0.5
TALLY_FRACTION = 0.05


class Host(Protocol):
    speech: Speech
    audio: Audio
    settings: Settings
    scores: Scores
    times_called: dict[str, int]
    progress: Progress
    microphone: Microphone
    announced_no_microphone: bool
    saved_game: SavedGame

    def push(self, screen: object) -> None: ...

    def pop(self) -> None: ...

    def replace(self, screen: object) -> None: ...

    def return_to_menu(self) -> None: ...

    def play_themed(self, name: str) -> None: ...


class GameScreen:
    def __init__(self, host: Host, rules: ModeRules, start_now: bool = False,
                 seed: int | None = None, saved: dict | None = None) -> None:
        self.title = rules.name
        self.rules = rules
        self._host = host
        self._rules = rules
        s = host.settings
        self._game = Game(rules, Options(s.commands, s.banter, s.theme, s.shout_it, s.microphone),
                          random.Random(seed), host.times_called)
        self._listening = False
        self._music: Voice | None = None
        self._last_grade: str | None = None
        # The latest voice for each one-shot sound, so the engine can cut one off.
        self._voices: dict[str, Voice] = {}
        self._x_move_pending = False
        self._unlock_message: str | None = None
        self._start_now = start_now
        self._saved = saved
        self._entered = False

    def enter(self, now: float) -> None:
        if self._entered:
            # Back from the pause menu; its Resume already restarted the game.
            return
        self._entered = True
        if self._saved is not None:
            # Bop_ItAppDelegate::startLoadedSavedGame: the saved game comes back paused.
            self._game.load(self._saved, now)
            self._host.push(PauseScreen(self._host, self))
            return
        self._game.prepare(now)
        if self._start_now:
            # Play Again goes straight into the game, as in the original.
            self._game.press("Bop", now)
        self._dispatch()

    def resume(self, now: float) -> None:
        self._game.resume(now)
        self._dispatch()

    def save(self) -> None:
        """PauseMenu::exitButtonPressed saved the game only once a move had been made."""
        if self._game.moves > 0:
            self._host.saved_game.write(self._game.save())

    def key(self, key: int, now: float) -> None:
        if key == pygame.K_ESCAPE:
            if self._game.can_pause:
                self._game.pause(now)
                self._dispatch()
                self._host.push(PauseScreen(self._host, self))
            elif self._game.state.name == "WAITING_TO_START":
                # Nothing to pause yet on "Bop It to start"; leave for the menu.
                self._host.return_to_menu()
            return
        if key == GAME_SCORE_KEY:
            # The original showed the score on screen during play.
            # Points as the original showed them in play: moves plus bonus score.
            g = self._game
            if g.rules.blitz_target is not None:
                # The original showed whole seconds during Blitz.
                seconds = int(g.blitz_elapsed(now))
                self._host.speech.speak(f"Moves {g.moves}. Time {seconds} seconds.", interrupt=True)
                return
            text = f"Moves {g.moves}. Points {_grouped(g.moves + g.bonus)}."
            if self._last_grade is not None:
                text += f" Last move {self._last_grade}."
            self._host.speech.speak(text, interrupt=True)
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
        if self._listening:
            self._game.hear(self._host.microphone.level(), now)
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
                voice = audio.play(name, pitch=pitch)
                if voice is not None:
                    self._voices[name] = voice
            case ev.StopSound(name):
                voice = self._voices.pop(name, None)
                if voice is not None:
                    voice.stop()
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
            case ev.MicListen(listening):
                self._set_listening(listening)
            case ev.XMove():
                # The original showed an X-Move banner; spoken on request with the grade.
                self._x_move_pending = True
            case ev.GameStarted():
                # "Once you start any new game, your saved game is lost."
                self._host.saved_game.remove()
            case ev.WaitingToStart():
                # The original showed "Bop It to start" on screen.
                speech.speak("Bop it to start.", interrupt=True)
            case ev.RhythmGraded(grade):
                # Shown on screen in the original; spoken on request (score key).
                self._last_grade = f"{grade}, X-Move" if self._x_move_pending else grade
                self._x_move_pending = False
            case ev.StreakEarned(kind):
                speech.speak(f"25 {kind} streak.")
            case ev.CommandUnlocked(command):
                # Comes just before the same command's introduction.
                self._unlock_message = self._host.progress.unlock(command)
            case ev.CommandIntroduced(command):
                # A first ever unlock gets the original's message instead.
                speech.speak(self._unlock_message or f"{command} added.")
                self._unlock_message = None
            case ev.HelpNeeded(command):
                # Replaces the original's touch instructions (see docs/DEVIATIONS.md).
                key = key_name_for(command) or "no key"
                speech.speak(f"{command} it. Key: {key}. Press Enter to continue.", interrupt=True)
            case ev.GameOver():
                self._host.replace(EndScreen(self._host, self._rules, event))
            case ev.BlitzFinished():
                self._host.replace(BlitzEndScreen(self._host, self._rules, event))
            case _:
                pass

    def _set_listening(self, listening: bool) -> None:
        mic = self._host.microphone
        if listening and not mic.open():
            if not self._host.announced_no_microphone:
                self._host.announced_no_microphone = True
                self._host.speech.speak("No microphone found. Use the Shout key.")
            return
        self._listening = listening
        if listening:
            mic.start()
        else:
            mic.stop()

    def _stop_music(self) -> None:
        if self._music is not None:
            self._music.stop()
            self._music = None


def _grouped(number: int) -> str:
    return f"{number:,}"


class EndScreen:
    """SoloEndGame. The screen slides in, then the scores appear with sounds on the
    original's schedule (SoloEndGame::doShowScores, showBonusPoints, showTotalScore,
    tallyTotalScore, showFeedback). Each value is spoken as it appears."""

    def __init__(self, host: Host, rules: ModeRules, result: ev.GameOver) -> None:
        self.title = "Game over"
        self._host = host
        self._rules = rules
        self._result = result
        self._previous_best = host.scores.add(rules.name, result.total, result.moves)
        self._timeline: list[tuple[float, Callable[[], None]]] = []
        self._menu = Menu("Game over", [
            Button("Play again", self._play_again, "SFX_Select"),
            Button("Menu", host.return_to_menu, "SFX_Select"),
        ])

    def enter(self, now: float) -> None:
        r = self._result
        speech = self._host.speech
        play = self._host.audio.play
        speech.speak("Game over.", interrupt=True, protect=True)
        t = now + END_SHOW_DELAY

        def scores() -> None:
            play("SFX_BonusScore")
            speech.speak(f"Moves {r.moves}. Points {_grouped(r.moves + r.bonus)}.", protect=True)

        steps: list[tuple[float, Callable[[], None]]] = [(t, scores)]
        if self._rules.rhythm_graded:
            def bonus() -> None:
                play("SFX_BonusScore")
                speech.speak(f"Bonus {_grouped(r.end_bonus)}.", protect=True)

            def total() -> None:
                if r.total == 0:
                    play("SFX_BonusScore")
                else:
                    play("SFX_ScoreAnimation")

            def tallied() -> None:
                speech.speak(f"Points {_grouped(r.total)}.", protect=True)

            tally_at = t + END_BONUS_DELAY + END_TOTAL_DELAY
            tally_end = tally_at + _tally_seconds(r)
            steps += [(t + END_BONUS_DELAY, bonus), (tally_at, total), (tally_end, tallied)]
            feedback_at = tally_end + END_FEEDBACK_DELAY
        else:
            # Classic leaves Bonus blank and goes straight to the feedback.
            feedback_at = t + END_BONUS_DELAY + END_FEEDBACK_DELAY
        steps.append((feedback_at, self._feedback))
        self._timeline = steps

    def key(self, key: int, now: float) -> None:
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.handle(nav, self._host.speech, self._host.play_themed)

    def update(self, now: float) -> None:
        while self._timeline and self._timeline[0][0] <= now:
            _, step = self._timeline.pop(0)
            step()

    def _feedback(self) -> None:
        if self._result.total > self._previous_best:
            self._host.audio.play("SFX_HighScore")
            self._host.speech.speak("New high score.", protect=True)
        self._host.speech.speak(self._menu.describe(), protect=True)

    def _play_again(self) -> None:
        self._host.replace(GameScreen(self._host, self._rules, start_now=True))


class PauseScreen:
    """PauseMenu, top to bottom: Resume, then Menu and Restart side by side, then the
    "game progress saved" label. All three buttons play SFX_Select."""

    def __init__(self, host: Host, game_screen: GameScreen) -> None:
        self.title = "Paused"
        self._host = host
        self._game_screen = game_screen
        self._now = 0.0
        self._menu = Menu("Paused", [
            Button("Resume", self._resume, "SFX_Select"),
            Button("Menu", self._exit, "SFX_Select"),
            Button("Restart", self._restart, "SFX_Select"),
            Button("game progress saved", lambda: None),
        ], on_back=self._resume_from_back)

    def enter(self, now: float) -> None:
        self._now = now
        self._menu.enter(self._host.speech)

    def key(self, key: int, now: float) -> None:
        self._now = now
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.handle(nav, self._host.speech, self._host.play_themed)

    def update(self, now: float) -> None:
        self._now = now

    def _resume(self) -> None:
        self._host.pop()
        self._game_screen.resume(self._now)

    def _resume_from_back(self) -> None:
        # The back key resumes, as pressing the original's pause button again closed the menu.
        self._host.play_themed("SFX_Select")
        self._resume()

    def _exit(self) -> None:
        self._game_screen.save()
        self._host.return_to_menu()

    def _restart(self) -> None:
        # PauseMenu::restartButtonPressed: straight into a new game.
        self._host.pop()
        self._host.replace(GameScreen(self._host, self._game_screen.rules, start_now=True))


class BlitzEndScreen:
    """SoloBlitzEndGame. The screen slides in and the short payoff music plays; a second
    later the time appears; half a second after that, SFX_HighScore for a new best."""

    def __init__(self, host: Host, rules: ModeRules, result: ev.BlitzFinished) -> None:
        self.title = "Finished"
        self._host = host
        self._rules = rules
        self._result = result
        compared = host.scores.add_time(rules.name, result.time)
        self._new_best = result.time < compared or compared == 0
        self._timeline: list[tuple[float, Callable[[], None]]] = []
        self._menu = Menu("Finished", [
            Button("Play again", self._play_again, "SFX_Select"),
            Button("Menu", host.return_to_menu, "SFX_Select"),
        ])

    def enter(self, now: float) -> None:
        speech = self._host.speech
        audio = self._host.audio
        speech.speak("Finished.", interrupt=True, protect=True)
        shown = now + BLITZ_PAYOFF_DELAY

        def payoff() -> None:
            audio.play("MUSIC_PayoffLoopShort", music=True)

        def time_shown() -> None:
            speech.speak(f"Time {self._result.time:.3f} seconds.", protect=True)
            if not self._new_best:
                speech.speak(self._menu.describe(), protect=True)

        def high_score() -> None:
            audio.play("SFX_HighScore")
            speech.speak("New high score.", protect=True)
            speech.speak(self._menu.describe(), protect=True)

        self._timeline = [(shown, payoff), (shown + BLITZ_TIME_DELAY, time_shown)]
        if self._new_best:
            self._timeline.append((shown + BLITZ_TIME_DELAY + BLITZ_HIGH_SCORE_DELAY, high_score))

    def key(self, key: int, now: float) -> None:
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.handle(nav, self._host.speech, self._host.play_themed)

    def update(self, now: float) -> None:
        while self._timeline and self._timeline[0][0] <= now:
            _, step = self._timeline.pop(0)
            step()

    def _play_again(self) -> None:
        self._host.replace(GameScreen(self._host, self._rules, start_now=True))


def _tally_seconds(result: ev.GameOver) -> float:
    """tallyTotalScore adds ceil(5 percent of the remainder) every 1/60 second."""
    remaining = result.moves + result.end_bonus
    if remaining <= 0:
        return 0.0
    step = math.ceil(remaining * TALLY_FRACTION)
    return math.ceil(remaining / step) * TALLY_INTERVAL
