"""The in-game screen and the solo end screen. They connect the engine to audio and speech."""

import logging
import math
import random
from collections.abc import Callable
from typing import Protocol

import pygame

from bopit.audio import Audio, Voice
from bopit.config import Settings
from bopit.debug.autoplay import Action, Bot
from bopit.debug.event_log import EventLog
from bopit.debug.options import DebugOptions
from bopit.engine import events as ev
from bopit.engine.game import PLAYER_NAMES, Game, ModeRules, Options
from bopit.input_map import (GAME_SCORE_KEY, H2H_SCORE_KEY, game_command_for, h2h_key_name,
                             h2h_slot_for, key_name_for, menu_nav_for)
from bopit.menu import Button, Menu
from bopit.microphone import Microphone
from bopit.progress import Progress
from bopit.savegame import SavedGame
from bopit.tips import Tips
from bopit.trophies import all_trophies, newly_earned
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
BLITZ_TIP_DELAY = 0.5
PASS_IT_SCORES_DELAY = 1.0  # MPPassitEndGame::viewDidLoad
# displayMPBlitzHEndGame: the results fade in over a second after a 2 second delay.
CHALLENGE_RESULTS_DELAY = 2.0
CHALLENGE_RANKED = 3        # MPBlitzEndGame shows the top three.
# Head 2 Head: the winner shows at once, MUSIC_PayoffLoop half a second later, and the
# results fade in over a second after 2 seconds; their buttons work after 0.4 seconds.
H2H_PAYOFF_DELAY = 0.5
H2H_RESULTS_DELAY = 2.0
H2H_BUTTONS_DELAY = 0.4
# handleNewTrophy: the trophy appears after a 1.5 second delay and a 1 second animation.
TROPHY_DELAY = 2.5
BOT_BREAK_DELAY = 3.0       # Debug mode: time to hear the break screen before Next.
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
    tips: Tips
    blitz_players: int
    # Debug mode (--debug); None in normal play.
    debug: DebugOptions | None
    event_log: EventLog | None

    def open_trophies(self) -> None: ...

    def push(self, screen: object) -> None: ...

    def pop(self) -> None: ...

    def replace(self, screen: object) -> None: ...

    def return_to_menu(self) -> None: ...

    def play_themed(self, name: str) -> None: ...


class GameScreen:
    def __init__(self, host: Host, rules: ModeRules, start_now: bool = False,
                 seed: int | None = None, saved: dict | None = None,
                 picked: tuple[str, ...] = (), wins: tuple[int, int] = (0, 0)) -> None:
        self.title = rules.name
        self.rules = rules
        self.picked = tuple(saved.get("picked", ())) if saved is not None else picked
        self._host = host
        self._rules = rules
        s = host.settings
        self._debug: DebugOptions | None = getattr(host, "debug", None)
        self._log: EventLog | None = getattr(host, "event_log", None)
        if self._debug is not None and seed is None:
            # A fixed seed if given; otherwise a logged one, so any run can be repeated.
            seed = self._debug.seed if self._debug.seed is not None else random.randrange(10**6)
        self.seed = seed
        self._bot = Bot(self._debug) if self._debug is not None and self._debug.bot else None
        self._game = Game(rules, Options(s.commands, s.banter, s.theme, s.shout_it, s.microphone,
                                         self.picked, getattr(host, "blitz_players", 2)),
                          random.Random(seed), host.times_called)
        # Head 2 Head's wins carry over to Play Again, as the mode object did.
        self._game.total_wins = list(wins)
        self._listening = False
        self._music: Voice | None = None
        self._last_grade: str | None = None
        # The latest voice for each one-shot sound, so the engine can cut one off.
        self._voices: dict[str, Voice] = {}
        self._x_move_pending = False
        self._new_trophy = False
        self._unlock_message: str | None = None
        self._start_now = start_now
        self._saved = saved
        self._entered = False

    def enter(self, now: float) -> None:
        if self._entered:
            # Back from the pause menu; its Resume already restarted the game.
            return
        self._entered = True
        if self._log is not None:
            d = self._debug
            bot = (f"bot reaction {d.reaction:.3f}, failure {d.failure.value} every "
                   f"{d.fail_every} turns" if d is not None and d.bot else "no bot")
            self._log.line(now, f"game screen: {self._rules.name}, seed {self.seed}, {bot}")
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

    @property
    def wins(self) -> tuple[int, int]:
        return (self._game.total_wins[0], self._game.total_wins[1])

    def resume(self, now: float) -> None:
        self._game.resume(now)
        self._dispatch()

    def next_player(self, now: float) -> None:
        self._game.next_player(now)
        self._dispatch()

    def save(self) -> None:
        """PauseMenu::exitButtonPressed saved the game only once a move had been made."""
        if self._game.moves > 0:
            data = self._game.save()
            data["picked"] = list(self.picked)
            self._host.saved_game.write(data)

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
        if self._rules.head_to_head:
            self._h2h_key(key, now)
            return
        if key == GAME_SCORE_KEY:
            # The original showed the score on screen during play.
            # Points as the original showed them in play: moves plus bonus score.
            g = self._game
            if g.rules.pass_it:
                # Multiplayer showed only the moves (displayMPScore).
                self._host.speech.speak(f"Moves {g.moves}.", interrupt=True)
                return
            if g.rules.challenge_target is not None:
                seconds = int(g.blitz_elapsed(now))
                self._host.speech.speak(
                    f"Player {g.current_player + 1}. Moves {g.moves}. Time {seconds} seconds.",
                    interrupt=True)
                return
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

    def _h2h_key(self, key: int, now: float) -> None:
        g = self._game
        if key == H2H_SCORE_KEY:
            # The original showed both points on screen during play.
            self._host.speech.speak(self._h2h_score_text(), interrupt=True)
            return
        slot = h2h_slot_for(key)
        if slot is None:
            return
        player, index = slot
        if index is None:
            command = "Bop"
        else:
            owned = g.commands_of(player)
            if index >= len(owned):
                return
            command = owned[index]
        log.info("key %s -> %s %s at %.3f", pygame.key.name(key), PLAYER_NAMES[player],
                 command, now)
        g.press_by(player, command, now)
        self._dispatch()

    def _h2h_score_text(self) -> str:
        scores = self._game.h2h_scores
        return f"{PLAYER_NAMES[0]} {scores[0]}, {PLAYER_NAMES[1]} {scores[1]}."

    def _h2h_keys_text(self) -> str:
        """Which key does what for each player. Our addition, as the keys are ours."""
        parts = []
        for player, name in enumerate(PLAYER_NAMES):
            keys = [f"Bop on {h2h_key_name(player, None)}"]
            keys += [f"{command} on {h2h_key_name(player, i)}"
                     for i, command in enumerate(self._game.commands_of(player))]
            parts.append(f"{name}: " + ", ".join(keys) + ".")
        return " ".join(parts)

    def update(self, now: float) -> None:
        if self._bot is not None:
            # Each bot action runs at its own planned time, not at the frame's.
            while (action := self._bot.due(now)) is not None:
                self._game.update(action.at)
                self._dispatch()
                self._perform(action)
                self._dispatch()
        self._game.update(now)
        if self._listening:
            self._game.hear(self._host.microphone.level(), now)
        self._dispatch()

    def next_player_ready(self) -> bool:
        """Debug mode: the bot presses Next on the Blitz Challenge break screen itself."""
        return self._bot is not None

    def _perform(self, action: Action) -> None:
        g = self._game
        state = g.state.name
        if action.kind == "start":
            if state == "WAITING_TO_START":
                self._bot_press(action)
        elif action.kind == "help":
            if state == "HELP":
                self._log_line(action.at, "bot: dismisses help")
                g.dismiss_help(action.at)
        elif action.note != "late" and (state != "IN_TURN"
                                        or g.turn_opened_at != action.turn_opened):
            # Planned for a turn that a pause cancelled.
            self._log_line(action.at, f"bot: drops its press of {action.command}")
        else:
            self._bot_press(action)

    def _bot_press(self, action: Action) -> None:
        who = f"{PLAYER_NAMES[action.player]} " if action.player is not None else ""
        note = f" ({action.note})" if action.note else ""
        self._log_line(action.at, f"bot: {who}presses {action.command}{note}")
        if action.player is not None:
            self._game.press_by(action.player, action.command, action.at)
        else:
            self._game.press(action.command, action.at)

    def _log_line(self, when: float, text: str) -> None:
        if self._log is not None:
            self._log.line(when, text)

    def _dispatch(self) -> None:
        for when, event in self._game.pop_timed_events():
            log.info("game %s", event)
            if self._log is not None:
                self._log.event(when, event)
            if self._bot is not None:
                self._bot.plan(when, event, self._game)
            self._handle(event)

    def _handle(self, event: ev.Event) -> None:
        audio = self._host.audio
        speech = self._host.speech
        match event:
            case ev.PlaySound(name, pitch, position, pan):
                voice = audio.play(name, pitch=pitch, pan=pan)
                if voice is not None:
                    if position:
                        voice.seek(position)
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
                voice = audio.play(name, pitch=pitch, music=True)
                if voice is not None:
                    self._voices[name] = voice
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
            case ev.WaitingToStart() if self._rules.head_to_head:
                speech.speak(self._h2h_keys_text() + " Bop it to start.", interrupt=True)
            case ev.WaitingToStart():
                # The original showed "Bop It to start" on screen.
                speech.speak("Bop it to start.", interrupt=True)
            case ev.PointScored(player, scores):
                # The original animated the scorer's points; see docs/DEVIATIONS.md.
                speech.speak(f"{PLAYER_NAMES[player]} {scores[player]}.", interrupt=True)
            case ev.HeadToHeadWon():
                self._host.replace(HeadToHeadEndScreen(self._host, self._rules, event,
                                                       self.picked))
            case ev.RhythmGraded(grade):
                # Shown on screen in the original; spoken on request (score key).
                self._last_grade = f"{grade}, X-Move" if self._x_move_pending else grade
                self._x_move_pending = False
            case ev.StreakEarned(kind):
                speech.speak(f"25 {kind} streak.")
            case ev.CommandUnlocked(command):
                # Comes just before the same command's introduction. A first unlock is also
                # that BopJect's trophy.
                self._unlock_message = self._host.progress.unlock(command)
                if self._unlock_message is not None:
                    self._new_trophy = True
            case ev.CommandIntroduced(command):
                # A first ever unlock gets the original's message instead.
                speech.speak(self._unlock_message or f"{command} added.")
                self._unlock_message = None
            case ev.HelpNeeded(command):
                # Replaces the original's touch instructions (see docs/DEVIATIONS.md).
                key = key_name_for(command) or "no key"
                speech.speak(f"{command} it. Key: {key}. Press Enter to continue.", interrupt=True)
            case ev.MoveMade(command, _, True) if (self._rules.tracks_trophies
                                                  and self._rules.blitz_target is None):
                # Classic, Basic and Extreme count lifetime moves (their winTurn); Blitz does not.
                self._host.progress.hit(command)
            case ev.ScoreChanged() if (self._rules.tracks_trophies
                                       and self._rules.blitz_target is None):
                self._check_trophies()
            case ev.GameOver() if self._rules.pass_it:
                self._host.replace(PassItEndScreen(self._host, self._rules, event, self.picked))
            case ev.GameOver():
                # failDone saved the move history.
                self._host.progress.save()
                self._host.replace(EndScreen(self._host, self._rules, event, self._new_trophy))
            case ev.ChallengeBreak(player, time):
                self._host.push(ChallengeBreakScreen(self._host, self, player, time))
            case ev.ChallengeFinished(times):
                self._host.replace(ChallengeEndScreen(self._host, self._rules, times))
            case ev.BlitzFinished():
                # winBlitz checks trophies once, at the finish.
                self._check_trophies(event.time)
                self._host.replace(BlitzEndScreen(self._host, self._rules, event, self._new_trophy))
            case _:
                pass

    def _check_trophies(self, blitz_time: float | None = None) -> None:
        """TrophyManager::checkForTrophySuccess. The original flashed a "new trophy" image."""
        g = self._game
        progress = self._host.progress
        found = newly_earned(all_trophies(self._host.settings.shout_it), progress.trophies,
                             g.moves, g.x_moves, progress.hits, blitz_time)
        if found:
            progress.earn([t.title for t in found])
            self._new_trophy = True
            self._host.speech.speak("New trophy.")

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


class _Timeline:
    """Steps that run at set times, in order; steps may add later steps. When the last step
    has run, the end screen's menu is announced."""

    def __init__(self) -> None:
        self._steps: list[tuple[float, Callable[[], None]]] = []
        self.now = 0.0

    def at(self, when: float, step: Callable[[], None]) -> None:
        self._steps.append((when, step))
        self._steps.sort(key=lambda s: s[0])

    def run(self, now: float) -> bool:
        """Run what is due. True once everything has run."""
        self.now = now
        while self._steps and self._steps[0][0] <= now:
            _, step = self._steps.pop(0)
            step()
        return not self._steps


class _EndScreenBase:
    def __init__(self, host: Host, rules: ModeRules, title: str, new_trophy: bool) -> None:
        self.title = title
        self._host = host
        self._rules = rules
        self._new_trophy = new_trophy
        self._timeline = _Timeline()
        self._announced = False
        self._menu = Menu(title, [
            Button("Play again", self._play_again, "SFX_Select"),
            Button("Menu", host.return_to_menu, "SFX_Select"),
        ])

    def key(self, key: int, now: float) -> None:
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.handle(nav, self._host.speech, self._host.play_themed)

    def update(self, now: float) -> None:
        if self._timeline.run(now) and not self._announced:
            self._announced = True
            self._host.speech.speak(self._menu.describe(), protect=True)

    def _show_trophy(self) -> None:
        """displayTrophy: SFX_HighScore, the trophy, and its button to the Trophies page, which
        sits above Play Again on screen. The original named no trophy here."""
        self._host.audio.play("SFX_HighScore")
        self._host.speech.speak("New trophy.", protect=True)
        # The trophies button made no sound (trophiesButtonPress).
        self._menu.items.insert(0, Button("Trophies", self._host.open_trophies))

    def _show_tip(self) -> None:
        tip = self._host.tips.maybe_tip()
        if tip is not None:
            self._host.speech.speak(tip, protect=True)

    def _play_again(self) -> None:
        self._host.replace(GameScreen(self._host, self._rules, start_now=True))


class EndScreen(_EndScreenBase):
    """SoloEndGame. The screen slides in, then the scores appear with sounds on the
    original's schedule (SoloEndGame::doShowScores, showBonusPoints, showTotalScore,
    tallyTotalScore, showFeedback, handleNewTrophy). Each value is spoken as it appears."""

    def __init__(self, host: Host, rules: ModeRules, result: ev.GameOver, new_trophy: bool) -> None:
        super().__init__(host, rules, "Game over", new_trophy)
        self._result = result
        self._previous_best = host.scores.add(rules.name, result.total, result.moves)
        self._new_best = result.total > self._previous_best

    def enter(self, now: float) -> None:
        r = self._result
        speech = self._host.speech
        play = self._host.audio.play
        speech.speak("Game over.", interrupt=True, protect=True)
        t = now + END_SHOW_DELAY

        def scores() -> None:
            play("SFX_BonusScore")
            speech.speak(f"Moves {r.moves}. Points {_grouped(r.moves + r.bonus)}.", protect=True)
            # doShowScores: without a new best, a trophy shows now (after its animation).
            if not self._new_best and self._new_trophy:
                self._timeline.at(self._timeline.now + TROPHY_DELAY, self._show_trophy)

        self._timeline.at(t, scores)
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
            self._timeline.at(t + END_BONUS_DELAY, bonus)
            self._timeline.at(tally_at, total)
            self._timeline.at(tally_end, tallied)
            feedback_at = tally_end + END_FEEDBACK_DELAY
        else:
            # Classic leaves Bonus blank and goes straight to the feedback.
            feedback_at = t + END_BONUS_DELAY + END_FEEDBACK_DELAY
        self._timeline.at(feedback_at, self._feedback)

    def _feedback(self) -> None:
        """showFeedback: a new best gets SFX_HighScore and then any trophy; otherwise, with
        no trophy, a tip may be shown."""
        if self._new_best:
            self._host.audio.play("SFX_HighScore")
            self._host.speech.speak("New high score.", protect=True)
            if self._new_trophy:
                self._timeline.at(self._timeline.now + TROPHY_DELAY, self._show_trophy)
        elif not self._new_trophy:
            self._show_tip()


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
        # returnToMenu saved the move history.
        self._host.progress.save()
        self._host.return_to_menu()

    def _restart(self) -> None:
        # PauseMenu::restartButtonPressed: straight into a new game.
        self._host.pop()
        self._host.replace(GameScreen(self._host, self._game_screen.rules, start_now=True,
                                      picked=self._game_screen.picked,
                                      wins=self._game_screen.wins))


class PassItEndScreen:
    """MPPassitEndGame: a second after it appears, SFX_BonusScore and the group's moves.
    Nothing is saved (its saveMoves was empty). Play Again and Menu play SFX_Select."""

    def __init__(self, host: Host, rules: ModeRules, result: ev.GameOver,
                 picked: tuple[str, ...]) -> None:
        self.title = "Game over"
        self._host = host
        self._rules = rules
        self._result = result
        self._picked = picked
        self._timeline = _Timeline()
        self._announced = False
        self._menu = Menu("Game over", [
            Button("Play again", self._play_again, "SFX_Select"),
            Button("Menu", host.return_to_menu, "SFX_Select"),
        ])

    def enter(self, now: float) -> None:
        self._host.speech.speak("Game over.", interrupt=True, protect=True)

        def moves() -> None:
            self._host.audio.play("SFX_BonusScore")
            self._host.speech.speak(f"Moves {self._result.moves}.", protect=True)

        self._timeline.at(now + PASS_IT_SCORES_DELAY, moves)

    def key(self, key: int, now: float) -> None:
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.handle(nav, self._host.speech, self._host.play_themed)

    def update(self, now: float) -> None:
        if self._timeline.run(now) and not self._announced:
            self._announced = True
            self._host.speech.speak(self._menu.describe(), protect=True)

    def _play_again(self) -> None:
        self._host.replace(GameScreen(self._host, self._rules, start_now=True, picked=self._picked))


class BlitzEndScreen(_EndScreenBase):
    """SoloBlitzEndGame. The screen slides in and the short payoff music plays; a second
    later the time appears; half a second after that, SFX_HighScore for a new best. Then a
    trophy (after its animation) or a tip, as SoloBlitzEndGame::doShowScores decides."""

    def __init__(self, host: Host, rules: ModeRules, result: ev.BlitzFinished,
                 new_trophy: bool) -> None:
        super().__init__(host, rules, "Finished", new_trophy)
        self._result = result
        self._compared = host.scores.add_time(rules.name, result.time)
        self._new_best = result.time < self._compared or self._compared == 0

    def enter(self, now: float) -> None:
        speech = self._host.speech
        audio = self._host.audio
        speech.speak("Finished.", interrupt=True, protect=True)
        shown = now + BLITZ_PAYOFF_DELAY
        time_at = shown + BLITZ_TIME_DELAY

        def payoff() -> None:
            audio.play("MUSIC_PayoffLoopShort", music=True)

        def time_shown() -> None:
            speech.speak(f"Time {self._result.time:.3f} seconds.", protect=True)

        def high_score() -> None:
            audio.play("SFX_HighScore")
            speech.speak("New high score.", protect=True)

        self._timeline.at(shown, payoff)
        self._timeline.at(time_at, time_shown)
        if self._new_best:
            self._timeline.at(time_at + BLITZ_HIGH_SCORE_DELAY, high_score)
        if self._compared <= self._result.time or self._compared == 0 or self._new_trophy:
            if self._new_trophy:
                self._timeline.at(time_at + TROPHY_DELAY, self._show_trophy)
            else:
                self._timeline.at(time_at + BLITZ_TIP_DELAY, self._show_tip)


class ChallengeBreakScreen:
    """MPBlitzBreak: MUSIC_PayoffLoopShort, "Player N Time" and the time, and a GO button
    (labelled "next") shown at once. GO plays SFX_Select and the next player starts 1.1
    seconds later."""

    def __init__(self, host: Host, game_screen: GameScreen, player: int, time: float) -> None:
        self.title = "Break"
        self._host = host
        self._game_screen = game_screen
        self._player = player
        self._time = time
        self._now = 0.0
        self._entered_at = 0.0
        self._menu = Menu("Break", [Button("Next", self._go, "SFX_Select")])

    def enter(self, now: float) -> None:
        self._now = now
        self._entered_at = now
        self._host.audio.play("MUSIC_PayoffLoopShort", music=True)
        self._host.speech.speak(f"Player {self._player} time, {self._time:.3f} seconds.",
                                interrupt=True, protect=True)
        self._host.speech.speak(self._menu.describe(), protect=True)

    def key(self, key: int, now: float) -> None:
        self._now = now
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.handle(nav, self._host.speech, self._host.play_themed)

    def update(self, now: float) -> None:
        self._now = now
        if (self._game_screen.next_player_ready()
                and now >= self._entered_at + BOT_BREAK_DELAY):
            self._go()
            return
        self._game_screen.update(now)

    def _go(self) -> None:
        self._host.pop()
        self._game_screen.next_player(self._now)


class HeadToHeadEndScreen:
    """showH2HWinner and MPH2HEndGame: "Green wins" or "Blue wins" at once, MUSIC_PayoffLoop
    half a second later, then the results fade in with each player's total wins. Menu (left)
    and Play Again (right) play SFX_Select and work 0.4 seconds after the game ends."""

    def __init__(self, host: Host, rules: ModeRules, result: ev.HeadToHeadWon,
                 picked: tuple[str, ...]) -> None:
        self.title = "Winner"
        self._host = host
        self._rules = rules
        self._result = result
        self._picked = picked
        self._timeline = _Timeline()
        self._announced = False
        self._buttons_at = 0.0
        self._menu = Menu("Winner", [
            Button("Menu", host.return_to_menu, "SFX_Select"),
            Button("Play again", self._play_again, "SFX_Select"),
        ])

    def enter(self, now: float) -> None:
        r = self._result
        speech = self._host.speech
        speech.speak(f"{PLAYER_NAMES[r.player]} wins, {r.scores[r.player]} to "
                     f"{r.scores[1 - r.player]}.", interrupt=True, protect=True)
        self._buttons_at = now + H2H_BUTTONS_DELAY

        def payoff() -> None:
            self._host.audio.play("MUSIC_PayoffLoop", music=True)

        def results() -> None:
            speech.speak(f"Wins: {PLAYER_NAMES[0]} {r.wins[0]}, {PLAYER_NAMES[1]} {r.wins[1]}.",
                         protect=True)

        self._timeline.at(now + H2H_PAYOFF_DELAY, payoff)
        self._timeline.at(now + H2H_RESULTS_DELAY, results)

    def key(self, key: int, now: float) -> None:
        nav = menu_nav_for(key)
        if nav is None:
            return
        if nav.name == "SELECT" and now < self._buttons_at:
            return
        self._menu.handle(nav, self._host.speech, self._host.play_themed)

    def update(self, now: float) -> None:
        if self._timeline.run(now) and not self._announced:
            self._announced = True
            self._host.speech.speak(self._menu.describe(), protect=True)

    def _play_again(self) -> None:
        # playAgainButtonPressed: straight into a new game; the wins carry on.
        self._host.replace(GameScreen(self._host, self._rules, start_now=True,
                                      picked=self._picked, wins=self._result.wins))


def challenge_ranking(times: tuple[float, ...]) -> list[tuple[int, float]]:
    """MPBlitzEndGame::sortPlayers: fastest first. Each time is matched back to the first
    player with that time, so tied players would show the same number, as in the original."""
    return [(times.index(t) + 1, t) for t in sorted(times)]


class ChallengeEndScreen:
    """MPBlitzEndGame: MUSIC_PayoffLoop plays as the screen fades in after 2 seconds,
    showing "Player N wins" and the top three players with their times. Nothing is saved.
    Menu and Play Again sit side by side, Menu on the left; both play SFX_Select."""

    def __init__(self, host: Host, rules: ModeRules, times: tuple[float, ...]) -> None:
        self.title = "Results"
        self._host = host
        self._rules = rules
        self._ranking = challenge_ranking(times)
        self._timeline = _Timeline()
        self._announced = False
        self._menu = Menu("Results", [
            Button("Menu", host.return_to_menu, "SFX_Select"),
            Button("Play again", self._play_again, "SFX_Select"),
        ])

    def enter(self, now: float) -> None:
        self._host.audio.play("MUSIC_PayoffLoop", music=True)

        def results() -> None:
            winner = self._ranking[0][0]
            rows = " ".join(f"Player {player}, {time:.3f} seconds."
                            for player, time in self._ranking[:CHALLENGE_RANKED])
            self._host.speech.speak(f"Player {winner} wins. {rows}", interrupt=True, protect=True)

        self._timeline.at(now + CHALLENGE_RESULTS_DELAY, results)

    def key(self, key: int, now: float) -> None:
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.handle(nav, self._host.speech, self._host.play_themed)

    def update(self, now: float) -> None:
        if self._timeline.run(now) and not self._announced:
            self._announced = True
            self._host.speech.speak(self._menu.describe(), protect=True)

    def _play_again(self) -> None:
        # playAgainButtonPressed: straight into a new game with the same players.
        self._host.replace(GameScreen(self._host, self._rules, start_now=True))


def _tally_seconds(result: ev.GameOver) -> float:
    """tallyTotalScore adds ceil(5 percent of the remainder) every 1/60 second."""
    remaining = result.moves + result.end_bonus
    if remaining <= 0:
        return 0.0
    step = math.ceil(remaining * TALLY_FRACTION)
    return math.ceil(remaining / step) * TALLY_INTERVAL
