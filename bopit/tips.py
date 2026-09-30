"""End screen gameplay tips (TextTipDisplayer)."""

import random

# Verbatim from the binary, in the original's order. Which ones this port shows is
# decided in docs/DEVIATIONS.md.
ALL_TIPS = (
    "Bop Tip: Want more challenge? Try the SFX mode! Turn it on in Options>Settings",
    "Bop Tip: Trouble with X-Moves? Try doing the move with a little more oomf!",
    "Bop Tip: Trouble with X-Moves? Try holding the device flat, like it’s on a table",
    "Bop Tip: Playing in a noisy environment? Try Silent Mode. Turn it on in Options>Settings",
    "Bop Tip: Want to unlock BopJects? Play the Solo Basic game and unlock as you progress",
    "Bop Tip: Trouble with a BopJect? Try doing the finger gesture directly on top of it",
    "Bop Tip: Need help with the BopJects? Go to Options>Help>Tutorials",
    "Bop Tip: Want Trophies? Go to Games>Trophies to see what you’ve earned",
    "Bop Tip: Get a good score? Tap Submit Score to post it on your Facebook wall",
    "Bop Tip: Friendly competition? Tap Submit Score to post your score to the leaderboard",
    "Bop Tip: Bop It! XT is the newest handheld Bop It game from Hasbro. Get it at your local retailer!",
    "Bop Tip: Got an iPad? Get Bop It! HD and try the All Play game with family or friends",
)
# The tips this port shows, in the original's order (see docs/DEVIATIONS.md): touch and
# phone tips rewritten for the keyboard and microphone, the Facebook and leaderboard tips
# removed, and the Tutorials tip left out until tutorials exist.
PORT_TIPS = (
    ALL_TIPS[0],
    ALL_TIPS[1],
    "Bop Tip: Trouble with X-Moves? Shout it loud and close to your microphone",
    "Bop Tip: Playing in a noisy environment? Turn the Microphone off in Options>Settings",
    ALL_TIPS[4],
    "Bop Tip: Trouble with a BopJect? Wait for the command to finish, then press its key",
    ALL_TIPS[7],
    ALL_TIPS[10],
    ALL_TIPS[11],
)
# TextTipDisplayer::canDisplayTipNow: a tip is shown only when a random 0 to 99 is under 26.
TIP_CHANCE = 26


class Tips:
    """Lives for the whole session, as the original's shared TextTipDisplayer did."""

    def __init__(self, tips: tuple[str, ...], rng: random.Random | None = None) -> None:
        self._tips = list(tips)
        self._unused = len(self._tips)
        self._rng = rng or random.Random()

    def maybe_tip(self) -> str | None:
        """getRandomTip: usually nothing; otherwise a tip not shown since the list was used up."""
        if not self._tips or self._rng.randrange(100) >= TIP_CHANCE:
            return None
        index = self._rng.randrange(self._unused)
        tip = self._tips[index]
        last = self._unused - 1
        self._tips[index], self._tips[last] = self._tips[last], self._tips[index]
        self._unused -= 1
        if self._unused < 1:
            self._unused = len(self._tips)
        return tip
