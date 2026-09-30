"""Debug mode settings, from the command line."""

import argparse
from dataclasses import dataclass
from enum import Enum


class Failure(Enum):
    NONE = "none"       # Always right.
    WRONG = "wrong"     # Press a different command.
    LATE = "late"       # Press just after the turn has timed out.
    MISS = "miss"       # Press nothing.


@dataclass(frozen=True)
class DebugOptions:
    # False: log only, and you play yourself.
    bot: bool = True
    # Seconds from the turn opening (when the callout's voice starts) to the bot's press, at
    # normal speed. Like every game timer it is divided by the pitch, so it keeps its place in
    # the window as the game speeds up. The window is 1.1.
    reaction: float = 0.3
    failure: Failure = Failure.NONE
    # Fail on every Nth turn. In the solo modes (except Blitz) the first failure ends the game.
    fail_every: int = 10
    # A fixed random seed for every game, so runs repeat exactly.
    seed: int | None = None


def add_arguments(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("debug mode")
    group.add_argument("--debug", action="store_true",
                       help="let the game play itself and log every event to a text file")
    group.add_argument("--no-bot", action="store_true",
                       help="with --debug, log only and play yourself")
    group.add_argument("--reaction", type=float, default=0.3, metavar="SECONDS",
                       help="bot reaction time at normal speed, 0 to 1.1 (default 0.3)")
    group.add_argument("--fail", choices=[f.value for f in Failure], default="none",
                       help="how the bot fails on purpose (default none)")
    group.add_argument("--fail-every", type=int, default=10, metavar="N",
                       help="the bot fails on every Nth turn (default 10)")
    group.add_argument("--seed", type=int, default=None, help="fixed random seed")


def from_arguments(args: argparse.Namespace) -> DebugOptions | None:
    if not args.debug:
        return None
    return DebugOptions(bot=not args.no_bot, reaction=args.reaction, failure=Failure(args.fail),
                        fail_every=max(1, args.fail_every), seed=args.seed)
