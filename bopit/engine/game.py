"""One game of Bop It, following the original's GameController and solo mode classes.

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
from bopit.engine.commands import all_commands, callout_sound, response_sound
from bopit.engine.rhythm import Grade, RhythmState
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
# Exact lengths of the looping "a" parts, in seconds, measured from the files (frames / 22050).
LOOP_LENGTHS = {
    "MUSIC_GameLoop_01a": 53740 / 22050, "MUSIC_GameLoop_01a_HLWN": 53740 / 22050,
    "MUSIC_GameLoop_01a_XMAS": 53748 / 22050, "MUSIC_GameLoop_02a": 53745 / 22050,
    "MUSIC_GameLoop_03a": 53742 / 22050,
    "MUSIC_BlitzLoop_01a": 53742 / 22050, "MUSIC_BlitzLoop_01a_HLWN": 53740 / 22050,
    "MUSIC_BlitzLoop_01a_XMAS": 53748 / 22050,
}
DIE_LINES = ("VO_Die_01", "VO_Die_02", "VO_Die_03", "VO_Die_04")
# Commands with a fixed screen position (Command_Bop::init, Command_Poke::init).
FIXED_LOCATIONS = {"Bop": 4, "Poke": 5}
# Where a newly unlocked command goes, by how many are active (GameController::unlockNextCommand).
UNLOCK_LOCATIONS = {4: 1, 3: 2, 2: 3}
MAX_INDEX_TO_UNLOCK = 10    # GameController::init
# Shout It X-Move. Listening starts Shout's callout length (Command_Shout::init) into the turn,
# per pitch, and a microphone average level at or above the threshold wins
# (GameSettings shoutItVolumeLevel; the level is the linear 0 to 1 average power).
SHOUT_CALL_LENGTH = 0.46
SHOUT_THRESHOLD = 0.6
X_MOVE_BONUS = 25
FREQUENCY_STEP = 8          # GameController::increaseFrequencyUnlock
# Pass It (MultiPlayerModeBase): a pass after 4 to 6 more successes, and the next player starts
# 3.25 per pitch after the pass music begins. The original began the pass half a beat after the
# success; this port lets the bar finish so "Pass!" lands on the downbeat (docs/DEVIATIONS.md).
# The success's "b" part is one bar end away: 0.813 seconds of the file (17917 / 22050).
PASS_BAR_END = 17917 / 22050
PASS_LENGTH = 3.25
PASS_MUSIC = ("MUSIC_PassIt_01", "MUSIC_PassIt_02", "MUSIC_PassIt_03")
# Every callout file starts with about one beat of silence, so the voice lands as the turn
# opens. When a turn opens at once, as after a pass, the original started the callout this
# far in (GameController::playCommandCalloutSoundNow).
CALLOUT_NOW_POSITION = 0.805
# Where the picked commands go (Pass It and Head 2 Head prepareActiveCommands).
PICKED_LOCATIONS = (0, 3, 2, 1)
# Blitz Challenge (MultiBlitzMode): after GO on the break screen, the next player starts
# 1.1 per pitch later (blitzBreakEnd).
CHALLENGE_RESTART_DELAY = 1.1


@dataclass(frozen=True)
class ModeRules:
    name: str
    # Commands activated at the start as (command, screen position), in the original's order.
    commands: tuple[tuple[str, int], ...]
    pitch_shift_amount: float
    pitch_shift_frequency: int = 12
    # Successes before the first unlock. None means commands never unlock.
    first_unlock: int | None = None
    # Basic and Extreme bring in Twist and Pull by script (their winTurn).
    scripted_intro: bool = False
    # Basic set some commands' call counts to 1 where Extreme set 0; this affects help.
    intro_call_count: int = 0
    rhythm_graded: bool = False
    # Classic throws the end bonus away when the game ends (SoloClassicMode::failDone).
    keeps_end_bonus: bool = True
    # The "a" and "b" music parts, in order. Blitz has its own pair.
    music_tracks: tuple[str, ...] = MUSIC_TRACKS
    # Blitz: finish after this many successes; mistakes cost time instead of ending the game.
    blitz_target: int | None = None
    # Pass It: Bop plus the picked commands, passing to the next player every 4 to 6 moves.
    pass_it: bool = False
    # Pass It Basic set Bop as the first command and counted it as called twice.
    pass_it_single: bool = False
    # Pass It Extreme loaded its music without the theme filter.
    themed_music: bool = True
    # Solo modes had a trophy manager and counted lifetime moves; multiplayer modes did not.
    tracks_trophies: bool = True
    # Blitz Challenge: each player in turn does this many successes against the clock.
    challenge_target: int | None = None


CLASSIC = ModeRules("Classic", (("Bop", 4), ("Twist", 0), ("Pull", 3)), pitch_shift_amount=0.03,
                    keeps_end_bonus=False)
BASIC = ModeRules("Basic", (("Bop", 4),), pitch_shift_amount=0.02, first_unlock=12,
                  scripted_intro=True, intro_call_count=1, rhythm_graded=True)
BLITZ = ModeRules("Blitz", (("Bop", 4), ("Twist", 0), ("Pull", 3), ("Spin", 2), ("Flick", 1)),
                  pitch_shift_amount=0.0, pitch_shift_frequency=50_000_000,
                  music_tracks=("MUSIC_BlitzLoop_01a", "MUSIC_BlitzLoop_01b"), blitz_target=20)
PASS_IT_BASIC = ModeRules("Pass It Basic", (("Bop", 4),), pitch_shift_amount=0.02,
                          pass_it=True, pass_it_single=True, tracks_trophies=False)
PASS_IT_EXTREME = ModeRules("Pass It Extreme", (("Bop", 4),), pitch_shift_amount=0.02,
                            pass_it=True, themed_music=False, tracks_trophies=False)
BLITZ_CHALLENGE = ModeRules("Blitz Challenge", BLITZ.commands, pitch_shift_amount=0.0,
                            pitch_shift_frequency=50_000_000, music_tracks=BLITZ.music_tracks,
                            tracks_trophies=False, challenge_target=15)
EXTREME = ModeRules("Extreme", (("Bop", 4),), pitch_shift_amount=0.02, first_unlock=8,
                    scripted_intro=True, intro_call_count=0, rhythm_graded=True)


@dataclass(frozen=True)
class Options:
    """The settings a game reads."""
    commands_mode: str = "VOX"
    banter: bool = True
    theme: int = 0
    shout_it: bool = True
    # Our addition: the Shout It X-Move through the microphone.
    microphone: bool = True
    # The commands picked for Pass It and Head 2 Head, in the picker's order, without Bop.
    picked: tuple[str, ...] = ()
    # Blitz Challenge: how many players take a turn.
    players: int = 2


class State(Enum):
    WAITING_TO_START = auto()
    BETWEEN_TURNS = auto()
    IN_TURN = auto()
    PAUSED = auto()
    PASSING = auto()
    BREAK = auto()
    HELP = auto()
    FAILING = auto()
    OVER = auto()


class MusicClock:
    """Where the game music loop is, worked out from the engine's own commands to it.
    The original asked the audio engine; this is exact and reproducible."""

    def __init__(self) -> None:
        self._length = 1.0
        self._anchor_time = 0.0
        self._anchor_position = 0.0
        self._pitch = 1.0

    def start(self, name: str, position: float, pitch: float, now: float) -> None:
        self._length = LOOP_LENGTHS.get(name, 1.0)
        self.seek(position, now)
        self._pitch = pitch

    def seek(self, position: float, now: float) -> None:
        self._anchor_time = now
        self._anchor_position = position

    def set_pitch(self, pitch: float, now: float) -> None:
        self.seek(self.position(now), now)
        self._pitch = pitch

    def position(self, now: float) -> float:
        elapsed = (now - self._anchor_time) * self._pitch
        return (self._anchor_position + elapsed) % self._length


class Game:
    def __init__(self, rules: ModeRules, options: Options, rng: random.Random,
                 times_called: dict[str, int] | None = None) -> None:
        """times_called persists between games, as the original's Command objects did."""
        self.rules = rules
        self.options = options
        self._rng = rng
        self._banter = Banter(rng)
        self._master = (("Bop",) + options.picked) if rules.pass_it else all_commands(options.shout_it)
        self._pitch_frequency = rules.pitch_shift_frequency
        self._turn_to_pass = 0
        self._timers: list[tuple[float, int, Callable[[float], None]]] = []
        self._sequence = itertools.count()
        self._events: list[ev.Event] = []
        self._music = MusicClock()
        self.state = State.OVER
        self.active: list[str] = []
        self.locations: dict[str, int] = {}
        self.times_called = times_called if times_called is not None else {}
        self.current: str | None = None
        self._next: str | None = None
        self._forced: str | None = None
        self._turn_opened_at = 0.0
        self.rhythm = RhythmState()
        self.pitch = 1.0
        self.moves = 0
        self.bonus = 0
        self._base_bonus = BASE_BONUS_START
        self._speed_ups = 0
        self._music_index = 0
        self._next_unlock_index = 3
        self._num_to_next_unlock = 0
        self._unlock_counter = 0
        self._blitz_started = 0.0
        self.blitz_time: float | None = None
        self._waiting_to_win = False
        self._listening = False
        self.x_moves = 0
        self._paused_blitz_time: float | None = None
        # Blitz Challenge: each player's time, and whose turn it is (from 0).
        self.player_times: list[float] = []
        self.current_player = 0
        self._players = options.players

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

    def hear(self, level: float, now: float) -> None:
        """The microphone's current average level, 0 to 1, while listening."""
        self.update(now)
        if not self._listening or self.state != State.IN_TURN or self.current != "Shout":
            return
        if level >= SHOUT_THRESHOLD:
            # GameController::gotAudio:peakPower: an X-Move win.
            self.rhythm.end_bonus += X_MOVE_BONUS
            self.x_moves += 1
            self._emit(ev.XMove("Shout"))
            self._emit(ev.MoveMade("Shout", "Shout", True, now - self._turn_opened_at))
            self._win_turn(now)

    @property
    def can_pause(self) -> bool:
        # GameController::pauseGame does nothing once the player has failed.
        return self.state in (State.BETWEEN_TURNS, State.IN_TURN)

    def pause(self, now: float) -> None:
        """GameController::pauseGame: stop the turn, the queued callout and the music."""
        self.update(now)
        if not self.can_pause:
            return
        self._cancel_timers()
        self._stop_listening()
        if self._forced is not None:
            self._activate(self._forced, self.locations.get(self._forced, 0))
        # The original only cut off the queued callout when it was not the last active command.
        if self._next in self.active and self.active.index(self._next) < len(self.active) - 1:
            self._emit(ev.StopSound(callout_sound(self._next, self.options.commands_mode,
                                                  self.options.theme)))
        self._emit(ev.MusicStop())
        if self._timed and self.blitz_time is None:
            self._paused_blitz_time = now - self._blitz_started
        self.state = State.PAUSED

    def resume(self, now: float) -> None:
        """GameController::resumeGame: music back on, a new command, and a turn a beat later."""
        if self.state != State.PAUSED:
            return
        if self._paused_blitz_time is not None:
            # SoloSpeedMode::resumeGame: the stopwatch carries on from where it stopped.
            self._blitz_started = now - self._paused_blitz_time
            self._paused_blitz_time = None
        self._start_music(self._music_name(self._music_index), LOOP_OFFSET, now)
        if self._forced is None:
            self._next = self._rng.choice(self.active)
            self._call(self._next)
        else:
            self._call(self._forced)
        self.state = State.BETWEEN_TURNS
        self._schedule(now + BEAT / self.pitch, self._start_turn)

    def save(self) -> dict:
        """What the original's saved game kept (GameController::encodeWithCoder). Only a
        paused game is saved."""
        return {
            "mode": self.rules.name, "moves": self.moves, "bonus": self.bonus,
            "end_bonus": self.rhythm.end_bonus, "num_to_next_unlock": self._num_to_next_unlock,
            "next_unlock_index": self._next_unlock_index, "unlock_counter": self._unlock_counter,
            "pitch": self.pitch, "active": [[c, self.locations[c]] for c in self.active],
            "forced": self._forced, "blitz_time": self._paused_blitz_time or 0.0,
            "x_moves": self.x_moves, "perfect_count": self.rhythm.perfect_count,
            "good_count": self.rhythm.good_count, "ok_count": self.rhythm.ok_count,
            "base_bonus": self._base_bonus, "music_index": self._music_index,
            "turn_to_pass": self._turn_to_pass,
            # MultiBlitzMode::encodeWithCoder kept only the number of players.
            "players": self._players,
        }

    def load(self, data: dict, now: float) -> None:
        """Restore a saved game, paused. Fields the original did not save start fresh."""
        self.moves = data["moves"]
        self.bonus = data["bonus"]
        self.rhythm = RhythmState(perfect_count=data["perfect_count"],
                                  good_count=data["good_count"], ok_count=data["ok_count"],
                                  end_bonus=data["end_bonus"])
        self._num_to_next_unlock = data["num_to_next_unlock"]
        self._next_unlock_index = data["next_unlock_index"]
        self._unlock_counter = data["unlock_counter"]
        self.pitch = data["pitch"]
        self.active = [c for c, _ in data["active"]]
        self.locations = {c: loc for c, loc in data["active"]}
        self._forced = data["forced"]
        self.x_moves = data["x_moves"]
        self._base_bonus = data["base_bonus"]
        self._music_index = data["music_index"]
        self._turn_to_pass = data.get("turn_to_pass", 0)
        self._players = data.get("players", self._players)
        # Not saved by the original: the times list comes back empty and the turn at player 1.
        self.player_times = []
        self.current_player = 0
        if self.rules.pass_it:
            self._pitch_frequency = self._turn_to_pass
        self._speed_ups = 0
        self._paused_blitz_time = data["blitz_time"]
        self._blitz_started = now - self._paused_blitz_time
        self.blitz_time = None
        self._waiting_to_win = False
        self._next = None
        self.state = State.PAUSED

    def next_player(self, now: float) -> None:
        """GO on the Blitz Challenge break screen (MultiBlitzMode::blitzBreakEnd)."""
        if self.state != State.BREAK or not self._waiting_to_win:
            return
        self._waiting_to_win = False
        self._schedule(now + CHALLENGE_RESTART_DELAY / self.pitch, self._challenge_restart)

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
    def _timed(self) -> bool:
        return self.rules.blitz_target is not None or self.rules.challenge_target is not None

    def blitz_elapsed(self, now: float) -> float:
        """The Blitz stopwatch: from the start of the game (or of this player's turn) until
        the finish."""
        if self.blitz_time is not None:
            return self.blitz_time
        return now - self._blitz_started if self.state != State.WAITING_TO_START else 0.0

    @property
    def end_bonus(self) -> int:
        return self.rhythm.end_bonus

    @property
    def total(self) -> int:
        return self.moves + self.bonus + self.end_bonus

    # Game flow

    def _start_game(self, now: float) -> None:
        self.pitch = 1.0
        self.moves = 0
        self.bonus = 0
        self.rhythm = RhythmState()
        self._base_bonus = BASE_BONUS_START
        self._speed_ups = 0
        self._music_index = 0
        self._unlock_counter = 0
        self._blitz_started = now
        self.x_moves = 0
        self.blitz_time = None
        self._waiting_to_win = False
        if self.rules.challenge_target is not None:
            # MultiBlitzMode::startGame: a zero time for each player, starting with the first.
            self.player_times = [0.0] * self._players
            self.current_player = 0
        self.active = []
        for command, location in self.rules.commands:
            self._activate(command, location)
        if self.rules.pass_it:
            for command, location in zip(self._master[1:5], PICKED_LOCATIONS):
                self._activate(command, location)
        for command in self.active:
            self.times_called[command] = 0
        self._emit(ev.GameStarted(self.rules.name))
        self._start_music(self._music_name(self._music_index), LOOP_OFFSET, now)
        self._next = self._rng.choice(self.active)
        self.times_called[self._next] = 0
        self._call(self._next)
        if self.rules.scripted_intro:
            # SoloSingleObject and SoloMultipleMode startGame: Bop first, then unlocks.
            self._forced = self.active[0]
            self.times_called[self._forced] = 1
        self._next_unlock_index = 3
        self._num_to_next_unlock = (self.rules.first_unlock if self.rules.first_unlock is not None
                                    else 2**31 - 1)
        self._pitch_frequency = self.rules.pitch_shift_frequency
        if self.rules.pass_it:
            # MultiPassItMode::startGame and MultiPassItSingleMode::startGame.
            self._next_unlock_index = 1
            self._pitch_frequency = self._set_turn_to_pass()
            if self.rules.pass_it_single:
                self._forced = self.active[0]
                # Set to 1, then its startTurn counted one more call.
                self.times_called[self._forced] = 2
        self.state = State.BETWEEN_TURNS
        self._schedule(now + BEAT / self.pitch, self._start_turn)

    def _start_turn(self, now: float) -> None:
        if self._forced is not None:
            self.current = self._forced
            self._forced = None
        else:
            self.current = self._next
        self.times_called[self.current] = self.times_called.get(self.current, 0) + 1
        self._turn_opened_at = now
        self.state = State.IN_TURN
        deadline = now + TURN_TIMEOUT / self.pitch
        self._emit(ev.TurnOpened(self.current, deadline))
        self._schedule(deadline, self._command_timeout)
        if self.current == "Shout" and self.options.microphone:
            self._schedule(now + SHOUT_CALL_LENGTH / self.pitch, self._start_listening)

    def _start_listening(self, now: float) -> None:
        if self.state == State.IN_TURN:
            self._listening = True
            self._emit(ev.MicListen(True))

    def _stop_listening(self) -> None:
        if self._listening:
            self._listening = False
            self._emit(ev.MicListen(False))

    def _command_timeout(self, now: float) -> None:
        if self.state != State.IN_TURN:
            return
        self._emit(ev.TurnTimedOut(self.current or ""))
        self._fail_turn(now)

    def _win_turn(self, now: float) -> None:
        self._cancel_timers()
        self._stop_listening()
        target = self.rules.blitz_target
        if target is not None and self.moves > target - 2:
            # SoloSpeedMode::winTurn: the last success stops the clock.
            self.blitz_time = now - self._blitz_started
            self._waiting_to_win = True
        if self.rules.rhythm_graded:
            self._grade(now)
        if self.rules.scripted_intro:
            self._scripted_unlocks()
        command = self.current or ""
        self._emit(ev.PlaySound(response_sound(command, self.options.theme), self.pitch))
        self._emit(ev.MusicSegment(self._music_name(self._music_index + 1), self.pitch))
        self._seek_music(LOOP_OFFSET, now)
        self.bonus += self._base_bonus
        self.moves += 1
        self._emit(ev.ScoreChanged(self.moves, self.bonus))
        self._num_to_next_unlock -= 1
        if self._num_to_next_unlock < 1:
            self._unlock_next_command()
            self._increase_frequency_unlock()
        # queueNewCommandAndPlay: the forced command if any, otherwise a random active one.
        if self._forced is None:
            self._next = self._rng.choice(self.active)
            self._call(self._next)
        else:
            if self._forced not in self.active:
                self._emit(ev.CommandIntroduced(self._forced))
            self._call(self._forced)
        self.state = State.BETWEEN_TURNS
        if not self._waiting_to_win:
            self._schedule(now + BEAT / self.pitch, self._success_done)
        if target is not None and self.moves > target - 1:
            self._win_blitz()
        if self.rules.pass_it and self.moves > 0 and self.moves % self._turn_to_pass == 0:
            self._start_pass(now)
        challenge = self.rules.challenge_target
        if challenge is not None and self.moves > challenge - 1 and self._next is not None:
            # MultiBlitzMode::winTurn: the last success cuts off the callout it just queued.
            self._emit(ev.StopSound(callout_sound(self._next, self.options.commands_mode,
                                                  self.options.theme)))

    def _grade(self, now: float) -> None:
        grade = self.rhythm.grade(self._music.position(now))
        if grade != Grade.MISSED:
            self._emit(ev.RhythmGraded(grade.value))
        streak = self.rhythm.post_process()
        if streak is not None:
            self._emit(ev.StreakEarned(streak.name.capitalize()))

    def _scripted_unlocks(self) -> None:
        """SoloSingleObject::winTurn and SoloMultipleMode::winTurn, before the base winTurn."""
        count = self.rules.intro_call_count
        if self.moves == 6:
            self._forced = self._master[2]
            self.locations[self._forced] = 3
            self._num_to_next_unlock = 9
            self.times_called[self._forced] = 0
        elif self.moves == 1:
            self._forced = self._master[1]
            self.locations[self._forced] = 0
            if count == 0:
                self.times_called[self._forced] = 0
        elif self.moves == 0:
            self._forced = self.active[0]
            self.times_called[self._forced] = count

    def _unlock_next_command(self) -> None:
        """GameController::unlockNextCommand."""
        if self._next_unlock_index < len(self._master):
            command = self._master[self._next_unlock_index]
            self._base_bonus += BASE_BONUS_STEP
            count = len(self.active)
            if count >= 5:
                location = 5 if command == "Poke" else self.locations[self.active[1]]
            else:
                location = UNLOCK_LOCATIONS.get(count, 0)
            self._emit(ev.CommandUnlocked(command))
        else:
            command = self._random_unlockable()
            tries = 0
            while command in self.active:
                tries += 1
                command = self._random_unlockable()
                if tries > 5:
                    return
            location = 4
            while location in (4, 5):
                location = self._rng.getrandbits(32) % 6
        self._forced = command
        self.locations[command] = location
        self._next_unlock_index += 1
        self._unlock_counter += 1

    def _random_unlockable(self) -> str:
        return self._master[self._rng.randrange(MAX_INDEX_TO_UNLOCK) + 1]

    def _increase_frequency_unlock(self) -> None:
        if self._next_unlock_index < len(self._master):
            self._num_to_next_unlock = self._unlock_counter + FREQUENCY_STEP
        else:
            self._num_to_next_unlock = FREQUENCY_STEP

    def _success_done(self, now: float) -> None:
        challenge = self.rules.challenge_target
        if challenge is not None and self.moves >= challenge:
            self._challenge_turn_done(now)
            return
        if self._forced is not None:
            self._activate(self._forced, self.locations.get(self._forced, 0))
        if self.moves != 0 and self.moves % self._pitch_frequency == 0:
            self.pitch += self.rules.pitch_shift_amount
            self._music.set_pitch(self.pitch, now)
            self._emit(ev.MusicPitch(self.pitch))
            self._emit(ev.SpeedUp(self.pitch))
            self._base_bonus += BASE_BONUS_STEP
            self._speed_ups += 1
            if self._speed_ups == SPEED_UPS_PER_TRACK:
                self._speed_ups = 0
                self._change_track(now)
        self._start_turn(now)

    def _change_track(self, now: float) -> None:
        # Only the Original theme has more than one track: 01, then 02, then 03, then 01.
        if self.options.theme == 0:
            if self._music_index < 2:
                self._music_index = 2
            elif self._music_index == 2:
                self._music_index = 4
            else:
                self._music_index = 0
        self._emit(ev.MusicStop())
        self._start_music(self._music_name(self._music_index), 0.0, now)

    # Pass It

    def _set_turn_to_pass(self) -> int:
        """MultiPlayerModeBase::setTurnToPass: 4, 5 or 6 more successes. Also the pitch shift
        frequency, which is why Pass It in practice never speeds up."""
        self._turn_to_pass = self.moves + (self._rng.getrandbits(32) % 3 | 4)
        return self._turn_to_pass

    def _start_pass(self, now: float) -> None:
        """A pass (MultiPassItMode::winTurn). The queued callout is cut at once. The loop and
        the success's "b" part finish their bar, and VO_Pass starts now so that its one-beat
        lead-in ends, and "Pass!" is heard, on the next downbeat."""
        self._waiting_to_win = True
        self.state = State.PASSING
        if self._next is not None:
            self._emit(ev.StopSound(callout_sound(self._next, self.options.commands_mode,
                                                  self.options.theme)))
        self._cancel_timers()
        self._emit(ev.MusicSegment("VO_Pass", self.pitch))
        self._schedule(now + PASS_BAR_END / self.pitch, self._show_pass)

    def _show_pass(self, now: float) -> None:
        """MultiPlayerModeBase::showPassItScreen, on the downbeat after the passing success."""
        self._emit(ev.MusicStop())
        if self._music_index == 0 or self.options.theme != 0:
            music = PASS_MUSIC[0]
        elif self._music_index == 4:
            music = PASS_MUSIC[2]
        elif self._music_index == 2:
            music = PASS_MUSIC[1]
        else:
            music = None
        if music is not None:
            self._emit(ev.MusicSegment(themed(music, self.options.theme), self.pitch))
        self._emit(ev.PassIt())
        self._schedule(now + PASS_LENGTH / self.pitch, self._pass_end)

    def _pass_end(self, now: float) -> None:
        """MultiPlayerModeBase::passItEnd: the next player's turn starts at once."""
        self._waiting_to_win = False
        self._pitch_frequency = self._set_turn_to_pass()
        name = self._music_name(self._music_index)
        self._music.start(name, 0.0, self.pitch, now)
        self._emit(ev.MusicStart(name, self.pitch, 0.0))
        # queueNewCommandAndPlayNow: always a random active command.
        self._next = self._rng.choice(self.active)
        self._forced = None
        self._call(self._next, position=CALLOUT_NOW_POSITION)
        self._start_turn(now)

    # Blitz Challenge

    def _challenge_turn_done(self, now: float) -> None:
        """MultiBlitzMode::successDone once the player has 15: the clock stops a beat after
        the last success, the loop stops (its "b" part plays on) and the time is kept. Then
        the break screen, or after the last player, the results."""
        if self._next is not None:
            self._emit(ev.StopSound(callout_sound(self._next, self.options.commands_mode,
                                                  self.options.theme)))
        time = now - self._blitz_started
        self.blitz_time = time
        self._emit(ev.MusicStop())
        if self.current_player < len(self.player_times):
            self.player_times[self.current_player] = time
        # The original compared unsigned numbers, so with no times list (a resumed saved
        # game) every player was followed by another break.
        if not self.player_times or self.current_player < len(self.player_times) - 1:
            self.current_player += 1
            self._waiting_to_win = True
            # resetForNextPlayer and resetValues.
            self.moves = 0
            self.pitch = 1.0
            self.state = State.BREAK
            self._emit(ev.ChallengeBreak(self.current_player, time))
        else:
            self._waiting_to_win = False
            self.state = State.OVER
            self._emit(ev.ChallengeFinished(tuple(self.player_times)))

    def _challenge_restart(self, now: float) -> None:
        """MultiBlitzMode::blitzBreakEndDone: the clock restarts, the loop plays from its
        start and a callout plays at once as the turn opens."""
        self._blitz_started = now
        self.blitz_time = None
        self._start_music(self._music_name(self._music_index), 0.0, now)
        self._next = self._rng.choice(self.active)
        self._forced = None
        self._call(self._next, position=CALLOUT_NOW_POSITION)
        self._start_turn(now)

    def _win_blitz(self) -> None:
        """SoloSpeedMode::winBlitz: cut off the queued callout and the music, and finish."""
        self._emit(ev.StopSound(callout_sound(self._next or "", self.options.commands_mode,
                                              self.options.theme)))
        self._emit(ev.MusicStop())
        self.state = State.OVER
        self._emit(ev.BlitzFinished(self.blitz_time or 0.0, self.moves))

    def _fail_blitz_turn(self, now: float) -> None:
        """SoloSpeedMode::failTurn: a mistake costs time. The die line plays and a new
        command is called; the music and the clock keep going."""
        die = self._rng.choice(DIE_LINES)
        self._emit(ev.PlaySound(themed(die, self.options.theme)))
        self.state = State.BETWEEN_TURNS
        if not self._waiting_to_win:
            self._schedule(now + BEAT / self.pitch, self._success_done)
            self._seek_music(LOOP_OFFSET, now)
            self._next = self._rng.choice(self.active)
            self._call(self._next)

    def _fail_turn(self, now: float) -> None:
        self._cancel_timers()
        self._stop_listening()
        if self._timed:
            # MultiBlitzMode::failTurn is the same as SoloSpeedMode::failTurn.
            self._fail_blitz_turn(now)
            return
        self.state = State.FAILING
        self._emit(ev.MusicStop())
        die = self._rng.choice(DIE_LINES)
        self._emit(ev.PlaySound(themed(die, self.options.theme)))
        command = self.current or ""
        if self.times_called.get(command, 0) <= HELP_CALL_LIMIT:
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
        if not self.rules.keeps_end_bonus:
            self.rhythm.end_bonus = 0
        self._emit(ev.GameOver(self.moves, self.bonus, self.end_bonus, self.total))

    # Helpers

    def _activate(self, command: str, location: int) -> None:
        """GameController::activateCommand:forLoc: the command takes the position and
        replaces whatever was there."""
        location = FIXED_LOCATIONS.get(command, location)
        for other in self.active:
            if self.locations.get(other) == location:
                self.active.remove(other)
                break
        self.locations[command] = location
        self.active.append(command)

    def _call(self, command: str, position: float = 0.0) -> None:
        self._emit(ev.CommandCalled(command))
        self._emit(ev.PlaySound(
            callout_sound(command, self.options.commands_mode, self.options.theme), self.pitch,
            position))

    def _start_music(self, name: str, position: float, now: float) -> None:
        self._music.start(name, position, self.pitch, now)
        self._emit(ev.MusicStart(name, self.pitch, position))

    def _seek_music(self, position: float, now: float) -> None:
        self._music.seek(position, now)
        self._emit(ev.MusicSeek(position))

    def _music_name(self, index: int) -> str:
        name = self.rules.music_tracks[index]
        # Only the first track has theme variants; the original filtered only that one.
        return themed(name, self.options.theme) if index < 2 and self.rules.themed_music else name

    def _schedule(self, due: float, step: Callable[[float], None]) -> None:
        heapq.heappush(self._timers, (due, next(self._sequence), step))

    def _cancel_timers(self) -> None:
        self._timers.clear()

    def _emit(self, event: ev.Event) -> None:
        self._events.append(event)
