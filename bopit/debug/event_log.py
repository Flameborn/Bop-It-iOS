"""The debug event log: one plain line per event, with the time in seconds since the game
screen opened, to the millisecond. Written to logs/debug-<date>-<time>.txt."""

import time
from pathlib import Path
from typing import TextIO

from bopit.config import LOG_DIR
from bopit.engine import events as ev
from bopit.engine.game import PLAYER_NAMES


def describe(event: ev.Event, when: float = 0.0) -> str | None:
    """One line for an engine event that happened at when, or None to leave it out."""
    match event:
        case ev.WaitingToStart():
            return "waiting to start"
        case ev.GameStarted(mode):
            return f"game started, {mode}"
        case ev.CommandCalled(command):
            return f"command called: {command}"
        case ev.TurnOpened(command, deadline):
            return f"turn opened: {command}, window {deadline - when:.3f}"
        case ev.MoveMade(command, expected, correct, delta):
            result = "correct" if correct else "wrong"
            return f"response: {command}, expected {expected}, {result}, delta {delta:.3f}"
        case ev.TurnTimedOut(command):
            return f"timed out: {command}"
        case ev.ScoreChanged(moves, bonus):
            return f"score: moves {moves}, bonus {bonus}"
        case ev.SpeedUp(pitch):
            return f"speed up: pitch {pitch:.2f}"
        case ev.RhythmGraded(grade):
            return f"rhythm: {grade}"
        case ev.StreakEarned(kind):
            return f"streak: {kind}"
        case ev.CommandUnlocked(command):
            return f"unlocked: {command}"
        case ev.CommandIntroduced(command):
            return f"introduced: {command}"
        case ev.XMove(command):
            return f"x-move: {command}"
        case ev.HelpNeeded(command):
            return f"help: {command}"
        case ev.PassIt():
            return "pass it"
        case ev.PointScored(player, scores):
            return f"point: {PLAYER_NAMES[player]}, Green {scores[0]}, Blue {scores[1]}"
        case ev.HeadToHeadWon(player, scores, wins):
            return (f"won: {PLAYER_NAMES[player]}, {scores[0]} to {scores[1]}, "
                    f"wins Green {wins[0]}, Blue {wins[1]}")
        case ev.BlitzFinished(seconds, moves):
            return f"blitz finished: {seconds:.3f} seconds, moves {moves}"
        case ev.ChallengeBreak(player, seconds):
            return f"challenge break: player {player}, {seconds:.3f} seconds"
        case ev.ChallengeFinished(times):
            return "challenge finished: " + ", ".join(f"{t:.3f}" for t in times)
        case ev.GameOver(moves, bonus, end_bonus, total):
            return f"game over: moves {moves}, bonus {bonus}, end bonus {end_bonus}, total {total}"
        case ev.PlaySound(name, pitch, position, pan):
            extra = f", from {position:.3f}" if position else ""
            extra += f", pan {pan:+.1f}" if pan else ""
            return f"sound: {name}, pitch {pitch:.2f}{extra}"
        case ev.StopSound(name):
            return f"sound stopped: {name}"
        case ev.MusicStart(name, pitch, position):
            return f"music: {name}, pitch {pitch:.2f}, from {position:.3f}"
        case ev.MusicSegment(name, pitch):
            return f"music part: {name}, pitch {pitch:.2f}"
        case ev.MusicSeek(position):
            return f"music seek: {position:.3f}"
        case ev.MusicPitch(pitch):
            return f"music pitch: {pitch:.2f}"
        case ev.MusicStop():
            return "music stopped"
        case ev.MicListen(listening):
            return "microphone listening" if listening else "microphone stopped"
        case _:
            return None


class EventLog:
    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._origin: float | None = None

    @classmethod
    def open(cls, log_dir: Path = LOG_DIR) -> "EventLog":
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / time.strftime("debug-%Y%m%d-%H%M%S.txt")
        # Line buffered, so the file is complete even if the game is closed abruptly.
        return cls(path.open("w", encoding="utf-8", buffering=1))

    @property
    def path(self) -> str:
        return getattr(self._stream, "name", "")

    def line(self, when: float, text: str) -> None:
        if self._origin is None:
            self._origin = when
        self._stream.write(f"{when - self._origin:.3f} {text}\n")

    def event(self, when: float, event: ev.Event) -> None:
        text = describe(event, when)
        if text is not None:
            self.line(when, text)

    def close(self) -> None:
        self._stream.close()
