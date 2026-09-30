"""Trophies, as the original's TrophyManager built and checked them.

The list order is the original's: the nine BopJect unlocks, then moves in a game, X-Moves in
a game, lifetime moves per command, then Blitz times. See docs/ORIGINAL_BEHAVIOR.md.
"""

from dataclasses import dataclass

from bopit.engine.commands import all_commands
from bopit.progress import UNLOCK_MESSAGES

# TrophyManager::setUpBopjectUnlockedTrophies, in its order, with medals.
UNLOCK_TROPHIES = (("Spin", "bronze"), ("Flick", "bronze"), ("Shout", "bronze"),
                   ("Squeeze", "silver"), ("Crank", "silver"), ("Shake", "silver"),
                   ("Nail", "gold"), ("Brush", "gold"), ("Poke", "gold"))
# Command pastTenseName values (Command_*::init).
PLURALS = {"Bop": "Bops", "Twist": "Twists", "Pull": "Pulls", "Spin": "Spins",
           "Flick": "Flicks", "Shout": "Shouts", "Squeeze": "Squeezes", "Crank": "Cranks",
           "Shake": "Shakes", "Nail": "Nails", "Brush": "Brushes", "Poke": "Pokes"}


@dataclass(frozen=True)
class Trophy:
    title: str
    medal: str
    kind: str          # unlock, moves, x_moves, lifetime, blitz
    target: float = 0
    command: str | None = None


def all_trophies(shout_it: bool) -> list[Trophy]:
    """TrophyManager::loadTrophies. Shout's lifetime trophies exist only while Shout It is on,
    because they are built from the command list."""
    trophies = [Trophy(UNLOCK_MESSAGES[c], medal, "unlock", command=c) for c, medal in UNLOCK_TROPHIES]
    for target, medal in ((50, "bronze"), (100, "silver"), (200, "gold")):
        trophies.append(Trophy(f"Got to {target}!", medal, "moves", target))
    for target, medal, title in ((10, "bronze", "Did 10 X-Moves"), (25, "silver", "Did 25 X-Moves!"),
                                 (50, "silver", "Did 50 X-Moves!!"), (100, "gold", "Did 100 X-Moves!!!")):
        trophies.append(Trophy(title, medal, "x_moves", target))
    for command in all_commands(shout_it):
        plural = PLURALS[command]
        trophies.append(Trophy(f"100 {plural}", "silver", "lifetime", 100, command))
        # The original's format string was "500 %@!!".
        trophies.append(Trophy(f"500 {plural}!!", "gold", "lifetime", 500, command))
    for target, medal in ((25, "gold"), (30, "silver"), (35, "bronze")):
        trophies.append(Trophy(f"Blitzed It under {target}s", medal, "blitz", target))
    return trophies


def newly_earned(trophies: list[Trophy], earned: set[str], moves: int, x_moves: int,
                 hits: dict[str, int], blitz_time: float | None = None) -> list[Trophy]:
    """The checkForSuccess of every trophy not yet earned. Unlock trophies are earned when
    the command unlocks, not here."""
    found = []
    for trophy in trophies:
        if trophy.title in earned:
            continue
        if trophy.kind == "moves":
            hit = moves >= trophy.target
        elif trophy.kind == "x_moves":
            hit = x_moves >= trophy.target
        elif trophy.kind == "lifetime":
            hit = hits.get(trophy.command or "", 0) >= trophy.target
        elif trophy.kind == "blitz":
            # BlitzTimeTrophyBase: only a finished Blitz (more than 19 moves) with a real time.
            hit = (blitz_time is not None and blitz_time != 0 and moves > 19
                   and blitz_time <= trophy.target)
        else:
            hit = False
        if hit:
            found.append(trophy)
    return found
