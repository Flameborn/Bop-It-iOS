"""The autoplay bot. It watches the engine's events and plans each press at an exact time,
so its timing is reproducible and does not depend on the frame rate."""

from dataclasses import dataclass

from bopit.debug.options import DebugOptions, Failure
from bopit.engine import events as ev
from bopit.engine.game import GREEN, Game

START_DELAY = 1.5       # "Bop it to start" to the bot's first press.
HELP_DELAY = 4.0        # Time to hear the help popup before dismissing it.
LATE_BY = 0.05          # How far past the deadline a late press comes.


@dataclass(frozen=True)
class Action:
    at: float
    kind: str                       # "start", "press" or "help"
    command: str = ""
    player: int | None = None       # Head 2 Head only.
    # The turn this press belongs to, so a press planned before a pause is dropped.
    turn_opened: float | None = None
    note: str = ""                  # Why, for the log: "right", "wrong", "late".


class Bot:
    def __init__(self, options: DebugOptions) -> None:
        self._options = options
        self._pending: list[Action] = []
        self.turns = 0

    def plan(self, when: float, event: ev.Event, game: Game) -> None:
        match event:
            case ev.WaitingToStart():
                self._add(Action(when + START_DELAY, "start", "Bop",
                                 GREEN if game.rules.head_to_head else None))
            case ev.HelpNeeded():
                self._add(Action(when + HELP_DELAY, "help"))
            case ev.TurnOpened(command, deadline):
                self.turns += 1
                self._plan_move(when, command, deadline, game)
            case _:
                pass

    def due(self, now: float) -> Action | None:
        """The next action due by now, removed from the plan."""
        if self._pending and self._pending[0].at <= now:
            return self._pending.pop(0)
        return None

    def clear(self) -> None:
        self._pending.clear()

    def _plan_move(self, opened: float, command: str, deadline: float, game: Game) -> None:
        o = self._options
        failing = o.failure != Failure.NONE and self.turns % o.fail_every == 0
        failure = o.failure if failing else Failure.NONE
        if failure == Failure.MISS:
            return
        player = self._player_for(command, game)
        at = opened + o.reaction / game.pitch
        note = "right"
        if failure == Failure.WRONG:
            command, player = self._wrong(command, player, game)
            note = "wrong"
        elif failure == Failure.LATE:
            at = deadline + LATE_BY
            note = "late"
        self._add(Action(at, "press", command, player, opened, note))

    def _player_for(self, command: str, game: Game) -> int | None:
        if not game.rules.head_to_head:
            return None
        owner = game.owner(command)
        # Bop goes to each player in turn, so both score.
        return owner if owner is not None else self.turns % 2

    def _wrong(self, command: str, player: int | None, game: Game) -> tuple[str, int | None]:
        if game.rules.head_to_head and player is not None:
            # The player blows it with another of their own keys.
            options = ["Bop"] + game.commands_of(player)
        else:
            options = list(game.active)
        others = [c for c in options if c != command]
        return (others[0] if others else command), player

    def _add(self, action: Action) -> None:
        self._pending.append(action)
        self._pending.sort(key=lambda a: a.at)
