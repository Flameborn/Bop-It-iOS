"""What the engine tells the rest of the game. The app turns these into sound and speech."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlaySound:
    """A one-shot sound at the SFX volume, optionally starting part way in (seconds)."""
    name: str
    pitch: float = 1.0
    position: float = 0.0


@dataclass(frozen=True)
class StopSound:
    """Cut off a one-shot sound, such as a callout that is no longer needed."""
    name: str


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
class MicListen:
    """Open (True) or close (False) the microphone. Only its level is used."""
    listening: bool


@dataclass(frozen=True)
class XMove:
    """A move made the X-Move way, which for this port means shouting into the microphone."""
    command: str


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
class PassIt:
    """Pass It: the device goes to the next player. The original showed "PASS IT"."""


@dataclass(frozen=True)
class HelpNeeded:
    """The original's help popup after failing a command called 2 times or fewer.
    The game waits for Game.dismiss_help."""
    command: str


@dataclass(frozen=True)
class BlitzFinished:
    """Blitz ends on its 20th success. time is in seconds."""
    time: float
    moves: int


@dataclass(frozen=True)
class GameOver:
    moves: int
    bonus: int
    end_bonus: int
    total: int


Event = (PlaySound | StopSound | MusicStart | MusicSegment | MusicSeek | MusicPitch | MusicStop | MicListen | XMove
         | WaitingToStart | GameStarted | CommandCalled | TurnOpened | MoveMade
         | TurnTimedOut | ScoreChanged | SpeedUp | RhythmGraded | StreakEarned
         | CommandUnlocked | CommandIntroduced | PassIt | HelpNeeded | BlitzFinished | GameOver)
