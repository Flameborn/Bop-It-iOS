"""One game of Bop It, following the original's GameController.

Time is passed in explicitly, in seconds. Scheduled steps run at their exact due time, not
at whenever update() happens to be called, so runs are reproducible. Every "per pitch"
delay is divided by the current pitch: that is how the original speeds up.
See docs/ORIGINAL_BEHAVIOR.md, section Game engine.
"""

import heapq
import itertools
import random
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto

from bopit.engine import events as ev
from bopit.engine.banter import Banter
from bopit.engine.commands import callout_sound, response_sound
from bopit.themes import themed

BEAT = 0.81                 # Callout to turn start, and success to next turn (per pitch).
TURN_TIMEOUT = 1.1          # Time allowed for a move (per pitch).
LOOP_OFFSET = 1.62          # Where the music loop jumps to on each success.
BASE_BONUS_START = 100
BASE_BONUS_STEP = 5
FAIL_STEP = 1.0             # Die line to banter, and banter to game over. Not per pitch.
HELP_CALL_LIMIT = 2         # Failing a command called this many times or fewer shows help.
SPEED_UPS_PER_TRACK = 3
MUSIC_TRACKS = ("MUSIC_GameLoop_01a", "MUSIC_GameLoop_01b", "MUSIC_GameLoop_02a",
                "MUSIC_GameLoop_02b", "MUSIC_GameLoop_03a", "MUSIC_GameLoop_03b")
DIE_LINES = ("VO_Die_01", "VO_Die_02", "VO_Die_03", "VO_Die_04")


@dataclass(frozen=True)
class ModeRules:
    name: str
    # Active commands at the start, Bop first, in the order the original activated them.
    commands: tuple[str, ...]
    pitch_shift_amount: float
    pitch_shift_frequency: int = 12


CLASSIC = ModeRules("Classic", ("Bop", "Twist", "Pull"), pitch_shift_amount=0.03)


@dataclass(frozen=True)
class Options:
    """The settings a game reads."""
    commands_mode: str = "VOX"
    banter: bool = True
    theme: int = 0


class State(Enum):
    WAITING_TO_START = auto()
    BETWEEN_TURNS = auto()
    IN_TURN = auto()
    HELP = auto()
    FAILING = auto()
    OVER = auto()


class Game:
    def __init__(self, rules: ModeRules, options: Options, rng: random.Random) -> None:
        self.rules = rules
        self.options = options
        self._rng = rng
        self._banter = Banter(rng)
        self._timers: list[tuple[float, int, Callable[[float], None]]] = []
        self._sequence = itertools.count()
        self._events: list[ev.Event] = []
        self.state = State.OVER
        self.active: list[str] = []
        self.current: str | None = None
        self._next: str | None = None
        self._turn_opened_at = 0.0
        self._times_called: dict[str, int] = {}
        self.pitch = 1.0
        self.moves = 0
        self.bonus = 0
        self.end_bonus = 0
        self._base_bonus = BASE_BONUS_START
        self._speed_ups = 0
        self._music_index = 0

    # Public interface

    def prepare(self, now: float) -> None:
        """The "Bop It to start" screen. Any input starts the game."""
        self.state = State.WAITING_TO_START
        self._emit(ev.WaitingToStart())

    def press(self, command: str, now: float) -> None:
        """The player performed a command."""
        self.update(now)
        if self.state == State.WAITING_TO_START:
            self._start_game(now)
        elif self.state == State.IN_TURN:
            expected = self.current or ""
            correct = command == expected
            self._emit(ev.MoveMade(command, expected, correct, now - self._turn_opened_at))
            if correct:
                self._win_turn(now)
            else:
                self._fail_turn(now)
        # Between turns input is ignored, as in the original.

    def dismiss_help(self, now: float) -> None:
        if self.state == State.HELP:
            self._fail_sound_done(now)

    def update(self, now: float) -> None:
        """Run every scheduled step that is due, each at its own due time."""
        while self._timers and self._timers[0][0] <= now:
            due, _, step = heapq.heappop(self._timers)
            step(due)

    def pop_events(self) -> list[ev.Event]:
        events, self._events = self._events, []
        return events

    @property
    def total(self) -> int:
        return self.moves + self.bonus + self.end_bonus

    # Game flow

    def _start_game(self, now: float) -> None:
        self.pitch = 1.0
        self.moves = 0
        self.bonus = 0
        self.end_bonus = 0
        self._base_bonus = BASE_BONUS_START
        self._speed_ups = 0
        self._music_index = 0
        self.active = list(self.rules.commands)
        self._times_called = {c: 0 for c in self.active}
        self._emit(ev.GameStarted(self.rules.name))
        self._emit(ev.MusicStart(self._music_name(self._music_index), self.pitch, LOOP_OFFSET))
        self._next = self._rng.choice(self.active)
        self._call(self._next)
        self.state = State.BETWEEN_TURNS
        self._schedule(now + BEAT / self.pitch, self._start_turn)

    def _start_turn(self, now: float) -> None:
        self.current = self._next
        self._times_called[self.current] += 1
        self._turn_opened_at = now
        self.state = State.IN_TURN
        deadline = now + TURN_TIMEOUT / self.pitch
        self._emit(ev.TurnOpened(self.current, deadline))
        self._schedule(deadline, self._command_timeout)

    def _command_timeout(self, now: float) -> None:
        if self.state != State.IN_TURN:
            return
        self._emit(ev.TurnTimedOut(self.current or ""))
        self._fail_turn(now)

    def _win_turn(self, now: float) -> None:
        self._cancel_timers()
        command = self.current or ""
        self._emit(ev.PlaySound(response_sound(command, self.options.theme), self.pitch))
        self._emit(ev.MusicSegment(self._music_name(self._music_index + 1), self.pitch))
        self._emit(ev.MusicSeek(LOOP_OFFSET))
        self.bonus += self._base_bonus
        self.moves += 1
        self._emit(ev.ScoreChanged(self.moves, self.bonus))
        self._next = self._rng.choice(self.active)
        self._call(self._next)
        self.state = State.BETWEEN_TURNS
        self._schedule(now + BEAT / self.pitch, self._success_done)

    def _success_done(self, now: float) -> None:
        if self.moves != 0 and self.moves % self.rules.pitch_shift_frequency == 0:
            self.pitch += self.rules.pitch_shift_amount
            self._emit(ev.MusicPitch(self.pitch))
            self._emit(ev.SpeedUp(self.pitch))
            self._base_bonus += BASE_BONUS_STEP
            self._speed_ups += 1
            if self._speed_ups == SPEED_UPS_PER_TRACK:
                self._speed_ups = 0
                self._change_track()
        self._start_turn(now)

    def _change_track(self) -> None:
        # Only the Original theme has more than one track: 01, then 02, then 03, then 01.
        if self.options.theme == 0:
            if self._music_index < 2:
                self._music_index = 2
            elif self._music_index == 2:
                self._music_index = 4
            else:
                self._music_index = 0
        self._emit(ev.MusicStop())
        self._emit(ev.MusicStart(self._music_name(self._music_index), self.pitch, 0.0))

    def _fail_turn(self, now: float) -> None:
        self._cancel_timers()
        self.state = State.FAILING
        self._emit(ev.MusicStop())
        die = self._rng.choice(DIE_LINES)
        self._emit(ev.PlaySound(themed(die, self.options.theme)))
        command = self.current or ""
        if self._times_called.get(command, 0) <= HELP_CALL_LIMIT:
            self.state = State.HELP
            self._emit(ev.HelpNeeded(command))
        else:
            self._schedule(now + FAIL_STEP, self._fail_sound_done)

    def _fail_sound_done(self, now: float) -> None:
        self.state = State.FAILING
        if self.options.banter:
            self._emit(ev.PlaySound(self._banter.pick(self.moves)))
        self._schedule(now + FAIL_STEP, self._fail_done)

    def _fail_done(self, now: float) -> None:
        self.state = State.OVER
        # Classic has no end bonus (SoloClassicMode::failDone).
        self.end_bonus = 0
        self._emit(ev.GameOver(self.moves, self.bonus, self.end_bonus, self.total))

    # Helpers

    def _call(self, command: str) -> None:
        self._emit(ev.CommandCalled(command))
        self._emit(ev.PlaySound(
            callout_sound(command, self.options.commands_mode, self.options.theme), self.pitch))

    def _music_name(self, index: int) -> str:
        name = MUSIC_TRACKS[index]
        # Only the first track has theme variants; the original filtered only that one.
        return themed(name, self.options.theme) if index < 2 else name

    def _schedule(self, due: float, step: Callable[[float], None]) -> None:
        heapq.heappush(self._timers, (due, next(self._sequence), step))

    def _cancel_timers(self) -> None:
        self._timers.clear()

    def _emit(self, event: ev.Event) -> None:
        self._events.append(event)
