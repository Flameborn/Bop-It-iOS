"""What the engine tells the rest of the game. The app turns these into sound and speech."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlaySound:
    """A one-shot sound at the SFX volume."""
    name: str
    pitch: float = 1.0


@dataclass(frozen=True)
class MusicStart:
    """Start the game music loop, replacing any current one."""
    name: str
    pitch: float
    position: float


@dataclass(frozen=True)
class MusicSegment:
    """A one-shot music part (a "b" part) at the music volume."""
    name: str
    pitch: float


@dataclass(frozen=True)
class MusicSeek:
    position: float


@dataclass(frozen=True)
class MusicPitch:
    pitch: float


@dataclass(frozen=True)
class MusicStop:
    pass


@dataclass(frozen=True)
class WaitingToStart:
    """The original's "Bop It to start" screen."""


@dataclass(frozen=True)
class GameStarted:
    mode: str


@dataclass(frozen=True)
class CommandCalled:
    command: str


@dataclass(frozen=True)
class TurnOpened:
    command: str
    deadline: float


@dataclass(frozen=True)
class MoveMade:
    command: str
    expected: str
    correct: bool
    # Seconds since the turn opened.
    reaction: float


@dataclass(frozen=True)
class TurnTimedOut:
    command: str


@dataclass(frozen=True)
class ScoreChanged:
    moves: int
    bonus: int


@dataclass(frozen=True)
class SpeedUp:
    pitch: float


@dataclass(frozen=True)
class RhythmGraded:
    """Basic and Extreme: Perfect, Good or OK. The original showed it on screen."""
    grade: str


@dataclass(frozen=True)
class StreakEarned:
    """A 25 move Perfect or Good streak. The original showed it on screen."""
    kind: str


@dataclass(frozen=True)
class CommandUnlocked:
    """A regular unlock (GameController::unlockNextCommand), which in the original also
    completed that command's first-unlock trophy."""
    command: str


@dataclass(frozen=True)
class CommandIntroduced:
    """A command not in play is called and enters play. The original showed it appearing."""
    command: str


@dataclass(frozen=True)
class HelpNeeded:
    """The original's help popup after failing a command called 2 times or fewer.
    The game waits for Game.dismiss_help."""
    command: str


@dataclass(frozen=True)
class GameOver:
    moves: int
    bonus: int
    end_bonus: int
    total: int


Event = (PlaySound | MusicStart | MusicSegment | MusicSeek | MusicPitch | MusicStop
         | WaitingToStart | GameStarted | CommandCalled | TurnOpened | MoveMade
         | TurnTimedOut | ScoreChanged | SpeedUp | RhythmGraded | StreakEarned
         | CommandUnlocked | CommandIntroduced | HelpNeeded | GameOver)
